"""Isolate shutdown allocations; -- prepare or -- seat. Inspect Blender's exit log."""
import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
mode = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'prepare'
assert mode in {'prepare', 'seat'}
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = '16'
axis = bpy.data.objects.new('axis', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
assert bpy.ops.opendental.get_crown_form(ob_list='16') == {'FINISHED'}
bpy.ops.curve.primitive_bezier_circle_add(radius=3)
tooth.margin = bpy.context.object.name
assert bpy.ops.opendental.accept_margin() == {'FINISHED'}
if mode == 'seat':
    assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_SHUTDOWN_PROBE_COMPLETED', mode, flush=True)
