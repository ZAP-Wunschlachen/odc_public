"""Preview removes a sphere's underhang and creates one marked open skirt."""
import sys
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=10,location=(3,4,5))
source=bpy.context.object
source.scale=(1.3,.7,2)
bpy.context.view_layer.update()
world=source.matrix_world.copy()
coordinates=[v.co.copy() for v in source.data.vertices]
original=source.data
before=set(bpy.data.objects)
with bpy.context.temp_override(area=area,region=region):
    area.spaces.active.region_3d.view_rotation=(1,0,0,0)
    bpy.context.scene.UNDERCUTS_props.Modelsprop='Preview'
    assert bpy.ops.opendental.blockout_model(smooth=False)=={'FINISHED'}
result=bpy.context.object
assert set(bpy.data.objects)-before=={result}
assert result!=source and result.matrix_world==world
assert source.data==original and source.matrix_world==world
assert all(v.co==co for v,co in zip(source.data.vertices,coordinates))
bm=bmesh.new();bm.from_mesh(result.data);bm.verts.ensure_lookup_table()
assert len(bm.faces)==288
assert len(bm.verts)-len(bm.edges)+len(bm.faces)==1
assert all(edge.is_boundary or edge.is_manifold for edge in bm.edges)
boundary=[edge for edge in bm.edges if edge.is_boundary]
assert len(boundary)==32
for edge in boundary:
    for vertex in edge.verts:
        assert abs((world@vertex.co).z-(-5))<1e-4
# Upper geometry remains at its original top; skirt depth is 10 world units.
assert abs(max((world@vertex.co).z for vertex in bm.verts)-25)<1e-4
assert sum(face.material_index==1 for face in bm.faces)==32
for face in bm.faces:
    extends_down=min((world@vertex.co).z for vertex in face.verts)<4.9
    assert face.material_index==int(extends_down)
assert all(vertex.link_faces for vertex in bm.verts)
reached=set();pending=[bm.verts[0]]
while pending:
    vertex=pending.pop()
    if vertex not in reached:
        reached.add(vertex);pending.extend(edge.other_vert(vertex) for edge in vertex.link_edges)
assert len(reached)==len(bm.verts)
bm.free()
print('ODC_BLOCKOUT_PREVIEW_PASSED')
