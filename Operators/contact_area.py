"""Reversible local contact-area previews, in world-space millimetres.

The editable ellipse is a deformation region, not a promised clinical contact
area. Its target clearance is measured from the unchanged source and cannot be
lowered here. A smooth quadratic neighbour fit avoids copying scan noise.
"""
import heapq
import itertools
import json
import math

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .dundee_cervical import _mesh_arrays, _check_proposal, _self_intersections

EXTERIOR = 'ODC Exterior'
PROTECTED = 'ODC Contact Protected'
PREVIEW_TAG = 'odc_contact_area_preview'
GAP_TOLERANCE = 1.e-6  # Numerical tolerance in world-space model millimetres.


def _unit(value):
    length = np.linalg.norm(value)
    if length < 1.e-10:
        raise ValueError('Kontaktachse ist nicht eindeutig; Kontaktpunkt und Einschubachse prüfen')
    return value / length


def _weights(obj, name):
    group = obj.vertex_groups.get(name)
    if group is None:
        raise ValueError('Kontaktbereich ist nicht vorbereitet: %s fehlt' % name)
    result = np.array([next((g.weight for g in v.groups if g.group == group.index), 0.)
                       for v in obj.data.vertices])
    if not np.any(result > .5):
        raise ValueError('Kontaktbereich ist nicht vorbereitet: %s ist leer' % name)
    return result


def _world(obj):
    if obj is None or obj.type != 'MESH' or obj.mode != 'OBJECT':
        raise ValueError('Krone und Nachbarflächen müssen Meshobjekte im Objektmodus sein')
    if obj.data.shape_keys is not None or any(m.show_viewport for m in obj.modifiers):
        raise ValueError('Formschlüssel und aktive Modifier vor der Kontaktvorschau auf einer Kopie anwenden')
    if obj.matrix_world.to_3x3().determinant() <= 0:
        raise ValueError('Gespiegelte oder singuläre Objekttransformation zuerst korrigieren')
    local, faces, edges = _mesh_arrays(obj.data)
    matrix = np.array(obj.matrix_world)
    points = local @ matrix[:3, :3].T + matrix[:3, 3]
    if not len(faces) or not np.isfinite(points).all():
        raise ValueError('Leere oder ungültige Kontaktgeometrie')
    return local, points, faces, edges


def _topology(obj):
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        if any(not v.link_faces for v in bm.verts) or any(
                not e.is_manifold and not e.is_boundary for e in bm.edges):
            raise ValueError('Krone enthält lose oder nichtmannigfaltige Geometrie')
        if any(e.is_manifold and not e.is_contiguous for e in bm.edges):
            raise ValueError('Widersprüchliche Flächenausrichtung der Krone korrigieren')
        seen, pending = set(), [bm.verts[0]]
        while pending:
            v = pending.pop()
            if v.index not in seen:
                seen.add(v.index)
                pending.extend(e.other_vert(v) for e in v.link_edges)
        if len(seen) != len(bm.verts):
            raise ValueError('Kontaktvorschau benötigt eine zusammenhängende Kronenoberfläche')
        return np.array([v.index for v in bm.verts if v.is_boundary], dtype=int)
    finally:
        bm.free()


def _point_triangle_squared(p, t):
    """Vectorized point/triangle distance, including face interiors."""
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    ab, ac, ap = b-a, c-a, p-a
    normal = np.cross(ab, ac)
    nn = np.sum(normal*normal, axis=1)
    if np.any(nn < 1.e-24):
        raise ValueError('Entartete Dreiecke in der Kontaktgeometrie')
    plane = np.sum(ap*normal, axis=1)
    projected = ap - (plane/nn)[:, None]*normal
    aa, bb, cc = (np.sum(ab*ab, axis=1), np.sum(ab*ac, axis=1),
                  np.sum(ac*ac, axis=1))
    d, e = np.sum(projected*ab, axis=1), np.sum(projected*ac, axis=1)
    denominator = nn
    u, v = (cc*d-bb*e)/denominator, (aa*e-bb*d)/denominator
    result = np.where((u >= 0) & (v >= 0) & (u+v <= 1), plane*plane/nn, np.inf)
    for start, end in ((a, b), (b, c), (c, a)):
        edge = end-start
        f = np.clip(np.sum((p-start)*edge, axis=1)/np.sum(edge*edge, axis=1), 0., 1.)
        delta = p-start-f[:, None]*edge
        result = np.minimum(result, np.sum(delta*delta, axis=1))
    return result


