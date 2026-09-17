"""Exercise actual Accept Margin, replacement, repeat and failed input preservation."""
import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = '25'
bpy.ops.curve.primitive_bezier_circle_add(radius=2, location=(3,4,5))
margin = bpy.context.object
original_matrix = margin.matrix_world.copy()
tooth.margin = margin.name
axis = bpy.data.objects.new('axis_fixture', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
for _ in range(2):
    assert bpy.ops.opendental.accept_margin() == {'FINISHED'}
    margin = bpy.data.objects[tooth.margin]
    ribbon = bpy.data.objects[tooth.pmargin]
    assert margin.type == 'MESH' and len(margin.data.vertices) == 200
    assert margin.matrix_world == original_matrix
    assert len(ribbon.data.vertices) == 400 and len(ribbon.data.polygons) == 200
    assert ribbon.hide_get()
    assert len([o for o in scene.objects if o.name.startswith('25_Psuedo Margin')]) == 1
# Invalid open input must preserve it and the last accepted ribbon.
bpy.ops.curve.primitive_bezier_curve_add()
invalid = bpy.context.object
tooth.margin = invalid.name
old_ribbon = tooth.pmargin
count = len(bpy.data.meshes)
assert bpy.ops.opendental.accept_margin() == {'CANCELLED'}
assert bpy.data.objects[tooth.margin] == invalid
assert tooth.pmargin == old_ribbon and old_ribbon in bpy.data.objects
assert len(bpy.data.meshes) == count
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_ACCEPT_MARGIN_PASSED', bpy.app.version_string)
