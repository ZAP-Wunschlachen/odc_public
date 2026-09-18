"""Run inside a disposable Blender profile; invoked by run_installation.py."""
import os, sys, importlib
from pathlib import Path
import bpy, addon_utils
stage, archive = sys.argv[sys.argv.index('--')+1:]
scripts = Path(os.environ['BLENDER_USER_SCRIPTS']).resolve()
config = Path(os.environ['BLENDER_USER_CONFIG']).resolve()
assert Path(bpy.utils.user_resource('SCRIPTS')).resolve() == scripts
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == config
module_name = 'odc_public'
if stage == 'install':
    assert bpy.ops.preferences.addon_install(filepath=archive) == {'FINISHED'}
    assert bpy.ops.preferences.addon_enable(module=module_name) == {'FINISHED'}
else:
    assert module_name in bpy.context.preferences.addons
    assert addon_utils.check(module_name) == (True, True), addon_utils.check(module_name)
module = importlib.import_module(module_name)
installed = scripts / 'addons' / module_name
assert Path(module.__file__).resolve() == installed / '__init__.py'
prefs = bpy.context.preferences.addons[module_name].preferences
for field in ('tooth_lib', 'mat_lib', 'imp_lib', 'drill_lib', 'ortho_lib'):
    library = Path(getattr(prefs, field)).resolve()
    assert library.is_relative_to(installed) and library.is_file(), (field, library)
    with bpy.data.libraries.load(str(library)) as (source, target):
        assert source.objects or source.materials, library
# Load a real bundled tooth from the installed path, not the checkout.
with bpy.data.libraries.load(prefs.tooth_lib) as (source, target):
    assert set(source.objects) == {f'{q}{n}' for q in (1, 2, 3, 4) for n in range(1, 9)}
    target.objects = ['11']
tooth = target.objects[0]
assert tooth is not None and tooth.type == 'MESH' and len(tooth.data.vertices) > 0
assert tooth.get('odc_library') == 'dundee' and tooth.get('License') == 'CC BY 4.0'
assert all(tooth.vertex_groups.get(name) for name in ('CEJ', 'CervicalBlend', 'AnatomyProtected'))
assert tooth.asset_data is not None
bpy.context.scene.collection.objects.link(tooth)
assert bpy.ops.opendental.draw_arch_curve.get_rna_type()
assert bpy.ops.opendental.teeth_to_arch.get_rna_type()
assert bpy.ops.opendental.limit_physics_movements.get_rna_type()
if stage == 'install':
    assert bpy.ops.wm.save_userpref() == {'FINISHED'}
elif stage == 'remove':
    # Blender's removal operator redraws a UI area even in background mode.
    with bpy.context.temp_override(area=bpy.context.screen.areas[0]):
        assert bpy.ops.preferences.addon_remove(module=module_name) == {'FINISHED'}
    assert module_name not in bpy.context.preferences.addons
    assert not installed.exists()
    assert not hasattr(bpy.types.Scene, 'odc_teeth')
print('ODC_INSTALLATION_' + stage.upper() + '_PASSED', bpy.app.version_string, flush=True)
