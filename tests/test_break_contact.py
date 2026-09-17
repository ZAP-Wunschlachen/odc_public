import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_cube_add(location=(-.75,0,0))
left = bpy.context.object
bpy.ops.mesh.primitive_cube_add(location=(.75,0,0))
right = bpy.context.object
left.select_set(True)
assert bpy.ops.opendental.break_contact(method='1', sep=.2) == {'FINISHED'}
bpy.context.view_layer.update()
extents = []
for obj in (left,right):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    xs = [(evaluated.matrix_world @ v.co).x for v in mesh.vertices]
    extents.append((min(xs),max(xs)))
    evaluated.to_mesh_clear()
assert abs(extents[0][1]+.2) < 1e-5, extents
assert abs(extents[1][0]-.2) < 1e-5, extents
assert abs(extents[0][0]+1.75) < 1e-5
assert abs(extents[1][1]-1.75) < 1e-5
assert left.modifiers['Contact'].target == right.modifiers['Contact'].target
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BREAK_CONTACT_PASSED', bpy.app.version_string)
