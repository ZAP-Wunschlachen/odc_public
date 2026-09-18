"""Fill selected mesh boundaries without modifying another object's shared data."""
import sys
from pathlib import Path
import bpy, bmesh, addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
assert not bpy.ops.opendental.fill.poll(), 'Fill must reject missing active mesh'
bpy.ops.object.empty_add()
assert not bpy.ops.opendental.fill.poll(), 'Fill must reject non-mesh objects'
bpy.ops.mesh.primitive_cube_add(size=2)
obj=bpy.context.object
bm=bmesh.new();bm.from_mesh(obj.data)
top=max(bm.faces,key=lambda face:face.calc_center_median().z)
bmesh.ops.delete(bm,geom=[top],context='FACES_ONLY')
for face in bm.faces: face.select_set(False)
for edge in bm.edges: edge.select_set(False)
for vertex in bm.verts: vertex.select_set(False)
for edge in bm.edges:
    if all(vertex.co.z>.9 for vertex in edge.verts):
        edge.select_set(True)
bm.to_mesh(obj.data);bm.free()
sibling=bpy.data.objects.new('Shared open cube',obj.data)
bpy.context.collection.objects.link(sibling)
original=sibling.data
original_coords=[tuple(v.co) for v in original.vertices]
assert bpy.ops.opendental.fill()=={'FINISHED'}
assert bpy.context.mode=='EDIT_MESH'
bpy.ops.object.mode_set(mode='OBJECT')
assert obj.data!=original and sibling.data==original
assert len(original.polygons)==5
assert [tuple(v.co) for v in original.vertices]==original_coords
assert len(obj.data.polygons)==6
bm=bmesh.new();bm.from_mesh(obj.data)
assert all(edge.is_manifold for edge in bm.edges)
assert abs(abs(bm.calc_volume())-8)<1e-5
bm.free()
# No vertex selection is not a successful fill.
for vertex in obj.data.vertices: vertex.select=False
for edge in obj.data.edges: edge.select=False
for face in obj.data.polygons: face.select=False
assert bpy.ops.opendental.fill()=={'CANCELLED'}
assert len(obj.data.polygons)==6
# In Edit Mode use the live BMesh selection rather than stale Mesh flags.
bpy.ops.mesh.primitive_plane_add(size=2, location=(4,0,0))
plane=bpy.context.object
bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(plane.data)
bmesh.ops.delete(bm,geom=list(bm.faces),context='FACES_ONLY')
for edge in bm.edges: edge.select_set(True)
bmesh.update_edit_mesh(plane.data)
assert bpy.ops.opendental.fill()=={'FINISHED'}
assert bpy.context.mode=='EDIT_MESH'
bm=bmesh.from_edit_mesh(plane.data)
assert len(bm.faces)==1 and abs(bm.faces[0].calc_area()-4)<1e-5
bpy.ops.object.mode_set(mode='OBJECT')
assert len(sibling.data.polygons)==5
print('ODC_FILL_HOLES_PASSED',bpy.app.version_string)
