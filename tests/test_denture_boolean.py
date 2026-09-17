import sys
from pathlib import Path
import bpy
import bmesh
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_cube_add(size=4)
outer = bpy.context.object
before = len(outer.modifiers)
assert bpy.ops.opendental.denture_boolean_intaglio() == {'CANCELLED'}
assert len(outer.modifiers) == before
bpy.ops.mesh.primitive_cube_add(size=2)
inner = bpy.context.object
inner.name = 'Master cast'
bpy.context.view_layer.objects.active = outer
assert bpy.ops.opendental.denture_boolean_intaglio(ob=inner.name) == {'FINISHED'}
assert outer.modifiers[-1].object == inner
bpy.context.view_layer.update()
bm = bmesh.new()
bm.from_object(outer, bpy.context.evaluated_depsgraph_get())
assert all(edge.is_manifold for edge in bm.edges)
assert abs(bm.calc_volume(signed=True)-56) < 1e-5
bm.free()
assert len(outer.data.vertices) == 8 and len(inner.data.vertices) == 8
print('ODC_DENTURE_BOOLEAN_PASSED', bpy.app.version_string)
