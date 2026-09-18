"""Solid blockout stays closed and extrudes along the world-space insertion axis."""
import sys,importlib
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Vector,Euler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
scene=bpy.context.scene
other_scene=bpy.data.scenes.new('Other project')
other_scene.pre_surveyed=True
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
for stored in (False,True):
    bpy.ops.mesh.primitive_cube_add(size=4,location=(3,4,5))
    source=bpy.context.object
    source.rotation_euler=(.2,.3,.4);source.scale=(1.4,.7,1.8)
    sibling=bpy.data.objects.new('Shared data sibling',source.data)
    scene.collection.objects.link(sibling)
    sibling.location=(20,0,0)
    bpy.context.view_layer.update()
    original=source.data;coords=[v.co.copy() for v in original.vertices]
    world=source.matrix_world.copy()
    rotation=Euler((.4,-.2,.3) if stored else (.1,.3,-.2)).to_quaternion()
    direction=rotation@Vector((0,0,1))
    projected=[(world@v.co).dot(direction) for v in original.vertices]
    with bpy.context.temp_override(area=area,region=region):
        area.spaces.active.region_3d.view_rotation=(1,0,0,0) if stored else rotation
        scene.pre_surveyed=stored
        scene.UNDERCUTS_view_props.survey_quaternion=rotation
        scene.UNDERCUTS_props.Modelsprop='Solid'
        scene.tool_settings.use_snap=True
        scene.transform_orientation_slots[0].type='NORMAL'
        assert bpy.ops.opendental.blockout_model()=={'FINISHED'}
    assert source.data!=original and sibling.data==original
    assert all(v.co==co for v,co in zip(original.vertices,coords))
    assert source.matrix_world==world
    assert scene.tool_settings.use_snap and scene.transform_orientation_slots[0].type=='NORMAL'
    assert not scene.pre_surveyed and other_scene.pre_surveyed
    bm=bmesh.new();bm.from_mesh(source.data)
    assert bm.faces and all(edge.is_manifold for edge in bm.edges)
    assert bm.calc_volume(signed=True)>0
    bm.free()
    final=[(world@v.co).dot(direction) for v in source.data.vertices]
    assert abs(min(final)-(min(projected)-10))<.3,(min(final),min(projected)-10)
    assert abs(max(final)-max(projected))<.3,(max(final),max(projected))
# Completing a survey must protect the blocked result from later preview replacement.
bpy.ops.mesh.primitive_cube_add(size=4)
original_model=bpy.context.object
with bpy.context.temp_override(area=area,region=region):
    area.spaces.active.region_3d.view_rotation=(1,0,0,0)
    scene.UNDERCUTS_view_props.colorprop='Blue'
    assert bpy.ops.opendental.view_silhouette_survey(smooth=False)=={'FINISHED'}
    surveyed=bpy.context.object
    outlines=[obj.name for obj in scene.objects if obj.get('odc_survey_owner')==surveyed]
    assert len(outlines)==1
    assert bpy.ops.opendental.blockout_model()=={'FINISHED'}
    blocked=bpy.context.object
    assert blocked==surveyed and blocked.get('odc_survey_source') is None
    assert all(name not in scene.objects for name in outlines)
    finished_data=blocked.data
    bpy.ops.object.select_all(action='DESELECT')
    original_model.hide_set(False);original_model.select_set(True)
    bpy.context.view_layer.objects.active=original_model
    assert bpy.ops.opendental.view_silhouette_survey(smooth=False)=={'FINISHED'}
    assert blocked.name in scene.objects and blocked.data==finished_data
# If remeshing cancels after extrusion, restore the input and remove working data.
bpy.ops.mesh.primitive_cube_add(size=4)
source=bpy.context.object
original=source.data
coordinates=[v.co.copy() for v in original.vertices]
meshes=set(bpy.data.meshes)
module=importlib.import_module(f'{ROOT.name}.Operators.blockout_undercuts')
fake=SimpleNamespace(data=bpy.data,types=bpy.types,ops=SimpleNamespace(
    object=bpy.ops.object,mesh=bpy.ops.mesh,
    opendental=SimpleNamespace(remesh_model=lambda *args: {'CANCELLED'})))
with bpy.context.temp_override(area=area,region=region):
    scene.pre_surveyed=True
    with patch.object(module,'bpy',fake):
        assert bpy.ops.opendental.view_blockout_undercuts_solid()=={'CANCELLED'}
assert source.data==original and set(bpy.data.meshes)==meshes
assert all(v.co==co for v,co in zip(original.vertices,coordinates))
assert source.select_get() and bpy.context.object==source and source.mode=='OBJECT'
assert scene.pre_surveyed
print('ODC_BLOCKOUT_SOLID_PASSED')
