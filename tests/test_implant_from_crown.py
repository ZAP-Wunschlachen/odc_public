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
tooth = bpy.context.scene.odc_teeth.add()
tooth.name = '25'
tooth.contour = bpy.context.object.name
crown = bpy.context.object
crown.location = (3,4,5)
crown.rotation_euler = (.2,.3,.4)
space = bpy.context.scene.odc_implants.add()
space.name = '25'
asset = u.obj_list_from_lib(u.get_settings().imp_lib, exclude='_')[0]
bpy.context.view_layer.update()
cej = u.box_feature_locations(crown, Vector((0,0,-1)))
direction = crown.matrix_world.to_quaternion() @ Vector((0,0,-1))
for depth in (3, 5):
    assert bpy.ops.opendental.implant_from_crown(imp=asset, depth=depth, hardware=False) == {'FINISHED'}
    implant = bpy.data.objects[space.implant]
    bpy.context.view_layer.update()
    length = max(v[2] for v in implant.bound_box)-min(v[2] for v in implant.bound_box)
    platform = implant.matrix_world @ Vector((0,0,-length))
    assert (platform-(cej+depth*direction)).length < 1e-5
    assert (implant.matrix_world.to_quaternion() @ Vector((0,0,1))-direction).length < 1e-5
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_IMPLANT_FROM_CROWN_PASSED', bpy.app.version_string)
