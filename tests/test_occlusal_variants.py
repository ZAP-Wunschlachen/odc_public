"""The occlusal setup operator must honor its Mirror and Reverse options."""
import sys,math
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
for mirror,reverse in ((False,True),(True,False),(True,True)):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 curve=bpy.data.curves.new('Occlusal arch','CURVE');curve.dimensions='3D'
 spline=curve.splines.new('POLY');spline.points.add(32)
 for i,point in enumerate(spline.points):
  angle=(math.pi/2 if mirror else math.pi)*i/32
  point.co=(25*math.cos(angle),25*math.sin(angle),0,1);point.select=False
 original=[tuple(point.co) for point in spline.points]
 source=bpy.data.objects.new('Occlusal arch',curve);bpy.context.collection.objects.link(source)
 source.select_set(True);bpy.context.view_layer.objects.active=source
 assert bpy.ops.opendental.occlusal_scheme(mirror=mirror,reverse=reverse)=={'FINISHED'}
 path=bpy.context.object
 assert path.type=='CURVE'
 if mirror:
  assert path!=source and len(path.data.splines)==1
  assert len(path.data.splines[0].points)==65
  assert [tuple(point.co) for point in spline.points]==original
 else:
  assert tuple(path.data.splines[0].points[0].co)==original[-1], 'Reverse was ignored'
 teeth=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
 assert len(teeth)==28,len(teeth)
 bpy.context.view_layer.update()
 positions=[obj.matrix_world.translation for obj in teeth]
 assert min(point.x for point in positions)<-15 and max(point.x for point in positions)>15
 assert all(math.isfinite(value) for obj in teeth for row in obj.matrix_world for value in row)
print('ODC_OCCLUSAL_VARIANTS_PASSED',bpy.app.version_string)
