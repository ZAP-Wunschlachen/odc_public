import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
obj = bpy.context.object
hidden = bpy.data.objects.new('hidden', None)
bpy.context.scene.collection.objects.link(hidden)
hidden.hide_set(True)
settings = bpy.context.tool_settings
settings.mesh_select_mode = (False, True, False)
settings.snap_elements = {'VERTEX'}
settings.transform_pivot_point = 'CURSOR'
bpy.ops.object.mode_set(mode='EDIT')
state = u.scene_preserv(bpy.context)
bpy.ops.object.mode_set(mode='OBJECT')
hidden.hide_set(False)
settings.snap_elements = {'FACE'}
settings.transform_pivot_point = 'MEDIAN_POINT'
bpy.ops.mesh.primitive_cube_add()
created = bpy.context.object
u.scene_reconstruct(bpy.context, *state)
assert bpy.context.object == obj and obj.mode == 'EDIT'
assert hidden.hide_get()
assert tuple(settings.mesh_select_mode) == (False, True, False)
assert settings.snap_elements == {'VERTEX'}
assert settings.transform_pivot_point == 'CURSOR'
assert not created.hide_get() and not created.select_get()
bpy.ops.object.mode_set(mode='OBJECT')
# Removed snapshot objects must not prevent restoration.
state = u.scene_preserv(bpy.context)
bpy.data.objects.remove(obj, do_unlink=True)
u.scene_reconstruct(bpy.context, *state)
assert bpy.context.view_layer.objects.active is None
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_SCENE_STATE_PASSED', bpy.app.version_string)
