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
window = region = obj = occupied = None
def send(kind):
    for value in ('PRESS','RELEASE'):
        window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
def run():
    global phase,window,region,obj,occupied
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.object
            occupied = bpy.data.objects.new('47', None)
            bpy.context.scene.collection.objects.link(occupied)
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=window,area=area,region=region):
                view = area.spaces.active.region_3d
                view.view_rotation = Quaternion((1,0,0,0))
                view.view_location = Vector((0,0,0))
                view.view_distance = 10
                view.view_perspective = 'ORTHO'
                assert bpy.ops.opendental.fast_label_teeth('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('DOWN_ARROW')
        elif phase == 1:
            send('LEFTMOUSE')
        elif phase == 2:
            assert obj.name == 'Cube'
            assert occupied.name == '47'
            occupied.name = 'Previously labeled'
            send('LEFTMOUSE')
        elif phase == 3:
            assert obj.name == '47', obj.name
            assert obj.show_name
            send('RET')
        else:
            assert not any(op.bl_idname == 'OPENDENTAL_OT_fast_label_teeth' for op in window.modal_operators)
            print('ODC_LABEL_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .8
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
