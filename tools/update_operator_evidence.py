"""Attach current installed-suite evidence to the declaration inventory (Blender)."""
import ast,json,runpy
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1]
state=runpy.run_path(str(ROOT/'tests/test_registration.py'))
classes=[cls for cls in state['expected'] if issubclass(cls,(bpy.types.Operator,bpy.types.Panel))]
current={cls.bl_idname:cls for cls in classes}
references={}
for test in (ROOT/'tests').glob('test_*.py'):
 if test.name in {'test_registration.py','test_poll_contexts.py'}:continue
 for node in ast.walk(ast.parse(test.read_text())):
  if isinstance(node,ast.Call):
   function=ast.unparse(node.func)
   if function.startswith('bpy.ops.') and len(function.split('.'))==4:
    references.setdefault(function[8:],set()).add('tests/'+test.name)
# These tests execute explicit parameter lists through getattr; see their loops.
for names,file in [
 (('remove_bridge_restoration','remove_implant_restoration','remove_splint'),'test_plan_removal.py'),
 (('show_man_teeth','show_left_teeth','show_right_teeth'),'test_ortho_staging.py'),
 (('start_crown_help','start_implant_help','start_bridge_help','start_guide_help'),'test_help_overlays.py')]:
 for name in names:references.setdefault('opendental.'+name,set()).add('tests/'+file)
results={}
for suite in ('headless','foreground'):
 for result in json.loads((ROOT/'tests/artifacts/installation'/('installed_'+suite)/'results.json').read_text()):
  results[result['test']]=result['passed']
path=ROOT/'docs/operator_inventory.json';rows=json.loads(path.read_text())
for cls in classes:
 if not any(row['bl_idname']==cls.bl_idname or row['class']==cls.__name__ for row in rows):
  owner=cls.__module__.removeprefix(ROOT.name).lstrip('.')
  rows.append({'module':owner.replace('.','/')+'.py' if owner else '__init__.py',
               'class':cls.__name__,'bl_idname':cls.bl_idname,'bl_label':cls.bl_label})
for row in rows:
 cls=current.get(row['bl_idname']) or next((cls for cls in classes if cls.__name__==row['class']),None)
 row['registration_status']='registered' if cls else 'not_in_upstream_active_registration'
 if cls:row['bl_idname']=cls.bl_idname
 files=({'tests/test_panel_drawing.py'} if cls and issubclass(cls,bpy.types.Panel)
        else references.get(row['bl_idname'],set()))
 row['test_files']=sorted(files)
 if cls:
  assert files,(row['bl_idname'],'No execution reference')
  assert all(results.get(Path(file).stem) for file in files),(row['bl_idname'],files)
  row['test_status']='passing_test_references_blender_5_1_2'
 else:
  row['test_status']='explicit_module_tests_only' if files and all(results.get(Path(file).stem) for file in files) else 'inactive_upstream_declaration'
 row['evidence_note']='Passing referenced cases do not establish every option, input geometry or clinical outcome.'
path.write_text(json.dumps(rows,indent=2)+'\n')
print('ODC_INVENTORY_EVIDENCE',len(rows),'declarations;',len(classes),'active operators/panels')
