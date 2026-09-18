"""Clean a holed principal component while removing disconnected fragments."""
import sys
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
bm=bmesh.new()
bmesh.ops.create_cube(bm,size=.2,matrix=Matrix.Translation((8,0,0)))
result=bmesh.ops.create_cube(bm,size=4)
large=set(result['verts'])
face=next(f for f in bm.faces if all(v in large for v in f.verts))
bmesh.ops.delete(bm,geom=[face],context='FACES_ONLY')
bm.verts.new((10,10,10))
mesh=bpy.data.meshes.new('Dirty mesh');bm.to_mesh(mesh);bm.free()
model=bpy.data.objects.new('Model',mesh);bpy.context.collection.objects.link(model)
model.location=(3,4,5);model.select_set(True);bpy.context.view_layer.objects.active=model
shared=bpy.data.objects.new('Shared input',mesh);bpy.context.collection.objects.link(shared)
original=[v.co.copy() for v in mesh.vertices]
assert bpy.ops.opendental.clean_model()=={'FINISHED'}
assert model.name in bpy.data.objects
assert model.mode=='OBJECT'
assert model.data!=mesh and shared.data==mesh
assert [v.co for v in mesh.vertices]==original
bm=bmesh.new();bm.from_mesh(model.data)
assert len(bm.verts)==8
assert all(e.is_manifold for e in bm.edges)
assert abs(bm.calc_volume(signed=False)-64)<1e-4
bm.free()
assert tuple(model.location)==(3,4,5)
print('ODC_CLEAN_MODEL_PASSED')
