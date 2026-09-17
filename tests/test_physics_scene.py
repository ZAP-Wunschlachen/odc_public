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
    copies = [o for o in scene.objects if o.get('odc_physics_copy') and o.type == 'MESH']
    assert len(copies) == 1
    copy = copies[0]
    assert copy != source and copy.data == source.data
    assert copy.matrix_world == source.matrix_world
    assert source.name in source_scene.objects
    assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
    assert copy.rigid_body is not None and source.rigid_body is None
    for repeat in range(2):
        copy.select_set(True)
        bpy.context.view_layer.objects.active = copy
        assert bpy.ops.opendental.add_forcefields() == {'FINISHED'}
        fields = [child for child in copy.children if child.get('odc_tooth_forcefield')]
        assert len(fields) == 1
        field = fields[0]
        bpy.context.view_layer.update()
        assert (field.matrix_world.translation-copy.matrix_world.translation).length < 1e-5
        assert field.field.type == 'FORCE'
        assert abs(field.field.strength+1000) < 1e-5
        assert abs(field.field.radial_min-copy.dimensions.x/1.8) < 1e-5
    assert not scene.use_gravity
    assert scene.rigidbody_world.solver_iterations == 15
print('ODC_PHYSICS_SCENE_PASSED', bpy.app.version_string)
