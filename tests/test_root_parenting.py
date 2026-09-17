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
tooth.location.x = 3
bpy.ops.mesh.primitive_cube_add(size=4, location=(3,2,1))
jaw = bpy.context.object
jaw.name = 'UpperJaw'
original = [v.co.copy() for v in jaw.data.vertices]
for attempt in range(2):
    assert bpy.ops.opendental.set_roots_parents(link_to_cast=True) == {'FINISHED'}
    assert len([m for m in jaw.modifiers if m.type == 'ARMATURE']) == 1
    assert len([m for m in jaw.modifiers if m.type == 'VERTEX_WEIGHT_PROXIMITY']) == 1
    assert jaw.modifiers[-1].type == 'ARMATURE'
    assert jaw.vertex_groups.get('11_root') is not None
bpy.context.view_layer.update()
def evaluated_positions():
    evaluated = jaw.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    positions = [v.co.copy() for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return positions
before_jaw = evaluated_positions()
tooth.location.x += 1
bpy.context.view_layer.update()
after_jaw = evaluated_positions()
assert max((a-b).length for a,b in zip(after_jaw,before_jaw)) > .1
assert all(abs(a.y-b.y) < 1e-5 and abs(a.z-b.z) < 1e-5 for a,b in zip(after_jaw,before_jaw))
assert [v.co for v in jaw.data.vertices] == original
print('ODC_ROOT_PARENTING_PASSED', bpy.app.version_string)
