"""Contact assessment uses the restoration, preserves context and evaluates distances."""
import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=10)
target = bpy.context.object
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,.25))
crown = bpy.context.object
bpy.ops.mesh.primitive_cube_add(location=(20,20,20))
contour = bpy.context.object
tooth = scene.odc_teeth.add()
tooth.name = '25'
tooth.restoration = crown.name
tooth.contour = contour.name
tooth.opposing = target.name
active = bpy.context.object
selected = set(bpy.context.selected_objects)
assert bpy.ops.opendental.asses_contacts(min_d=0, max_d=.5) == {'FINISHED'}
assert bpy.context.object == active and set(bpy.context.selected_objects) == selected
assert not contour.modifiers
assert len(crown.modifiers) == 1
bpy.context.view_layer.update()
def weights():
    evaluated = crown.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    result = [v.groups[0].weight for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return result
assert all(abs(w-.5) < 1e-5 for w in weights()), weights()
assert bpy.ops.opendental.asses_contacts(min_d=0, max_d=1) == {'FINISHED'}
bpy.context.view_layer.update()
assert len(crown.modifiers) == 1
assert all(abs(w-.25) < 1e-5 for w in weights()), weights()
target.location.z = .25
bpy.context.view_layer.update()
assert all(abs(w) < 1e-5 for w in weights()), weights()
assert bpy.ops.opendental.asses_contacts(min_d=.5, max_d=.5) == {'CANCELLED'}
assert crown.modifiers[0].max_dist == 1
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CROWN_CONTACT_ASSESSMENT_PASSED', bpy.app.version_string)
