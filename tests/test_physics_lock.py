import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
scene.name = 'Physics Sim'
bpy.ops.mesh.primitive_cube_add(location=(0,0,10))
obj = bpy.context.object
bpy.ops.rigidbody.object_add()
assert bpy.ops.opendental.lock_physics_movements() == {'FINISHED'}
for frame in range(1,25):
    scene.frame_set(frame)
assert abs(obj.matrix_world.translation.z-10) < 1e-5, obj.matrix_world.translation.z
scene.frame_set(1)
assert bpy.ops.opendental.unlock_physics_movements() == {'FINISHED'}
for frame in range(1,25):
    scene.frame_set(frame)
assert obj.matrix_world.translation.z < 9, obj.matrix_world.translation.z
print('ODC_PHYSICS_LOCK_PASSED', bpy.app.version_string)
