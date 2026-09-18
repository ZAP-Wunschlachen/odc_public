"""Cut a synthetic sphere using a closed, extruded curve."""
import sys,os,traceback
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=5)
        model=bpy.context.object
        bpy.context.scene.ODC_modops_props.cutting_target=model.name
        bpy.ops.curve.primitive_bezier_circle_add(radius=4.5)
        curve=bpy.context.object;curve.data.dimensions='3D';curve.data.extrude=3
        bpy.context.scene['odc_cutting_curve']=curve
        other=bpy.data.objects.new('Unrelated',None);bpy.context.collection.objects.link(other)
        foreign_mesh=bpy.data.meshes.new('Unrelated surface')
        foreign_mesh.from_pydata([(20,0,0),(21,0,0),(20,1,0)],[],[(0,1,2)])
        foreign=bpy.data.objects.new('Unrelated surface',foreign_mesh);bpy.context.collection.objects.link(foreign)
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(area=area,region=region):
            assert bpy.ops.opendental.curve_cut()=={'FINISHED'}
        outputs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o!=foreign]
        assert len(outputs)>=2,[(o.name,len(o.data.vertices)) for o in outputs]
        assert all(o.data.polygons for o in outputs)
        assert other.name in bpy.data.objects
        assert foreign.name in bpy.data.objects and foreign.data==foreign_mesh
        assert len(foreign_mesh.vertices)==3 and len(foreign_mesh.polygons)==1
        session=outputs[0].get('odc_curve_cut_session')
        assert session and all(o.get('odc_curve_cut_session')==session for o in outputs)
        bpy.ops.object.select_all(action='DESELECT')
        retained=max(outputs,key=lambda o:sum(v.co.z for v in o.data.vertices)/len(o.data.vertices))
        retained.select_set(True);bpy.context.view_layer.objects.active=retained
        before_coords=[v.co.copy() for v in retained.data.vertices]
        assert bpy.ops.opendental.trim_model()=={'FINISHED'}
        assert [o for o in bpy.context.scene.objects if o.type=='MESH' and o!=foreign]==[retained]
        assert retained.name=='Sphere'
        assert before_coords==[v.co for v in retained.data.vertices]
        assert foreign.name in bpy.data.objects and other.name in bpy.data.objects
        assert retained.get('odc_curve_cut_session') is None
        assert bpy.ops.opendental.trim_model()=={'CANCELLED'}
        print('ODC_CURVE_CUT_PASSED' ,retained.name,flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
