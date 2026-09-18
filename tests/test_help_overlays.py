"""Start, replace, update and stop all four help overlays."""
import sys,os,traceback,importlib
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
phase=0
names=('crown','implant','bridge','guide')
def run():
    global phase,module,area,region
    try:
        if phase==0:
            assert addon_utils.enable(ROOT.name,default_set=True)
            module=importlib.import_module(f'{ROOT.name}.Operators.help')
            area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
            region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            if phase<4:
                name=names[phase]
                assert getattr(bpy.ops.opendental,'start_'+name+'_help')()=={'FINISHED'}
                handlers=[getattr(module,n+'_help_parser') for n in names]
                assert sum(h in bpy.app.handlers.depsgraph_update_post for h in handlers)==1
                getattr(module,name+'_help_parser')(bpy.context.scene,bpy.context.evaluated_depsgraph_get())
                assert module.help_display_box.raw_text
                if name=='bridge':assert 'Need to plan a bridge' in module.help_display_box.raw_text
                area.tag_redraw()
                phase+=1;return .8
            assert bpy.ops.opendental.stop_help()=={'FINISHED'}
            assert bpy.ops.opendental.stop_help()=={'FINISHED'}
            assert not any(getattr(module,n+'_help_parser') in bpy.app.handlers.depsgraph_update_post for n in names)
            assert all(getattr(module,n+'_help_draw_handle') is None for n in names)
        addon_utils.disable(ROOT.name,default_set=True)
        print('ODC_HELP_OVERLAYS_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
