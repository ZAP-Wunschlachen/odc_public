import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
m = importlib.import_module(f'{ROOT.name}.Operators.bridge_methods')
scene = bpy.context.scene
u.get_settings().behavior = '2'
for name in ('24','25'):
    bpy.ops.mesh.primitive_cube_add()
    tooth = scene.odc_teeth.add()
    tooth.name = name
    tooth.contour = bpy.context.object.name
for tooth in scene.odc_teeth:
    bpy.data.objects[tooth.contour].select_set(True)
assert bpy.ops.opendental.define_bridge() == {'FINISHED'}
bridge = scene.odc_bridges[0]
assert set(bridge.tooth_string.split(':')) == {'24','25'}
assert m.active_spanning_restoration(bpy.context) == [bridge]
# Direct bridge object matching works independently of member-tooth fallback.
scene.odc_teeth.clear()
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
bridge.bridge = obj.name
u.get_settings().behavior = '1'
assert m.active_spanning_restoration(bpy.context) == [bridge]
assert m.active_spanning_restoration(bpy.context, exclude=('bridge',)) == []
bridge['unrelated_note'] = obj.name
bridge.bridge = ''
assert m.active_spanning_restoration(bpy.context) == []
bpy.context.view_layer.objects.active = None
assert m.active_spanning_restoration(bpy.context) == []
u.get_settings().behavior = '0'
assert m.active_spanning_restoration(bpy.context) == [bridge]
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BRIDGE_SELECTION_PASSED', bpy.app.version_string)
