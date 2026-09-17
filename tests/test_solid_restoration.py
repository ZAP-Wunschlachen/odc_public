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
assert bpy.ops.opendental.calculate_inside(chamfer=.2, gap=.07, holy_zone=.2, no_undercuts=True) == {'FINISHED'}
print('INTAGLIO_PROBE_DONE', tooth.intaglio, flush=True)
inside = bpy.data.objects[tooth.intaglio]
assert len(inside.data.polygons) > 0
assert inside.vertex_groups.get('Holy Zone') is not None
assert inside.vertex_groups.get('Filled Zone') is not None
assert abs(inside.modifiers['Cement Gap'].offset-.07) < 1e-6
assert inside.modifiers['Cement Gap'].vertex_group == 'Filled Zone'
bpy.context.view_layer.update()
evaluated = inside.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
evaluated.to_mesh_clear()
# Measure actual evaluated distances to the triangulated preparation surface.
from mathutils.bvhtree import BVHTree
prep = bpy.data.objects[tooth.prep_model]
bvh = BVHTree.FromObject(prep, bpy.context.evaluated_depsgraph_get())
filled = inside.vertex_groups['Filled Zone'].index
filled_indices = [v.index for v in inside.data.vertices if any(g.group == filled and g.weight > .99 for g in v.groups)]
assert filled_indices
holy = inside.vertex_groups['Holy Zone'].index
holy_indices = {v.index for v in inside.data.vertices if any(g.group == holy and g.weight > .99 for g in v.groups)}
assert holy_indices and not holy_indices.intersection(filled_indices)
for gap in (.07, .12):
    inside.modifiers['Cement Gap'].offset = gap
    bpy.context.view_layer.update()
    evaluated = inside.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [prep.matrix_world.inverted() @ (evaluated.matrix_world @ mesh.vertices[i].co) for i in filled_indices]
    nearest = [bvh.find_nearest(point) for point in points]
    distances = [result[3] for result in nearest]
    signed = [(point-result[0]).dot(result[1]) for point, result in zip(points, nearest)]
    assert min(signed) > 0, 'Cement zone penetrates the preparation surface'
    evaluated.to_mesh_clear()
    print('MEASURED_CEMENT_GAP', gap, min(distances), max(distances), flush=True)
    assert max(abs(distance-gap) for distance in distances) < .001
previous_name = tooth.intaglio
before_rebuild = len(bpy.data.objects)
assert bpy.ops.opendental.calculate_inside(chamfer=.2, gap=.09, holy_zone=.2, no_undercuts=True) == {'FINISHED'}
assert len(bpy.data.objects) == before_rebuild
assert previous_name not in bpy.data.objects
assert abs(bpy.data.objects[tooth.intaglio].modifiers['Cement Gap'].offset-.09) < 1e-6
before_count = len(bpy.data.objects)
old_inside = tooth.intaglio
tooth.axis = ''
assert bpy.ops.opendental.calculate_inside(no_undercuts=True) == {'CANCELLED'}
assert len(bpy.data.objects) == before_count and tooth.intaglio == old_inside
method = int(sys.argv[sys.argv.index('--')+2]) if '--' in sys.argv and len(sys.argv) > sys.argv.index('--')+2 else 1
assert bpy.ops.opendental.make_solid_restoration(method=method) == {'FINISHED'}
solid = bpy.data.objects[tooth.solid]
import bmesh
bm = bmesh.new()
bm.from_mesh(solid.data)
assert bm.faces
assert all(e.is_manifold for e in bm.edges), 'Unclosed solid restoration'
assert all(math.isfinite(c) for v in bm.verts for c in v.co)
bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_SOLID_RESTORATION_PASSED', bpy.app.version_string)
