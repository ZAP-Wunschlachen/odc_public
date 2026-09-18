"""Conservative cervical editing of prepared, triangulated crown templates.

This module edits a validated outer shell, never a clinical cement-space profile.
It leaves protected anatomy unchanged and commits only after geometric checks.
"""
import hashlib
import heapq
import math

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def is_dundee(obj):
    return (obj is not None and obj.get('odc_library') == 'dundee'
            and obj.get('odc_topology') == 'triangulated_crown')


def _positions(mesh):
    result = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', result)
    return result.reshape((-1, 3))


def _weights(obj, name):
    group = obj.vertex_groups.get(name)
    if group is None:
        raise ValueError('Dundee crown is missing the prepared %s group' % name)
    return np.array([next((g.weight for g in v.groups if g.group == group.index), 0.)
                     for v in obj.data.vertices], dtype=float)


def ordered_loop(edges):
    """Return one simple closed loop; reject branches and additional loops."""
    neighbors = {}
    for a, b in edges:
        neighbors.setdefault(a, []).append(b)
        neighbors.setdefault(b, []).append(a)
    if len(neighbors) < 3 or any(len(v) != 2 for v in neighbors.values()):
        raise ValueError('A single closed, unbranched cervical/margin loop is required')
    start = min(neighbors)
    result, previous, current = [start], start, min(neighbors[start])
    while current != start:
        if current in result:
            raise ValueError('The cervical/margin loop repeats a vertex')
        result.append(current)
        following = next(n for n in neighbors[current] if n != previous)
        previous, current = current, following
    if len(result) != len(neighbors):
        raise ValueError('Additional holes or disconnected margin loops were found')
    return np.array(result, dtype=int)


def _mesh_arrays(mesh):
    mesh.calc_loop_triangles()
    points = _positions(mesh)
    faces = np.array([tuple(t.vertices) for t in mesh.loop_triangles], dtype=int)
    edges = np.array([tuple(e.vertices) for e in mesh.edges], dtype=int)
    return points, faces, edges


def _boundary(mesh, check_winding=True):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        if any(not e.is_manifold and not e.is_boundary for e in bm.edges):
            raise ValueError('The crown contains nonmanifold or loose edges')
        if check_winding and any(e.is_manifold and not e.is_contiguous for e in bm.edges):
            raise ValueError('Correct inconsistent crown face winding before fitting')
        if any(not v.link_faces for v in bm.verts):
            raise ValueError('The crown contains loose vertices')
        loop = ordered_loop([(e.verts[0].index, e.verts[1].index)
                             for e in bm.edges if e.is_boundary])
        seen, pending = set(), [bm.verts[0]]
        while pending:
            vertex = pending.pop()
            if vertex.index in seen:
                continue
            seen.add(vertex.index)
            pending.extend(e.other_vert(vertex) for e in vertex.link_edges)
        if len(seen) != len(bm.verts):
            raise ValueError('The crown must be one connected shell')
        return loop
    finally:
        bm.free()


def _validate_contract(obj):
    if obj.type != 'MESH' or not obj.data.vertices or obj.mode != 'OBJECT':
        raise ValueError('Use an object-mode prepared Dundee mesh')
    if obj.data.shape_keys is not None:
        raise ValueError('Apply or remove shape keys before cervical fitting')
    if any(m.show_viewport for m in obj.modifiers):
        raise ValueError('Apply or disable live modifiers before cervical fitting')
    if obj.matrix_world.to_3x3().determinant() <= 0:
        raise ValueError('Apply mirrored transforms and correct normals before fitting')
    points, faces, edges = _mesh_arrays(obj.data)
    boundary = _boundary(obj.data)
    cej = _weights(obj, 'CEJ')
    blend = _weights(obj, 'CervicalBlend')
    protected = _weights(obj, 'AnatomyProtected') > .5
    if set(np.flatnonzero(cej > .5)) != set(boundary):
        raise ValueError('CEJ must identify exactly the only open crown boundary')
    if not np.all(blend[boundary] > .999) or np.any(protected[boundary]):
        raise ValueError('CEJ requires full CervicalBlend and no protected vertices')
    if not np.any(protected) or np.any(blend[protected] > 1.e-6):
        raise ValueError('Protected anatomy must exist and have zero CervicalBlend')
    if not np.all(np.isfinite(points)) or not np.all(np.isfinite(blend)):
        raise ValueError('Crown coordinates/weights must be finite')
    if np.any(blend < 0) or np.any(blend > 1):
        raise ValueError('CervicalBlend weights must be in [0, 1]')
    return points, faces, edges, boundary, blend, protected


