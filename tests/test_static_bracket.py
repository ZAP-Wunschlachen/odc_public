import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
assets = u.obj_list_from_lib(u.get_settings().ortho_lib)
assert assets
bpy.context.scene.cursor.location = (3,4,5)
existing = bpy.data.objects.new(assets[0],None)
bpy.context.scene.collection.objects.link(existing)
for asset in assets[:2]:
    before = set(bpy.context.scene.objects)
    assert bpy.ops.opendental.place_static_bracket(ob=asset) == {'FINISHED'}
    result, = set(bpy.context.scene.objects)-before
    assert result.type == 'MESH' and len(result.data.vertices) > 0
    assert (result.matrix_world.translation-bpy.context.scene.cursor.location).length < 1e-5
    assert result != existing
assert bpy.data.objects.get(existing.name) == existing
print('ODC_STATIC_BRACKET_PASSED',bpy.app.version_string)
