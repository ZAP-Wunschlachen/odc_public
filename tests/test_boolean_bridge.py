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
scene = bpy.context.scene
for names in (('24','25'), ('14','15'), ('11','21')):
    scene.odc_teeth.clear()
    scene.odc_bridges.clear()
    for index,name in enumerate(names):
        bpy.ops.mesh.primitive_cube_add(location=(index,0,0))
        tooth = scene.odc_teeth.add()
        tooth.name = name
        tooth.contour = bpy.context.object.name
    bridge = scene.odc_bridges.add()
    bridge.name = 'TestBridge'
    bridge.tooth_string = ':'.join(names)
    assert bpy.ops.opendental.bridge_boolean() == {'FINISHED'}
    obj = bpy.data.objects[bridge.bridge]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    assert bm.faces and all(e.is_manifold for e in bm.edges)
    assert abs(abs(bm.calc_volume())-12) < 1e-5
    bm.free()
    old_name = obj.name
    old_mesh = obj.data.name
    object_count = len(bpy.data.objects)
    assert bpy.ops.opendental.bridge_boolean() == {'FINISHED'}
    assert len(bpy.data.objects) == object_count
    assert old_name not in bpy.data.objects
    assert old_mesh not in bpy.data.meshes
    rebuilt = bpy.data.objects[bridge.bridge]
    bm = bmesh.new()
    bm.from_mesh(rebuilt.data)
    assert abs(abs(bm.calc_volume())-12) < 1e-5
    bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_BOOLEAN_BRIDGE_PASSED', bpy.app.version_string)
