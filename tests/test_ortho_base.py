import sys
from pathlib import Path
import bpy
import bmesh
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_cube_add(size=2)
obj = bpy.context.object
original = [v.co.copy() for v in obj.data.vertices]
assert bpy.ops.opendental.simple_base(base_height=-2) == {'CANCELLED'}
assert [v.co for v in obj.data.vertices] == original
bm = bmesh.new()
bm.from_mesh(obj.data)
bottom = min(bm.faces, key=lambda f:f.calc_center_median().z)
bmesh.ops.delete(bm, geom=[bottom], context='FACES_ONLY')
bm.to_mesh(obj.data)
bm.free()
assert bpy.ops.opendental.simple_base(base_height=-2) == {'FINISHED'}
bm = bmesh.new()
bm.from_mesh(obj.data)
assert all(edge.is_manifold for edge in bm.edges)
assert abs(bm.calc_volume(signed=True)-16) < 1e-5
assert min(v.co.z for v in bm.verts) == -3
assert max(v.co.z for v in bm.verts) == 1
bm.free()
print('ODC_ORTHO_BASE_PASSED', bpy.app.version_string)
