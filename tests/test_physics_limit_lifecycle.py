"""Owned joint persistence and cleanup when rebuilding a physics scene."""
import sys, tempfile
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 10))
source = bpy.context.object
source.name = 'Source tooth'
source_scene = bpy.context.scene
source_scene_name = source_scene.name
assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
body = bpy.context.object
body.select_set(True)
body.rigid_body.linear_damping = 0
body_name = body.name
assert bpy.ops.opendental.limit_physics_movements(occlusal=.5) == {'FINISHED'}
anchor = body.constraints['Limit Location'].space_object
anchor_name = anchor.name
mesh_name = anchor.data.name
scene = bpy.context.scene
scene.use_gravity = True
with tempfile.TemporaryDirectory(prefix='odc-joint-') as directory:
    path = str(Path(directory) / 'joint.blend')
    assert bpy.ops.wm.save_as_mainfile(filepath=path) == {'FINISHED'}
    assert bpy.ops.wm.open_mainfile(filepath=path) == {'FINISHED'}
    scene = bpy.context.scene
    body = scene.objects[body_name]
    anchor = scene.objects[anchor_name]
    assert body.constraints['Limit Location'].space_object == anchor
    assert anchor.rigid_body_constraint.object1 == body
    assert anchor.rigid_body_constraint.object2 == anchor
    heights = []
    for frame in range(1, 61):
        scene.frame_set(frame)
        heights.append(body.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.z)
    assert min(heights) >= 9.49 and min(heights) < 9.6, min(heights)
    # Rebuild from the original scene; no old body, joint or anchor mesh may leak.
    bpy.context.window.scene = bpy.data.scenes[source_scene_name]
    source = bpy.context.scene.objects['Source tooth']
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
    assert anchor_name not in bpy.data.objects, anchor_name
    assert mesh_name not in bpy.data.meshes, mesh_name
    owned = [o for o in bpy.data.objects if o.get('odc_physics_copy')]
    assert owned == [bpy.context.object], [o.name for o in owned]
    assert source.data == bpy.context.object.data
# A joint intentionally linked to another scene keeps its referenced body too.
assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
body = bpy.context.object
body.select_set(True)
assert bpy.ops.opendental.limit_physics_movements() == {'FINISHED'}
anchor = body.constraints['Limit Location'].space_object
other_scene = bpy.data.scenes.new('External anchor user')
other_scene.collection.objects.link(anchor)
body_name, anchor_name, mesh_name = body.name, anchor.name, anchor.data.name
bpy.context.window.scene = bpy.data.scenes[source_scene_name]
source = bpy.context.scene.objects['Source tooth']
source.select_set(True)
bpy.context.view_layer.objects.active = source
assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
assert bpy.data.objects.get(body_name) == body
assert other_scene.objects.get(anchor_name) == anchor
assert bpy.data.meshes.get(mesh_name) == anchor.data
assert anchor.rigid_body_constraint.object1 == body
assert body.constraints['Limit Location'].space_object == anchor
assert anchor.name not in bpy.context.scene.objects
assert body.name not in bpy.context.scene.objects
print('ODC_PHYSICS_LIMIT_LIFECYCLE_PASSED', bpy.app.version_string)
