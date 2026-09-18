"""Run inside Blender to compare upstream registration with the current add-on."""
import ast
import json
from pathlib import Path
import runpy
import subprocess
import bpy

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '99496cb'
state = runpy.run_path(str(ROOT/'tests/test_registration.py'))

def source_tree(path):
    source = subprocess.check_output(['git','show',BASELINE+':'+path], cwd=ROOT, text=True)
    return ast.parse(source)

def name_lists(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Tuple)):
            for target in node.targets:
                if isinstance(target, ast.Name) and all(isinstance(item, ast.Name) for item in node.value.elts):
                    result[target.id] = [item.id for item in node.value.elts]
    return result

root_tree = source_tree('__init__.py')
imports = {alias.asname or alias.name: node.module.replace('.', '/')+'/'+alias.name+'.py'
           for node in root_tree.body if isinstance(node, ast.ImportFrom) and node.level == 1
           for alias in node.names}
modules = ['__init__.py'] + [imports[name] for name in name_lists(root_tree)['addon_modules']]
original = {'operators':set(), 'panels':set()}
for path in modules:
    tree = source_tree(path)
    classes = {node.name:node for node in tree.body if isinstance(node, ast.ClassDef)}
    lists = name_lists(tree)
    register = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'register')
    loops = {node.target.id:lists[node.iter.id] for node in ast.walk(register)
             if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
             and isinstance(node.iter, ast.Name) and node.iter.id in lists}
    names = []
    for node in ast.walk(register):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == 'bpy.utils.register_class':
            assert len(node.args)==1 and isinstance(node.args[0],ast.Name), path
            argument = node.args[0].id
            names.extend(loops.get(argument,[argument]))
    for name in names:
        cls = classes[name]
        bases = [ast.unparse(base) for base in cls.bases]
        kind = 'operators' if any(base.split('.')[-1]=='Operator' for base in bases) else 'panels' if any(base.split('.')[-1]=='Panel' for base in bases) else None
        if kind is None:
            continue
        identifier = next(ast.literal_eval(node.value) for node in cls.body
                          if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='bl_idname' for target in node.targets))
        original[kind].add(identifier)
current = {'operators':{cls.bl_idname for cls in state['operators']},
           'panels':{cls.bl_idname for cls in state['expected'] if issubclass(cls,bpy.types.Panel)}}
report = {'upstream':BASELINE, 'current_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'blender':bpy.app.version_string, 'scope':{}}
for kind in original:
    # Same Bridges panel/class/label; its RNA name was corrected to Blender's
    # CATEGORY_PT_name convention during the port, not removed from the UI.
    aliases = {'OPENDENTAL_ODCBridges':'OPENDENTAL_PT_ODCBridges'} if kind=='panels' else {}
    assert all(old in original[kind] and new in current[kind] for old,new in aliases.items())
    normalized = {aliases.get(identifier,identifier) for identifier in original[kind]}
    report['scope'][kind] = {'upstream_count':len(original[kind]),'current_count':len(current[kind]),
                            'missing':sorted(normalized-current[kind]),'added':sorted(current[kind]-normalized),
                            'renamed':aliases}
print('ODC_UPSTREAM_SCOPE',json.dumps(report),flush=True)
assert all(not item['missing'] for item in report['scope'].values()), report
(ROOT/'docs/upstream_scope.json').write_text(json.dumps(report,indent=2)+'\n')
