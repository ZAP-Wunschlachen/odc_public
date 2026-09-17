import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_cube_add(location=(3,2,1))
tooth = bpy.context.object
tooth.name = '11'
bpy.ops.object.armature_add(location=(1,0,0))
arm = bpy.context.object
arm.name = 'Roots'
arm.data.bones[0].name = '11_root'
bpy.context.view_layer.update()
before = arm.pose.bones[0].matrix.copy()
assert bpy.ops.opendental.set_roots_parents() == {'FINISHED'}
bpy.context.view_layer.update()
assert len(arm.pose.bones[0].constraints) == 1
assert max(abs(arm.pose.bones[0].matrix[i][j]-before[i][j]) for i in range(4) for j in range(4)) < 1e-5
tooth.location.x += 2
bpy.context.view_layer.update()
assert abs(arm.pose.bones[0].matrix.translation.x-before.translation.x-2)<1e-5
assert bpy.ops.opendental.set_roots_parents() == {'FINISHED'}
assert len(arm.pose.bones[0].constraints) == 1
arm.hide_set(True)
bpy.context.view_layer.objects.active = tooth
assert bpy.ops.opendental.adjust_bone_roots() == {'FINISHED'}
assert bpy.context.object == arm and bpy.context.mode == 'EDIT_ARMATURE'
bpy.ops.object.mode_set(mode='OBJECT')
print('ODC_ROOT_PARENTING_PASSED', bpy.app.version_string)
