import sys
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
for diameter in (5, 3):
    assert bpy.ops.opendental.implant_inner_cylinder(thickness=diameter) == {'FINISHED'}
    cylinder = bpy.data.objects[space.inner]
    assert cylinder.parent == implant
    assert len(bpy.data.objects) == count+1
    bpy.context.view_layer.update()
    direction = implant.matrix_world.to_quaternion()
    expected = implant.matrix_world.translation + direction @ Vector((0,0,-(30+implant.dimensions.z)))
    assert (cylinder.matrix_world.translation-expected).length < 1e-5
    assert cylinder.matrix_world.to_quaternion().rotation_difference(direction).angle < 1e-5
    xs = [v.co.x for v in cylinder.data.vertices]
    zs = [v.co.z for v in cylinder.data.vertices]
    assert abs(max(xs)-min(xs)-diameter) < 1e-5
    assert abs(max(zs)-min(zs)-30) < 1e-5
    bm = bmesh.new()
    bm.from_mesh(cylinder.data)
    assert all(e.is_manifold for e in bm.edges)
    bm.free()
    group = cylinder.vertex_groups['Project']
    assigned = {v.index for v in cylinder.data.vertices
                if any(g.group == group.index and g.weight > .99 for g in v.groups)}
    upper = {v.index for v in cylinder.data.vertices if abs(v.co.z-max(zs)) < 1e-5}
    assert assigned == upper, 'Project must contain the complete upper cap only'

assert bpy.ops.opendental.implant_inner_cylinder(use_thickness=False) == {'FINISHED'}
cylinder = bpy.data.objects[space.inner]
xs = [v.co.x for v in cylinder.data.vertices]
assert abs(max(xs)-min(xs)-implant.dimensions.x) < 1e-5
assert len(bpy.data.objects) == count+1
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_INNER_CYLINDER_PASSED', bpy.app.version_string)
