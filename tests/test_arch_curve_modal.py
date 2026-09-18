"""Exercise the arch-curve panel action using actual window events."""
import sys, os, traceback, math
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
    global phase, window, area, region, object_count, curve_count, finished, finished_name, curve_points
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
            finished_name = finished.name
            curve_points = [tuple(point.co) for point in finished.data.splines[0].bezier_points]
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.ed.undo() == {'FINISHED'}
            assert finished_name not in bpy.data.objects
        elif phase == 9:
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.ed.redo() == {'FINISHED'}
            finished = bpy.data.objects[finished_name]
            assert bpy.context.object == finished
            assert [tuple(point.co) for point in finished.data.splines[0].bezier_points] == curve_points
        elif phase == 10:
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.teeth_to_arch(arch_type='0', shift='2') == {'FINISHED'}
            bpy.context.view_layer.update()
            teeth = [obj for obj in bpy.context.scene.objects
                     if any(c.type == 'FOLLOW_PATH' and c.target == finished for c in obj.constraints)]
            assert len(teeth) == 14, len(teeth)
            before = {obj.name: obj.matrix_world.copy() for obj in teeth}
            assert all(math.isfinite(value) for matrix in before.values() for row in matrix for value in row)
            assert all(min(obj.dimensions) > 0 for obj in teeth)
            assert max((a.translation-b.translation).length for a in before.values() for b in before.values()) > .1
            with bpy.context.temp_override(window=window, area=area, region=region):
                assert bpy.ops.opendental.arch_plan_keep() == {'FINISHED'}
            bpy.context.view_layer.update()
            for obj in teeth:
                assert not any(c.type == 'FOLLOW_PATH' and c.target == finished for c in obj.constraints)
                assert max(abs(obj.matrix_world[i][j]-before[obj.name][i][j])
                           for i in range(4) for j in range(4)) < 1e-4
            print('ODC_ARCH_CURVE_MODAL_PASSED', flush=True)
            bpy.ops.wm.quit_blender(); return None
        phase += 1
        return .6
    except Exception:
        traceback.print_exc(); os._exit(1)
bpy.app.timers.register(run, first_interval=2)