def _segment_squared(p, q, r, s):
    """Vectorized segment/segment distance, including skew interior minima."""
    u, v, w = q-p, s-r, p-r
    a, b, c = np.sum(u*u, axis=1), np.sum(u*v, axis=1), np.sum(v*v, axis=1)
    d, e = np.sum(u*w, axis=1), np.sum(v*w, axis=1)
    denominator = a*c-b*b
    with np.errstate(divide='ignore', invalid='ignore'):
        x = np.where(denominator > 1.e-20, np.clip((b*e-c*d)/denominator, 0., 1.), 0.)
    y = (b*x+e)/c
    x = np.where(y < 0., np.clip(-d/a, 0., 1.), x)
    x = np.where(y > 1., np.clip((b-d)/a, 0., 1.), x)
    y = np.clip(y, 0., 1.)
    delta = w+x[:, None]*u-y[:, None]*v
    return np.sum(delta*delta, axis=1)


def _triangle_pair_squared(a, b):
    result = np.full(len(a), np.inf)
    for i in range(3):
        result = np.minimum(result, _point_triangle_squared(a[:, i], b))
        result = np.minimum(result, _point_triangle_squared(b[:, i], a))
        for j in range(3):
            result = np.minimum(result, _segment_squared(a[:, i], a[:, (i+1) % 3],
                                                        b[:, j], b[:, (j+1) % 3]))
    return result


class _Node:
    def __init__(self, triangles, indices):
        self.low = triangles[indices].min(axis=(0, 1))
        self.high = triangles[indices].max(axis=(0, 1))
        self.indices, self.children = indices, None
        if len(indices) > 12:
            centers = triangles[indices].mean(axis=1)
            axis = np.argmax(np.ptp(centers, axis=0))
            ordered = indices[np.argsort(centers[:, axis])]
            half = len(ordered)//2
            self.children = (_Node(triangles, ordered[:half]), _Node(triangles, ordered[half:]))


def _box_squared(a, b):
    delta = np.maximum(np.maximum(a.low-b.high, b.low-a.high), 0.)
    return float(delta @ delta)


class Surface:
    def __init__(self, points, faces):
        self.points, self.faces = points, faces
        self.triangles = points[faces]
        self.tree = BVHTree.FromPolygons(points.tolist(), faces.tolist(), all_triangles=True)
        self.root = _Node(self.triangles, np.arange(len(faces)))


def clearance(first, second):
    """Exact triangle distance after an explicit triangle-intersection check.

    AABB branch-and-bound includes edge/edge minima; vertex-only sampling is
    insufficient for an oblique triangulated neighbour or a large crown face.
    """
    if first.tree.overlap(second.tree):
        return 0.
    count = itertools.count()
    queue = [(_box_squared(first.root, second.root), next(count), first.root, second.root)]
    best = math.inf
    while queue:
        bound, _, a, b = heapq.heappop(queue)
        if bound >= best:
            continue
        if a.children is None and b.children is None:
            aa = np.repeat(first.triangles[a.indices], len(b.indices), axis=0)
            bb = np.tile(second.triangles[b.indices], (len(a.indices), 1, 1))
            best = min(best, float(_triangle_pair_squared(aa, bb).min()))
        else:
            split_a = a.children is not None and (b.children is None or len(a.indices) >= len(b.indices))
            pairs = ((child, b) for child in a.children) if split_a else ((a, child) for child in b.children)
            for c, d in pairs:
                lower = _box_squared(c, d)
                if lower < best:
                    heapq.heappush(queue, (lower, next(count), c, d))
    return math.sqrt(max(best, 0.))


def _smooth(x):
    x = np.clip(x, 0., 1.)
    return x*x*x*(10.-15.*x+6.*x*x)


