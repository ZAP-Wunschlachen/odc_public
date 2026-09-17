import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Euler, Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
reorient = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils').reorient_object
bpy.ops.mesh.primitive_cube_add(location=(2,3,4))
obj = bpy.context.object
parent = bpy.data.objects.new('parent', None)
bpy.context.scene.collection.objects.link(parent)
parent.location = (4,5,6)
parent.rotation_euler = (.2,.3,.4)
parent.scale = (2,3,4)
obj.parent = parent
obj.rotation_euler = (.1,.3,.5)
shared = bpy.data.objects.new('shared_mesh', obj.data)
bpy.context.scene.collection.objects.link(shared)
bpy.context.view_layer.update()
original_data = shared.data
points = [obj.matrix_world @ v.co for v in obj.data.vertices]
rotation = Euler((.4,.5,.6)).to_quaternion()
reorient(obj, rotation)
bpy.context.view_layer.update()
assert obj.parent == parent and shared.data == original_data
assert obj.data != original_data
assert all((obj.matrix_world @ v.co-p).length < 1e-5 for v,p in zip(obj.data.vertices,points))
assert obj.matrix_world.to_quaternion().rotation_difference(rotation).angle < 1e-5
# Curve coordinates use the same direct transformation path.
bpy.ops.curve.primitive_bezier_curve_add(location=(3,4,5))
curve = bpy.context.object
points = [curve.matrix_world @ p.co for p in curve.data.splines[0].bezier_points]
reorient(curve, rotation.to_matrix())
bpy.context.view_layer.update()
assert all((curve.matrix_world @ p.co-old).length < 1e-5 for p,old in zip(curve.data.splines[0].bezier_points,points))
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_REORIENT_OBJECT_PASSED', bpy.app.version_string)
