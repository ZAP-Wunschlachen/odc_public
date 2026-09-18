"""Center active model on a cursor landmark and cancel without moving geometry."""
import sys,os,traceback,importlib
from pathlib import Path
import bpy,addon_utils
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
phase=0
def send(kind):
    for value in ('PRESS','RELEASE'):
        bpy.context.window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
def run():
    global phase,area,region,model,other,points,other_matrix
    try:
        if phase==0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            m=importlib.import_module(f'{ROOT.name}.Operators.model_ops')
            m.ShowMessageBox=lambda **kwargs:None
            bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
            model=bpy.context.object
            other=bpy.data.objects.new('Other',model.data.copy());bpy.context.collection.objects.link(other)
            other.location=(10,11,12);other.select_set(True)
            bpy.context.view_layer.update()
            other_matrix=other.matrix_world.copy()
            points=[model.matrix_world@v.co for v in model.data.vertices]
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            region=next(r for r in area.regions if r.type=='WINDOW')
            bpy.context.scene.cursor.location=(2,3,4)
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.center_model('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        elif phase==1:send('RET')
        elif phase==2:
            bpy.context.view_layer.update()
            assert all((model.matrix_world@v.co-(p-Vector((2,3,4)))).length<1e-5 for v,p in zip(model.data.vertices,points))
            assert other.matrix_world==other_matrix
            points=[model.matrix_world@v.co for v in model.data.vertices]
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.center_model('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
            bpy.context.scene.cursor.location=(8,9,10)
        elif phase==3:send('ESC')
        else:
            assert all((model.matrix_world@v.co-p).length<1e-5 for v,p in zip(model.data.vertices,points))
            assert other.matrix_world==other_matrix
            assert not any(op.bl_idname=='OPENDENTAL_OT_center_Model' for op in bpy.context.window.modal_operators)
            print('ODC_CENTER_MODEL_PASSED',flush=True)
            bpy.ops.wm.quit_blender();return None
        phase+=1;return .8
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
