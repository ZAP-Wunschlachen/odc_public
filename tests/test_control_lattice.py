import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
obj = bpy.context.object
for v in obj.data.vertices:
    v.co += Vector((1,2,3))
obj.rotation_euler = (.2,.3,.4)
obj.scale = (2,3,4)
bpy.context.view_layer.update()
assert (u.get_bbox_center(obj, world=False)-Vector((1,2,3))).length < 1e-6
assert (u.get_bbox_center(obj)-(obj.matrix_world @ Vector((1,2,3)))).length < 1e-5
before = [obj.matrix_world @ v.co for v in obj.data.vertices]
assert bpy.ops.opendental.lattice_deform() == {'FINISHED'}
lattice = obj.modifiers['Lattice'].object
object_count = len(bpy.data.objects)
assert bpy.ops.opendental.lattice_deform() == {'FINISHED'}
assert len(bpy.data.objects) == object_count
assert len([m for m in obj.modifiers if m.type == 'LATTICE']) == 1
bpy.context.view_layer.update()
assert len(lattice.data.points) == 27
inverse = lattice.matrix_world.inverted()
assert all(max(abs(c) for c in inverse @ p) < .5 for p in before)
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert all((evaluated.matrix_world @ v.co-p).length < 1e-5 for v,p in zip(mesh.vertices,before))
evaluated.to_mesh_clear()
# Moving a control plane must actually deform the evaluated object.
for point in lattice.data.points:
    if point.co_deform.z > .4:
        point.co_deform.z += .2
bpy.context.view_layer.update()
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert any((evaluated.matrix_world @ v.co-p).length > .01 for v,p in zip(mesh.vertices,before))
evaluated.to_mesh_clear()
# Bounding-box features and mean edge spacing use full affine transforms.
obj.modifiers.clear()
bpy.context.view_layer.update()
for specify in (Vector((0,0,1)), Vector((-1,-1,0)), Vector((1,-1,1))):
    expected = obj.matrix_world @ (Vector((1,2,3)) + specify)
    assert (u.box_feature_locations(obj, specify)-expected).length < 1e-5
assert abs(u.get_linear_density(obj.data, list(obj.data.edges), obj.matrix_world)-6) < 1e-5
assert abs(u.get_linear_density(obj.data, list(obj.data.edges))-2) < 1e-5
try:
    u.get_linear_density(obj.data, [])
except ValueError:
    pass
else:
    raise AssertionError('Empty edge selection must be rejected')
# Multi-object invocation skips non-mesh selections and keeps separate controls.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_cube_add(location=(-4,0,0))
other = bpy.context.object
empty = bpy.data.objects.new('Selected reference', None)
bpy.context.scene.collection.objects.link(empty)
empty.select_set(True)
obj.select_set(True)
before_objects = len(bpy.data.objects)
assert bpy.ops.opendental.lattice_deform() == {'FINISHED'}
assert len(bpy.data.objects) == before_objects + 2
assert obj.modifiers['Lattice'].object != other.modifiers['Lattice'].object
assert not empty.modifiers
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CONTROL_LATTICE_PASSED', bpy.app.version_string)
