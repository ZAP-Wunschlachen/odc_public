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
for shift in ('COM', 'BUCCAL', 'FOSSA'):
    m.teeth_to_curve(bpy.context, arch, 'MAX', u.get_settings().tooth_lib, shift=shift)
    bpy.context.view_layer.update()
    objects = [o for o in bpy.context.scene.objects if any(c.type == 'FOLLOW_PATH' and c.target == arch for c in o.constraints)]
    assert len(objects) == 14, len(objects)
    positions = []
    for obj in objects:
        assert all(math.isfinite(value) for row in obj.matrix_world for value in row)
        assert min(obj.dimensions) > 0
        assert len([c for c in obj.constraints if c.type == 'FOLLOW_PATH']) == 1
        positions.append(obj.matrix_world.translation.copy())
    assert max((a-b).length for a in positions for b in positions) > 20
print('ODC_TEETH_TO_CURVE_PASSED', bpy.app.version_string)
