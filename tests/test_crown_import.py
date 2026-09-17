"""Actual crown import, replacement and collection organization with bundled assets."""
import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Euler
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
scene = bpy.context.scene
scene.cursor.location = (2, 3, 4)
tooth = scene.odc_teeth.add()
tooth.name = '25'
tooth.rest_type = '0'
axis = bpy.data.objects.new('fixture_axis', None)
scene.collection.objects.link(axis)
axis.rotation_euler = Euler((.2, .3, .4))
tooth.axis = axis.name
bpy.context.view_layer.update()
# An existing object with the library asset's name must survive.
existing = bpy.data.objects.new('25', None)
scene.collection.objects.link(existing)
for iteration in range(2):
    assert bpy.ops.opendental.get_crown_form(ob_list='25') == {'FINISHED'}
    crown = bpy.data.objects[tooth.restoration]
    assert crown.type == 'MESH' and len(crown.data.vertices) > 0
    assert tooth.contour == crown.name
    assert (crown.location - scene.cursor.location).length < 1e-6
    assert crown.rotation_quaternion.rotation_difference(axis.matrix_world.to_quaternion()).angle < 1e-5
    assert bpy.data.objects['25'] == existing
    assert len([o for o in scene.objects if o.name.startswith('25_FullContour')]) == 1
    assert any(c.get('odc_collection_role') == 'Restorations' for c in crown.users_collection)
# Organization is idempotent and retains user collection memberships.
user_collection = bpy.data.collections.new('User collection')
scene.collection.children.link(user_collection)
user_collection.objects.link(crown)
count = len(bpy.data.collections)
u.layer_management(scene.odc_teeth)
u.layer_management(tooth)
assert len(bpy.data.collections) == count
assert crown.name in user_collection.objects
# Verification clears stale object references without erasing planning metadata.
tooth.margin = '__deleted_margin__'
tooth.log = 'preserve treatment notes'
tooth['custom_numeric'] = 12
tooth['custom_text'] = 'preserve custom metadata'
u.scene_verification(scene)
assert tooth.margin == ''
assert tooth.log == 'preserve treatment notes' and tooth.rest_type == '0'
assert tooth['custom_numeric'] == 12 and tooth['custom_text'] == 'preserve custom metadata'
assert tooth.restoration == crown.name
# Planning data and collections survive saving and reopening.
artifact = ROOT / 'tests/artifacts/crown_import.blend'
artifact.parent.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(artifact))
bpy.ops.wm.open_mainfile(filepath=str(artifact))
tooth = bpy.context.scene.odc_teeth[0]
assert tooth.contour == tooth.restoration
assert bpy.data.objects[tooth.contour].type == 'MESH'
assert any(c.get('odc_collection_role') == 'Restorations' for c in bpy.data.objects[tooth.contour].users_collection)
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CROWN_IMPORT_PASSED', bpy.app.version_string)
