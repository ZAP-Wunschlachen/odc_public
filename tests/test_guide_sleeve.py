import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
u.get_settings().behavior = '0'
space = bpy.context.scene.odc_implants.add()
space.name = '25'
implant = bpy.context.object
implant.location = (3,4,5)
implant.rotation_euler = (.3,.4,.5)
bpy.context.view_layer.update()
space.implant = implant.name
asset = u.obj_list_from_lib(u.get_settings().drill_lib, exclude='Drill')[0]
old_name = None
count = len(bpy.data.objects)
for depth in (20, 15):
    assert bpy.ops.opendental.place_guide_sleeve(drill=asset, depth=depth) == {'FINISHED'}
    sleeve = bpy.data.objects[space.sleeve]
    bpy.context.view_layer.update()
    expected = implant.matrix_world.translation + implant.matrix_world.to_quaternion() @ Vector((0,0,-depth))
    assert (sleeve.matrix_world.translation-expected).length < 1e-5
    assert sleeve.matrix_world.to_quaternion().rotation_difference(implant.matrix_world.to_quaternion()).angle < 1e-5
    assert sleeve.parent == implant and implant.users > 0
    assert len(bpy.data.objects) == count+1
    if old_name:
        assert bpy.data.objects.get(old_name) is None
    old_name = sleeve.name
space.implant = ''
assert bpy.ops.opendental.place_guide_sleeve(drill=asset) == {'CANCELLED'}
assert bpy.data.objects.get(old_name) is not None
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_GUIDE_SLEEVE_PASSED', bpy.app.version_string)
