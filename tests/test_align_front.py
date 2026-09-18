"""Viewport alignment supports Euler, quaternion and axis-angle objects."""
import sys,os,traceback,math
from pathlib import Path
import bpy,addon_utils
from mathutils import Euler,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
        model=bpy.context.object
        other=bpy.data.objects.new('Other',model.data);bpy.context.collection.objects.link(other)
        other.location=(10,11,12)
        bpy.context.view_layer.update()
        other_matrix=other.matrix_world.copy()
        coords=[v.co.copy() for v in model.data.vertices]
        with bpy.context.temp_override(area=area,region=region):
            for mode in ('XYZ','QUATERNION','AXIS_ANGLE'):
                model.rotation_mode=mode
                model.matrix_world=Matrix.Translation((3,4,5)) @ Euler((.1,.2,.3)).to_matrix().to_4x4()
                view=Euler((.4,.5,.6)).to_quaternion()
                area.spaces.active.region_3d.view_rotation=view
                bpy.context.view_layer.update()
                expected=Matrix.Rotation(math.pi/2,4,'X') @ view.to_matrix().to_4x4().inverted() @ model.matrix_world
                assert bpy.ops.opendental.align_to_front()=={'FINISHED'}
                bpy.context.view_layer.update()
                assert max(abs(model.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-5
                assert other.matrix_world==other_matrix
                assert coords==[v.co for v in model.data.vertices]
                assert model.rotation_mode==mode
        print('ODC_ALIGN_FRONT_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
