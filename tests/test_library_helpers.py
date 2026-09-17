"""Exercise bundled library I/O and shared helpers in the target Blender runtime."""
import sys
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True) is not None
utils = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
common = importlib.import_module(f'{ROOT.name}.Addon_utils.common_utilities')
settings = utils.get_settings()
assert common.get_settings() == settings
assert common.selection_mouse() in (['LEFTMOUSE', 'SHIFT+LEFTMOUSE'], ['RIGHTMOUSE', 'SHIFT+RIGHTMOUSE'])

# Every configured bundled object library must exist and load real mesh assets.
for field in ('imp_lib', 'drill_lib', 'ortho_lib'):
    path = getattr(settings, field)
    assert Path(path).is_file(), (field, path)
    asset_names = utils.obj_list_from_lib(path)
    assert asset_names, field
    loaded_mesh = False
    for name in asset_names:
        asset = utils.obj_from_lib(path, name)
        assert asset is not None
        if asset.type == 'MESH' and asset.data.vertices:
            loaded_mesh = True
    assert loaded_mesh, field
    print('BUNDLED_LIBRARY_LOADED', field, len(asset_names), flush=True)

names = utils.obj_list_from_lib(settings.tooth_lib)
assert '25' in names, names
first = utils.obj_from_lib(settings.tooth_lib, '25')
second = utils.obj_from_lib(settings.tooth_lib, '25')
assert first != second and first.name != second.name
assert first.type == second.type == 'MESH'
assert len(first.data.vertices) > 0
assert not first.users_collection and not second.users_collection
bpy.context.scene.collection.objects.link(second)
assert bpy.context.scene.objects.get(second.name) == second
linked = utils.obj_from_lib(settings.tooth_lib, '25', link=True)
assert linked.library is not None

materials = utils.mat_list_from_lib(settings.mat_lib)
assert isinstance(materials, list) and materials
mat = utils.mat_from_lib(settings.mat_lib, materials[0])
mat2 = utils.mat_from_lib(settings.mat_lib, materials[0])
assert mat is not None and mat2 is not None and mat != mat2
second.data.materials.append(mat)
assert second.data.materials[-1] == mat
for loader, path in [(utils.obj_from_lib, settings.tooth_lib), (utils.mat_from_lib, settings.mat_lib)]:
    try:
        loader(path, '__missing_fixture_asset__')
    except ValueError:
        pass
    else:
        raise AssertionError('Missing asset must report an error')

mesh = bpy.data.meshes.new('centroid_fixture')
mesh.from_pydata([(0, 0, 0), (2, 4, 6)], [], [])
transform = Matrix.Translation((5, 6, 7)) @ Matrix.Diagonal((2, 3, 4, 1))
expected = Vector((7, 12, 19))
assert (utils.get_com(mesh, [0, 1], transform) - expected).length < 1e-6
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
assert (utils.get_com_bme(bm, [0, 1], transform) - expected).length < 1e-6
bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_LIBRARY_HELPERS_PASSED', bpy.app.version_string)
