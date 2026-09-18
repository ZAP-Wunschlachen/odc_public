"""Scene centering preserves shared geometry, hierarchy and visibility."""
import sys
from pathlib import Path
import bpy, addon_utils
from mathutils import Matrix, Vector, Euler
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
assert bpy.ops.opendental.center_objects()=={'CANCELLED'}
bpy.ops.mesh.primitive_cube_add(size=2, location=(3,4,5))
first=bpy.context.object
for vertex in first.data.vertices:
    vertex.co += Vector((2,0,0))
parent=bpy.data.objects.new('Parent',None)
bpy.context.collection.objects.link(parent)
parent.matrix_world=Matrix.Translation((4,7,9)) @ Euler((.2,.3,.4)).to_matrix().to_4x4()
parent.scale=(1.5,.7,2)
first.parent=parent
second=bpy.data.objects.new('Shared sibling',first.data)
bpy.context.collection.objects.link(second)
second.location=(-7,2,4)
child=bpy.data.objects.new('Nested child',first.data)
bpy.context.collection.objects.link(child)
child.parent=first
child.location=(2,3,4)
child.hide_set(True)
collection=bpy.data.collections.new('Excluded')
bpy.context.scene.collection.children.link(collection)
excluded=bpy.data.objects.new('Excluded mesh',first.data)
collection.objects.link(excluded)
excluded.location=(20,8,5)
# Capture the true baseline before making Blender's excluded transform stale.
bpy.context.view_layer.update()
excluded.location=(21,9,6)
bpy.context.view_layer.update()
bpy.context.view_layer.layer_collection.children['Excluded'].exclude=True
excluded.location=(20,8,5)
bpy.context.view_layer.update()
objects=list(bpy.context.scene.objects)
worlds={obj:obj.matrix_world.copy() for obj in objects}
worlds[excluded]=Matrix.Translation((20,8,5))
centers=[worlds[obj] @ (sum((Vector(p) for p in obj.bound_box),Vector())/8)
         if obj.type=='MESH' else worlds[obj].translation.copy() for obj in objects]
center=sum(centers,Vector())/len(centers)
coordinates=[vertex.co.copy() for vertex in first.data.vertices]
active=bpy.context.view_layer.objects.active
selected=set(bpy.context.selected_objects)
assert bpy.ops.opendental.center_objects()=={'FINISHED'}
for obj,world in worlds.items():
    expected=Matrix.Translation(-center)@world
    assert max(abs(obj.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-5, obj.name
assert all(vertex.co==coordinate for vertex,coordinate in zip(first.data.vertices,coordinates))
assert first.data==second.data==child.data==excluded.data
assert first.parent==parent and child.parent==first
assert child.hide_get()
assert bpy.context.view_layer.layer_collection.children['Excluded'].exclude
assert bpy.context.view_layer.objects.active==active
assert set(bpy.context.selected_objects)==selected
before={obj:obj.matrix_world.copy() for obj in objects}
assert bpy.ops.opendental.center_objects()=={'FINISHED'}
assert all(max(abs(obj.matrix_world[i][j]-world[i][j]) for i in range(4) for j in range(4))<1e-5 for obj,world in before.items())
print('ODC_CENTER_OBJECTS_PASSED')
