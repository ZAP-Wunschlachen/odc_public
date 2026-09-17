import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
u.get_settings().behavior = '0'
scene = bpy.context.scene
sources = []
margins = []
for index, name in enumerate(('24','25')):
    tooth = scene.odc_teeth.add()
    tooth.name = name
    scene.odc_tooth_index = index
    scene.cursor.location = (index*8,0,0)
    assert bpy.ops.opendental.get_crown_form(ob_list=name) == {'FINISHED'}
    sources.append(bpy.data.objects[tooth.contour])
    axis = bpy.data.objects.new(name+'_axis', None)
    scene.collection.objects.link(axis)
    tooth.axis = axis.name
    bpy.ops.curve.primitive_bezier_circle_add(radius=3, location=(index*8,0,0))
    tooth.margin = bpy.context.object.name
    assert bpy.ops.opendental.accept_margin() == {'FINISHED'}
    assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}
    margins.append(bpy.data.objects[tooth.margin])
bridge = scene.odc_bridges.add()
bridge.name = '24x25'
bridge.tooth_string = '24:25'
assert bpy.ops.opendental.make_prebridge() == {'FINISHED'}
result = bpy.data.objects[bridge.bridge]
assert result not in sources
assert len(result.data.vertices) == sum(len(obj.data.vertices) for obj in sources)
assert result.vertex_groups.get('Bridge Margin') and result.vertex_groups.get('Connectors')
assert result.modifiers.get('Smooth Connectors')
assert all(obj.name in scene.objects for obj in sources)
combined_margin = bpy.data.objects[bridge.margin]
assert len(combined_margin.data.vertices) == sum(len(m.data.vertices) for m in margins)
assert result.modifiers['Bridge Margin'].target == combined_margin
from mathutils.kdtree import KDTree
tree = KDTree(len(combined_margin.data.vertices))
for vertex in combined_margin.data.vertices:
    tree.insert(combined_margin.matrix_world @ vertex.co, vertex.index)
tree.balance()
for margin in margins:
    assert all(tree.find(margin.matrix_world @ vertex.co)[2] < 1e-5 for vertex in margin.data.vertices)
assert all(m.name in scene.objects for m in margins)
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_PREBRIDGE_PASSED', bpy.app.version_string)
