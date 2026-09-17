"""Curve rebuilding preserves local/world coordinates and shared data ownership."""
import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Matrix, Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
Manager = importlib.import_module(f'{ROOT.name}.Operators.curve').CurveDataManager
manager = Manager(bpy.context)
manager.crv_obj.matrix_world = Matrix.Translation((3,4,5)) @ Matrix.Diagonal((2,3,4,1))
manager.b_pts = [Vector((0,0,0)),Vector((2,0,0)),Vector((2,2,0)),Vector((0,2,0))]
manager.started = True
manager.crv_data.splines[0].use_cyclic_u = True
manager.crv_data.resolution_u = 24
shared = bpy.data.objects.new('shared_curve', manager.crv_data)
bpy.context.scene.collection.objects.link(shared)
old_data = shared.data
manager.update_blender_curve_data()
assert shared.data == old_data and len(shared.data.splines[0].bezier_points) == 1
assert manager.crv_data.resolution_u == 24
assert manager.crv_data.splines[0].use_cyclic_u
for bp, expected in zip(manager.crv_data.splines[0].bezier_points, manager.b_pts):
    assert (manager.crv_obj.matrix_world @ bp.co-expected).length < 1e-6
manager.hovered = ['POINT', 1]
manager.click_delete_point()
assert len(manager.b_pts) == 3 and manager.selected == -1
assert manager.crv_data.splines[0].use_cyclic_u
for _ in range(3):
    manager.selected = 0
    manager.click_delete_point(mode='selected')
assert not manager.started and not manager.b_pts
assert manager.selected == -1 and manager.hovered == [None,-1]
assert not manager.crv_data.splines[0].use_cyclic_u
assert shared.data == old_data
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CURVE_TOPOLOGY_EDIT_PASSED', bpy.app.version_string)
