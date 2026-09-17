import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.context.scene.name = 'Physics Sim'
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
obj = bpy.context.object
for repeat in range(2):
    assert bpy.ops.opendental.limit_physics_movements(mes_dis=2, buc_ling=1, occlusal=.5) == {'FINISHED'}
    assert len(obj.constraints) == 1
obj.location = (8, 8, 8)
bpy.context.view_layer.update()
assert (obj.matrix_world.translation.x, obj.matrix_world.translation.y, obj.matrix_world.translation.z) == (5,5,5.5)
assert bpy.ops.opendental.unlimit_physics_movements() == {'FINISHED'}
bpy.context.view_layer.update()
assert tuple(obj.matrix_world.translation) == (8,8,8)
assert bpy.ops.opendental.lock_physics_movements() == {'FINISHED'}
assert all(obj.lock_location)
assert bpy.ops.opendental.unlock_physics_movements() == {'FINISHED'}
assert not any(obj.lock_location)
print('ODC_PHYSICS_LIMITS_PASSED', bpy.app.version_string)
