import sys
import math
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
m = importlib.import_module(f'{ROOT.name}.Operators.full_arch_methods')
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
curve = bpy.data.curves.new('Arch test', 'CURVE')
curve.dimensions = '3D'
curve.use_path = True
spline = curve.splines.new('POLY')
spline.points.add(32)
for i, point in enumerate(spline.points):
    angle = math.pi * i / 32
    point.co = (25*math.cos(angle), 25*math.sin(angle), 0, 1)
arch = bpy.data.objects.new('Arch test', curve)
bpy.context.scene.collection.objects.link(arch)
bpy.context.view_layer.objects.active = arch
arch.select_set(True)
assert bpy.ops.opendental.occlusal_scheme() == {'FINISHED'}
objects = [o for o in bpy.context.scene.objects if '_ArchPlanned' in o.name]
assert len(objects) == 28, len(objects)
for obj in objects:
    assert all(math.isfinite(value) for row in obj.matrix_world for value in row)
    assert min(obj.scale) > 0
print('ODC_OCCLUSAL_SCHEME_PASSED', bpy.app.version_string)