def _protection_fade(points, edges, allowed, length):
    """Metric surface-distance fade into protected regions, never mesh-index rings."""
    adjacency = [[] for _ in points]
    for a, b in edges:
        distance = float(np.linalg.norm(points[a]-points[b]))
        adjacency[a].append((int(b), distance))
        adjacency[b].append((int(a), distance))
    distances = np.full(len(points), length)
    queue = []
    for i in np.flatnonzero(~allowed):
        distances[i] = 0.
        heapq.heappush(queue, (0., int(i)))
    while queue:
        distance, i = heapq.heappop(queue)
        if distance != distances[i]:
            continue
        for j, edge in adjacency[i]:
            candidate = distance+edge
            if candidate < distances[j]:
                distances[j] = candidate
                heapq.heappush(queue, (candidate, j))
    return _smooth(distances/length)


def _basis(u, v):
    return np.column_stack((np.ones_like(u), u, v, u*u, u*v, v*v))


def _fit_surface(neighbour, width, height):
    """Use the actual ellipse; rectangular corners can include turned flanks.

    Prefer a 20% support margin. If that margin cannot be represented smoothly,
    the full requested ellipse must independently pass the same quality test.
    Actual target coverage for every displaced point is checked separately.
    """
    error = 'Nachbarfläche deckt die gewünschte Breite/Höhe nicht ausreichend ab'
    radius = np.sqrt((2.*neighbour[:, 0]/width)**2+(2.*neighbour[:, 1]/height)**2)
    for support in (1.2, 1.):
        fit = neighbour[radius <= support]
        if len(fit) < 12:
            continue
        design = _basis(fit[:, 0]/width, fit[:, 1]/height)
        if np.linalg.matrix_rank(design) < 6 or np.linalg.cond(design) > 1.e5:
            error = 'Nachbarfläche lässt sich lokal nicht eindeutig glätten'
            continue
        coefficients = np.linalg.lstsq(design, fit[:, 2], rcond=None)[0]
        for _ in range(5):
            residual = fit[:, 2]-design @ coefficients
            scale = max(float(np.median(np.abs(residual-np.median(residual))))*1.4826, 1.e-6)
            weights = np.sqrt(np.minimum(1., 1.5*scale/np.maximum(np.abs(residual), 1.e-12)))
            coefficients = np.linalg.lstsq(design*weights[:, None], fit[:, 2]*weights, rcond=None)[0]
        residual = fit[:, 2]-design @ coefficients
        if np.ptp(residual) > .15*min(width, height):
            error = 'Nachbarfläche ist für eine glatte lokale Kontaktvorschau zu unregelmäßig'
            continue
        return coefficients, residual, support
    raise ValueError(error)


