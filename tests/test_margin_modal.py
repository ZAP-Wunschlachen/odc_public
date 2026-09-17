"""Real window events exercise margin cancellation and closed-contour acceptance."""
import sys
import os
import traceback
from pathlib import Path
import bpy
import addon_utils
from mathutils import Quaternion
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
phase = 0
window = area = region = None
original_point = None

def send(kind, dx=0, dy=0):
    window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=region.x+region.width//2+dx, y=region.y+region.height//2+dy)
    window.event_simulate(type=kind, value='PRESS', x=region.x+region.width//2+dx, y=region.y+region.height//2+dy)
    window.event_simulate(type=kind, value='RELEASE', x=region.x+region.width//2+dx, y=region.y+region.height//2+dy)

def running():
    return any(op.bl_idname == 'OPENDENTAL_OT_mark_crown_margin' for op in window.modal_operators)

def run():
    global phase, window, area, region, original_point
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            tooth = bpy.context.scene.odc_teeth.add()
            tooth.name = '25'
            tooth.prep_model = bpy.context.object.name
            previous = bpy.data.objects.new('previous_margin', None)
            bpy.context.scene.collection.objects.link(previous)
            tooth.margin = previous.name
            with bpy.context.temp_override(window=window, area=area, region=region):
                area.spaces.active.region_3d.view_rotation = Quaternion((1,0,0,0))
                area.spaces.active.region_3d.view_location = (0,0,0)
                area.spaces.active.region_3d.view_distance = 6
                area.spaces.active.region_3d.view_perspective = 'ORTHO'
                assert bpy.ops.opendental.mark_crown_margin('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            assert running()
            send('LEFTMOUSE')
        elif phase == 1:
            tooth = bpy.context.scene.odc_teeth[0]
            assert tooth.margin and tooth.margin in bpy.data.objects, 'Space did not place axis'
            send('ESC')
        elif phase == 2:
            assert not running(), 'Cancel left modal handler active'
            assert bpy.context.scene.odc_teeth[0].margin == 'previous_margin'
            assert not bpy.data.objects['Cube'].hide_get()
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.mark_crown_margin('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('LEFTMOUSE')
        elif phase == 3:
            assert bpy.context.scene.odc_teeth[0].margin
            send('RET')
        elif phase == 4:
            assert running(), 'Incomplete margin was accepted'
            send('LEFTMOUSE', 70, 0)
        elif phase == 5:
            send('LEFTMOUSE', 70, 70)
        elif phase == 6:
            send('LEFTMOUSE', 0, 0)
        elif phase == 7:
            curve = bpy.data.objects[bpy.context.scene.odc_teeth[0].margin]
            assert len(curve.data.splines[0].bezier_points) == 3
            assert curve.data.splines[0].use_cyclic_u
            original_point = curve.data.splines[0].bezier_points[0].co.copy()
            send('S')
        elif phase == 8:
            window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=region.x+region.width//2+30, y=region.y+region.height//2+20)
        elif phase == 9:
            curve = bpy.data.objects[bpy.context.scene.odc_teeth[0].margin]
            assert (curve.data.splines[0].bezier_points[0].co-original_point).length > .001
            send('ESC')
        elif phase == 10:
            assert running(), 'Slice cancellation exited the entire tool'
            curve = bpy.data.objects[bpy.context.scene.odc_teeth[0].margin]
            assert (curve.data.splines[0].bezier_points[0].co-original_point).length < 1e-5
            send('RET')
        elif phase == 11:
            assert not running(), 'Finish left modal handler active'
            assert bpy.context.scene.odc_teeth[0].margin in bpy.data.objects
            print('ODC_MARGIN_MODAL_PASSED', flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .6
    except Exception:
        traceback.print_exc()
        print('ODC_MARGIN_MODAL_FAILED', flush=True)
        os._exit(1)
bpy.app.timers.register(run, first_interval=2)
