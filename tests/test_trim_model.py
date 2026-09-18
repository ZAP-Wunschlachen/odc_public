"""Keep multiple selected parts without touching another cutting session."""
import sys
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
parts=[]
for i in range(4):
    bpy.ops.mesh.primitive_cube_add(location=(i*3,0,0))
    obj=bpy.context.object
    obj['odc_curve_cut_session']='first' if i<3 else 'second'
    obj['odc_curve_cut_original_name']='Scan'
    parts.append(obj)
bpy.ops.object.select_all(action='DESELECT')
parts[0].select_set(True);parts[1].select_set(True)
bpy.context.view_layer.objects.active=parts[0]
other=parts[3];other_matrix=other.matrix_world.copy()
remove_mesh=parts[2].data.name
assert bpy.ops.opendental.trim_model()=={'FINISHED'}
assert set(bpy.context.scene.objects)=={parts[0],parts[1],other}
assert set(bpy.context.selected_objects)=={parts[0],parts[1]}
assert other.get('odc_curve_cut_session')=='second' and other.matrix_world==other_matrix
assert remove_mesh not in bpy.data.meshes
assert parts[0].name=='Scan'
print('ODC_TRIM_MODEL_PASSED')