def _field(points, faces, edges, allowed, seeds, axis, target, width, height, gap):
    if not math.isfinite(width+height) or min(width, height) <= 0:
        raise ValueError('Breite und Höhe des gewünschten Kontaktbereichs müssen größer als null sein')
    center = np.average(points[seeds > .5], axis=0, weights=seeds[seeds > .5])
    nearest, _, _, distance = target.tree.find_nearest(Vector(center))
    if nearest is None or distance <= GAP_TOLERANCE:
        raise ValueError('Kontaktpunkt liegt auf oder außerhalb einer geeigneten Nachbarfläche')
    normal = _unit(np.array(nearest)-center)
    vertical = _unit(axis-normal*np.dot(axis, normal))
    horizontal = _unit(np.cross(vertical, normal))
    frame = np.column_stack((horizontal, vertical, normal))
    local = (points-center) @ frame
    neighbour = (target.points-center) @ frame
    if (neighbour[:, 0].min() > -.5*width or neighbour[:, 0].max() < .5*width
            or neighbour[:, 1].min() > -.5*height or neighbour[:, 1].max() < .5*height):
        raise ValueError('Nachbarfläche deckt die gewünschte Breite/Höhe nicht ausreichend ab')
    # Fit a local single-valued surface with robust residual weights. Its
    # conservative lower envelope is offset by the measured starting gap.
    coefficients, residual, support = _fit_surface(neighbour, width, height)
    u, v = local[:, 0]/width, local[:, 1]/height
    surface_z = _basis(u, v) @ coefficients
    slope_u = (coefficients[1]+2.*coefficients[3]*u+coefficients[4]*v)/width
    slope_v = (coefficients[2]+coefficients[4]*u+2.*coefficients[5]*v)/height
    target_z = surface_z + min(0., float(residual.min())) - gap*np.sqrt(1.+slope_u*slope_u+slope_v*slope_v)
    radius = np.sqrt((2.*u)**2+(2.*v)**2)
    weight = 1.-_smooth((radius-.5)/.5)
    normals = np.zeros_like(points)
    tri = points[faces]
    cross = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    for i in range(3):
        np.add.at(normals, faces[:, i], cross)
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1.e-20)
    weight *= _smooth((normals @ normal-.1)/.4)
    weight *= _protection_fade(points, edges, allowed, .25*min(width, height))
    weight[~allowed] = 0.
    advance = np.maximum(target_z-local[:, 2], 0.)*weight
    active = advance > 1.e-9
    # Refuse extrapolation past scan boundaries. Projection is only a coverage
    # test; the proposed surface itself remains the smooth fitted surface.
    for p in points[active]:
        if target.tree.ray_cast(Vector(p), Vector(normal))[0] is None:
            raise ValueError('Kontaktbereich reicht über den Rand des Nachbarpatches hinaus')
    if not np.any(active):
        raise ValueError('Gewählte Fläche kann mit dem bisherigen Abstand nicht erweitert werden')
    return advance[:, None]*normal, {
        'width_mm': width, 'height_mm': height, 'original_gap_mm': gap,
        'fit_residual_range_mm': float(np.ptp(residual)),
        'fit_support_radius': support,
        'center_world': center.tolist(), 'normal_world': normal.tolist(),
        'width_axis_world': horizontal.tolist(), 'height_axis_world': vertical.tolist(),
    }


def _source(tooth):
    source = bpy.data.objects.get(tooth.restoration) or bpy.data.objects.get(tooth.contour)
    if source is None or source.get(PREVIEW_TAG):
        raise ValueError('Eine unveränderte Ausgangskrone im Zahnplan zuweisen')
    return source


def _validate_shape(before, after, faces, protected):
    try:
        _check_proposal(before, after, faces, protected)
    except ValueError as error:
        message = str(error).replace('Cervical fitting', 'Contact preview').replace('cervical', 'contact')
        raise ValueError('Kontaktvorschau verworfen: '+message) from error


