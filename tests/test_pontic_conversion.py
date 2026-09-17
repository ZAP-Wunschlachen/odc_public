import sys
import math
from pathlib import Path
import bpy
import bmesh
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = '25'
for variant in ('0', '1', '2'):
    tooth.rest_type = '0'
    assert bpy.ops.opendental.get_crown_form(ob_list='25') == {'FINISHED'}
    crown = bpy.data.objects[tooth.contour]
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,-2))
    tissue = bpy.context.object
    tooth.prep_model = tissue.name
    assert bpy.ops.opendental.pontic_from_crown(p_type=variant, offset=.4) == {'FINISHED'}
    assert tooth.rest_type == '1'
    assert bpy.context.object == tissue
    assert crown.vertex_groups.get('Tissue')
    if variant == '0':
        assert crown.modifiers['Ovate Pontic'].target is not None
    if variant == '1':
        assert crown.modifiers['Tissue Pontic'].target == tissue
        assert abs(crown.modifiers['Tissue Pontic'].offset-.4) < 1e-6
    bpy.context.view_layer.update()
    evaluated = crown.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    assert bm.faces and all(e.is_manifold for e in bm.edges)
    assert all(math.isfinite(c) for v in bm.verts for c in v.co)
    assert abs(bm.calc_volume()) > 0
    bm.free()
    evaluated.to_mesh_clear()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_PONTIC_CONVERSION_PASSED', bpy.app.version_string)
