"""Real window events exercise insertion-axis invoke, placement, cancel and finish."""
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

def send(kind):
    window.event_simulate(type=kind, value='PRESS', x=region.x+region.width//2, y=region.y+region.height//2)
    window.event_simulate(type=kind, value='RELEASE', x=region.x+region.width//2, y=region.y+region.height//2)

def running():
    return any(op.bl_idname == 'OPENDENTAL_OT_insertion_axis' for op in window.modal_operators)

def run():
    global phase, window, area, region
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            bpy.context.scene.odc_teeth.add().name = '25'
            with bpy.context.temp_override(window=window, area=area, region=region):
                area.spaces.active.region_3d.view_rotation = Quaternion((1,0,0,0))
                area.spaces.active.region_3d.view_location = (0,0,0)
                assert bpy.ops.opendental.insertion_axis('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            assert running()
            send('SPACE')
        elif phase == 1:
            tooth = bpy.context.scene.odc_teeth[0]
            assert tooth.axis and tooth.axis in bpy.data.objects, 'Space did not place axis'
            send('ESC')
        elif phase == 2:
            assert not running(), 'Cancel left modal handler active'
            assert bpy.context.scene.odc_teeth[0].axis == '', 'Cancel left new axis'
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.insertion_axis('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('LEFTMOUSE')
        elif phase == 3:
            assert bpy.context.scene.odc_teeth[0].axis
            send('RET')
        elif phase == 4:
            assert not running(), 'Finish left modal handler active'
            assert bpy.context.scene.odc_teeth[0].axis in bpy.data.objects
            print('ODC_AXIS_MODAL_PASSED', flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .6
    except Exception:
        traceback.print_exc()
        print('ODC_AXIS_MODAL_FAILED', flush=True)
        os._exit(1)
bpy.app.timers.register(run, first_interval=2)