def _curve_parameters(points):
    lengths = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    if np.min(lengths) < 1.e-7:
        raise ValueError('The cervical/margin loop contains coincident vertices')
    distances = np.r_[0., np.cumsum(lengths)]
    return distances / distances[-1]


def _sample_loop(points, parameters, samples):
    closed = np.vstack([points, points[0]])
    return np.column_stack([np.interp(np.mod(samples, 1.), parameters, closed[:, k])
                            for k in range(3)])


def _match_loop(source, target):
    """Ordered arclength correspondence, including target start/winding search."""
    if len(source) == len(target):
        # Preserve exact sample correspondence when a margin is a transformed
        # copy of the same loop. This also preserves tiny clipped CEJ segments.
        choices = []
        for direction in (target, target[::-1]):
            for shift in range(len(target)):
                points = np.roll(direction, shift, axis=0)
                choices.append((float(np.sum((points-source)**2)), direction, shift))
        _, direction, shift = min(choices, key=lambda item: item[0])
        return np.roll(direction, shift, axis=0).copy()
    source_t = _curve_parameters(source)[:-1]
    target_t = _curve_parameters(target)
    best = None
    for direction in (1, -1):
        def candidate(phase):
            points = _sample_loop(target, target_t, phase + direction * source_t)
            return float(np.mean(np.sum((points-source)**2, axis=1))), points
        count = 128
        errors = [candidate(i/count)[0] for i in range(count)]
        index = int(np.argmin(errors))
        lo, hi = (index-1)/count, (index+1)/count
        for _ in range(28):
            left, right = (2*lo+hi)/3, (lo+2*hi)/3
            if candidate(left)[0] < candidate(right)[0]:
                hi = right
            else:
                lo = left
        error, result = candidate((lo+hi)/2)
        if best is None or error < best[0]:
            best = error, result
    return best[1]


def _closest_loop(points, boundary):
    """Closest points on all 3-D CEJ segments, in bounded memory chunks."""
    vectors = np.roll(boundary, -1, axis=0)-boundary
    lengths = np.sum(vectors*vectors, axis=1)
    results, segments, fractions = [], [], []
    for chunk in np.array_split(points, max(1, math.ceil(len(points)/512))):
        delta = chunk[:, None, :]-boundary[None, :, :]
        t = np.clip(np.sum(delta*vectors[None, :, :], axis=2)/lengths, 0., 1.)
        projected = boundary[None, :, :]+t[:, :, None]*vectors[None, :, :]
        which = np.argmin(np.sum((chunk[:, None, :]-projected)**2, axis=2), axis=1)
        row = np.arange(len(chunk))
        results.append(projected[row, which])
        segments.append(which)
        fractions.append(t[row, which])
    return np.vstack(results), np.concatenate(segments), np.concatenate(fractions)


def _deform_field(points, edges, boundary, boundary_displacements, blend):
    """A weighted cervical field, smoothing displacement rather than anatomy."""
    # Reproduce the affine part exactly. Smoothing an affine movement directly
    # on an irregular triangle graph can crease extremely small CEJ triangles.
    design = np.column_stack([points, np.ones(len(points))])
    affine, _, _, _ = np.linalg.lstsq(design[boundary], boundary_displacements, rcond=1.e-8)
    affine_field = design @ affine
    residual = boundary_displacements-affine_field[boundary]
    _, segments, t = _closest_loop(points, points[boundary])
    field = ((1-t[:, None])*residual[segments]
             + t[:, None]*residual[(segments+1) % len(boundary)])
    # Smooth only the displacement field to remove nearest-segment transitions.
    # Fixed CEJ values retain the exact requested boundary; zero blend protects
    # anatomy and the pre-authored smooth falloff prevents a hard upper seam.
    degree = np.bincount(edges.ravel(), minlength=len(points))
    field[boundary] = residual
    for _ in range(24):
        neighbor_sum = np.zeros_like(field)
        np.add.at(neighbor_sum, edges[:, 0], field[edges[:, 1]])
        np.add.at(neighbor_sum, edges[:, 1], field[edges[:, 0]])
        field = .65*field + .35*neighbor_sum/degree[:, None]
        field[boundary] = residual
    return (field+affine_field) * blend[:, None]


