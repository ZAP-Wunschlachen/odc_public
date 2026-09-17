import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
source_scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
source = bpy.context.object
for attempt in range(2):
    bpy.context.window.scene = source_scene
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    bpy.context.view_layer.objects.active = source
    assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
    scene = bpy.context.scene
    assert scene.name == 'Physics Sim'
    copies = [o for o in scene.objects if o.get('odc_physics_copy')]
    assert len(copies) == 1
    copy = copies[0]
    assert copy != source and copy.data == source.data
    assert copy.matrix_world == source.matrix_world
    assert source.name in source_scene.objects
    assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
    assert copy.rigid_body is not None and source.rigid_body is None
    assert not scene.use_gravity
    assert scene.rigidbody_world.solver_iterations == 15
print('ODC_PHYSICS_SCENE_PASSED', bpy.app.version_string)
