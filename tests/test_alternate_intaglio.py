import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
asset = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '25'
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = asset
tooth.rest_type = '0'
assert bpy.ops.opendental.get_crown_form(ob_list=asset) == {'FINISHED'}
axis = bpy.data.objects.new('axis', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
bpy.ops.curve.primitive_bezier_circle_add(radius=3)
tooth.margin = bpy.context.object.name
assert bpy.ops.opendental.accept_margin() == {'FINISHED'}
assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}
print('ODC_CROWN_SEATING_EXECUTED', flush=True)
import math
from mathutils.kdtree import KDTree
crown = bpy.data.objects[tooth.contour]
margin = bpy.data.objects[tooth.margin]
tree = KDTree(len(margin.data.vertices))
for vertex in margin.data.vertices:
    tree.insert(margin.matrix_world @ vertex.co, vertex.index)
tree.balance()
group = crown.vertex_groups[tooth.margin]
indices = [v.index for v in crown.data.vertices if any(g.group == group.index and g.weight > .99 for g in v.groups)]
assert indices
assert max(tree.find(crown.matrix_world @ crown.data.vertices[i].co)[2] for i in indices) < 1e-4
assert all(math.isfinite(c) for v in crown.data.vertices for c in v.co)
assert any(m.type == 'SHRINKWRAP' and m.name == 'Final Seal' and m.target == margin for m in crown.modifiers)
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.9, location=(0,0,1))
tooth.prep_model = bpy.context.object.name
methods = importlib.import_module(f'{ROOT.name}.Operators.crown_methods')
assert bpy.ops.opendental.calculate_inside(chamfer=.2, gap=.07, holy_zone=.2, no_undercuts=False) == {'FINISHED'}
print('ODC_ALT_INTAGLIO_EXECUTED', tooth.intaglio, flush=True)
inside = bpy.data.objects[tooth.intaglio]
assert len(inside.data.polygons) > 0
assert inside.vertex_groups.get('Holy Zone') and inside.vertex_groups.get('filled_hole')
assert abs(inside.modifiers['Cement Gap'].offset-.07) < 1e-6
bpy.context.view_layer.update()
evaluated = inside.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
evaluated.to_mesh_clear()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_ALTERNATE_INTAGLIO_PASSED', bpy.app.version_string)
