import sys
import math
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
curve = bpy.data.curves.new('Double arch', 'CURVE')
curve.dimensions = '3D'
obj = bpy.data.objects.new('Double arch', curve)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
count = len(bpy.data.objects)
assert bpy.ops.opendental.meta_rim_from_curve() == {'CANCELLED'}
assert len(bpy.data.objects) == count
for z in (0, 6):
    spline = curve.splines.new('POLY')
    spline.points.add(20)
    for i, point in enumerate(spline.points):
        angle = math.pi*i/20
        point.co = (20*math.cos(angle),20*math.sin(angle),z,1)
obj.location = (3,4,5)
bpy.context.view_layer.update()
mesh_count = len(bpy.data.meshes)
for kind in ('CUBE','ELLIPSOID'):
    before = set(bpy.data.objects)
    assert bpy.ops.opendental.meta_rim_from_curve(meta_type=kind) == {'FINISHED'}
    result, = set(bpy.data.objects)-before
    assert len(result.data.elements) > 50
    assert all(abs(ball.co.z-3)<1e-5 and abs(ball.size_z-3)<1e-5 for ball in result.data.elements)
    assert all(ball.type == kind for ball in result.data.elements)
    assert len(bpy.data.meshes) == mesh_count
    bpy.context.view_layer.update()
    mesh = bpy.data.meshes.new_from_object(result.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    assert len(mesh.polygons) > 0
    bpy.data.meshes.remove(mesh)
print('ODC_META_RIM_PASSED', bpy.app.version_string)
