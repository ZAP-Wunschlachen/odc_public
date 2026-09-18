"""Foreground model-base construction from an open bottom boundary."""
import sys,os,traceback
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Quaternion,Euler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
        bpy.ops.mesh.primitive_cube_add(size=10,location=(3,4,5))
        source=bpy.context.object
        bm=bmesh.new();bm.from_mesh(source.data)
        face=min(bm.faces,key=lambda f:f.calc_center_median().z)
        bmesh.ops.delete(bm,geom=[face],context='FACES_ONLY')
        bm.to_mesh(source.data);bm.free()
        rotation=Euler((.3,.4,.5)).to_quaternion() if '--tilted' in sys.argv else Quaternion((1,0,0,0))
        source.matrix_world=rotation.to_matrix().to_4x4() @ source.matrix_world
        bpy.context.view_layer.update()
        points=[source.matrix_world@v.co for v in source.data.vertices]
        bpy.context.scene.ODC_modops_props.base_height=3
        bpy.context.scene.ODC_modops_props.show_box=False
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        area.spaces.active.region_3d.view_rotation=rotation
        with bpy.context.temp_override(area=area,region=region):
            assert bpy.ops.opendental.model_base()=={'FINISHED'}
        result=bpy.context.object
        assert result!=source and result.data!=source.data
        bpy.context.view_layer.update()
        assert all((source.matrix_world@v.co-p).length<1e-5 for v,p in zip(source.data.vertices,points))
        bm=bmesh.new();bm.from_mesh(result.data)
        assert bm.faces and all(e.is_manifold for e in bm.edges)
        assert bm.calc_volume(signed=False)>0
        bm.free()
        coords=[rotation.inverted() @ (result.matrix_world@v.co) for v in result.data.vertices]
        assert abs(min(p.z for p in coords)+3)<1e-4,min(p.z for p in coords)
        assert abs(max(p.z for p in coords)-10)<1e-4
        print('ODC_MODEL_BASE_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
