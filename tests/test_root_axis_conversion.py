import sys
import importlib
from types import SimpleNamespace
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
m = importlib.import_module(f'{ROOT.name}.Operators.ortho')
bpy.ops.mesh.primitive_cube_add()
tooth = bpy.context.object
tooth.name = '11'
bpy.ops.object.armature_add(location=(3,4,5))
arm = bpy.context.object
arm.name = 'Roots'
arm.rotation_euler = (.2,.3,.4)
arm.data.bones[0].name = '11root'
axis = bpy.data.objects.new('11root_empty',None)
bpy.context.scene.collection.objects.link(axis)
axis.location = (5,8,13)
axis.rotation_euler = (.4,.2,.1)
bpy.context.view_layer.update()
world = axis.matrix_world.copy()
m.OPENDENTAL_OT_add_bone_roots.empties_to_bones(SimpleNamespace(units=[tooth]), bpy.context)
bone = arm.data.bones['11root']
assert (arm.matrix_world @ bone.tail_local-world.translation).length < 1e-5
expected_head = world.translation - 16 * (world.to_quaternion() @ Vector((0,0,1)))
assert (arm.matrix_world @ bone.head_local-expected_head).length < 1e-5
assert bpy.data.objects.get('11root_empty') is None
bpy.ops.object.mode_set(mode='OBJECT')
print('ODC_ROOT_AXIS_CONVERSION_PASSED', bpy.app.version_string)
