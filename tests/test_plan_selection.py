"""Plan selection handles empty/stale lists and active/selected object modes."""
import sys,importlib
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
utils=importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
settings=utils.get_settings()
scene=bpy.context.scene
for collection,index,role,select in (
    ('odc_teeth','odc_tooth_index','contour',utils.tooth_selection),
    ('odc_implants','odc_implant_index','implant',utils.implant_selection),
    ('odc_splints','odc_splint_index','model',utils.splint_selction),
):
    items=getattr(scene,collection)
    settings.behavior='0'
    assert select(bpy.context)==[]
    bpy.ops.object.select_all(action='DESELECT')
    objects=[]
    for name in ('First','Second'):
        obj=bpy.data.objects.new(collection+' '+name,None)
        scene.collection.objects.link(obj)
        item=items.add();item.name=name;setattr(item,role,obj.name)
        objects.append(obj)
    setattr(scene,index,90)
    assert select(bpy.context)==[]
    assert getattr(scene,index)==90
    settings.behavior='1'
    bpy.context.view_layer.objects.active=objects[1];objects[1].select_set(True)
    assert [x.name for x in select(bpy.context)]==['Second'], collection
    settings.behavior='2';objects[0].select_set(True)
    assert [x.name for x in select(bpy.context)]==['Second','First']
    bpy.context.view_layer.objects.active=None
    assert {x.name for x in select(bpy.context)}=={'First','Second'}
    bpy.ops.object.select_all(action='DESELECT')
    assert select(bpy.context)==[]
    setattr(scene,index,0)
    assert [x.name for x in select(bpy.context)]==['First']
    # A shared model cannot identify one plan; use only an explicit valid list choice.
    setattr(items[0],role,objects[1].name)
    bpy.context.view_layer.objects.active=objects[1]
    objects[1].select_set(True)
    settings.behavior='1'
    assert utils.active_odc_item_candidate(items,objects[1],[]) is None
    setattr(scene,index,90)
    assert select(bpy.context)==[]
    setattr(scene,index,0)
    assert [x.name for x in select(bpy.context)]==['First']
    # Excluded roles must not create a match.
    assert utils.active_odc_item_candidate(items,objects[1],[role]) is None
    setattr(items[0],role,objects[0].name)
    assert utils.active_odc_item_candidate(items,objects[1],[]).name=='Second'
    items.clear()
    for mode in ('0','1','2'):
        settings.behavior=mode
        assert select(bpy.context)==[]
print('ODC_PLAN_SELECTION_PASSED')
