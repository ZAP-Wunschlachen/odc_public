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
def build(segments, twist, cubic):
    bm = bmesh.new()
    for x in (-2,2):
        vertices = bmesh.ops.create_cube(bm, size=2)['verts']
        bmesh.ops.translate(bm, verts=vertices, vec=Vector((x,0,0)))
    mesh = bpy.data.meshes.new('Parameter fixture')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('Parameter fixture', mesh)
    bpy.context.scene.collection.objects.link(obj)
    for name,x in (('A',-1),('B',1)):
        obj.vertex_groups.new(name=name).add([v.index for v in mesh.vertices if abs(v.co.x-x)<1e-6],1,'REPLACE')
    m.bridge_loop(bpy.context,obj,'A','B',segments,twist,cubic)
    return obj
base = build(2,0,.5)
dense = build(4,0,.5)
assert len(dense.data.vertices) > len(base.data.vertices)
straight = build(4,0,0)
curved = build(4,0,1)
assert any((a.co-b.co).length > 1e-5 for a,b in zip(straight.data.vertices,curved.data.vertices))
twisted = build(4,1,1)
assert any((a.co-b.co).length > 1e-5 for a,b in zip(curved.data.vertices,twisted.data.vertices))
for obj in (base,dense,straight,curved,twisted):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges)
    bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BRIDGE_CONNECTOR_PARAMETERS_PASSED', bpy.app.version_string)
