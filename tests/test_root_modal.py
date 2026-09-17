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
window = region = area = None
original_bone = original_axis = None
def run():
    global phase,window,region,area,original_bone,original_axis
    try:
        if phase == 0:
            assert addon_utils.enable(ROOT.name, default_set=True)
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add()
            bpy.context.object.name = '11'
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=window,area=area,region=region):
                view = area.spaces.active.region_3d
                view.view_rotation = Quaternion((1,0,0,0))
                view.view_location = Vector((0,0,0))
                view.view_distance = 10
                view.view_perspective = 'ORTHO'
                assert bpy.ops.opendental.add_bone_roots('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
        elif phase == 1:
            assert bpy.data.objects['Roots'].data.bones.get('11root') is not None
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='LEFTMOUSE',value=value,x=region.x+region.width-40,y=region.y+region.height//2)
        elif phase == 2:
            assert bpy.data.objects.get('11root_empty') is None
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='LEFTMOUSE',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 3:
            axis = bpy.data.objects.get('11root_empty')
            assert axis is not None
            assert abs(axis.location.z-1) < 1e-4, axis.location[:]
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='ESC',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 4:
            assert bpy.data.objects.get('Roots') is None
            assert bpy.data.objects.get('11root_empty') is None
            with bpy.context.temp_override(window=window,area=area,region=region):
                assert bpy.ops.opendental.add_bone_roots('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='LEFTMOUSE',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 5:
            assert bpy.data.objects.get('11root_empty') is not None
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='RET',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 6:
            bone = bpy.data.objects['Roots'].data.bones['11root']
            assert abs(bone.tail_local.z-1) < 1e-4
            assert abs(bone.head_local.z+15) < 1e-4
            assert bpy.data.objects.get('11root_empty') is None
            assert not any(op.bl_idname == 'OPENDENTAL_OT_add_bone_roots' for op in window.modal_operators)
            assert bpy.context.mode == 'OBJECT'
            original_bone = (bone.head_local.copy(), bone.tail_local.copy())
            axis = bpy.data.objects.new('11root_empty', None)
            bpy.context.scene.collection.objects.link(axis)
            axis.location = (5,6,7)
            axis.empty_display_type = 'CUBE'
            axis.empty_display_size = 3
            bpy.ops.mesh.primitive_cube_add(location=(8,0,0))
            bpy.context.object.name = '21'
            bpy.context.view_layer.update()
            original_axis = axis.matrix_world.copy()
            with bpy.context.temp_override(window=window,area=area,region=region):
                assert bpy.ops.opendental.add_bone_roots('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='LEFTMOUSE',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase == 7:
            assert bpy.data.objects['Roots'].data.bones.get('21root') is not None
            assert abs(bpy.data.objects['11root_empty'].location.z-1) < 1e-4
            for value in ('PRESS','RELEASE'):
                window.event_simulate(type='ESC',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        else:
            arm = bpy.data.objects['Roots']
            assert set(arm.data.bones.keys()) == {'11root'}
            bone = arm.data.bones['11root']
            assert (bone.head_local-original_bone[0]).length < 1e-5
            assert (bone.tail_local-original_bone[1]).length < 1e-5
            axis = bpy.data.objects['11root_empty']
            assert max(abs(axis.matrix_world[i][j]-original_axis[i][j]) for i in range(4) for j in range(4)) < 1e-5
            assert axis.empty_display_type == 'CUBE' and axis.empty_display_size == 3
            assert not any(op.bl_idname == 'OPENDENTAL_OT_add_bone_roots' for op in window.modal_operators)
            print('ODC_ROOT_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .8
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
