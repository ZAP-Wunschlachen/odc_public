import sys
import os
import traceback
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Quaternion, Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
phase = 0
def run():
    global phase, m, tooth, area, region
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            m = importlib.import_module(f'{ROOT.name}.Operators.bracket_placement')
            bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
            tooth = bpy.context.object
            area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(area=area,region=region):
                view = area.spaces.active.region_3d
                view.view_rotation = Quaternion((1,0,0,0))
                view.view_location = tooth.location
                view.view_distance = 10
                view.view_perspective = 'ORTHO'
                bpy.context.view_layer.update()
            area.tag_redraw()
            phase = 1
            return .8
        with bpy.context.temp_override(area=area,region=region):
            manager = m.BracketDataManager(bpy.context,snap_type='OBJECT',snap_object=tooth)
            manager.place_bracket(bpy.context,region.width/2,region.height/2,normal=True)
            assert (manager.bracket_obj.matrix_world.translation-Vector((3,4,6))).length < 1e-4, manager.bracket_obj.matrix_world.translation[:]
            slicer = m.BracektSlicer(bpy.context, manager)
            slicer.slice()
            assert len(slicer.slice_points_x) >= 4
            assert len(slicer.slice_points_y) >= 4
            assert all(abs(point.x-3) < 1e-4 for point in slicer.slice_points_x)
            assert all(abs(point.y-4) < 1e-4 for point in slicer.slice_points_y)
            assert len(slicer.reference_L) == 5
            slicer.bme.free()
            initial = manager.bracket_obj.matrix_world.copy()
            manager.spin_initiate()
            manager.spin_event('UP_ARROW',False)
            assert manager.bracket_obj.matrix_world != initial
            manager.spin_cancel()
            assert manager.bracket_obj.matrix_world == initial
        print('ODC_BRACKET_MANAGER_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
