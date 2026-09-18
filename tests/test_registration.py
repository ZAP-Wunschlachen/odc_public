"""Run with Blender --background --factory-startup --python tests/test_registration.py."""
import sys
import json
import traceback
import ast
import inspect
import types
from pathlib import Path
import bpy
import addon_utils

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

def fail(error):
    traceback.print_exc()
    verify_disabled()
    print('ODC_TEST_RESULT', json.dumps({'status': 'failed', 'error': str(error)}), flush=True)
    raise SystemExit(1)

try:
    module = addon_utils.enable(ROOT.name, default_set=True, persistent=False)
    if module is None:
        raise AssertionError('Add-on did not enable')
    # Derive expectations from the active register functions, including their
    # class lists and nested modules. Never silently skip missing RNA entries.
    expected = list(module.init_classes)
    visited = set()
    def collect_registered_classes(owner):
        if owner in visited:
            return
        visited.add(owner)
        tree = ast.parse(inspect.getsource(owner.register))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if ast.unparse(node.func) == 'bpy.utils.register_class':
                assert len(node.args) == 1 and isinstance(node.args[0], ast.Name)
                name = node.args[0].id
                if name == 'cls':
                    expected.extend(owner.classes)
                else:
                    expected.append(getattr(owner, name))
            elif (isinstance(node.func, ast.Attribute) and node.func.attr == 'register'
                  and isinstance(node.func.value, ast.Name)):
                child = getattr(owner, node.func.value.id, None)
                if isinstance(child, types.ModuleType):
                    collect_registered_classes(child)
    for owner in module.addon_modules:
        collect_registered_classes(owner)
    assert len(expected) >= 140, len(expected)
    assert len(expected) == len(set(expected)), 'Duplicate class declarations'
    operators = [cls for cls in expected if issubclass(cls, bpy.types.Operator)]
    def verify_enabled():
        for cls in expected:
            assert cls.is_registered, f'Missing class: {cls.__module__}.{cls.__name__}'
        for cls in operators:
            group, name = cls.bl_idname.split('.', 1)
            rna = getattr(getattr(bpy.ops, group), name).get_rna_type()
            assert rna.identifier == cls.bl_rna.identifier, cls.bl_idname
    def verify_disabled():
        for cls in expected:
            assert not cls.is_registered, f'Class leaked after disable: {cls.__name__}'
        for cls in operators:
            group, name = cls.bl_idname.split('.', 1)
            try:
                getattr(getattr(bpy.ops, group), name).get_rna_type()
            except (KeyError, RuntimeError):
                continue
            raise AssertionError(f'Operator leaked after disable: {cls.bl_idname}')
    verify_enabled()
    assert hasattr(bpy.context.scene, 'odc_teeth')
    tooth = bpy.context.scene.odc_teeth.add()
    tooth.name = '25'
    tooth.prep_model = 'test_preparation'
    assert tooth.prep_model == 'test_preparation'
    preferences = bpy.context.preferences.addons[ROOT.name].preferences
    assert Path(preferences.tooth_lib).is_file(), preferences.tooth_lib
    addon_utils.disable(ROOT.name, default_set=True)
    assert not hasattr(bpy.types.Scene, 'odc_teeth'), 'Scene properties leak after disable'
    verify_disabled()
    module = addon_utils.enable(ROOT.name, default_set=True, persistent=False)
    assert module is not None, 'Re-enable failed'
    verify_enabled()
    addon_utils.disable(ROOT.name, default_set=True)
    verify_disabled()
    print('ODC_TEST_RESULT', json.dumps({'status': 'passed', 'blender': bpy.app.version_string,
                                       'registered_operator_count': len(operators),
                                       'registered_class_count': len(expected),
                                       'tested': ['enable', 'restoration properties', 'library path', 'disable', 're-enable']}), flush=True)
except Exception as error:
    fail(error)
