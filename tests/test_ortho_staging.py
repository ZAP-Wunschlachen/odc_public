import sys
from pathlib import Path
import bpy
import addon_utils
from mathutils import Euler
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
objects['21'].rotation_mode = 'AXIS_ANGLE'
objects['21'].rotation_axis_angle = (0,1,0,0)
# All forms of hidden objects must be excluded from treatment staging.
invisible=[]
for number in ('12','13','14'):
    obj=bpy.data.objects.new(number,None)
    bpy.context.scene.collection.objects.link(obj)
    invisible.append(obj)
invisible[0].hide_viewport=True
hidden_collection=bpy.data.collections.new('Hidden teeth')
bpy.context.scene.collection.children.link(hidden_collection)
bpy.context.scene.collection.objects.unlink(invisible[1])
hidden_collection.objects.link(invisible[1])
hidden_collection.hide_viewport=True
excluded_collection=bpy.data.collections.new('Excluded teeth')
bpy.context.scene.collection.children.link(excluded_collection)
bpy.context.scene.collection.objects.unlink(invisible[2])
excluded_collection.objects.link(invisible[2])
bpy.context.view_layer.layer_collection.children[excluded_collection.name].exclude=True
visible=bpy.data.objects.new('15_Crown',None)
bpy.context.scene.collection.objects.link(visible)
visible.rotation_mode='XYZ'
scene = bpy.context.scene
scene.frame_set(1)
assert bpy.ops.opendental.set_treatment_keyframe() == {'FINISHED'}
scene.frame_set(10)
objects['11'].location.x = 4
objects['21'].location.x = 6
rotation=Euler((.1,.2,.3)).to_quaternion()
objects['11'].rotation_quaternion=rotation
objects['21'].rotation_axis_angle=(.7,1,0,0)
visible.rotation_euler=(.3,.4,.5)
assert bpy.ops.opendental.set_treatment_keyframe() == {'FINISHED'}
scene.frame_set(1)
assert abs(objects['11'].location.x) < 1e-6
assert objects['11'].rotation_quaternion.angle < 1e-6
assert abs(objects['21'].rotation_axis_angle[0]) < 1e-6
assert visible.rotation_euler.to_quaternion().angle < 1e-6
scene.frame_set(10)
assert abs(objects['11'].location.x-4) < 1e-6
assert abs(objects['21'].location.x-6) < 1e-6
assert objects['11'].rotation_quaternion.rotation_difference(rotation).angle < 1e-6
assert abs(objects['21'].rotation_axis_angle[0]-.7) < 1e-6
assert max(abs(a-b) for a,b in zip(visible.rotation_euler,(.3,.4,.5))) < 1e-6
assert all(obj.animation_data is None for obj in invisible)
assert objects['31'].animation_data is None
assert objects['UpperJaw'].animation_data is None
print('ODC_ORTHO_STAGING_PASSED', bpy.app.version_string)
