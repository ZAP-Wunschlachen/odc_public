import sys
import os
import traceback
from pathlib import Path
import bpy
import addon_utils
from mathutils import Quaternion, Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
phase = 0
window = region = obj = occupied = area = None
def send(kind):
    for value in ('PRESS','RELEASE'):
        window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
def run():
    global phase,window,region,obj,area,before
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.object
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            view = area.spaces.active.region_3d
            view.view_rotation = Quaternion((1,0,0,0))
            view.view_location = Vector((0,0,0))
            view.view_distance = 10
            view.view_perspective = 'ORTHO'
        elif phase in {1,6}:
            before = set(bpy.data.objects)
            with bpy.context.temp_override(window=window,area=area,region=region):
                assert bpy.ops.opendental.place_ortho_bracket('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
        elif phase == 2:
            window.event_simulate(type='MOUSEMOVE',value='NOTHING',x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 3:
            send('LEFTMOUSE')
        elif phase == 4:
            send('RET')
        elif phase == 5:
            assert not any(op.bl_idname == 'OPENDENTAL_OT_place_bracket' for op in window.modal_operators)
            added = set(bpy.data.objects)-before
            bracket = next(o for o in added if o.type == 'MESH')
            assert abs(bracket.matrix_world.translation.z-1) < 1e-4
            strokes = next(o for o in added if o.type == 'GREASEPENCIL')
            assert strokes.parent == bracket
            drawing = strokes.data.layers[0].frames[0].drawing
            assert len(drawing.strokes) == 2
            assert all(len(stroke.points) >= 4 for stroke in drawing.strokes)
        elif phase == 7:
            send('ESC')
        else:
            assert set(bpy.data.objects) == before
            assert not any(op.bl_idname == 'OPENDENTAL_OT_place_bracket' for op in window.modal_operators)
            print('ODC_BRACKET_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .8
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
