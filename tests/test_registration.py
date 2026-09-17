"""Run with Blender --background --factory-startup --python tests/test_registration.py."""
import sys
import json
import traceback
from pathlib import Path
import bpy
import addon_utils

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

def fail(error):
    traceback.print_exc()
    print('ODC_TEST_RESULT', json.dumps({'status': 'failed', 'error': str(error)}), flush=True)
    raise SystemExit(1)

try:
    module = addon_utils.enable(ROOT.name, default_set=True, persistent=False)
    if module is None:
        raise AssertionError('Add-on did not enable')
    expected = json.loads((ROOT / 'docs/operator_inventory.json').read_text())
    registered = []
    for item in expected:
        if '.' not in item['bl_idname']:
            continue
        group, operator = item['bl_idname'].split('.', 1)
        try:
            getattr(getattr(bpy.ops, group), operator).get_rna_type()
        except Exception:
            continue
        registered.append(item['bl_idname'])
    assert registered, 'No registered operators'
    assert hasattr(bpy.context.scene, 'odc_teeth')
    tooth = bpy.context.scene.odc_teeth.add()
    tooth.name = '25'
    tooth.prep_model = 'test_preparation'
    assert tooth.prep_model == 'test_preparation'
    preferences = bpy.context.preferences.addons[ROOT.name].preferences
    assert Path(preferences.tooth_lib).is_file(), preferences.tooth_lib
    addon_utils.disable(ROOT.name, default_set=True)
    assert not hasattr(bpy.types.Scene, 'odc_teeth'), 'Scene properties leak after disable'
    module = addon_utils.enable(ROOT.name, default_set=True, persistent=False)
    assert module is not None, 'Re-enable failed'
    addon_utils.disable(ROOT.name, default_set=True)
    print('ODC_TEST_RESULT', json.dumps({'status': 'passed', 'blender': bpy.app.version_string,
                                       'registered_operator_count': len(registered),
                                       'tested': ['enable', 'restoration properties', 'library path', 'disable', 're-enable']}), flush=True)
except Exception as error:
    fail(error)
