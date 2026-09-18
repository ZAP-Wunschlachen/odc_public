"""Draw every registered ODC panel using a real Blender UILayout."""
import sys, importlib, traceback, os, ast
from pathlib import Path
from types import SimpleNamespace
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
module = importlib.import_module(ROOT.name + '.Panels.panel')
panels = [value for value in vars(module).values()
          if isinstance(value, type) and issubclass(value, bpy.types.Panel) and value.is_registered]
assert len(panels) == 8, panels
errors = []
# Verify actual RNA lookup, including operators drawn only in alternate branches.
for node in ast.walk(ast.parse(Path(module.__file__).read_text())):
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'operator' and node.args
            and isinstance(node.args[0], ast.Constant)):
        namespace, name = node.args[0].value.split('.')
        try:
            getattr(getattr(bpy.ops, namespace), name).get_rna_type()
        except KeyError:
            errors.append('Missing panel operator: ' + node.args[0].value)
for prop in ('show_modops','show_teeth','show_implant','show_bridge','show_splint','show_ortho','show_dentures'):
    setattr(bpy.context.scene.odc_props, prop, True)
drawn = set()
class ODC_PT_draw_test(bpy.types.Panel):
    bl_idname = 'ODC_PT_draw_test'
    bl_label = 'ODC panel verification'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    def draw(self, context):
        for panel in panels:
            try:
                panel.draw(SimpleNamespace(layout=self.layout.box()), context)
                drawn.add(panel.__name__)
            except Exception:
                errors.append(traceback.format_exc())
bpy.utils.register_class(ODC_PT_draw_test)
phase = 0
def run():
    global phase
    try:
        if phase == 0:
            area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.wm.call_panel(name='ODC_PT_draw_test', keep_open=True)
            phase = 1
            return 1
        assert not errors, '\n'.join(errors)
        assert len(drawn) == 8, drawn
        if phase < 3:
            scene = bpy.context.scene
            if phase == 1:
                for collection in (scene.odc_teeth, scene.odc_implants, scene.odc_bridges, scene.odc_splints):
                    collection.add().name = '25'
                scene.frame_set(0)
                scene.ODC_modops_props.cutting_tool = 'Square Cutting Tool'
                scene.splint_mode = 'PAINT'
                bpy.context.object.data.materials.clear()
                bpy.context.object.data.materials.append(None)
                bpy.context.object.modifiers.new('Panel flexi branch', 'LAPLACIANDEFORM')
                bpy.context.object.modifiers.new('Panel lattice branch', 'LATTICE')
            else:
                bpy.context.view_layer.objects.active = None
            drawn.clear()
            area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.wm.call_panel(name='ODC_PT_draw_test', keep_open=True)
            phase += 1
            return 1
        print('ODC_PANEL_DRAWING_PASSED', flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc(); os._exit(1)
bpy.app.timers.register(run, first_interval=2)
