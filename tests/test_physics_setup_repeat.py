"""Repeating setup must preserve movement joints and unselected bodies."""
import sys
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for x in (0, 5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 10))
bpy.ops.object.select_all(action='SELECT')
assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
scene = bpy.context.scene
bodies = sorted([o for o in scene.objects if o.type == 'MESH'], key=lambda o:o.location.x)
for obj in bodies:
    obj.select_set(True)
assert bpy.ops.opendental.limit_physics_movements(occlusal=.5) == {'FINISHED'}
anchors = [o.constraints['Limit Location'].space_object for o in bodies]
collections = (scene.rigidbody_world.collection, scene.rigidbody_world.constraints)
count = len(bpy.data.objects)
for attempt in range(3):
    # Select just one body; the other body's simulation must stay intact.
    bpy.ops.object.select_all(action='DESELECT')
    bodies[attempt % 2].select_set(True)
    bpy.context.view_layer.objects.active = bodies[attempt % 2]
    assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
    assert len(bpy.data.objects) == count
    assert (scene.rigidbody_world.collection, scene.rigidbody_world.constraints) == collections
    for body, anchor in zip(bodies, anchors):
        assert body.rigid_body is not None
        assert body.name in scene.rigidbody_world.collection.objects
        assert anchor.name in scene.rigidbody_world.collection.objects
        assert anchor.name in scene.rigidbody_world.constraints.objects
        assert anchor.rigid_body.type == 'PASSIVE'
        assert not any(anchor.rigid_body.collision_collections)
        assert anchor.rigid_body_constraint.object1 == body
        assert anchor.rigid_body_constraint.object2 == anchor
        body.rigid_body.linear_damping = 0
    scene.use_gravity = True
    lowest = [10, 10]
    for frame in range(1, 61):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        for i, body in enumerate(bodies):
            height = body.evaluated_get(graph).matrix_world.translation.z
            lowest[i] = min(lowest[i], height)
    assert all(9.49 <= height < 9.6 for height in lowest), lowest
print('ODC_PHYSICS_SETUP_REPEAT_PASSED', bpy.app.version_string)
