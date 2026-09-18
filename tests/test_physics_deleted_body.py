"""Deleting a simulation body must stop its orphaned forcefield."""
import sys, importlib
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
module = importlib.import_module(f'{ROOT.name}.Operators.ortho')
source_scene = bpy.context.scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
sources = []
for x in (-2, 2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0))
    sources.append(bpy.context.object)
for obj in sources:
    obj.select_set(True)
assert bpy.ops.opendental.add_physics_scene() == {'FINISHED'}
assert bpy.ops.opendental.physics_sim_setup() == {'FINISHED'}
scene = bpy.context.scene
bodies = sorted((obj for obj in scene.objects if obj.type == 'MESH'), key=lambda obj: obj.location.x)
for obj in bodies:
    obj.select_set(True)
assert bpy.ops.opendental.add_forcefields() == {'FINISHED'}
fields = [obj for obj in scene.objects if obj.get('odc_tooth_forcefield')]
assert len(fields) == 2 and all(obj.parent is None for obj in fields)
assert bpy.app.handlers.frame_change_pre.count(module.update_tooth_forcefields) == 1
remaining, removed = bodies
orphan = next(field for field in fields if field.get('odc_forcefield_body') == removed)
live = next(field for field in fields if field.get('odc_forcefield_body') == remaining)
bpy.data.objects.remove(removed, do_unlink=True)
assert orphan.get('odc_forcefield_body') is None
initial = remaining.matrix_world.translation.copy()
scene.frame_set(0)
for frame in range(1, 31):
    scene.frame_set(frame)
    position = remaining.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation
    assert orphan.field.type == 'NONE', 'Deleted body still has an active forcefield'
    assert live.field.type == 'FORCE'
    assert (position-initial).length < 1e-6, (frame, position, initial)
assert all(source.name in source_scene.objects for source in sources)
print('ODC_PHYSICS_DELETED_BODY_PASSED')
