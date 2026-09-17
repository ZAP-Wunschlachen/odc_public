import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
obj = bpy.context.object
for v in obj.data.vertices:
    v.co += Vector((1,2,3))
obj.rotation_euler = (.2,.3,.4)
obj.scale = (2,3,4)
bpy.context.view_layer.update()
assert (u.get_bbox_center(obj, world=False)-Vector((1,2,3))).length < 1e-6
assert (u.get_bbox_center(obj)-(obj.matrix_world @ Vector((1,2,3)))).length < 1e-5
before = [obj.matrix_world @ v.co for v in obj.data.vertices]
lattice = u.bbox_to_lattice(bpy.context.scene,obj)
bpy.context.view_layer.update()
assert len(lattice.data.points) == 27
inverse = lattice.matrix_world.inverted()
assert all(max(abs(c) for c in inverse @ p) < .5 for p in before)
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert all((evaluated.matrix_world @ v.co-p).length < 1e-5 for v,p in zip(mesh.vertices,before))
evaluated.to_mesh_clear()
# Moving a control plane must actually deform the evaluated object.
for point in lattice.data.points:
    if point.co_deform.z > .4:
        point.co_deform.z += .2
bpy.context.view_layer.update()
evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert any((evaluated.matrix_world @ v.co-p).length > .01 for v,p in zip(mesh.vertices,before))
evaluated.to_mesh_clear()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CONTROL_LATTICE_PASSED', bpy.app.version_string)
