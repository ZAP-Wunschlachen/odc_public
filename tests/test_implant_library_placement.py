import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector, Euler
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
m = importlib.import_module(f'{ROOT.name}.Operators.implant_utils')
space = bpy.context.scene.odc_implants.add()
space.name = '25'
names = u.obj_list_from_lib(u.get_settings().imp_lib)
asset = next(name for name in names if any(n.startswith(name+'_') for n in names))
location = Vector((3,4,5))
rotation = Euler((.2,.3,.4)).to_quaternion()
old_name = None
counts = []
for orientation in (rotation, rotation.to_matrix().to_4x4()):
    implant = m.place_implant(bpy.context, space, location, orientation, asset)
    bpy.context.view_layer.update()
    assert (implant.matrix_world.translation-location).length < 1e-5
    assert implant.matrix_world.to_quaternion().rotation_difference(rotation).angle < 1e-5
    assert implant.children
    assert all(child.name in bpy.context.scene.objects for child in implant.children)
    counts.append(len(bpy.data.objects))
    if old_name:
        assert old_name not in bpy.data.objects
    old_name = implant.name
assert counts[0] == counts[1]
try:
    m.place_implant(bpy.context, space, location, rotation, '__missing__')
except ValueError:
    pass
else:
    raise AssertionError('Missing asset accepted')
assert space.implant == old_name and old_name in bpy.data.objects
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_IMPLANT_LIBRARY_PLACEMENT_PASSED', bpy.app.version_string)
