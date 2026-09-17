"""Refinement enters edit mode with a single surface constraint and preserves placement."""
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
bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(3,4,5))
prep = bpy.context.object
tooth.prep_model = prep.name
bpy.ops.curve.primitive_bezier_circle_add(radius=2, location=(3,4,5))
tooth.margin = bpy.context.object.name
for _ in range(2):
    assert bpy.ops.opendental.refine_margin() == {'FINISHED'}
    assert bpy.context.mode == 'EDIT_MESH'
    margin = bpy.context.object
    assert margin.name == tooth.margin and margin.type == 'MESH'
    assert len(margin.modifiers) == 1 and margin.modifiers[0].target == prep
    assert margin.modifiers[0].show_on_cage
    assert bpy.context.tool_settings.use_proportional_edit
    assert bpy.context.tool_settings.snap_elements == {'FACE'}
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    assert len(margin.data.vertices) == 200
    assert all(abs((margin.matrix_world @ v.co).z-5) < 1e-5 for v in margin.data.vertices)
# Exercise the complete refine -> accept transition with evaluated constraint.
axis = bpy.data.objects.new('axis_fixture', None)
scene.collection.objects.link(axis)
tooth.axis = axis.name
assert bpy.ops.opendental.refine_margin() == {'FINISHED'}
assert bpy.ops.opendental.accept_margin() == {'FINISHED'}
assert bpy.context.mode == 'OBJECT'
assert not bpy.context.tool_settings.use_proportional_edit
assert tooth.pmargin in bpy.data.objects
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_REFINE_MARGIN_PASSED', bpy.app.version_string)
