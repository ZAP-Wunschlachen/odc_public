"""Foreground hollowing of a closed synthetic model with name collisions."""
import sys,os,traceback
from pathlib import Path
import bpy,bmesh,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
        bpy.ops.mesh.primitive_cube_add(size=10,location=(3,4,5))
        source=bpy.context.object
        bpy.context.view_layer.update()
        points=[source.matrix_world@v.co for v in source.data.vertices]
        collision=bpy.data.objects.new('Mball_object',None);bpy.context.collection.objects.link(collision)
        bpy.context.scene.ODC_modops_props.show_box=False
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        before=set(bpy.data.objects)
        with bpy.context.temp_override(area=area,region=region):
            assert bpy.ops.opendental.hollow_model()=={'FINISHED'}
        result=bpy.context.object
        assert result!=source
        assert set(bpy.data.objects)-before=={result}
        assert collision.name in bpy.data.objects
        assert all((source.matrix_world@v.co-p).length<1e-5 for v,p in zip(source.data.vertices,points))
        bm=bmesh.new();bm.from_mesh(result.data)
        assert bm.faces and all(e.is_manifold for e in bm.edges)
        volume=bm.calc_volume(signed=False)
        assert 0<volume<999,volume
        bm.free()
        # A ray from inside must first hit the inward-facing cavity wall.
        hit,location,normal,_=result.ray_cast((0,0,0),(1,0,0))
        assert hit and 0<location.x<4.9,(hit,location)
        assert normal.x<0,normal
        print('ODC_HOLLOW_MODEL_PASSED',volume,flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
