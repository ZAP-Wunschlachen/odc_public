import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=3)
source = bpy.context.object
source.location = (4, 2, 1)
source.rotation_euler = (.1, .2, .3)
bpy.context.view_layer.update()
original = [tuple(v.co) for v in source.data.vertices]
assert bpy.ops.opendental.meta_scaffold_create(radius=2, finalize=True) == {'FINISHED'}
scaffold = bpy.data.objects['Meta Scaffold']
assert 0 < len(scaffold.data.vertices) < len(source.data.vertices)
assert max(abs(scaffold.matrix_world[i][j]-source.matrix_world[i][j]) for i in range(4) for j in range(4)) < 1e-5
bpy.context.view_layer.objects.active = scaffold
for finalize in (False, True):
    before = set(bpy.data.objects)
    assert bpy.ops.opendental.meta_offset_surface(radius=2.5, resolution=.8, finalize=finalize) == {'FINISHED'}
    added = set(bpy.data.objects)-before
    assert len(added) == 1
    result = added.pop()
    assert max(abs(result.matrix_world[i][j]-scaffold.matrix_world[i][j]) for i in range(4) for j in range(4)) < 1e-5
    if finalize:
        assert result.type == 'MESH' and len(result.data.polygons) > 0
    else:
        assert result.type == 'META'
        assert len(result.data.elements) == len(scaffold.data.vertices)
        for ball, vertex in zip(result.data.elements, scaffold.data.vertices):
            assert (ball.co-vertex.co).length < 1e-6
            assert abs(ball.radius-2.5) < 1e-6
assert [tuple(v.co) for v in source.data.vertices] == original
for finalize in (False, True):
    before = set(bpy.data.objects)
    assert bpy.ops.opendental.meta_custom_tray(tray_thickness=2, tray_offset=1.5, finalize=finalize) == {'FINISHED'}
    added = set(bpy.data.objects)-before
    assert len(added) == 1
    result = added.pop()
    if finalize:
        assert result.type == 'MESH' and len(result.data.polygons) > 0
    else:
        assert result.type == 'META'
        assert len(result.data.elements) == len(scaffold.data.vertices)
        assert all(abs(ball.radius-3.5) < 1e-6 for ball in result.data.elements)
print('ODC_META_SURFACE_PASSED', bpy.app.version_string)
