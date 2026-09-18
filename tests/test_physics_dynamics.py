"""Real two-body attraction, repeatable reset and evaluated result transfer."""
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
runs = []
for attempt in range(2):
    scene.frame_set(0)
    previous = None
    trajectory = []
    for frame in range(1, 31):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        poses = {obj: obj.evaluated_get(graph).matrix_world.copy() for obj in bodies}
        if previous is not None:
            for field in fields:
                expected = previous[field['odc_forcefield_body']].translation
                assert (field.matrix_world.translation - expected).length < 1e-6
        left, right = [poses[obj].translation for obj in bodies]
        assert (left + right).length < 1e-5, (frame, left, right)
        assert abs(left.y) + abs(left.z) < 1e-6
        trajectory.append((left.x, right.x))
        previous = poses
    assert trajectory[-1][0] > -1.995 and trajectory[-1][1] < 1.995, trajectory[-1]
    assert all(trajectory[n][0] >= trajectory[n-1][0] for n in range(1, 30))
    runs.append(trajectory)
assert max(abs(a-b) for p, q in zip(*runs) for a, b in zip(p, q)) < 1e-6
assert [tuple(obj.location) for obj in sources] == [(-2, 0, 0), (2, 0, 0)]
assert bpy.ops.opendental.keep_simulation_results() == {'FINISHED'}
assert bpy.context.scene == source_scene
for body, world in previous.items():
    source = body['odc_source_object']
    assert (source.matrix_world.translation - world.translation).length < 1e-6
addon_utils.disable(ROOT.name, default_set=True)
assert module.update_tooth_forcefields not in bpy.app.handlers.frame_change_pre
print('ODC_PHYSICS_DYNAMICS_PASSED')
