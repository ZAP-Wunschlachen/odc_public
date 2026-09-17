"""Verify dental role materials without modifying the user's selection or visibility."""
import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
scene = bpy.context.scene
bpy.ops.mesh.primitive_cube_add()
prep = bpy.context.object
bpy.ops.mesh.primitive_cube_add()
crown = bpy.context.object
item = scene.odc_teeth.add()
item.name = '25'
item.prep_model = prep.name
item.restoration = crown.name
item.contour = crown.name
prep.hide_set(True)
bpy.context.preferences.filepaths.use_relative_paths = True
active = bpy.context.view_layer.objects.active
selected = set(bpy.context.selected_objects)
u.material_management(bpy.context, scene.odc_teeth)
assert prep.data.materials[0].name == 'prep'
assert crown.data.materials[0].name == 'restoration'
assert len(crown.material_slots) == 1
assert prep.hide_get()
assert bpy.context.view_layer.objects.active == active
assert set(bpy.context.selected_objects) == selected
assert bpy.context.preferences.filepaths.use_relative_paths
custom = bpy.data.materials.new('custom_color')
extra = bpy.data.materials.new('extra_slot')
crown.data.materials[0] = custom
crown.data.materials.append(extra)
crown.data.polygons[0].material_index = 1
count = len(bpy.data.materials)
u.material_management(bpy.context, item)
assert crown.material_slots[0].material == custom
u.material_management(bpy.context, item, force=True)
assert crown.material_slots[0].material.name == 'restoration'
assert crown.material_slots[1].material == extra
assert crown.data.polygons[0].material_index == 1
assert len(bpy.data.materials) == count
assert prep.hide_get() and bpy.context.view_layer.objects.active == active
# The actual master operator must store Blender's final name after a collision.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.mesh.primitive_cube_add()
master = bpy.context.object
master.name = 'ScanFixture'
collision = bpy.data.objects.new('Master_ScanF', None)
scene.collection.objects.link(collision)
assert bpy.ops.opendental.set_master() == {'FINISHED'}
assert scene.odc_props.master == master.name
assert master.name != collision.name
assert master.data.materials[0].name == 'master'
assert any(c.get('odc_collection_role') == 'Models' for c in master.users_collection)
assert bpy.data.objects[collision.name] == collision
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_DENTAL_MATERIALS_PASSED', bpy.app.version_string)