def build_preview(tooth):
    """Return validated local coordinates and metrics; never mutate scene data."""
    source = _source(tooth)
    local, points, faces, edges = _world(source)
    if any(len(face.vertices) != 3 for face in source.data.polygons):
        raise ValueError('Ausgangskrone für diese Vorschau zuerst auf einer Kopie triangulieren')
    boundary = _topology(source)
    allowed = (_weights(source, EXTERIOR) > .5) & ~(_weights(source, PROTECTED) > .5)
    allowed[boundary] = False
    if _self_intersections(points, faces):
        raise ValueError('Die Ausgangskrone enthält bereits einen Selbstschnitt')
    _validate_shape(points, points, faces, ~allowed)
    axis_obj = bpy.data.objects.get(tooth.axis)
    if axis_obj is None:
        raise ValueError('Einschubachse im Zahnplan zuweisen')
    axis = _unit(np.array(axis_obj.matrix_world.to_3x3() @ Vector((0., 0., 1.))))
    original = Surface(points, faces)
    fields, metrics, targets, gaps = [], {}, [], []
    for role, group in (('mesial', 'Mesial Contact'), ('distal', 'Distal Contact')):
        if not getattr(tooth, 'contact_area_'+role):
            continue
        target_obj = bpy.data.objects.get(getattr(tooth, role))
        if target_obj is None or target_obj == source:
            raise ValueError('Separate %se Nachbarfläche im Zahnplan zuweisen' % role)
        _, target_points, target_faces, _ = _world(target_obj)
        target = Surface(target_points, target_faces)
        gap = clearance(original, target)
        if gap <= GAP_TOLERANCE:
            raise ValueError('Ausgangskrone und %ser Nachbar schneiden oder berühren sich bereits' % role)
        seeds = _weights(source, group)
        if not np.any((seeds > .5) & allowed):
            raise ValueError('%ser Kontaktpunkt liegt vollständig im geschützten Bereich' % role)
        field, info = _field(points, faces, edges, allowed, seeds, axis, target,
                             getattr(tooth, 'contact_area_'+role+'_width'),
                             getattr(tooth, 'contact_area_'+role+'_height'), gap)
        fields.append(field)
        metrics[role] = info
        targets.append(target)
        gaps.append(gap)
    if not fields:
        raise ValueError('Mesial und/oder distal für die Kontaktvorschau auswählen')
    # Existing assigned neighbours and opposing scan remain clearance
    # constraints even when their own deformation checkbox is disabled.
    constraints = []
    for role in ('mesial', 'distal', 'opposing'):
        if role in metrics:
            continue
        target_obj = bpy.data.objects.get(getattr(tooth, role))
        if target_obj is None:
            continue
        if target_obj == source:
            raise ValueError('Kontaktziel darf nicht die Ausgangskrone sein')
        _, target_points, target_faces, _ = _world(target_obj)
        target = Surface(target_points, target_faces)
        gap = clearance(original, target)
        if gap <= GAP_TOLERANCE:
            raise ValueError('Ausgangskrone berührt oder schneidet bereits das zugewiesene %s-Ziel' % role)
        constraints.append((role, target, gap))
    if len(fields) == 2 and np.any((np.linalg.norm(fields[0], axis=1) > 1.e-9) &
                                  (np.linalg.norm(fields[1], axis=1) > 1.e-9)):
        raise ValueError('Mesialer und distaler Änderungsbereich überlappen; Breite/Höhe verringern')
    displacement = np.sum(fields, axis=0)
    changed = np.linalg.norm(displacement, axis=1) > 1.e-9
    inverse = np.array(source.matrix_world.inverted())
    matrix = np.array(source.matrix_world)
    # No pointwise clipping to the scan: reduce one global smooth field instead.
    # If geometry cannot retain clearance, refuse instead of silently accepting
    # a negligible or irregular deformation.
    factor = 1.
    for _ in range(9):
        proposed_world = points+factor*displacement
        proposed = proposed_world @ inverse[:3, :3].T + inverse[:3, 3]
        proposed[~changed] = local[~changed]
        proposed = proposed.astype(np.float32).astype(np.float64)
        stored_world = proposed @ matrix[:3, :3].T + matrix[:3, 3]
        surface = Surface(stored_world, faces)
        check_targets = targets+[entry[1] for entry in constraints]
        check_gaps = gaps+[entry[2] for entry in constraints]
        measured = [clearance(surface, target) for target in check_targets]
        if all(after >= before-GAP_TOLERANCE for after, before in zip(measured, check_gaps)):
            break
        factor *= .5
    else:
        raise ValueError('Größere Kontaktfläche würde den bisherigen Abstand unterschreiten; Vorschau verworfen')
    if np.max(np.linalg.norm(factor*displacement, axis=1)) < 1.e-5:
        raise ValueError('Mit diesen Werten entsteht keine messbare Flächenerweiterung')
    _validate_shape(points, proposed_world, faces, ~changed)
    # Blender stores coordinates as float32; the line search already measured
    # these actual stored coordinates, including exact outside preservation.
    _validate_shape(points, stored_world, faces, ~changed)
    stored_surface = Surface(stored_world, faces)
    for (role, info), target, gap in zip(metrics.items(), targets, gaps):
        final_gap = clearance(stored_surface, target)
        if final_gap < gap-GAP_TOLERANCE:
            raise ValueError('Numerische Speicherung würde den bisherigen Abstand unterschreiten')
        info['preview_gap_mm'] = final_gap
        info['field_fraction'] = factor
    for role, target, gap in constraints:
        final_gap = clearance(stored_surface, target)
        if final_gap < gap-GAP_TOLERANCE:
            raise ValueError('Vorschau würde den bisherigen Abstand zum %s-Ziel unterschreiten' % role)
        metrics[role+'_constraint'] = {'original_gap_mm': gap, 'preview_gap_mm': final_gap}
    metrics['changed_vertices'] = int(changed.sum())
    metrics['max_displacement_mm'] = float(np.linalg.norm(stored_world-points, axis=1).max())
    return source, proposed, metrics


