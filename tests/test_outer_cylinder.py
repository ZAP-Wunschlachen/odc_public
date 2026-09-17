import sys
import math
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
u.get_settings().behavior = '0'
space = bpy.context.scene.odc_implants.add()
space.name = '25'
implant = bpy.context.object
implant.location = (3,4,5)
implant.rotation_euler = (.2,.3,.4)
space.implant = implant.name
bpy.context.view_layer.update()
count = len(bpy.data.objects)
for trim, depth in ((0, 20), (.5, 15)):
    assert bpy.ops.opendental.implant_guide_cylinder(width=6, depth=depth, trim_width=trim) == {'FINISHED'}
    cylinder = bpy.data.objects[space.outer]
    assert cylinder.parent == implant
    assert len(bpy.data.objects) == count+1
    bpy.context.view_layer.update()
    orientation = implant.matrix_world.to_quaternion()
    expected = implant.matrix_world.translation + orientation @ Vector((0,0,-depth))
    assert (cylinder.matrix_world.translation-expected).length < 1e-5
    assert cylinder.matrix_world.to_quaternion().rotation_difference(orientation).angle < 1e-5
    xs = [v.co.x for v in cylinder.data.vertices]
    ys = [v.co.y for v in cylinder.data.vertices]
    zs = [v.co.z for v in cylinder.data.vertices]
    assert abs(max(xs)-min(xs)-6) < 1e-5
    assert abs(max(ys)-min(ys)-(6-2*trim)) < 1e-5
    assert abs(max(zs)-min(zs)-.1) < 1e-5
    bm = bmesh.new()
    bm.from_mesh(cylinder.data)
    assert all(e.is_manifold for e in bm.edges)
    bm.free()
    group = cylinder.vertex_groups['Project']
    assigned = {v.index for v in cylinder.data.vertices if any(g.group == group.index for g in v.groups)}
    assert assigned == {v.index for v in cylinder.data.vertices if abs(v.co.z-.1) < 1e-5}
# Wedges follow the existing 64-segment angular quantization.
for fraction in (.25, .65, .9, 1):
    assert bpy.ops.opendental.implant_guide_cylinder(width=6, depth=18, use_wedge=True, pctg=fraction) == {'FINISHED'}
    cylinder = bpy.data.objects[space.outer]
    bm = bmesh.new()
    bm.from_mesh(cylinder.data)
    assert bm.faces and all(e.is_manifold for e in bm.edges)
    segments = 64 if fraction >= .99 else round(fraction*64)
    expected_volume = segments * .5 * 9 * math.sin(2*math.pi/64) * .1
    assert abs(abs(bm.calc_volume())-expected_volume) < 1e-5
    assert all(math.isfinite(c) for v in bm.verts for c in v.co)
    bm.free()
    group = cylinder.vertex_groups['Project']
    assigned = {v.index for v in cylinder.data.vertices if any(g.group == group.index for g in v.groups)}
    assert assigned == {v.index for v in cylinder.data.vertices if abs(v.co.z-.1) < 1e-5}
    assert len(bpy.data.objects) == count+1
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_OUTER_CYLINDER_PASSED', bpy.app.version_string)
