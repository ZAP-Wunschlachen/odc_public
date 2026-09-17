import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
obj = bpy.context.object
control = u.bbox_to_lattice(bpy.context.scene, obj)
for point in control.data.points:
    if point.co_deform.z > .4:
        point.co_deform.z += .3
other = obj.copy()
other.data = obj.data.copy()
bpy.context.scene.collection.objects.link(other)
other.select_set(False)
bpy.context.view_layer.update()
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
expected = [v.co.copy() for v in mesh.vertices]
evaluated.to_mesh_clear()
assert bpy.ops.opendental.keep_shape() == {'FINISHED'}
assert not obj.modifiers
assert all((v.co-p).length < 1e-5 for v,p in zip(obj.data.vertices,expected))
assert control.name in bpy.data.objects
assert other.modifiers[0].object == control
obj.select_set(False)
other.select_set(True)
bpy.context.view_layer.objects.active = other
name = control.name
assert bpy.ops.opendental.keep_shape() == {'FINISHED'}
assert name not in bpy.data.objects
assert bpy.context.object == other and other.select_get()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_KEEP_SHAPE_PASSED', bpy.app.version_string)
