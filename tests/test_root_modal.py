import sys
import os
import traceback
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
phase = 0
window = region = None
def run():
    global phase,window,region
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            bpy.ops.mesh.primitive_cube_add()
            bpy.context.object.name = '11'
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=window,area=area,region=region):
                assert bpy.ops.opendental.add_bone_roots('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
        elif phase == 1:
            assert bpy.data.objects['Roots'].data.bones.get('11root') is not None
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='RET',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        else:
            assert not any(op.bl_idname == 'OPENDENTAL_OT_add_bone_roots' for op in window.modal_operators)
            assert bpy.context.mode == 'OBJECT'
            print('ODC_ROOT_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .8
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
