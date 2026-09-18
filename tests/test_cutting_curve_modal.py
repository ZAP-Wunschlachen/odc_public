"""Start and cancel the interactive curve cutter."""
import sys,os,traceback
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
phase=0
def run():
    global phase,model,area,region,before,collision,curve
    try:
        if phase==0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            bpy.ops.mesh.primitive_cube_add(size=10)
            model=bpy.context.object
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            region=next(r for r in area.regions if r.type=='WINDOW')
            bpy.context.scene.cursor.location=(0,0,5)
            collision=bpy.data.objects.new('Cutting_curve',None)
            bpy.context.collection.objects.link(collision)
            before=set(bpy.data.objects)
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.make_curve('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
        elif phase==1:
            added=set(bpy.data.objects)-before
            assert len(added)==1
            curve=added.pop()
            assert curve.type=='CURVE' and curve!=collision
            assert bpy.context.scene.get('odc_cutting_curve')==curve
            assert curve.modifiers[0].target==model
            for value in ('PRESS','RELEASE'):
                bpy.context.window.event_simulate(type='ESC',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase==2:
            assert set(bpy.data.objects)==before
            assert bpy.context.object==model
            with bpy.context.temp_override(area=area,region=region):
                assert bpy.ops.opendental.make_curve('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
            curve=bpy.context.object
            for kind in ('DEL','RET'):
                for value in ('PRESS','RELEASE'):
                    bpy.context.window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase in {3,4,5}:
            if phase==3:
                assert len(curve.data.splines[0].bezier_points)==1
                assert not curve.data.splines[0].use_cyclic_u
                assert len(curve.modifiers)==1
            bpy.context.scene.cursor.location={3:(2,0,5),4:(2,2,5),5:(0,2,5)}[phase]
            # Release follows the cursor tool's normal placement action.
            bpy.context.window.event_simulate(type='LEFTMOUSE',value='RELEASE',x=region.x+region.width//2,y=region.y+region.height//2)
        elif phase==6:
            assert len(curve.data.splines[0].bezier_points)==4
            for value in ('PRESS','RELEASE'):
                bpy.context.window.event_simulate(type='RET',value=value,x=region.x+region.width//2,y=region.y+region.height//2)
        else:
            assert curve.data.splines[0].use_cyclic_u
            assert len(curve.modifiers)==0
            assert curve.type=='CURVE'
            assert all(abs((curve.matrix_world@p.co).z-5)<1e-4 for p in curve.data.splines[0].bezier_points)
            assert collision.name=='Cutting_curve'
            print('ODC_CUTTING_CURVE_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender();return None
        phase+=1;return .8
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
