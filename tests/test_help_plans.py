"""Help follows populated plans, current seating modifiers and removed units."""
import sys, importlib
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
help_module = importlib.import_module(f'{ROOT.name}.Operators.help')
scene = bpy.context.scene

def mesh(name):
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    scene.collection.objects.link(obj)
    return obj

tooth = scene.odc_teeth.add()
tooth.name = '25'
assert 'Please mark margin' in help_module.tooth_help_text(tooth)
for role in ('prep_model', 'axis', 'margin', 'pmargin', 'contour', 'intaglio', 'solid'):
    setattr(tooth, role, mesh(role).name)
assert help_module.tooth_help_text(tooth).count('DONE') == 7
pontic = scene.odc_teeth.add()
pontic.name = '26'
pontic.rest_type = '1'
pontic.contour = mesh('Pontic').name
assert 'Pontic Crown Steps: 26' in help_module.tooth_help_text(pontic)
bridge = scene.odc_bridges.add()
bridge.name = '25x26'
bridge.tooth_string = '25:26'
assert 'Not all abutments seated' in help_module.bridge_help_text(bridge)
seal = bpy.data.objects[tooth.contour].modifiers.new('Final Seal', 'SHRINKWRAP')
seal.target = bpy.data.objects[tooth.margin]
text = help_module.bridge_help_text(bridge)
assert text.count('DONE') == 5, text
seal.show_viewport = False
assert 'Not all abutments seated' in help_module.bridge_help_text(bridge)
seal.show_viewport = True
seal.target = bpy.data.objects[tooth.prep_model]
assert 'Not all abutments seated' in help_module.bridge_help_text(bridge)
scene.odc_teeth.remove(1)
assert 'Missing planned units: 26' in help_module.bridge_help_text(bridge)
bridge.tooth_string = ''
assert 'Please add tooth units' in help_module.bridge_help_text(bridge)
implant = scene.odc_implants.add()
implant.name = '27'
assert 'Place Implant' in help_module.implant_help_text(implant)
bpy.ops.mesh.primitive_cube_add(size=2)
cylinder = bpy.context.object
implant.inner = cylinder.name
implant.outer = cylinder.name
implant.implant = mesh('Implant').name
cylinder.location.z = 5
bpy.context.view_layer.update()
text = help_module.implant_help_text(implant)
assert 'Hole Diameter: 2.00mm' in text, text
assert 'Cylinder Depth: 5.00mm' in text, text
print('ODC_HELP_PLANS_PASSED')