def _triangle_normals(points, faces):
    triangles = points[faces]
    normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    areas = np.linalg.norm(normals, axis=1)
    return normals / np.maximum(areas[:, None], 1.e-30), areas


def _self_intersections(points, faces):
    tree = BVHTree.FromPolygons(points.tolist(), faces.tolist(), all_triangles=True)
    sets = [set(f) for f in faces]
    return [(a, b) for a, b in tree.overlap(tree)
            if a < b and sets[a].isdisjoint(sets[b])]


def _check_proposal(before, after, faces, protected):
    if not np.all(np.isfinite(after)):
        raise ValueError('Cervical fitting produced non-finite geometry; no change was applied')
    if not np.array_equal(before[protected], after[protected]):
        raise ValueError('Cervical fitting would alter protected anatomy')
    old_normals, old_area = _triangle_normals(before, faces)
    new_normals, new_area = _triangle_normals(after, faces)
    if np.any(old_area < 1.e-12):
        raise ValueError('Repair degenerate source triangles before fitting')
    if np.any(new_area < .1*old_area):
        ratio = float(np.min(new_area/old_area))
        raise ValueError('The requested fit collapses cervical triangles (area ratio %.4f); pre-position the crown' % ratio)
    changed = np.max(np.linalg.norm((after-before)[faces], axis=2), axis=1) > 1.e-7
    normal_dot = np.sum(old_normals[changed]*new_normals[changed], axis=1)
    if np.any(normal_dot < math.cos(math.radians(75))):
        angle = math.degrees(math.acos(float(np.clip(np.min(normal_dot), -1., 1.))))
        raise ValueError('The requested fit folds the cervical surface (%.1f degree face rotation); pre-position the crown' % angle)
    edge_faces = {}
    for fi, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            edge_faces.setdefault(tuple(sorted((int(a), int(b)))), []).append(fi)
    pairs = np.array([pair for pair in edge_faces.values() if len(pair) == 2], dtype=int)
    if len(pairs):
        a, b = pairs.T
        new_angle = np.arccos(np.clip(np.sum(new_normals[a]*new_normals[b], axis=1), -1., 1.))
        old_angle = np.arccos(np.clip(np.sum(old_normals[a]*old_normals[b], axis=1), -1., 1.))
        bad = (changed[a] | changed[b]) & (new_angle > math.radians(70)) & (new_angle-old_angle > math.radians(30))
        if np.any(bad):
            i = int(np.flatnonzero(bad)[np.argmax((new_angle-old_angle)[bad])])
            raise ValueError('The requested fit introduces a %.1f degree cervical crease (previously %.1f)' %
                             (math.degrees(new_angle[i]), math.degrees(old_angle[i])))
    if _self_intersections(after, faces):
        raise ValueError('Cervical fitting intersects the crown surface; no change was applied')


def _commit(obj, points):
    obj.data.vertices.foreach_set('co', points.ravel())
    obj.data.update()


def seat(context, tooth, influence=1.):
    obj = bpy.data.objects[tooth.contour]
    before, faces, edges, boundary, blend, protected = _validate_contract(obj)
    margin = bpy.data.objects[tooth.margin]
    if margin.type != 'MESH':
        raise ValueError('Accept the margin as a mesh loop before seating the crown')
    loop = ordered_loop([tuple(e.vertices) for e in margin.data.edges])
    transform = obj.matrix_world.inverted() @ margin.matrix_world
    target = np.array([transform @ margin.data.vertices[int(i)].co for i in loop])
    nearest, _, _ = _closest_loop(before[boundary], target)
    # Once all existing points lie on this polyline, keep their correspondence.
    # Reparameterizing a sampled curved loop repeatedly would otherwise creep.
    if np.max(np.linalg.norm(nearest-before[boundary], axis=1)) < 1.e-6:
        matched = before[boundary].copy()
    else:
        matched = _match_loop(before[boundary], target)
    delta = matched-before[boundary]
    if np.max(np.linalg.norm(delta, axis=1)) > .4*np.max(np.ptp(before, axis=0)):
        raise ValueError('The crown is too far from the margin; position/scale it before seating')
    # Authored blend weights encode the safe editable band. Influence adjusts
    # its falloff only and never exposes protected points to deformation.
    blend = blend**(1./max(.1, min(float(influence), 2.)))
    proposed = before + _deform_field(before, edges, boundary, delta, blend)
    proposed[boundary] = matched
    proposed[protected] = before[protected]
    _check_proposal(before, proposed, faces, protected)
    _commit(obj, proposed)
    group = obj.vertex_groups.get(tooth.margin) or obj.vertex_groups.new(name=tooth.margin)
    group.remove(list(range(len(before))))
    group.add(boundary.tolist(), 1., 'REPLACE')
    obj['odc_seating_method'] = 'ordered_polyline_cervical_field_v1'
    obj['odc_seating_max_displacement_mm'] = float(np.max(np.linalg.norm(proposed-before, axis=1)))
    # No nearest-vertex Final Seal modifier: it could collapse this denser loop.
    if 'odc_convergence_result_hash' in obj:
        del obj['odc_convergence_result_hash']
    return [boundary.tolist()]


