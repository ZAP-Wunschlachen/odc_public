import sys
import math
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = '25'
assert bpy.ops.opendental.get_crown_form(ob_list='25') == {'FINISHED'}
axis = bpy.data.objects.new('axis', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
crown = bpy.data.objects[tooth.contour]
# Identify boundary and its adjacent ring independently from the operator.
import bmesh
bm = bmesh.new()
bm.from_mesh(crown.data)
boundary = {v.index for e in bm.edges if e.is_boundary for v in e.verts}
pairs = [(e.verts[0].index, e.verts[1].index) for e in bm.edges
         if (e.verts[0].index in boundary) != (e.verts[1].index in boundary)]
pairs = [(a,b) if a in boundary else (b,a) for a,b in pairs]
bm.free()
assert pairs
before = [v.co.copy() for v in crown.data.vertices]
for angle in (.15, .3):
    lengths = [(crown.data.vertices[b].co-crown.data.vertices[a].co).length for a,b in pairs]
    assert bpy.ops.opendental.cervical_convergence(ang=angle) == {'FINISHED'}
    for (a,b), length in zip(pairs, lengths):
        edge = crown.data.vertices[b].co-crown.data.vertices[a].co
        assert abs(edge.length-length) < 1e-5
        assert abs(edge.angle(Vector((0,0,1)))-angle) < 1e-5
    assert all((crown.data.vertices[i].co-before[i]).length < 1e-6 for i in boundary)
assert all(math.isfinite(c) for v in crown.data.vertices for c in v.co)
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CERVICAL_CONVERGENCE_PASSED', bpy.app.version_string)
