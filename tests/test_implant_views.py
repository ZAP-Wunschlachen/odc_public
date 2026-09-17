import sys
import traceback
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name, default_set=True)
        area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(area=area, region=region):
            view = area.spaces.active
            assert bpy.ops.opendental.slice_view(thickness=2) == {'FINISHED'}
            assert len(view.region_quadviews) == 4
            assert abs(view.clip_end-view.clip_start-2) < 1e-4
            assert bpy.ops.opendental.normal_view() == {'FINISHED'}
            assert not view.region_quadviews
            assert abs(view.clip_end-view.clip_start-10000) < .01
        addon_utils.disable(ROOT.name, default_set=True)
        print('ODC_IMPLANT_VIEWS_PASSED', flush=True)
    except Exception:
        traceback.print_exc()
        import os
        os._exit(1)
    bpy.ops.wm.quit_blender()
bpy.app.timers.register(run, first_interval=2)
