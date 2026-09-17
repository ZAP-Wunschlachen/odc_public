import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
convert = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils').bezier_to_mesh
bpy.ops.curve.primitive_bezier_circle_add(radius=2, location=(5,6,7))
curve = bpy.context.object
mesh = convert(curve, 'margin_fixture', 200)
assert len(mesh.vertices) == len(mesh.edges) == 200
assert not mesh.polygons
assert all(abs(v.co.length - 2) < .01 for v in mesh.vertices)
assert curve.type == 'CURVE' and len(curve.data.splines[0].bezier_points) == 4
# Open curve endpoints stay open and are preserved.
bpy.ops.curve.primitive_bezier_curve_add()
curve = bpy.context.object
mesh = convert(curve, 'open_fixture', 30)
assert len(mesh.vertices) == 30 and len(mesh.edges) == 29
assert (mesh.vertices[0].co - curve.data.splines[0].bezier_points[0].co).length < 1e-6
assert (mesh.vertices[-1].co - curve.data.splines[0].bezier_points[-1].co).length < 1e-6
curve.data.bevel_depth = .1
bpy.context.view_layer.update()
try:
    convert(curve, 'invalid_fixture')
except ValueError:
    pass
else:
    raise AssertionError('Beveled surface must not be silently interpreted as margin')
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_MARGIN_CURVE_PASSED', bpy.app.version_string)
