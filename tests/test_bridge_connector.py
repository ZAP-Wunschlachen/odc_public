import sys
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
m = importlib.import_module(f'{ROOT.name}.Operators.bridge_methods')
bm = bmesh.new()
for x in (-2,2):
    vertices = bmesh.ops.create_cube(bm, size=2)['verts']
    bmesh.ops.translate(bm, verts=vertices, vec=Vector((x,0,0)))
mesh = bpy.data.meshes.new('Connector fixture')
bm.to_mesh(mesh)
bm.free()
obj = bpy.data.objects.new('Connector fixture', mesh)
bpy.context.scene.collection.objects.link(obj)
for name, x in (('A',-1),('B',1)):
    group = obj.vertex_groups.new(name=name)
    group.add([v.index for v in mesh.vertices if abs(v.co.x-x)<1e-6],1,'REPLACE')
obj.vertex_groups.new(name='Connectors')
m.bridge_loop_2(bpy.context,obj,'A','B',3,0,.5,group3='Connectors')
bm = bmesh.new()
bm.from_mesh(obj.data)
assert bm.faces and all(e.is_manifold for e in bm.edges)
# A single connected component proves that the two boxes were joined.
bm.verts.ensure_lookup_table()
seen = set()
queue = [bm.verts[0]] if bm.verts else []
while queue:
    v = queue.pop()
    if v in seen: continue
    seen.add(v)
    queue.extend(e.other_vert(v) for e in v.link_edges)
assert len(seen) == len(bm.verts)
bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BRIDGE_CONNECTOR_PASSED', bpy.app.version_string)
