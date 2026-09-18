"""Implant plan creation rejects duplicate names without losing existing data."""
import sys,importlib,tempfile
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
module=importlib.import_module(f'{ROOT.name}.Operators.classes')
scene=bpy.context.scene
for name in ('Existing implant geometry','Existing drill hole'):
    obj=bpy.data.objects.new(name,bpy.data.meshes.new(name))
    scene.collection.objects.link(obj)
objects=set(bpy.data.objects)
assert bpy.ops.opendental.add_implant_restoration(name='Custom implant',rest_type='1')=={'FINISHED'}
item=scene.odc_implants['Custom implant']
item.implant='Existing implant geometry'
item.inner='Existing drill hole'
assert bpy.ops.opendental.add_implant_restoration(name='Custom implant',rest_type='0')=={'CANCELLED'}
assert len(scene.odc_implants)==1
assert item.rest_type=='1' and item.implant=='Existing implant geometry' and item.inner=='Existing drill hole'
assert bpy.ops.opendental.add_implant_restoration(ob_list='0')=={'FINISHED'}
assert scene.odc_implants[-1].name==str(module.teeth[0])
assert bpy.ops.opendental.add_implant_restoration(name=str(module.teeth[0]))=={'CANCELLED'}
assert bpy.ops.opendental.add_implant_restoration(ob_list='0')=={'CANCELLED'}
assert len(scene.odc_implants)==2
assert bpy.ops.opendental.add_implant_restoration(name='Another implant')=={'FINISHED'}
assert len(scene.odc_implants)==3
assert set(bpy.data.objects)==objects
expected=[(x.name,x.rest_type,x.implant,x.inner) for x in scene.odc_implants]
with tempfile.TemporaryDirectory(prefix='odc-implant-plan-') as folder:
    filename=str(Path(folder)/'plans.blend')
    assert bpy.ops.wm.save_as_mainfile(filepath=filename)=={'FINISHED'}
    assert bpy.ops.wm.open_mainfile(filepath=filename)=={'FINISHED'}
    assert [(x.name,x.rest_type,x.implant,x.inner) for x in bpy.context.scene.odc_implants]==expected
print('ODC_IMPLANT_PLAN_ADD_PASSED')
