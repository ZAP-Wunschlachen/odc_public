"""Triangulated cervical fitting preserves anatomy and rejects unsafe changes."""
import importlib
import math
import sys
from pathlib import Path

import bpy
import addon_utils
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
m = importlib.import_module(f'{ROOT.name}.Operators.dundee_cervical')
scene = bpy.context.scene


def shell(name, count=37):
    vertices, faces = [], []
    levels = ((3., 0.), (3.035, .24), (3.11, .55), (3.17, .95),
              (3.15, 1.4), (3., 1.9), (2.75, 2.5), (2.2, 3.2), (1.35, 3.8))
    for j, (radius, z) in enumerate(levels):
        for i in range(count):
            angle = 2*math.pi*(i + .13*math.sin(j))/count
            vertices.append((radius*math.cos(angle), .88*radius*math.sin(angle),
                             z + .06*math.cos(3*angle)*(1-j/len(levels))))
            if j:
                a, b, c, d = (j-1)*count+i, (j-1)*count+(i+1)%count, j*count+(i+1)%count, j*count+i
                faces.extend(((a, b, d), (b, c, d)))
    tip = len(vertices)
    vertices.append((.1, 0., 4.1))
    for i in range(count):
        faces.append(((len(levels)-1)*count+i, (len(levels)-1)*count+(i+1)%count, tip))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj['odc_library'] = 'dundee'
    obj['odc_topology'] = 'triangulated_crown'
    cej = obj.vertex_groups.new(name='CEJ')
    cej.add(list(range(count)), 1., 'REPLACE')
    blend = obj.vertex_groups.new(name='CervicalBlend')
    protected = obj.vertex_groups.new(name='AnatomyProtected')
    for v in mesh.vertices:
        j = v.index//count
        t = min(1., max(0., j/4))
        weight = 1-t*t*t*(10-15*t+6*t*t)
        if weight:
            blend.add([v.index], weight, 'REPLACE')
        else:
            protected.add([v.index], 1., 'REPLACE')
    return obj


obj = shell('Triangulated test crown')
tooth = scene.odc_teeth.add()
tooth.name = '25'
tooth.contour = tooth.restoration = obj.name
axis = bpy.data.objects.new('Insertion axis', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
# Exercise real transforms; local crown axes need not align to world axes.
obj.matrix_world = Matrix.Translation((2., 3., 4.)) @ Matrix.Rotation(.27, 4, 'Y')
axis.matrix_world = obj.matrix_world.copy()
target_points = []
count = 83
for i in range(count):
    angle = 2*math.pi*i/count
    local = (2.94*math.cos(angle)+.06, 2.60*math.sin(angle)-.03,
             -.1+.06*math.cos(3*angle))
    target_points.append(local)
mesh = bpy.data.meshes.new('Accepted margin')
mesh.from_pydata(target_points, [(i, (i+1)%count) for i in range(count)], [])
margin = bpy.data.objects.new('Accepted margin', mesh)
scene.collection.objects.link(margin)
margin.matrix_world = obj.matrix_world.copy()
tooth.margin = margin.name
tooth.pmargin = margin.name
bpy.context.view_layer.update()
before = m._positions(obj.data)
protected = m._weights(obj, 'AnatomyProtected') > .5
boundary = m._boundary(obj.data)
assert obj.vertex_groups.get('Equator') is None
assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}
after = m._positions(obj.data)
assert np.array_equal(after[protected], before[protected])
nearest, _, _ = m._closest_loop(after[boundary], np.array(target_points))
assert np.max(np.linalg.norm(after[boundary]-nearest, axis=1)) < 1.e-5
assert min(np.linalg.norm(np.roll(after[boundary], -1, axis=0)-after[boundary], axis=1)) > .1
assert not obj.modifiers, 'No unchecked nearest-vertex shrinkwrap may alter the dense boundary'
assert not m._self_intersections(after, m._mesh_arrays(obj.data)[1])
# Repeat seating must keep already seated boundary and protected anatomy stable.
assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}
assert np.max(np.linalg.norm(m._positions(obj.data)-after, axis=1)) < 1.e-4

pre_convergence = m._positions(obj.data)
for angle in (.12, .2):
    assert bpy.ops.opendental.cervical_convergence(ang=angle) == {'FINISHED'}
    points = m._positions(obj.data)
    assert np.array_equal(points[boundary], pre_convergence[boundary])
    assert np.array_equal(points[protected], before[protected])
    assert not m._self_intersections(points, m._mesh_arrays(obj.data)[1])
    assert bpy.ops.opendental.cervical_convergence(ang=angle) == {'FINISHED'}
    assert np.max(np.abs(m._positions(obj.data)-points)) < 1.e-6

# A remote margin is rejected before any mesh/group mutation.
snapshot = m._positions(obj.data)
margin.location.x += 30
bpy.context.view_layer.update()
assert bpy.ops.opendental.seat_to_margin() == {'CANCELLED'}
assert np.array_equal(snapshot, m._positions(obj.data))
margin.location.x -= 30
bpy.context.view_layer.update()
assert bpy.ops.opendental.cervical_convergence(ang=math.pi/2) == {'CANCELLED'}
assert np.array_equal(snapshot, m._positions(obj.data))

# Exact CEJ contract and additional openings must not reach the legacy walker.
obj.vertex_groups['CEJ'].remove([int(boundary[0])])
assert bpy.ops.opendental.seat_to_margin() == {'CANCELLED'}
assert np.array_equal(snapshot, m._positions(obj.data))
obj.vertex_groups['CEJ'].add([int(boundary[0])], 1., 'REPLACE')
bad = snapshot.copy()
bad[boundary[:3]] = bad[boundary[0]]
try:
    m._check_proposal(snapshot, bad, m._mesh_arrays(obj.data)[1], protected)
except ValueError:
    pass
else:
    raise AssertionError('Triangle collapse must be rejected')
assert np.array_equal(snapshot, m._positions(obj.data))

# Solid construction must not discard a fixed number of dense triangle rows.
# Use different boundary counts on outer and inner surfaces.
outer = shell('Assembly outer', count=43)
inside = shell('Assembly inner', count=61)
source_metadata = {'Source URL': 'https://example.invalid/synthetic-fixture',
                   'License': 'CC BY 4.0', 'License URL': 'https://creativecommons.org/licenses/by/4.0/',
                   'Author': 'Synthetic test fixture', 'Source SHA256': 'fixture-only',
                   'Source filename': 'synthetic', 'FDI': '25', 'Mirrored from FDI': '15',
                   'Source identification review': 'Fixture identification note must survive'}
for key, value in source_metadata.items():
    outer[key] = value
for v in inside.data.vertices:
    v.co.x *= .82
    v.co.y *= .82
    v.co.z = .82*v.co.z+.1
inside.data.update()
tooth.contour = tooth.restoration = outer.name
tooth.intaglio = inside.name
outer_before = m._positions(outer.data)
inner_before = m._positions(inside.data)
import bmesh
for method in (0, 1):
    assert bpy.ops.opendental.make_solid_restoration(method=method) == {'FINISHED'}
    solid = bpy.data.objects[tooth.solid]
    points, faces, _ = m._mesh_arrays(solid.data)
    assert not m._self_intersections(points, faces)
    bm = bmesh.new()
    bm.from_mesh(solid.data)
    assert all(e.is_manifold for e in bm.edges)
    assert bm.calc_volume(signed=True) > 0
    assert len(bm.verts)-len(bm.edges)+len(bm.faces) == 2
    bm.free()
    assert np.array_equal(m._positions(outer.data), outer_before)
    assert np.array_equal(m._positions(inside.data), inner_before)
    assert len([o for o in scene.objects if o.get('odc_topology') == 'closed_restoration']) == 1
    assert solid['odc_join_collar_mm'] == .15
    assert all(solid.get(key) == value for key, value in source_metadata.items())

# Intersecting input is rejected, and the last successful solid is retained.
previous = tooth.solid
object_count = len(bpy.data.objects)
inside.location.x += 3
bpy.context.view_layer.update()
assert bpy.ops.opendental.make_solid_restoration() == {'CANCELLED'}
assert tooth.solid == previous and len(bpy.data.objects) == object_count
print('ODC_DUNDEE_CERVICAL_PASSED', bpy.app.version_string)
