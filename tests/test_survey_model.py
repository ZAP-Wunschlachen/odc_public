"""Public survey operator: transformed geometry, ownership and scene-local state."""
import sys
from pathlib import Path
import bpy,addon_utils
from mathutils import Vector,Euler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
scene=bpy.context.scene
other_scene=bpy.data.scenes.new('Other project')
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
bpy.ops.mesh.primitive_cube_add(size=2,location=(3,4,5))
source=bpy.context.object
source.vertex_groups.new(name='Keep original group')
material=bpy.data.materials.new('Original');source.data.materials.append(material)
original_data=source.data
coordinates=[v.co.copy() for v in source.data.vertices]
foreign=[]
for suffix in ('_survey(Green)','_survey(Green)_silhouette'):
    obj=bpy.data.objects.new(source.name+suffix,None);scene.collection.objects.link(obj);foreign.append(obj)
with bpy.context.temp_override(area=area,region=region):
    area.spaces.active.region_3d.view_rotation=(1,0,0,0)
    before=set(bpy.data.objects)
    assert bpy.ops.opendental.view_silhouette_survey(smooth=False)=={'CANCELLED'}
    assert set(bpy.data.objects)==before and not scene.pre_surveyed
    scene.UNDERCUTS_view_props.colorprop='Green'
    for attempt in range(3):
        if attempt < 2:
            source.hide_set(False)
            bpy.ops.object.select_all(action='DESELECT')
            source.select_set(True);bpy.context.view_layer.objects.active=source
        if attempt == 1:
            source.rotation_euler=(.2,.3,.4);source.scale=(2,.7,1.3)
        bpy.context.view_layer.update()
        world=source.matrix_world.copy()
        normals=world.inverted().transposed().to_3x3()
        back={face.index:(normals@face.normal).dot(Vector((0,0,1))) < -1e-6 for face in source.data.polygons}
        adjacent={}
        for face in source.data.polygons:
            for edge in face.edge_keys:adjacent.setdefault(tuple(sorted(edge)),[]).append(face.index)
        expected=[edge for edge,faces in adjacent.items() if back[faces[0]]!=back[faces[1]]]
        assert bpy.ops.opendental.view_silhouette_survey(smooth=False)=={'FINISHED'}
        survey=bpy.context.object
        assert survey.get('odc_survey_source')==source
        silhouettes=[obj for obj in scene.objects if obj.get('odc_survey_owner')==survey]
        assert len(silhouettes)==1
        silhouette=silhouettes[0]
        assert len(silhouette.data.edges)==len(expected)
        assert len(silhouette.data.polygons)==0
        def key(point):return tuple(round(value,4) for value in point)
        actual_edges={frozenset(key(silhouette.matrix_world@silhouette.data.vertices[i].co) for i in edge.vertices) for edge in silhouette.data.edges}
        expected_edges={frozenset(key(world@source.data.vertices[i].co) for i in edge) for edge in expected}
        assert actual_edges==expected_edges
        assert [f.material_index for f in survey.data.polygons]==[int(back[f.index]) for f in source.data.polygons]
        assert sum(obj.get('odc_survey_source')==source for obj in scene.objects)==1
        assert source.data==original_data and source.matrix_world==world
        assert all(v.co==co for v,co in zip(source.data.vertices,coordinates))
        assert source.vertex_groups.get('Keep original group') is not None
        assert list(source.data.materials)==[material]
        assert all(obj.name in scene.objects for obj in foreign)
        assert scene.pre_surveyed and not other_scene.pre_surveyed
print('ODC_SURVEY_MODEL_PASSED')
