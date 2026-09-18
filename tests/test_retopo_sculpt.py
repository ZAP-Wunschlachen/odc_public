"""Foreground sculpt setup, repeat invocation and incompatible-modifier guard."""
import sys,os,traceback
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8)
        model=bpy.context.object
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            assert bpy.ops.opendental.retopo_smooth()=={'FINISHED'}
            assert model.mode=='SCULPT' and model.use_dynamic_topology_sculpting
            sculpt=bpy.context.tool_settings.sculpt
            assert sculpt.brush.sculpt_brush_type=='SIMPLIFY'
            assert sculpt.brush.use_frontface and sculpt.brush.use_automasking_topology
            assert abs(sculpt.brush.strength-.5)<1e-6
            assert sculpt.detail_type_method=='CONSTANT' and sculpt.constant_detail_resolution==16
            assert sculpt.unified_paint_settings.size==50
            assert not sculpt.use_symmetry_x
            assert bpy.ops.opendental.retopo_smooth()=={'FINISHED'}
            assert model.use_dynamic_topology_sculpting
            bpy.ops.sculpt.dynamic_topology_toggle()
            bpy.ops.object.mode_set(mode='OBJECT')
            model.modifiers.new('Multires','MULTIRES')
            coords=[v.co.copy() for v in model.data.vertices]
            assert bpy.ops.opendental.retopo_smooth()=={'CANCELLED'}
            assert model.mode=='OBJECT' and not model.use_dynamic_topology_sculpting
            assert coords==[v.co for v in model.data.vertices]
        print('ODC_RETOPO_SCULPT_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
