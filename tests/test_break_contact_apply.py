import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
for method in ('0','1'):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_cube_add(location=(-.75,0,0))
    left = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(location=(.75,0,0))
    right = bpy.context.object
    left.select_set(True)
    count = len(bpy.data.objects)
    assert bpy.ops.opendental.break_contact(method=method, sep=.2, apply=True) == {'FINISHED'}
    assert len(bpy.data.objects) == count
    assert not left.modifiers and not right.modifiers
    assert max((left.matrix_world @ v.co).x for v in left.data.vertices) < 0
    assert min((right.matrix_world @ v.co).x for v in right.data.vertices) > 0
    assert bpy.context.object == right
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BREAK_CONTACT_APPLY_PASSED', bpy.app.version_string)