def _owned_preview(tooth):
    obj = tooth.contact_area_preview_object or bpy.data.objects.get(tooth.contact_area_preview)
    if obj is not None and not obj.get(PREVIEW_TAG):
        raise ValueError('Gespeicherte Vorschau verweist auf ein fremdes Objekt; keine Änderung vorgenommen')
    return obj


def preview(context, tooth):
    previous = _owned_preview(tooth)
    if previous is None and tooth.contact_area_source_object is not None:
        raise ValueError('Die vorige Vorschau wurde gelöscht; zuerst Zurücksetzen wählen')
    source, points, metrics = build_preview(tooth)
    if previous is not None and previous.get('odc_contact_source_object',
                                             bpy.data.objects.get(previous.get('odc_contact_source', ''))) != source:
        raise ValueError('Ausgangskrone wurde gewechselt; bestehende Vorschau zuerst zurücksetzen')
    hidden = previous.get('odc_contact_source_hidden', False) if previous else source.hide_get()
    render_hidden = previous.get('odc_contact_source_render_hidden', False) if previous else source.hide_render
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = source.name+' | Kontaktvorschau'
    obj.data.vertices.foreach_set('co', points.ravel())
    obj.data.update()
    obj[PREVIEW_TAG] = True
    obj['odc_contact_source'] = source.name
    obj['odc_contact_source_object'] = source
    obj['odc_contact_source_hidden'] = hidden
    obj['odc_contact_source_render_hidden'] = render_hidden
    obj['odc_contact_area_metrics'] = json.dumps(metrics, sort_keys=True)
    context.collection.objects.link(obj)
    obj.hide_viewport = False
    obj.hide_set(False)
    obj.hide_render = False
    if previous is not None:
        mesh = previous.data
        bpy.data.objects.remove(previous, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    source.hide_set(True)
    source.hide_render = True
    for selected in context.selected_objects:
        selected.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    tooth.contact_area_preview = obj.name
    tooth.contact_area_preview_object = obj
    tooth.contact_area_source_object = source
    tooth.contact_area_source_hidden = bool(hidden)
    tooth.contact_area_source_render_hidden = bool(render_hidden)
    for role in ('mesial', 'distal'):
        setattr(tooth, 'contact_area_'+role+'_gap', metrics.get(role, {}).get('original_gap_mm', -1.))
    tooth.contact_area_status = '%d Punkte lokal angepasst; %.3f mm maximale Änderung' % (
        metrics['changed_vertices'], metrics['max_displacement_mm'])
    fraction = min(metrics[side]['field_fraction'] for side in ('mesial', 'distal') if side in metrics)
    if fraction < 1.:
        tooth.contact_area_status += ' (%.0f%% des Feldes)' % (fraction*100.)
    return obj, metrics


def reset(context, tooth):
    obj = _owned_preview(tooth)
    source = tooth.contact_area_source_object
    if obj is not None:
        source = obj.get('odc_contact_source_object') or bpy.data.objects.get(obj.get('odc_contact_source', ''))
        if source is not None:
            source.hide_set(bool(obj.get('odc_contact_source_hidden', False)))
            source.hide_render = bool(obj.get('odc_contact_source_render_hidden', False))
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        if source is not None and not source.hide_get():
            source.select_set(True)
            context.view_layer.objects.active = source
    elif source is not None:
        source.hide_set(tooth.contact_area_source_hidden)
        source.hide_render = tooth.contact_area_source_render_hidden
        if not source.hide_get():
            source.select_set(True)
            context.view_layer.objects.active = source
    tooth.contact_area_preview = ''
    tooth.contact_area_preview_object = None
    tooth.contact_area_source_object = None
    tooth.contact_area_status = ''
    tooth.contact_area_mesial_gap = -1.
    tooth.contact_area_distal_gap = -1.
    return True
