"""Preparation assignment and extraction preserve world geometry and source data."""
import sys
from pathlib import Path
import bpy
import bmesh
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.context.preferences.addons[ROOT.name].preferences.workflow = '0'
scene = bpy.context.scene
tooth = scene.odc_teeth.add()
tooth.name = '25'
bpy.ops.mesh.primitive_cube_add(location=(3, 4, 5))
master = bpy.context.object
master.rotation_euler = (.2, .4, .1)
master.scale = (2, 3, 4)
scene.odc_props.master = master.name
material = bpy.data.materials.new('scan_material')
master.data.materials.append(material)
bpy.context.view_layer.update()
def coords(obj):
    return sorted(tuple(round(x, 5) for x in obj.matrix_world @ v.co) for v in obj.data.vertices)
original = coords(master)
assert bpy.ops.opendental.set_as_prep() == {'FINISHED'}
prep = bpy.data.objects[tooth.prep_model]
bpy.context.view_layer.update()
assert prep != master and prep.data != master.data
assert prep.parent == master
assert coords(prep) == original == coords(master)
# Extract one face; source geometry must remain unchanged.
master.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
master.select_set(True)
bpy.context.view_layer.objects.active = master
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(master.data)
bm.faces.ensure_lookup_table()
bm.faces[0].select_set(True)
bmesh.update_edit_mesh(master.data)
assert bpy.ops.opendental.set_as_prep() == {'FINISHED'}
extracted = bpy.data.objects[tooth.prep_model]
bpy.context.view_layer.update()
assert extracted != prep and len(extracted.data.polygons) == 1
assert len(extracted.data.vertices) == 4
assert extracted.data.materials[0] == material
assert coords(master) == original and len(master.data.polygons) == 6
assert all(v in original for v in coords(extracted))
# Existing abutment parenting must survive explicit abutment assignment.
bpy.ops.mesh.primitive_cube_add()
abutment = bpy.context.object
parent = bpy.data.objects.new('implant_fixture', None)
scene.collection.objects.link(parent)
abutment.parent = parent
assert bpy.ops.opendental.set_as_prep(abutment=True) == {'FINISHED'}
assert bpy.data.objects[tooth.prep_model] == abutment
assert abutment.parent == parent
# Parallel workflow returns to editing the source; empty selections cancel safely.
bpy.context.preferences.addons[ROOT.name].preferences.workflow = '1'
assert bpy.ops.opendental.set_as_prep(abutment=True) == {'FINISHED'}
assert bpy.context.mode == 'EDIT_MESH' and bpy.context.object == abutment
bpy.ops.mesh.select_all(action='DESELECT')
count = len(bpy.data.objects)
previous = tooth.prep_model
assert bpy.ops.opendental.set_as_prep() == {'CANCELLED'}
assert len(bpy.data.objects) == count and tooth.prep_model == previous
bpy.ops.object.mode_set(mode='OBJECT')
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_PREPARATION_ASSIGNMENT_PASSED', bpy.app.version_string)
