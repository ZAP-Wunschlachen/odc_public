"""Evaluate directional contact projection rather than just inspecting settings."""
import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.mesh.primitive_plane_add(size=10)
target = bpy.context.object
bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,1))
crown = bpy.context.object
tooth = bpy.context.scene.odc_teeth.add()
tooth.name = '25'
tooth.restoration = crown.name
tooth.opposing = target.name
original = [v.co.copy() for v in crown.data.vertices]
def world_vertices():
    bpy.context.view_layer.update()
    evaluated = crown.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    verts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return verts
assert bpy.ops.opendental.grind_occlusion(overlap=.05) == {'FINISHED'}
assert all(abs(v.z-.05) < 1e-5 for v in world_vertices())
assert bpy.ops.opendental.grind_occlusion(overlap=.1) == {'FINISHED'}
assert len(crown.modifiers) == 1
assert all(abs(v.z-.1) < 1e-5 for v in world_vertices())
assert [v.co for v in crown.data.vertices] == original
# Missing neighbors do not add targetless modifiers.
assert bpy.ops.opendental.grind_contacts() == {'CANCELLED'}
assert len(crown.modifiers) == 1
# Rotate the fixture to test local X projection for both contact directions.
crown.modifiers.clear()
from math import pi
target.rotation_euler.y = pi/2
from mathutils import Matrix
crown.data.transform(Matrix.Rotation(pi/2, 4, 'Y'))
crown.location = (1,0,0)
tooth.mesial = target.name
assert bpy.ops.opendental.grind_contacts(distal=False, overlap=.04) == {'FINISHED'}
assert all(abs(v.x-.04) < 1e-5 for v in world_vertices()), world_vertices()
assert bpy.ops.opendental.grind_contacts(distal=False, overlap=.08) == {'FINISHED'}
assert len(crown.modifiers) == 1
assert all(abs(v.x-.08) < 1e-5 for v in world_vertices())
crown.modifiers.clear()
# Original distal negative offset projects beyond the target plane.
crown.location.x = -1
tooth.distal = target.name
assert bpy.ops.opendental.grind_contacts(mesial=False, overlap=.04) == {'FINISHED'}
assert all(abs(v.x-.04) < 1e-5 for v in world_vertices()), world_vertices()
assert bpy.ops.opendental.grind_contacts(mesial=False, overlap=.08) == {'FINISHED'}
assert len(crown.modifiers) == 1
assert all(abs(v.x-.08) < 1e-5 for v in world_vertices())
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_CONTACT_ADJUSTMENT_PASSED', bpy.app.version_string)