def _hash(points):
    return hashlib.sha256(np.asarray(points, dtype=np.float32).tobytes()).hexdigest()


def converge(context, tooth, angle):
    if not math.isfinite(angle) or angle < 0 or angle > math.radians(45):
        raise ValueError('Prepared Dundee cervical convergence supports 0 to 45 degrees')
    obj = bpy.data.objects[tooth.contour]
    current, faces, edges, boundary, blend, protected = _validate_contract(obj)
    name = 'odc_cervical_reference'
    attribute = obj.data.attributes.get(name)
    before = current.copy()
    if (attribute is not None and attribute.domain == 'POINT' and attribute.data_type == 'FLOAT_VECTOR'
            and obj.get('odc_convergence_result_hash') == _hash(current)):
        attribute.data.foreach_get('vector', before.ravel())
    axis = bpy.data.objects[tooth.axis]
    z = np.array((axis.matrix_world.to_quaternion() @ Vector((0, 0, 1))).normalized())
    # Compute the requested angle in world space, including existing nonuniform
    # patient-fit scales. Convert back before restoring exact protected points.
    world = np.array([obj.matrix_world @ Vector(p) for p in before])
    nearest, _, _ = _closest_loop(world, world[boundary])
    height = np.sum((world-nearest)*z, axis=1)
    center = np.mean(world[boundary], axis=0)
    radial = nearest-center
    radial -= np.sum(radial*z, axis=1)[:, None]*z
    radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1.e-20)
    # Change the radial rise only. Tangential components along a scalloped CEJ
    # must survive; projecting them away collapses irregular cut triangles.
    radial_rise = np.sum((world-nearest)*radial, axis=1)
    delta = (height*math.tan(angle)-radial_rise)[:, None]*radial
    proposed_world = world + delta*blend[:, None]
    inverse = obj.matrix_world.inverted()
    proposed = np.array([inverse @ Vector(p) for p in proposed_world])
    proposed[blend == 0.] = before[blend == 0.]
    proposed[boundary] = before[boundary]
    proposed[protected] = before[protected]
    _check_proposal(current, proposed, faces, protected)
    _commit(obj, proposed)
    if attribute is None:
        attribute = obj.data.attributes.new(name, 'FLOAT_VECTOR', 'POINT')
    attribute.data.foreach_set('vector', before.ravel())
    obj['odc_convergence_result_hash'] = _hash(_positions(obj.data))
    obj['odc_cervical_angle_degrees'] = math.degrees(angle)
    obj['odc_convergence_method'] = 'boundary_anchored_blended_field_v1'
    return True


