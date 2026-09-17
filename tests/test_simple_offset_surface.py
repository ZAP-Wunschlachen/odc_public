import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_plane_add(size=4)
obj = bpy.context.object
original = [v.co.copy() for v in obj.data.vertices]
for smooth, shrink in ((False, False), (True, False), (False, True), (True, True)):
    before = set(bpy.data.objects)
    assert bpy.ops.opendental.simple_offset_surface(offset=.4, duplicate=True, smooth=smooth, shrink=shrink) == {'FINISHED'}
    result, = set(bpy.data.objects)-before
    assert all(abs(v.co.z-.4) < 1e-6 for v in result.data.vertices)
    assert [v.co for v in obj.data.vertices] == original
    assert len([m for m in result.modifiers if m.type == 'SMOOTH']) == int(smooth)+int(shrink)
    assert len([m for m in result.modifiers if m.type == 'SHRINKWRAP']) == int(shrink)
    bpy.context.view_layer.update()
    evaluated = result.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    assert all(abs(v.co.z-.4) < 1e-5 for v in mesh.vertices)
    evaluated.to_mesh_clear()
assert bpy.ops.opendental.simple_offset_surface(offset=-.2, duplicate=False) == {'FINISHED'}
assert all(abs(v.co.z+.2) < 1e-6 for v in obj.data.vertices)
print('ODC_SIMPLE_OFFSET_PASSED', bpy.app.version_string)
