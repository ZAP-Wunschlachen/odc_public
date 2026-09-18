"""The preferences report reads real addon settings and changes no scene data."""
import sys,io,contextlib
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
prefs=bpy.context.preferences.addons[ROOT.name].preferences
for field in ('tooth_lib','imp_lib','mat_lib','drill_lib','ortho_lib'):
    setattr(prefs,field,'/test/preferences/'+field+'.blend')
prefs.behavior='1';prefs.workflow='2'
objects=set(bpy.data.objects)
output=io.StringIO()
with contextlib.redirect_stdout(output):
    assert bpy.ops.opendental.odc_addon_pref()=={'FINISHED'}
text=output.getvalue()
for field in ('tooth_lib','imp_lib','mat_lib','drill_lib','ortho_lib'):
    assert getattr(prefs,field) in text
assert 'ACTIVE' in text and 'MULTIPLE_PARALLEL' in text
assert set(bpy.data.objects)==objects
print('ODC_PREFERENCES_REPORT_PASSED')
