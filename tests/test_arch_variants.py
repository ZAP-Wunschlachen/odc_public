"""Mirror/reverse tooth setup must remain connected to the active arch."""
import sys, math
from pathlib import Path
import bpy, addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
for mirror,reverse in ((False,True),(True,False),(True,True)):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    curve=bpy.data.curves.new('Arch variant','CURVE');curve.dimensions='3D'
    spline=curve.splines.new('POLY');spline.points.add(32)
    for i,point in enumerate(spline.points):
        angle=(math.pi/2 if mirror else math.pi)*i/32
        point.co=(25*math.cos(angle),25*math.sin(angle),0,1)
    arch=bpy.data.objects.new('Arch variant',curve)
    bpy.context.collection.objects.link(arch)
    original_points=[tuple(point.co) for point in spline.points]
    original_resolution=curve.resolution_u
    for point in spline.points:point.select=False
    arch.select_set(True);bpy.context.view_layer.objects.active=arch
    assert bpy.ops.opendental.teeth_to_arch(arch_type='0',shift='2',mirror=mirror,reverse=reverse)=={'FINISHED'}
    bpy.context.view_layer.update()
    teeth=[obj for obj in bpy.context.scene.objects if any(c.type=='FOLLOW_PATH' for c in obj.constraints)]
    assert len(teeth)==14,(mirror,reverse,len(teeth))
    targets={c.target for obj in teeth for c in obj.constraints if c.type=='FOLLOW_PATH'}
    assert len(targets)==1
    target=targets.pop()
    assert bpy.context.object==target, ('Active curve is not the tooth path',mirror,reverse)
    if reverse and not mirror:
        assert tuple(target.data.splines[0].points[0].co)==original_points[-1], 'Reverse ignored unselected control points'
    assert target.data.use_path
    if mirror:
        assert arch.data==curve and not arch.modifiers
        assert curve.resolution_u==original_resolution
        assert [tuple(point.co) for point in spline.points]==original_points
        assert len(target.data.splines)==1, len(target.data.splines)
        target_points=target.data.splines[0].points
        assert len(target_points)==65, len(target_points)
        assert all(abs(math.hypot(point.co.x,point.co.y)-25)<1e-4 for point in target_points), 'Mirror changed the semicircle shape'

    positions=[obj.matrix_world.translation.copy() for obj in teeth]
    assert max((a-b).length for a in positions for b in positions)>20
    before={obj.name:obj.matrix_world.copy() for obj in teeth}
    assert bpy.ops.opendental.arch_plan_keep()=={'FINISHED'}
    bpy.context.view_layer.update()
    for obj in teeth:
        assert not any(c.type=='FOLLOW_PATH' for c in obj.constraints)
        assert max(abs(obj.matrix_world[i][j]-before[obj.name][i][j]) for i in range(4) for j in range(4))<1e-4
# Unsupported anterior mirroring cancels before creating or changing geometry.
objects=set(bpy.data.objects);meshes=set(bpy.data.meshes);curves=set(bpy.data.curves)
assert bpy.ops.opendental.teeth_to_arch(arch_type='7',mirror=True)=={'CANCELLED'}
assert set(bpy.data.objects)==objects and set(bpy.data.meshes)==meshes and set(bpy.data.curves)==curves
print('ODC_ARCH_VARIANTS_PASSED',bpy.app.version_string)
