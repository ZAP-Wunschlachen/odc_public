"""Foreground tests with real viewport projection and scene/object surface queries."""
import sys
import os
import traceback
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Matrix, Quaternion
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name, default_set=True)
        Manager = importlib.import_module(f'{ROOT.name}.Operators.curve').CurveDataManager
        area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
            bpy.ops.mesh.primitive_plane_add(size=100)
            surface = bpy.context.object
            rv = area.spaces.active.region_3d
            rv.view_rotation = Quaternion((1,0,0,0))
            rv.view_perspective = 'ORTHO'
            rv.view_location = (0,0,0)
            for mode in ('SCENE', 'OBJECT'):
                manager = Manager(bpy.context, snap_type=mode, snap_object=surface, shrink_mod=True)
                manager.crv_obj.matrix_world = Matrix.Translation((2,3,4))
                bpy.context.view_layer.update()
                for delta in (-50,0,50):
                    manager.click_add_point(bpy.context, region.width//2+delta, region.height//2)
                assert len(manager.b_pts) == 3
                assert all(abs(p.z) < 1e-5 for p in manager.b_pts)
                for point, bp in zip(manager.b_pts, manager.crv_data.splines[0].bezier_points):
                    assert (manager.crv_obj.matrix_world @ bp.co-point).length < 1e-5
                manager.selected = 1
                old = manager.b_pts[1].copy()
                assert manager.grab_initiate()
                manager.grab_mouse_move(bpy.context, region.width//2, region.height//2+50)
                assert (manager.b_pts[1]-old).length > .01
                manager.grab_cancel()
                assert (manager.b_pts[1]-old).length < 1e-5
                assert (manager.crv_obj.matrix_world @ manager.crv_data.splines[0].bezier_points[1].co-old).length < 1e-5
            # Open U-shaped paths must not expose a phantom closing edge.
            from bpy_extras.view3d_utils import region_2d_to_location_3d
            from mathutils import Vector
            manager = Manager(bpy.context, snap_type='OBJECT', snap_object=surface)
            cx, cy = region.width/2, region.height/2
            screen_points = [(cx-150,cy-150),(cx-150,cy+150),(cx+150,cy+150),(cx+150,cy-150)]
            manager.b_pts = [region_2d_to_location_3d(region, rv, p, Vector((0,0,0))) for p in screen_points]
            manager.started = True
            manager.update_blender_curve_data()
            manager.hover(bpy.context, cx, cy-150)
            assert manager.hovered == [None,-1]
            manager.crv_data.splines[0].use_cyclic_u = True
            manager.hover(bpy.context, cx, cy-150)
            assert manager.hovered == ['EDGE',3]
            manager.click_add_point(bpy.context, cx, cy-150)
            assert len(manager.b_pts) == 5
            for point, bp in zip(manager.b_pts, manager.crv_data.splines[0].bezier_points):
                assert (manager.crv_obj.matrix_world @ bp.co-point).length < 1e-5
            manager.hover(bpy.context, *screen_points[0])
            assert manager.hovered == ['POINT',0]
        print('ODC_CURVE_MANAGER_PASSED', flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run, first_interval=2)