def _clip_collar(points, faces, boundary, transform, width):
    """Clip a metric geodesic collar, preserving all surviving source faces."""
    edges = {tuple(sorted((int(a), int(b)))) for face in faces
             for a, b in zip(face, np.roll(face, -1))}
    world = np.array([transform @ Vector(p) for p in points])
    adjacency = [[] for _ in points]
    for a, b in edges:
        length = float(np.linalg.norm(world[a]-world[b]))
        adjacency[a].append((b, length))
        adjacency[b].append((a, length))
    distances = np.full(len(points), np.inf)
    pending = []
    for i in boundary:
        distances[i] = 0.
        heapq.heappush(pending, (0., int(i)))
    while pending:
        distance, i = heapq.heappop(pending)
        if distance != distances[i]:
            continue
        for j, length in adjacency[i]:
            candidate = distance+length
            if candidate < distances[j]:
                distances[j] = candidate
                heapq.heappush(pending, (candidate, j))
    if not np.isfinite(distances).all() or distances.max() < 4*width:
        raise ValueError('The crown is too small or disconnected for the metric cervical join')
    new_points, new_faces, originals, intersections = [], [], {}, {}
    def original(i):
        if i not in originals:
            originals[i] = len(new_points)
            new_points.append(points[i])
        return originals[i]
    def crossing(a, b):
        key = tuple(sorted((a, b)))
        if key not in intersections:
            fraction = (width-distances[a])/(distances[b]-distances[a])
            intersections[key] = len(new_points)
            new_points.append(points[a]+fraction*(points[b]-points[a]))
        return intersections[key]
    for face in faces:
        clipped = []
        for a, b in zip(face, np.roll(face, -1)):
            inside_a, inside_b = distances[a] >= width, distances[b] >= width
            if inside_a:
                clipped.append(original(int(a)))
            if inside_a != inside_b:
                clipped.append(crossing(int(a), int(b)))
        for i in range(1, len(clipped)-1):
            new_faces.append((clipped[0], clipped[i], clipped[i+1]))
    return np.array(new_points), np.array(new_faces, dtype=int)


def _array_boundary(points, faces):
    counts = {}
    for face in faces:
        for a, b in zip(face, np.roll(face, -1)):
            key = tuple(sorted((int(a), int(b))))
            counts[key] = counts.get(key, 0)+1
    if any(n > 2 for n in counts.values()):
        raise ValueError('Nonmanifold geometry at the proposed cervical join')
    return ordered_loop([edge for edge, count in counts.items() if count == 1])


def _zip_loops(points, outer, inner):
    """Monotone perimeter zipper; no equal vertex count or ring assumption."""
    def normal(loop):
        values = points[loop]
        return np.sum(np.cross(values, np.roll(values, -1, axis=0)), axis=0)
    if np.dot(normal(outer), normal(inner)) < 0:
        inner = inner[::-1]
    first = int(np.argmin(np.linalg.norm(points[inner]-points[outer[0]], axis=1)))
    inner = np.roll(inner, -first)
    outer_t, inner_t = _curve_parameters(points[outer]), _curve_parameters(points[inner])
    i = j = 0
    faces = []
    while i < len(outer) or j < len(inner):
        a, b = int(outer[i % len(outer)]), int(inner[j % len(inner)])
        if i < len(outer) and (j == len(inner) or outer_t[i+1] <= inner_t[j+1]):
            faces.append((a, int(outer[(i+1) % len(outer)]), b))
            i += 1
        else:
            faces.append((a, int(inner[(j+1) % len(inner)]), b))
            j += 1
    return np.array(faces, dtype=int)


