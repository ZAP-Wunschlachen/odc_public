import sys
import math
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
tooth = bpy.context.scene.odc_teeth.add()
tooth.name = '25'
tooth.rest_type = '0'
assert bpy.ops.opendental.get_crown_form(ob_list='25') == {'FINISHED'}
crown = bpy.data.objects[tooth.contour]
before = [v.co.copy() for v in crown.data.vertices]
assert bpy.ops.opendental.prep_from_crown(margin_width=.5, reduction=.7) == {'FINISHED'}
prep = bpy.data.objects[tooth.intaglio]
assert prep != crown and prep.data.polygons
assert prep.vertex_groups.get('Margin') and prep.vertex_groups.get('filled_hole')
assert prep.modifiers['Occlusal Reduction'].target == crown
assert abs(prep.modifiers['Occlusal Reduction'].offset+.7) < 1e-6
assert len(before) == len(crown.data.vertices)
assert all((v.co-p).length < 1e-6 for v,p in zip(crown.data.vertices,before))
bpy.context.view_layer.update()
evaluated = prep.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
assert mesh.polygons and all(math.isfinite(c) for v in mesh.vertices for c in v.co)
evaluated.to_mesh_clear()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_PREP_FROM_CROWN_PASSED', bpy.app.version_string)
