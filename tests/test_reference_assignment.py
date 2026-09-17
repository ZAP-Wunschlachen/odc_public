"""Actual neighboring and opposing assignments honor active planning scope."""
import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
assert not bpy.ops.opendental.set_mesial.poll()
assert not bpy.ops.opendental.set_distal.poll()
bpy.ops.mesh.primitive_cube_add()
neighbor = bpy.context.object
assert bpy.ops.opendental.set_opposing(for_all=False) == {'CANCELLED'}
assert bpy.ops.opendental.set_opposing(for_all=True) == {'FINISHED'}
assert scene.odc_props.opposing == neighbor.name
for name in ('24', '25', '26'):
    scene.odc_teeth.add().name = name
scene.odc_tooth_index = 1
assert bpy.ops.opendental.set_mesial() == {'FINISHED'}
assert scene.odc_teeth[1].mesial == neighbor.name
assert not scene.odc_teeth[0].mesial and not scene.odc_teeth[2].mesial
bpy.ops.mesh.primitive_cube_add()
distal = bpy.context.object
assert bpy.ops.opendental.set_distal() == {'FINISHED'}
assert scene.odc_teeth[1].distal == distal.name
assert not scene.odc_teeth[0].distal and not scene.odc_teeth[2].distal
assert bpy.ops.opendental.set_opposing(for_all=False) == {'FINISHED'}
assert scene.odc_teeth[1].opposing == distal.name
assert not scene.odc_teeth[0].opposing and not scene.odc_teeth[2].opposing
assert scene.odc_props.opposing == neighbor.name
assert bpy.ops.opendental.set_opposing(for_all=True) == {'FINISHED'}
assert all(t.opposing == distal.name for t in scene.odc_teeth)
assert scene.odc_props.opposing == distal.name
scene.odc_tooth_index = 99
assert not bpy.ops.opendental.set_mesial.poll()
assert not bpy.ops.opendental.set_distal.poll()
assert bpy.ops.opendental.set_opposing(for_all=False) == {'CANCELLED'}
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_REFERENCE_ASSIGNMENT_PASSED', bpy.app.version_string)
