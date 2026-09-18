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
    assert sum(bool(o.get('odc_physics_copy')) for o in bpy.data.objects) == 1, [(o.name, o.users, [c.name for c in o.users_collection]) for o in bpy.data.objects if o.get('odc_physics_copy')]
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
        fields = [item for item in scene.objects if item.get('odc_forcefield_body') == copy]
        assert len(fields) == 1
        field = fields[0]
        bpy.context.view_layer.update()
        assert (field.matrix_world.translation-copy.matrix_world.translation).length < 1e-5
        assert field.field.type == 'FORCE'
        assert abs(field.field.strength+1000) < 1e-5
        assert abs(field.field.radial_min-copy.dimensions.x/1.8) < 1e-5
    assert not scene.use_gravity
    assert scene.rigidbody_world.solver_iterations == 15
# Explicit source mapping must not overwrite another object sharing the mesh.
bpy.context.window.scene = source_scene
sibling = bpy.data.objects.new('Shared mesh sibling', source.data)
source_scene.collection.objects.link(sibling)
sibling.location = (-8,0,0)
bpy.context.window.scene = scene
copy.location = (7,8,9)
bpy.context.view_layer.update()
expected = copy.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
assert bpy.ops.opendental.keep_simulation_results() == {'FINISHED'}
assert bpy.context.scene == source_scene
assert (source.matrix_world.translation-expected.translation).length < 1e-5
assert tuple(sibling.location) == (-8,0,0)
print('ODC_PHYSICS_SCENE_PASSED', bpy.app.version_string)
