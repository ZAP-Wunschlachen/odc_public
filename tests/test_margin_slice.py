import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
Manager = importlib.import_module(f'{ROOT.name}.Operators.curve').CurveDataManager
Slicer = importlib.import_module(f'{ROOT.name}.Operators.margin').MarginSlicer
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
surface = bpy.context.object
surface.scale = (2,3,4)
bpy.context.view_layer.update()
tooth = bpy.context.scene.odc_teeth.add()
tooth.name = '25'
manager = Manager(bpy.context, snap_type='OBJECT', snap_object=surface)
manager.crv_obj.matrix_world = Matrix.Translation((8,9,10))
slicer = Slicer(tooth, bpy.context, manager)
assert not slicer.prepare_slice()
manager.b_pts = [Vector((5,3,5)), Vector((5,4,5)), Vector((5,5,5))]
manager.update_blender_curve_data()
manager.selected = 1
assert slicer.prepare_slice()
assert (slicer.cut_pt - Vector((5,4,5))).length < 1e-6
assert len(slicer.slice_points) >= 4
assert all(abs(p.y-4) < 1e-5 for p in slicer.slice_points)
assert len(slicer.points_2d) == len(slicer.slice_points)
assert all(0 <= component <= 200.001 for p in slicer.points_2d for component in p)
slicer.slice_cancel()
assert not slicer.slice_points
slicer.bme.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_MARGIN_SLICE_PASSED', bpy.app.version_string)
