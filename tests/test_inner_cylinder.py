import sys
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
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
    xs = [v.co.x for v in cylinder.data.vertices]
    zs = [v.co.z for v in cylinder.data.vertices]
    assert abs(max(xs)-min(xs)-diameter) < 1e-5
    assert abs(max(zs)-min(zs)-30) < 1e-5
    bm = bmesh.new()
    bm.from_mesh(cylinder.data)
    assert all(e.is_manifold for e in bm.edges)
    bm.free()
    assert cylinder.vertex_groups.get('Project')
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_INNER_CYLINDER_PASSED', bpy.app.version_string)
