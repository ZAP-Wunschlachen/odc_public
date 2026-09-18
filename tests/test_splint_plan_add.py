"""Splint plans link active/selected models and preserve data on save/reopen."""
import sys,tempfile
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
scene=bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
model=bpy.context.object
model_name=model.name
objects=set(bpy.data.objects)
assert bpy.ops.opendental.add_splint(name='Active model')=={'FINISHED'}
assert scene.odc_splints[-1].model==model_name
assert bpy.ops.opendental.add_splint(name='Unlinked',link_active=False)=={'FINISHED'}
assert scene.odc_splints[-1].model==''
bpy.context.view_layer.objects.active=None
assert bpy.ops.opendental.add_splint(name='Selected model')=={'FINISHED'}
assert scene.odc_splints[-1].model==model_name
bpy.ops.object.select_all(action='DESELECT')
assert bpy.ops.opendental.add_splint(name='Pending model')=={'FINISHED'}
assert scene.odc_splints[-1].model==''
assert set(bpy.data.objects)==objects
expected=[(item.name,item.model) for item in scene.odc_splints]
with tempfile.TemporaryDirectory(prefix='odc-splint-plan-') as folder:
    filename=str(Path(folder)/'plans.blend')
    assert bpy.ops.wm.save_as_mainfile(filepath=filename)=={'FINISHED'}
    assert bpy.ops.wm.open_mainfile(filepath=filename)=={'FINISHED'}
    assert [(item.name,item.model) for item in bpy.context.scene.odc_splints]==expected
print('ODC_SPLINT_PLAN_ADD_PASSED')
