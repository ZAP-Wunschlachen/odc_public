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
assets = u.obj_list_from_lib(u.get_settings().imp_lib, exclude='_')
bpy.context.scene.cursor.location = (3,4,5)
platform = Vector((3,4,5))
for index, asset in enumerate(assets[:2]):
    if index:
        old = bpy.data.objects[space.implant]
        old.rotation_euler = (.2,.3,.4)
        old.rotation_mode = 'XYZ'
        bpy.context.view_layer.update()
        length = max(v[2] for v in old.bound_box)-min(v[2] for v in old.bound_box)
        platform = old.matrix_world @ Vector((0,0,-length))
        rotation = old.matrix_world.to_quaternion()
    assert bpy.ops.opendental.place_implant(imp=asset, hardware=True) == {'FINISHED'}
    implant = bpy.data.objects[space.implant]
    bpy.context.view_layer.update()
    length = max(v[2] for v in implant.bound_box)-min(v[2] for v in implant.bound_box)
    assert (implant.matrix_world @ Vector((0,0,-length))-platform).length < 1e-5
    if index:
        assert implant.matrix_world.to_quaternion().rotation_difference(rotation).angle < 1e-5
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_PLACE_IMPLANT_OPERATOR_PASSED', bpy.app.version_string)
