"""Behavior checks with synthetic geometry; no patient scans or user preferences."""
import sys,json,traceback,math
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True,persistent=False)
results=[]
def reset():
    if bpy.context.object and bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    for name in ['odc_teeth','odc_implants','odc_bridges','odc_splints']:getattr(bpy.context.scene,name).clear()
def cube(location=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=2,location=location)
    return bpy.context.object
def select(*objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
def check(name,fn):
    reset()
    try:
        fn();results.append({'test':name,'status':'passed'})
    except Exception as e:
        traceback.print_exc();results.append({'test':name,'status':'failed','error':str(e)})
def join_separate():
    a=cube();b=cube((5,0,0));select(a,b)
    assert bpy.ops.opendental.join_models()=={'FINISHED'}
    assert len(bpy.context.scene.objects)==1 and len(a.data.vertices)==16
    assert bpy.ops.opendental.separate_models()=={'FINISHED'}
    assert len(bpy.context.scene.objects)==2
    assert sorted(len(o.data.vertices) for o in bpy.context.scene.objects)==[8,8]
def parenting():
    a=cube((2,0,0));b=cube((5,1,0));select(a,b)
    before=b.matrix_world.copy()
    assert bpy.ops.opendental.parent_models()=={'FINISHED'}
    assert b.parent==a
    bpy.context.view_layer.update()
    assert max(abs(b.matrix_world[i][j]-before[i][j]) for i in range(4) for j in range(4))<1e-5
    select(b)
    assert bpy.ops.opendental.unparent_models()=={'FINISHED'}
    assert b.parent is None
    bpy.context.view_layer.update()
    assert max(abs(b.matrix_world[i][j]-before[i][j]) for i in range(4) for j in range(4))<1e-5

def color():
    a=cube()
    assert bpy.ops.opendental.model_color()=={'FINISHED'}
    assert len(a.data.materials)==1
    assert bpy.ops.opendental.remove_model_color()=={'FINISHED'}
    assert len(a.data.materials)==0

def decimate():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16)
    a=bpy.context.object;before=len(a.data.polygons)
    bpy.context.scene.ODC_modops_props.decimate_ratio=.25
    assert bpy.ops.opendental.decimate_model()=={'FINISHED'}
    assert 0<len(a.data.polygons)<before*.8
    assert len(a.modifiers)==0

def offset():
    a=cube();before=[v.co.copy() for v in a.data.vertices]
    bpy.context.scene.ODC_modops_props.offset=.2
    assert bpy.ops.opendental.add_offset()=={'FINISHED'}
    b=bpy.context.object;assert a!=b and len(b.data.vertices)==8
    displacement=[(v.co-before[i]).length for i,v in enumerate(b.data.vertices)]
    assert all(abs(d-.2)<1e-4 for d in displacement),displacement
    assert all((v.co-before[i]).length<1e-8 for i,v in enumerate(a.data.vertices))

def remesh():
    a=cube()
    assert bpy.ops.opendental.remesh_model()=={'FINISHED'}
    assert len(a.data.vertices)>8
    bm=bmesh.new();bm.from_mesh(a.data)
    assert all(e.is_manifold for e in bm.edges)
    bm.free()

def clearance():
    a=cube();b=cube((2.1,0,0));select(a,b)
    assert bpy.ops.opendental.check_clearance(min_d=.05,max_d=.4)=={'FINISHED'}
    for obj,target in [(a,b),(b,a)]:
        group=obj.vertex_groups['clearance '+target.name]
        weights=[group.weight(v.index) for v in obj.data.vertices]
        assert max(weights)>min(weights)
        assert abs(max(weights)-(0.4-0.1)/(0.4-0.05))<1e-5,weights
    b.location.x=10
    bpy.context.view_layer.update()
    group=a.vertex_groups['clearance '+b.name]
    assert all(group.weight(v.index)==0 for v in a.data.vertices), 'Clearance did not refresh after target movement'
    # Repeating the command updates the existing measurement, not a new group.
    select(a,b)
    assert bpy.ops.opendental.check_clearance(min_d=.02,max_d=.8)=={'FINISHED'}
    assert len(a.vertex_groups)==1 and len(b.vertex_groups)==1


def planning():
    assert bpy.ops.opendental.add_tooth_restoration(name='25',rest_type='0')=={'FINISHED'}
    assert len(bpy.context.scene.odc_teeth)==1 and bpy.context.scene.odc_teeth[0].name=='25'
    assert bpy.ops.opendental.remove_tooth_restoration()=={'FINISHED'}
    assert len(bpy.context.scene.odc_teeth)==0

def cursor():
    bpy.context.scene.cursor.location=(3,4,5)
    assert bpy.ops.opendental.center_cursor()=={'FINISHED'}
    assert bpy.context.scene.cursor.location.length<1e-6

for name,fn in [('join_separate',join_separate),('parenting_preserves_world_transform',parenting),('model_color',color),('decimate',decimate),('offset_distance_and_source_preservation',offset),('remesh_closed_surface',remesh),('clearance_respects_input_distances',clearance),('restoration_planning',planning),('center_cursor',cursor)]:check(name,fn)
reset();addon_utils.disable(ROOT.name,default_set=True)
report={'blender':bpy.app.version_string,'results':results,'passed':sum(r['status']=='passed' for r in results),'failed':sum(r['status']=='failed' for r in results)}
report_path=ROOT/'tests/artifacts/model_workflows.json'
report_path.parent.mkdir(parents=True,exist_ok=True)
report_path.write_text(json.dumps(report,indent=2))
print('ODC_TEST_RESULT',json.dumps(report),flush=True)
if report['failed']:raise SystemExit(1)
