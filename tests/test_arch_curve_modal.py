"""Exercise the arch-curve panel action using actual window events."""
import sys, os, traceback
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
phase = 0
window = area = region = None

def send(kind, dx=0, dy=0):
    for value in ('PRESS', 'RELEASE'):
        window.event_simulate(type=kind, value=value,
                              x=region.x+region.width//2+dx, y=region.y+region.height//2+dy)
def running():
    return any(op.bl_idname == 'OPENDENTAL_OT_draw_arch_curve' for op in window.modal_operators)
def run():
    global phase, window, area, region, object_count, curve_count, finished
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            object_count, curve_count = len(bpy.data.objects), len(bpy.data.curves)
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.draw_arch_curve('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('RET')
        elif phase == 1:
            assert running()
            send('LEFTMOUSE', -80, 0)
        elif phase == 2:
            send('LEFTMOUSE', 0, 60)
        elif phase == 3:
            send('LEFTMOUSE', 80, 0)
        elif phase == 4:
            send('BACK_SPACE')
        elif phase == 5:
            send('RET')
        elif phase == 6:
            assert not running()
            finished = bpy.context.object
            assert finished.type == 'CURVE'
            assert len(finished.data.splines[0].bezier_points) == 2
            assert not finished.data.splines[0].use_cyclic_u
            points = finished.data.splines[0].bezier_points
            assert (points[0].co-points[1].co).length > .1
            assert bpy.context.selected_objects == [finished]
            assert len(bpy.data.objects) == object_count+1
            assert len(bpy.data.curves) == curve_count+1
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.teeth_to_arch.poll()
                assert bpy.ops.opendental.draw_arch_curve('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('LEFTMOUSE')
        elif phase == 7:
            send('ESC')
        elif phase == 8:
            assert not running()
            assert bpy.context.object == finished
            assert bpy.context.selected_objects == [finished]
            assert len(bpy.data.objects) == object_count+1
            assert len(bpy.data.curves) == curve_count+1
            print('ODC_ARCH_CURVE_MODAL_PASSED', flush=True)
            bpy.ops.wm.quit_blender(); return None
        phase += 1
        return .6
    except Exception:
        traceback.print_exc(); os._exit(1)
bpy.app.timers.register(run, first_interval=2)
