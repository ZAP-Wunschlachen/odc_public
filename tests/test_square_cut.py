"""Square-cutter Boolean modes, explicit target and cleanup."""
import sys
from pathlib import Path
import bpy,bmesh,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete()
collision=bpy.data.objects.new('my_frame_cutter',None);bpy.context.collection.objects.link(collision)
for mode,volume in [('Cut inner',4),('Keep inner',4)]:
    bpy.ops.mesh.primitive_cube_add(size=2)
    model=bpy.context.object
    sibling=bpy.data.objects.new('Shared input',model.data);bpy.context.collection.objects.link(sibling)
    original=sibling.data
    bpy.ops.mesh.primitive_cube_add(size=2,location=(1,0,0))
    cutter=bpy.context.object;cutter['odc_square_target']=model
    bpy.context.scene.ODC_modops_props.cutting_mode=mode
    assert bpy.ops.opendental.square_cut_confirm()=={'FINISHED'}
    bm=bmesh.new();bm.from_mesh(model.data)
    assert all(e.is_manifold for e in bm.edges)
    assert abs(bm.calc_volume(signed=False)-volume)<1e-5
    bm.free()
    xs=[v.co.x for v in model.data.vertices]
    assert (max(xs)<=1e-5 if mode=='Cut inner' else min(xs)>=-1e-5)
    assert sibling.data==original and model.data!=original
    assert len(original.vertices)==8
    assert bpy.context.object==cutter
    assert bpy.ops.opendental.square_cut_exit()=={'FINISHED'}
    assert bpy.context.object==model
    assert collision.name=='my_frame_cutter'
assert bpy.ops.opendental.square_cut_confirm()=={'CANCELLED'}
assert bpy.ops.opendental.square_cut_exit()=={'CANCELLED'}
print('ODC_SQUARE_CUT_PASSED')