def make_solid(context, tooth, collar_width=.15):
    """Join evaluated outer/inner surfaces across a metric cervical collar.

    The 0.15 mm collar replaces a topology-dependent four-row deletion. It is
    geometry for the join, not a cement gap or a material minimum thickness.
    Every output is checked as a closed surface before replacing a prior solid.
    """
    restoration = bpy.data.objects[tooth.contour]
    intaglio = bpy.data.objects[tooth.intaglio]
    if not 0 < collar_width <= .5:
        raise ValueError('Metric cervical join width must be in (0, 0.5] mm')
    arrays = []
    for obj in (restoration, intaglio):
        evaluated = obj.evaluated_get(context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            points, faces, _ = _mesh_arrays(mesh)
            # Legacy intaglio generation can contain inconsistent face winding;
            # final joined normals are recalculated without altering geometry.
            boundary = _boundary(mesh, check_winding=obj is restoration)
            transform = restoration.matrix_world.inverted() @ evaluated.matrix_world
            points = np.array([transform @ Vector(p) for p in points])
            arrays.append((points, faces, boundary))
        finally:
            evaluated.to_mesh_clear()
    outer, outer_faces, outer_boundary = arrays[0]
    inner, inner_faces, inner_boundary = arrays[1]
    outer, outer_faces = _clip_collar(outer, outer_faces, outer_boundary,
                                     restoration.matrix_world, collar_width)
    outer_boundary = _array_boundary(outer, outer_faces)
    count = len(outer)
    points = np.vstack([outer, inner])
    seam = _zip_loops(points, outer_boundary, inner_boundary+count)
    faces = np.vstack([outer_faces, inner_faces+count, seam])
    _, areas = _triangle_normals(points, faces)
    if not np.isfinite(points).all() or np.any(areas < 1.e-10):
        raise ValueError('The cervical join has collapsed faces; verify crown and inside margins')
    if _self_intersections(points, faces):
        raise ValueError('Crown and inside intersect; adjust their fit before making a solid')
    mesh = bpy.data.meshes.new(tooth.name+'_DundeeSolid')
    bm = bmesh.new()
    try:
        mesh.from_pydata(points.tolist(), [], faces.tolist())
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if not all(e.is_manifold for e in bm.edges):
            raise ValueError('The cervical join is not a closed manifold; no solid was created')
        volume = bm.calc_volume(signed=True)
        if abs(volume) < 1.e-6:
            raise ValueError('The proposed solid has no valid enclosed volume')
        if volume < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
    except Exception:
        bpy.data.meshes.remove(mesh)
        raise
    finally:
        bm.free()
    solid = bpy.data.objects.new(tooth.name+'_DundeeSolid', mesh)
    solid.matrix_world = restoration.matrix_world.copy()
    for material in restoration.data.materials:
        mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
    for name in ('odc_library', 'odc_source_url', 'odc_license', 'odc_author',
                 'Source URL', 'License', 'License URL', 'Author', 'Source SHA256',
                 'Source filename', 'FDI', 'Mirrored from FDI', 'Source identification review'):
        if name in restoration:
            solid[name] = restoration[name]
    solid['odc_topology'] = 'closed_restoration'
    solid['odc_join_collar_mm'] = collar_width
    solid['odc_join_method'] = 'metric_collar_boundary_zipper_v1'
    group = solid.vertex_groups.new(name='CEJ')
    group.add(sorted(set(seam.ravel().tolist())), 1., 'REPLACE')
    context.scene.collection.objects.link(solid)
    previous = bpy.data.objects.get(tooth.solid)
    tooth.solid = solid.name
    if previous is not None and previous not in (restoration, intaglio):
        old_mesh = previous.data if previous.type == 'MESH' else None
        bpy.data.objects.remove(previous, do_unlink=True)
        if old_mesh is not None and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    return solid


def close_pontic(obj):
    """Add a validated rounded cervical closure without touching the anatomy."""
    before, _, _, boundary, _, protected = _validate_contract(obj)
    center = np.mean(before[boundary], axis=0)
    floor_z = float(np.min(before[boundary, 2]))
    mesh = obj.data.copy()
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        previous = [bm.verts[int(i)] for i in boundary]
        # Ring heights describe a reusable pontic draft, not tissue clearance.
        for factor, depth in ((.72, .3), (.34, .6)):
            ring = []
            for point in before[boundary]:
                q = center + factor*(point-center)
                q[2] = floor_z-depth
                ring.append(bm.verts.new(q))
            for i in range(len(ring)):
                j = (i+1) % len(ring)
                bm.faces.new((previous[i], previous[j], ring[j]))
                bm.faces.new((previous[i], ring[j], ring[i]))
            previous = ring
        tip = bm.verts.new((center[0], center[1], floor_z-.72))
        for i in range(len(previous)):
            bm.faces.new((previous[i], previous[(i+1) % len(previous)], tip))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if not all(e.is_manifold for e in bm.edges):
            raise ValueError('The Dundee pontic could not be closed safely')
        if bm.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        after, faces, _ = _mesh_arrays(mesh)
        _, areas = _triangle_normals(after, faces)
        if np.any(areas < 1.e-12) or _self_intersections(after, faces):
            raise ValueError('The pontic closure intersects the crown; inspect its cervical boundary')
        if not np.array_equal(before, after[:len(before)]):
            raise ValueError('The pontic closure changed the source anatomy')
    except Exception:
        bpy.data.meshes.remove(mesh)
        raise
    finally:
        bm.free()
    old = obj.data
    obj.data = mesh
    if old.users == 0:
        bpy.data.meshes.remove(old)
    obj['odc_topology'] = 'closed_pontic'
    obj['odc_pontic_method'] = 'rounded_cervical_closure_v1'
    obj['odc_pontic_tissue_clearance'] = 'Not fitted; requires case-specific adaptation'
    group = obj.vertex_groups.get('filled_hole') or obj.vertex_groups.new(name='filled_hole')
    group.add(list(range(len(before), len(mesh.vertices))), 1., 'REPLACE')
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj
