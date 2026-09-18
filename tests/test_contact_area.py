"""Synthetic local contact previews: area, exact clearance, invariants, reset."""
import json
import math
import sys
from pathlib import Path

import addon_utils
import bpy
import bmesh
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
from odc_public.Operators import contact_area as area


def object_mesh(name, points, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def group(obj, name, ids):
    obj.vertex_groups.new(name=name).add([int(i) for i in ids], 1., 'REPLACE')


# A closed convex-ish shell, in millimetres, with two curved proximal faces.
n = 25
values = np.linspace(-3., 3., n)
front = np.array([(-.04*(y*y+z*z), y, z) for y in values for z in values])
back = front.copy()
back[:, 0] = -2.-front[:, 0]
points = np.concatenate((front, back))
faces = []
for offset, reverse in ((0, False), (n*n, True)):
    for i in range(n-1):
        for j in range(n-1):
            a, b = offset+i*n+j, offset+(i+1)*n+j
            for triangle in ((a, b, b+1), (a, b+1, a+1)):
                faces.append(tuple(reversed(triangle)) if reverse else triangle)
boundary = list(range(n)) + list(range(2*n-1, n*n, n)) + list(range(n*n-2, n*(n-1)-1, -1)) + list(range(n*(n-2), 0, -n))
for a, b in zip(boundary, boundary[1:]+boundary[:1]):
    faces.extend(((a, a+n*n, b+n*n), (a, b+n*n, b)))
crown = object_mesh('Synthetic source', points, faces)
bm = bmesh.new()
bm.from_mesh(crown.data)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(crown.data)
bm.free()
group(crown, area.EXTERIOR, range(n*n))
protected = np.flatnonzero((np.abs(points[:, 1]) > 2.4) | (np.abs(points[:, 2]) > 1.5))
group(crown, area.PROTECTED, protected)
center = (n//2)*n+n//2
group(crown, 'Mesial Contact', [center])
group(crown, 'Distal Contact', [center+n*n])
crown['License'] = 'Synthetic fixture'
target_points = [(0.04, y, z) for y in np.linspace(-4., 4., 21) for z in np.linspace(-4., 4., 21)]
target_faces = []
for i in range(20):
    for j in range(20):
        a, b = i*21+j, (i+1)*21+j
        target_faces.extend(((a, b+1, b), (a, a+1, b+1)))
target = object_mesh('Synthetic mesial', target_points, target_faces)
distal_points = np.array(target_points)
distal_points[:, 0] = -2.06
distal = object_mesh('Synthetic distal', distal_points, [tuple(reversed(f)) for f in target_faces])
axis = bpy.data.objects.new('Synthetic insertion axis', None)
bpy.context.collection.objects.link(axis)
tooth = bpy.context.scene.odc_teeth.add()
tooth.name = '25'
tooth.restoration = crown.name
tooth.mesial, tooth.distal, tooth.axis = target.name, distal.name, axis.name
tooth.contact_area_mesial = True
tooth.contact_area_mesial_width = 2.
tooth.contact_area_mesial_height = 2.
original_local = area._world(crown)[0].copy()

# Exact distance catches an edge/edge closest pair missed by vertex sampling.
a = np.array([[-2., 0., 0.], [2., 0., 0.], [0., -.2, -3.]])
b = np.array([[0., -2., .2], [0., 2., .2], [.2, 0., 3.]])
assert abs(area.clearance(area.Surface(a, np.array([[0, 1, 2]])),
                          area.Surface(b, np.array([[0, 1, 2]])))-.2) < 1.e-9

source, narrow, narrow_metrics = area.build_preview(tooth)
tooth.contact_area_mesial_width = 4.
source, wide, wide_metrics = area.build_preview(tooth)
assert wide_metrics['mesial']['preview_gap_mm'] >= .04-area.GAP_TOLERANCE
assert wide_metrics['mesial']['field_fraction'] == 1.
assert np.array_equal(wide[protected], original_local[protected])
assert np.array_equal(wide[n*n:], original_local[n*n:])  # Intaglio/other surface excluded.
assert np.array_equal(wide[np.abs(points[:, 1]) >= 2.], original_local[np.abs(points[:, 1]) >= 2.])
narrow_flat = int(np.count_nonzero(np.abs(narrow[:n*n, 0]) < .002))
wide_flat = int(np.count_nonzero(np.abs(wide[:n*n, 0]) < .002))
assert wide_flat > narrow_flat, (wide_flat, narrow_flat)
assert wide_metrics['changed_vertices'] > narrow_metrics['changed_vertices']

# Same result for nonuniformly transformed object geometry and baked world data.
rotation = Matrix.Rotation(.63, 4, 'Z') @ Matrix.Rotation(.41, 4, 'Y')
translation = Matrix.Translation((7.2, -9.1, 3.4))
world_transform = translation @ rotation
scale = Matrix.Diagonal((1.3, .8, 1.15, 1.))
crown.data.transform(scale.inverted())
crown.matrix_world = world_transform @ scale
target.matrix_world = distal.matrix_world = axis.matrix_world = world_transform
bpy.context.view_layer.update()
_, transformed, transformed_metrics = area.build_preview(tooth)
wide_world = wide @ np.array(world_transform)[:3, :3].T + np.array(world_transform)[:3, 3]
result_world = transformed @ np.array(crown.matrix_world)[:3, :3].T + np.array(crown.matrix_world)[:3, 3]
assert np.max(np.linalg.norm(wide_world-result_world, axis=1)) < 2.e-5
before = area._world(crown)[0].copy()
assert bpy.ops.opendental.contact_area_preview() == {'FINISHED'}
first = bpy.data.objects[tooth.contact_area_preview]
first_points = area._world(first)[0].copy()
first_mesh = first.data.name
assert first['License'] == 'Synthetic fixture'
assert np.array_equal(area._world(crown)[0], before)
assert tooth.restoration == crown.name
assert crown.hide_get() and crown.hide_render
assert bpy.ops.opendental.contact_area_preview() == {'FINISHED'}
second = bpy.data.objects[tooth.contact_area_preview]
assert np.array_equal(area._world(second)[0], first_points)
assert first_mesh not in bpy.data.meshes
assert len([o for o in bpy.data.objects if o.get(area.PREVIEW_TAG)]) == 1

# Invalid updates are atomic and keep the last reviewable preview intact.
previous_name = second.name
tooth.contact_area_mesial_width = 100.
assert bpy.ops.opendental.contact_area_preview() == {'CANCELLED'}
assert tooth.contact_area_preview == previous_name
assert np.array_equal(area._world(second)[0], first_points)
assert np.array_equal(area._world(crown)[0], before)
second.name = 'Renamed preview'
crown.name = 'Renamed source'
tooth.restoration = crown.name
assert bpy.ops.opendental.contact_area_reset() == {'FINISHED'}
assert not tooth.contact_area_preview and previous_name not in bpy.data.objects
assert 'Renamed preview' not in bpy.data.objects
assert not crown.hide_get() and not crown.hide_render
assert np.array_equal(area._world(crown)[0], before)
tooth.contact_area_mesial_width = 3.
preview, _ = area.preview(bpy.context, tooth)
mesh = preview.data
bpy.data.objects.remove(preview, do_unlink=True)
bpy.data.meshes.remove(mesh)
assert crown.hide_get()
assert bpy.ops.opendental.contact_area_reset() == {'FINISHED'}
assert not crown.hide_get() and not crown.hide_render

# Distal uses its world-space neighbour direction and retains its own gap.
tooth.contact_area_mesial_width = 3.
tooth.contact_area_distal = True
tooth.contact_area_distal_width = 3.
tooth.contact_area_distal_height = 2.
crown.vertex_groups[area.EXTERIOR].add(list(range(n*n, 2*n*n)), 1., 'REPLACE')
_, both, info = area.build_preview(tooth)
assert info['distal']['preview_gap_mm'] >= info['distal']['original_gap_mm']-area.GAP_TOLERANCE
assert abs(info['distal']['original_gap_mm']-.06) < 2.e-6
assert np.count_nonzero(np.linalg.norm(both[n*n:]-before[n*n:], axis=1) > 1.e-6) > 10

# A deliberately folded candidate is rejected before a preview can be written.
real_field = area._field
def folded_field(*args, **kwargs):
    field, metrics = real_field(*args, **kwargs)
    field[center] += np.array(rotation.to_3x3()) @ np.array([0., 2., 0.])
    return field, metrics
area._field = folded_field
tooth.contact_area_distal = False
try:
    area.build_preview(tooth)
    raise AssertionError('Folded proposal accepted')
except ValueError as error:
    assert 'verworfen' in str(error), error
finally:
    area._field = real_field
assert not tooth.contact_area_preview
assert np.array_equal(area._world(crown)[0], before)

# Intersecting source/target and missing protection are explicitly rejected.
target.location = (np.array(world_transform) @ np.array((-.12, 0., 0., 1.)))[:3]
bpy.context.view_layer.update()
try:
    area.build_preview(tooth)
    raise AssertionError('Intersecting target accepted')
except ValueError as error:
    assert 'schneiden' in str(error), error
target.matrix_world = world_transform
crown.vertex_groups.remove(crown.vertex_groups[area.PROTECTED])
try:
    area.build_preview(tooth)
    raise AssertionError('Missing protection accepted')
except ValueError as error:
    assert area.PROTECTED in str(error), error
assert np.array_equal(area._world(crown)[0], before)
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CONTACT_AREA_PASSED', json.dumps({'narrow_vertices': narrow_metrics['changed_vertices'],
      'wide_vertices': wide_metrics['changed_vertices'], 'narrow_flat': narrow_flat, 'wide_flat': wide_flat}))
