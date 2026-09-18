"""Foreground point picking across a 3D viewport and Image Editor."""
import sys,os,traceback,importlib
from pathlib import Path
import bpy,addon_utils
from mathutils import Quaternion,Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
phase=0
state=None
def send(kind,region,x=None,y=None):
    x=region.width//2 if x is None else x
    y=region.height//2 if y is None else y
    for value in ('PRESS','RELEASE'):
        bpy.context.window.event_simulate(type=kind,value=value,x=region.x+x,y=region.y+y)
def run():
    global phase,area,region,editor,imgregion,state,objects_before,m
    try:
        if phase==0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            m=importlib.import_module(f'{ROOT.name}.Operators.image_object_registration')
            m.register()
            original=m.view3d_draw_callback_2d
            def capture(operator,context):
                global state
                state=operator
                original(operator,context)
            m.view3d_draw_callback_2d=capture
            bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
            bpy.ops.mesh.primitive_cube_add()
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            region=next(r for r in area.regions if r.type=='WINDOW')
            editor=next(a for a in bpy.context.screen.areas if a.type=='PROPERTIES')
            editor.type='IMAGE_EDITOR'
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.view3d.img_obj_register('INVOKE_DEFAULT')=={'CANCELLED'}
            editor.spaces.active.image=bpy.data.images.new('Synthetic image',width=256,height=256)
            view=area.spaces.active.region_3d
            view.view_rotation=Quaternion((1,0,0,0));view.view_location=Vector((0,0,0))
            view.view_distance=10;view.view_perspective='ORTHO'
        elif phase==1:
            imgregion=next(r for r in editor.regions if r.type=='WINDOW')
            with bpy.context.temp_override(area=editor,region=imgregion):
                bpy.ops.image.view_all()
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.view3d.img_obj_register('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
            objects_before=set(bpy.data.objects)
        elif phase==2:
            send('LEFTMOUSE',region)
        elif phase==3:
            assert len(state.points_3d)==1
            assert abs(state.points_3d[0].z-1)<1e-4,state.points_3d
            assert state.points_3d[0].xy.length<.01,state.points_3d
            x,y=imgregion.view2d.view_to_region(.5,.5,clip=False)
            send('LEFTMOUSE',imgregion,x,y)
        elif phase==4:
            assert len(state.pixel_coords)==1,state.pixel_coords
            assert (state.pixel_coords[0]-Vector((128,128))).length<2,state.pixel_coords
            send('M',region)
        elif phase==5:
            assert set(bpy.data.objects)==objects_before
            send('ESC',region)
        else:
            assert not any(op.bl_idname=='VIEW3D_OT_image_view3d_modal' for op in bpy.context.window.modal_operators)
            assert set(bpy.data.objects)==objects_before
            print('ODC_IMAGE_REGISTRATION_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase+=1
        return .8
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
