"""Plan list deletion keeps valid active indices and tolerates empty/stale lists."""
import sys
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
scene=bpy.context.scene
objects=set(bpy.data.objects)
for collection,index,operator in [
 ('odc_teeth','odc_tooth_index','remove_tooth_restoration'),
 ('odc_implants','odc_implant_index','remove_implant_restoration'),
 ('odc_splints','odc_splint_index','remove_splint'),
 ('odc_bridges','odc_bridge_index','remove_bridge_restoration')]:
    items=getattr(scene,collection);items.clear()
    invoke=getattr(bpy.ops.opendental,operator)
    assert invoke()=={'CANCELLED'}
    for name in ('First','Middle','Last'):items.add().name=name
    setattr(scene,index,2)
    assert invoke()=={'FINISHED'}
    assert [x.name for x in items]==['First','Middle']
    assert getattr(scene,index)==1
    setattr(scene,index,15)
    assert invoke()=={'CANCELLED'} and len(items)==2
    setattr(scene,index,0)
    assert invoke()=={'FINISHED'}
    assert [x.name for x in items]==['Middle'] and getattr(scene,index)==0
    assert invoke()=={'FINISHED'}
    assert not items and getattr(scene,index)==0
    assert invoke()=={'CANCELLED'}
assert set(bpy.data.objects)==objects
print('ODC_PLAN_REMOVAL_PASSED')
