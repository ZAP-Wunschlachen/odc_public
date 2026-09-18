"""Invalid tray boundaries cancel before any object or scene changes."""
import sys, importlib
from pathlib import Path
import bpy, addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
module=importlib.import_module(f'{ROOT.name}.Operators.bridge')
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
for points,edges,faces in [
    ([],[],[]),
    ([(0,0,0),(1,0,0),(0,1,0)],[(0,1),(1,2)],[]),
    ([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)]),
    ([(0,0,0),(1,0,0),(0,1,0),(3,0,0),(4,0,0),(3,1,0)],
     [(0,1),(1,2),(2,0),(3,4),(4,5),(5,3)],[]),
]:
    mesh=bpy.data.meshes.new('Boundary')
    mesh.from_pydata(points,edges,faces)
    obj=bpy.data.objects.new('Boundary',mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    before=set(bpy.data.objects)
    coordinates=[v.co.copy() for v in mesh.vertices]
    with bpy.context.temp_override(area=area,region=region):
        assert bpy.ops.opendental.cloth_fill_tray()=={'CANCELLED'}
    assert set(bpy.data.objects)==before and obj.data==mesh
    assert all(v.co==co for v,co in zip(mesh.vertices,coordinates))
    assert bpy.context.object==obj and obj.select_get()
    bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.meshes.remove(mesh)
mesh=bpy.data.meshes.new('Valid loop')
mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[(0,1),(1,2),(2,0)],[])
obj=bpy.data.objects.new('Valid loop',mesh)
assert module.cloth_loop_error(obj) is None
curve=bpy.data.curves.new('Curve boundary','CURVE')
obj=bpy.data.objects.new('Curve boundary',curve)
assert module.cloth_loop_error(obj)
spline=curve.splines.new('BEZIER')
assert module.cloth_loop_error(obj)
spline.bezier_points.add(2)
assert module.cloth_loop_error(obj) is None
curve.splines.new('POLY')
assert module.cloth_loop_error(obj)
print('ODC_CLOTH_FILL_VALIDATION_PASSED')
