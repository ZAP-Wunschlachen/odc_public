"""Injected failures restore data, selection and tools at three pipeline stages."""
import sys, importlib
from pathlib import Path
from unittest.mock import patch
import bpy, addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
module=importlib.import_module(f'{ROOT.name}.Operators.full_arch_methods')
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
def check(kind):
    if kind == 'mesh':
        bpy.ops.mesh.primitive_circle_add(vertices=32,radius=10,fill_type='NOTHING')
    else:
        bpy.ops.curve.primitive_bezier_circle_add(radius=10)
    source=bpy.context.object
    parent=bpy.data.objects.new('Parent',None)
    bpy.context.collection.objects.link(parent)
    source.parent=parent
    parent.select_set(True)
    bpy.context.view_layer.update()
    world=source.matrix_world.copy()
    data=source.data
    vertices=data.vertices if kind=='mesh' else data.splines[0].bezier_points
    coords=[v.co.copy() for v in vertices]
    selected=set(bpy.context.selected_objects)
    objects=set(bpy.data.objects);meshes=set(bpy.data.meshes);curves=set(bpy.data.curves)
    bpy.context.scene.cursor.location=(8,9,10)
    bpy.context.tool_settings.transform_pivot_point='CURSOR'
    bpy.context.scene.transform_orientation_slots[0].type='NORMAL'
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    for owner,name in ((module.odcutils,'reorient_object'),(module,'space_selected'),(module.odcutils,'parent_in_place')):
        with bpy.context.temp_override(area=area,region=region):
            area.spaces.active.region_3d.view_rotation=(1,0,0,0)
            with patch.object(owner,name,side_effect=RuntimeError('Injected '+name)) as failure:
                assert bpy.ops.opendental.cloth_fill_tray(oct=5,smooth=3)=={'CANCELLED'}
                assert failure.call_count==1
        assert set(bpy.data.objects)==objects
        assert set(bpy.data.meshes)==meshes and set(bpy.data.curves)==curves
        assert source.data==data and source.matrix_world==world
        assert all(v.co==co for v,co in zip(vertices,coords))
        assert set(bpy.context.selected_objects)==selected and bpy.context.object==source
        assert bpy.context.mode=='OBJECT'
        assert tuple(bpy.context.scene.cursor.location)==(8,9,10)
        assert bpy.context.tool_settings.transform_pivot_point=='CURSOR'
        assert bpy.context.scene.transform_orientation_slots[0].type=='NORMAL'
        assert tuple(bpy.context.tool_settings.mesh_select_mode)==(False,False,True)

for kind in ('mesh','curve'):
    check(kind)
print('ODC_CLOTH_FILL_FAILURE_PASSED')
