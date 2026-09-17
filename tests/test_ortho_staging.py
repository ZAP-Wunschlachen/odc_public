import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
assert bpy.ops.opendental.set_treatment_keyframe() == {'CANCELLED'}
objects = {}
for name in ('11','21','31','41','UpperJaw','LowerJaw'):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    objects[name] = obj
for operator, expected in (
    ('show_max_teeth', {'11','21'}),
    ('show_man_teeth', {'31','41'}),
    ('show_right_teeth', {'11','41'}),
    ('show_left_teeth', {'21','31'})):
    assert getattr(bpy.ops.opendental, operator)() == {'FINISHED'}
    assert {name for name,obj in objects.items() if not obj.hide_get()} == expected
assert bpy.ops.opendental.show_max_teeth(show_master=True) == {'FINISHED'}
assert not objects['UpperJaw'].hide_get() and objects['LowerJaw'].hide_get()
objects['11'].rotation_mode = 'QUATERNION'
scene = bpy.context.scene
scene.frame_set(1)
assert bpy.ops.opendental.set_treatment_keyframe() == {'FINISHED'}
scene.frame_set(10)
objects['11'].location.x = 4
objects['21'].location.x = 6
assert bpy.ops.opendental.set_treatment_keyframe() == {'FINISHED'}
scene.frame_set(1)
assert abs(objects['11'].location.x) < 1e-6
scene.frame_set(10)
assert abs(objects['11'].location.x-4) < 1e-6
assert abs(objects['21'].location.x-6) < 1e-6
assert objects['31'].animation_data is None
assert objects['UpperJaw'].animation_data is None
print('ODC_ORTHO_STAGING_PASSED', bpy.app.version_string)
