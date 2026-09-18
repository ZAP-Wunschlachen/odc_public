"""Join evaluated outer/inner surfaces without changing source geometry."""
import sys
from pathlib import Path
import bpy,bmesh,addon_utils
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
tooth=bpy.context.scene.odc_teeth.add();tooth.name='25'
def cap(name,radius,height):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(-radius,-radius,0),(radius,-radius,0),(radius,radius,0),(-radius,radius,0),
                     (-radius,-radius,height),(radius,-radius,height),(radius,radius,height),(-radius,radius,height)],[],
                    [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.matrix_world=Matrix.Translation((3,4,5));return obj
outer=cap('Outer',2,4);inner=cap('Inner',1.5,3.5)
tooth.contour=outer.name;tooth.intaglio=inner.name
outer.select_set(True);bpy.context.view_layer.objects.active=outer
original=[v.co.copy() for v in outer.data.vertices]
mod=outer.modifiers.new('Subdivision','SUBSURF');mod.levels=1
collision=bpy.data.objects.new('25_Solid Crown',None);bpy.context.collection.objects.link(collision)
assert bpy.ops.opendental.manufacture_restoration()=={'FINISHED'}
result=bpy.data.objects[tooth.solid]
assert result!=outer and result!=inner and result!=collision
bm=bmesh.new();bm.from_mesh(result.data)
assert all(e.is_manifold for e in bm.edges)
assert bm.calc_volume(signed=False)>0
bm.free()
assert [v.co for v in outer.data.vertices]==original
assert outer.modifiers.get('Subdivision')==mod
assert inner.name in bpy.data.objects and collision.name in bpy.data.objects
assert min(v.co.x for v in result.data.vertices)>0
# Missing input must not produce a partial object.
objects_before=set(bpy.data.objects)
tooth.intaglio='Missing'
assert bpy.ops.opendental.manufacture_restoration()=={'CANCELLED'}
assert set(bpy.data.objects)==objects_before
print('ODC_MANUFACTURE_RESTORATION_PASSED')
# Unbridgeable closed inputs cancel without output datablocks.
bpy.ops.mesh.primitive_cube_add()
closed=bpy.context.object
tooth.contour=closed.name;tooth.intaglio=closed.name
objects_before=set(bpy.data.objects);meshes_before=set(bpy.data.meshes)
assert bpy.ops.opendental.manufacture_restoration()=={'CANCELLED'}
assert set(bpy.data.objects)==objects_before and set(bpy.data.meshes)==meshes_before
print('ODC_MANUFACTURE_INVALID_LOOPS_PASSED')
