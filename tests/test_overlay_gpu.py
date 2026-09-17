"""Run in a separate foreground Blender instance to exercise the actual GPU."""
import sys
import importlib
import traceback
from pathlib import Path
import bpy
import addon_utils
import gpu
from mathutils import Matrix
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
def run():
    try:
        assert addon_utils.enable(ROOT.name, default_set=True)
        TextBox = importlib.import_module(f'{ROOT.name}.Operators.textbox').TextBox
        draw = importlib.import_module(f'{ROOT.name}.Operators.bgl_utils').insertion_axis_callback
        area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
        region = next(r for r in area.regions if r.type == 'WINDOW')
        with bpy.context.temp_override(area=area, region=region):
            width, height = region.width, region.height
            offscreen = gpu.types.GPUOffScreen(width, height)
            with offscreen.bind():
                gpu.state.active_framebuffer_get().clear(color=(.08, .08, .08, 1))
                with gpu.matrix.push_pop():
                    gpu.matrix.load_matrix(Matrix.Identity(4))
                    gpu.matrix.load_projection_matrix(Matrix(((2/width,0,0,-1),(0,2/height,0,-1),(0,0,-1,0),(0,0,0,1))))
                    box = TextBox(bpy.context, width/2, height-60, 300, 200, 10, 20, 'Set axis for 25\nEnter to finish\nESC to cancel')
                    box.draw()
                    draw(None, bpy.context)
                pixels = gpu.state.active_framebuffer_get().read_color(0,0,width,height,4,0,'FLOAT')
                pixels.dimensions = width * height * 4
                assert sum(value > .9 for value in list(pixels)[0::4]) > 50
                img = bpy.data.images.new('overlay_fixture', width, height)
                img.pixels.foreach_set(pixels)
                target = ROOT / 'tests/artifacts/axis_overlay.png'
                target.parent.mkdir(exist_ok=True)
                img.filepath_raw = str(target)
                img.file_format = 'PNG'
                img.save()
            offscreen.free()
        print('ODC_OVERLAY_GPU_PASSED', flush=True)
    except Exception:
        traceback.print_exc()
        print('ODC_OVERLAY_GPU_FAILED', flush=True)
        import os
        os._exit(1)
    bpy.ops.wm.quit_blender()
    return None
bpy.app.timers.register(run, first_interval=2)
