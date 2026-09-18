"""Public blockout dispatch forwards inputs and cancellation (not geometry proof)."""
import sys,importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import bpy,addon_utils
from mathutils import Euler,Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
module=importlib.import_module(f'{ROOT.name}.Operators.blockout_undercuts')
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
bpy.ops.mesh.primitive_cube_add()
source=bpy.context.object
scene=bpy.context.scene
with bpy.context.temp_override(area=area,region=region):
    scene.UNDERCUTS_props.Modelsprop='Preview'
    current=Euler((.2,.3,.4)).to_quaternion()
    stored=Euler((.7,.1,.2)).to_quaternion()
    area.spaces.active.region_3d.view_rotation=current
    scene.UNDERCUTS_view_props.survey_quaternion=stored
    for surveyed,expected in ((False,current),(True,stored)):
        scene.pre_surveyed=surveyed
        with patch.object(module.bmesh_fns,'remove_undercuts') as preview:
            assert bpy.ops.opendental.blockout_model(world=False,smooth=False)=={'FINISHED'}
            preview.assert_called_once()
            args=preview.call_args.args
            assert args[1]==source
            assert (args[2]-(expected@Vector((0,0,1)))).length<1e-6
            assert args[3:] == (False,False)
    scene.UNDERCUTS_props.Modelsprop='Solid'
    for outcome in ({'CANCELLED'},{'FINISHED'}):
        calls=[]
        def solid():
            calls.append(True)
            return outcome
        fake=SimpleNamespace(ops=SimpleNamespace(opendental=SimpleNamespace(view_blockout_undercuts_solid=solid)))
        with patch.object(module,'bpy',fake):
            assert bpy.ops.opendental.blockout_model()==outcome
        assert calls==[True]
    source.select_set(False)
    assert not bpy.ops.opendental.blockout_model.poll()
    assert not bpy.ops.opendental.view_blockout_undercuts_solid.poll()
    source.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    assert not bpy.ops.opendental.blockout_model.poll()
    assert not bpy.ops.opendental.view_blockout_undercuts_solid.poll()
    bpy.ops.object.mode_set(mode='OBJECT')
print('ODC_BLOCKOUT_DISPATCH_PASSED')
