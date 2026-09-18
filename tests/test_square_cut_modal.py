"""Square cutter placement and cancellation in a real viewport."""
import sys,os,traceback,importlib
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
phase=0
def send(kind):
    for value in ('PRESS','RELEASE'):
        bpy.context.window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
def run():
    global phase,area,region,model,other,original,objects,mesh,coords
    try:
        if phase==0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            m=importlib.import_module(f'{ROOT.name}.Operators.model_ops');m.ShowMessageBox=lambda **kwargs:None
            bpy.ops.mesh.primitive_cube_add(location=(3,4,5));model=bpy.context.object
            other=bpy.data.objects.new('my_frame_cutter',None);bpy.context.collection.objects.link(other)
            other.select_set(True)
            bpy.context.tool_settings.use_snap=True
            bpy.context.scene.ODC_modops_props.cutting_target='Previous'
            original=model.matrix_world.copy();mesh=model.data;coords=[v.co.copy() for v in mesh.vertices]
            objects=set(bpy.data.objects)
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            region=next(r for r in area.regions if r.type=='WINDOW')
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.square_cut('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        elif phase==1:send('ESC')
        elif phase==2:
            assert set(bpy.data.objects)==objects
            assert model.matrix_world==original and model.data==mesh
            assert coords==[v.co for v in mesh.vertices]
            assert other.select_get() and not other.hide_get()
            assert bpy.context.tool_settings.use_snap
            assert bpy.context.scene.ODC_modops_props.cutting_target=='Previous'
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.square_cut('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        elif phase==3:send('RET')
        else:
            added=set(bpy.data.objects)-objects
            assert len(added)==1
            cutter=added.pop()
            assert cutter.type=='MESH' and cutter.get('odc_square_target')==model
            assert other.name=='my_frame_cutter'
            assert bpy.context.object==cutter and cutter.display_type=='WIRE'
            assert bpy.context.scene.ODC_modops_props.cutting_target==model.name
            assert bpy.ops.opendental.square_cut_exit()=={'FINISHED'}
            assert set(bpy.data.objects)==objects
            print('ODC_SQUARE_CUT_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender();return None
        phase+=1;return .8
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
