"""Report generation accepts numeric and custom plan names and replaces old text."""
import sys
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
scene=bpy.context.scene
for name in ('25','Custom unit'):
    tooth=scene.odc_teeth.add();tooth.name=name;tooth.contour='Contour '+name
assert bpy.ops.opendental.crown_report()=={'FINISHED'}
report=bpy.data.texts['Crown Report']
text=report.as_string()
assert 'Tooth #25' in text and 'Tooth #Custom unit' in text
assert 'Contour 25' in text and 'Contour Custom unit' in text
report.write('STALE CONTENT')
assert bpy.ops.opendental.crown_report()=={'FINISHED'}
assert bpy.data.texts['Crown Report']==report
assert 'STALE CONTENT' not in report.as_string()
print('ODC_CROWN_REPORT_PASSED')
