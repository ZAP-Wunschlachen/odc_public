import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
control = bpy.data.objects.new('Hook control',None)
bpy.context.scene.collection.objects.link(control)
hook = obj.modifiers.new('Tooth hook','HOOK')
hook.object = control
hook.vertex_indices_set([0,1,2,3])
control.location.x = 2
# A second object references the same control and must keep it alive.
bpy.ops.mesh.primitive_cube_add(location=(5,0,0))
other = bpy.context.object
other_hook = other.modifiers.new('Shared hook','HOOK')
other_hook.object = control
other_hook.vertex_indices_set([0])
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.context.view_layer.update()
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
expected = [v.co.copy() for v in mesh.vertices]
evaluated.to_mesh_clear()
assert bpy.ops.opendental.flexitooth_keep() == {'FINISHED'}
assert not obj.modifiers
assert all((v.co-p).length < 1e-5 for v,p in zip(obj.data.vertices,expected))
assert bpy.data.objects.get('Hook control') == control
bpy.ops.object.select_all(action='DESELECT')
other.select_set(True)
bpy.context.view_layer.objects.active = other
assert bpy.ops.opendental.flexitooth_keep() == {'FINISHED'}
assert bpy.data.objects.get('Hook control') is None
assert bpy.context.object == other
print('ODC_FLEXITOOTH_KEEP_PASSED',bpy.app.version_string)
