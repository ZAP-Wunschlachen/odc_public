"""Exercise tooth/type selection, commit, cancellation and existing plan updates."""
import sys, os, traceback, importlib
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
phase = 0

def click(point, kind='LEFTMOUSE'):
    for value in ('PRESS', 'RELEASE'):
        bpy.context.window.event_simulate(type=kind, value=value,
            x=region.x+int(point[0]), y=region.y+int(point[1]))

def inside(loop, scale, offset):
    # Choose a pixel away from outlines, using the actual button polygon.
    xs = [p[0] for p in loop]; ys = [p[1] for p in loop]
    for fy in [i/20 for i in range(1, 20)]:
        for fx in [i/20 for i in range(1, 20)]:
            point = (scale*(min(xs)+(max(xs)-min(xs))*fx)+offset[0],
                     scale*(min(ys)+(max(ys)-min(ys))*fy)+offset[1])
            point = (int(point[0]), int(point[1]))
            if all(drawing.point_inside_loop(loop, (point[0]+dx, point[1]+dy), scale, offset)
                   for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))):
                return point
    raise AssertionError('No interior point')

def invoke():
    with bpy.context.temp_override(area=area, region=region):
        assert bpy.ops.opendental.plan_restorations('INVOKE_DEFAULT') == {'RUNNING_MODAL'}

def run():
    global phase, area, region, drawing, teeth, types, existing
    try:
        scene = bpy.context.scene
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            data = importlib.import_module(f'{ROOT.name}.odcmenus.button_data')
            drawing = importlib.import_module(f'{ROOT.name}.Operators.bgl_utils')
            area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            width = min(.8*region.width, .5824333739982135*.8*region.height)
            height = width/.5824333739982135
            offset = ((region.width-width)/2, (region.height-height)/2)
            rest_offset = (offset[0]+width*.25, offset[1]+height*.25/.5824333739982135)
            teeth = {name: inside(loop, width, offset) for name, loop in zip(data.tooth_button_names, data.tooth_button_data)}
            types = [inside(loop, width*.5, rest_offset) for loop in data.rest_button_data]
            existing = scene.odc_teeth.add(); existing.name = '24'; existing.contour = 'Preserve this reference'
            invoke()
        elif phase == 1: click(teeth['25'])
        elif phase == 2: click(types[1])
        elif phase == 3: click(teeth['25'])
        elif phase == 4: click(types[4])
        elif phase == 5: click(teeth['26'])
        elif phase == 6: click(teeth['26'], 'RET')
        elif phase == 7:
            assert len(scene.odc_teeth) == 2 and scene.odc_teeth['25'].rest_type == '1'
            assert len(scene.odc_implants) == 1 and scene.odc_implants[0].name == '26'
            invoke()
        elif phase == 8: click(teeth['27'])
        elif phase == 9: click(teeth['27'], 'ESC')
        elif phase == 10:
            assert len(scene.odc_teeth) == 2 and '27' not in scene.odc_teeth
            invoke()
        elif phase == 11: click(types[2])
        elif phase == 12: click(teeth['24'])
        elif phase == 13: click(teeth['28'])
        elif phase == 14: click(teeth['28'], 'RIGHTMOUSE')
        elif phase == 15: click(types[4])
        elif phase == 16: click(teeth['26'])
        elif phase == 17: click((2, 2))
        elif phase == 18:
            assert len(scene.odc_teeth) == 2 and '28' not in scene.odc_teeth
            assert scene.odc_teeth['24'].rest_type == '2'
            assert scene.odc_teeth['24'].contour == 'Preserve this reference'
            assert len(scene.odc_implants) == 1
            with bpy.context.temp_override(area=area, region=region):
                assert bpy.ops.opendental.plan_restorations('EXEC_DEFAULT') == {'CANCELLED'}
                assert bpy.ops.ed.undo() == {'FINISHED'}
        elif phase == 19:
            assert scene.odc_teeth['24'].rest_type == '0'
            assert scene.odc_teeth['25'].rest_type == '1'
            with bpy.context.temp_override(area=area, region=region):
                assert bpy.ops.ed.redo() == {'FINISHED'}
        else:
            assert scene.odc_teeth['24'].rest_type == '2'
            assert scene.odc_teeth['24'].contour == 'Preserve this reference'
            print('ODC_PLAN_RESTORATIONS_MODAL_PASSED', flush=True)
            bpy.ops.wm.quit_blender(); return None
        area.tag_redraw()
        phase += 1
        return .5
    except Exception:
        traceback.print_exc(); os._exit(1)
bpy.app.timers.register(run, first_interval=2)
