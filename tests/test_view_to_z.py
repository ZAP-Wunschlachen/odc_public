"""Foreground view-aligned local coordinate conversion."""
import sys,os,traceback,math
from pathlib import Path
import bpy,addon_utils
from mathutils import Euler,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
        obj=bpy.context.object
        obj.rotation_euler=(.2,.3,.4)
        shared=bpy.data.objects.new('Shared',obj.data);bpy.context.collection.objects.link(shared)
        old_data=shared.data
        bpy.context.view_layer.update()
        points=[obj.matrix_world@v.co for v in obj.data.vertices]
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        rotation=Euler((.4,.5,.6)).to_quaternion()
        area.spaces.active.region_3d.view_rotation=rotation
        with bpy.context.temp_override(area=area,region=region):
            assert bpy.ops.view3d.view_to_z(keep_orientation=False)=={'FINISHED'}
            bpy.context.view_layer.update()
            assert obj.matrix_world.to_quaternion().rotation_difference(rotation).angle<1e-5
            assert all((obj.matrix_world@v.co-p).length<1e-5 for v,p in zip(obj.data.vertices,points))
            assert shared.data==old_data and obj.data!=old_data
            assert bpy.ops.view3d.view_to_z(keep_orientation=True)=={'FINISHED'}
            bpy.context.view_layer.update()
            assert all(math.isfinite(c) for v in obj.data.vertices for c in obj.matrix_world@v.co)
        print('ODC_VIEW_TO_Z_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
