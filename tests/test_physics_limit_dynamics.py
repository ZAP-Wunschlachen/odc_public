"""Movement limits must constrain evaluated rigid-body motion, not just transforms."""
import sys
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
scene.name = 'Physics Sim'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,10))
obj = bpy.context.object
# Also upgrade a limit created before the object became a rigid body.
assert bpy.ops.opendental.limit_physics_movements() == {'FINISHED'}
bpy.ops.rigidbody.object_add()
assert bpy.ops.opendental.limit_physics_movements() == {'FINISHED'}
assert bpy.ops.opendental.unlimit_physics_movements() == {'FINISHED'}
from mathutils import Vector
import math
for angle in (0, math.pi / 2):
    scene.frame_set(0)
    obj.rotation_euler.y = angle
    bpy.context.view_layer.update()
    rotation = obj.matrix_world.to_quaternion()
    scene.gravity = rotation @ Vector((0, 0, -9.81))
    origin = obj.matrix_world.translation.copy()
    count = len(bpy.data.objects)
    meshes = len(bpy.data.meshes)
    for repeat in range(2):
        assert bpy.ops.opendental.limit_physics_movements(mes_dis=2, buc_ling=1, occlusal=.5) == {'FINISHED'}
        assert len(bpy.data.objects) == count + 1
        assert bpy.context.object == obj and bpy.context.selected_objects == [obj]
    displacements = []
    for frame in range(1, 61):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        delta = rotation.inverted() @ (obj.evaluated_get(graph).matrix_world.translation - origin)
        displacements.append(delta.z)
        assert abs(delta.x) < .01 and abs(delta.y) < .01, delta
    assert min(displacements) >= -.51, min(displacements)
    assert min(displacements) < -.4, min(displacements)
    assert bpy.ops.opendental.unlimit_physics_movements() == {'FINISHED'}
    assert len(bpy.data.objects) == count
    assert len(bpy.data.meshes) == meshes
    for frame in range(1, 61):
        scene.frame_set(frame)
    delta = rotation.inverted() @ (obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation - origin)
    assert delta.z < -1, delta
print('ODC_PHYSICS_LIMIT_DYNAMICS_PASSED', bpy.app.version_string)
