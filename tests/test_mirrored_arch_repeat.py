"""Repeated mirrored linked setup reuses one path and one tooth per plan."""
import sys,math
from pathlib import Path
import bpy,addon_utils
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
curve=bpy.data.curves.new('Half arch','CURVE');curve.dimensions='3D'
spline=curve.splines.new('POLY');spline.points.add(32)
for i,point in enumerate(spline.points):
 angle=math.pi/2*i/32;point.co=(25*math.cos(angle),25*math.sin(angle),0,1)
source=bpy.data.objects.new('Half arch',curve);bpy.context.collection.objects.link(source)
for number in ('11','21'):
 bpy.context.scene.odc_teeth.add().name=number
first_path=None;first_teeth=None
for attempt in range(3):
 bpy.ops.object.select_all(action='DESELECT')
 active=source if attempt<2 else first_path
 active.select_set(True);bpy.context.view_layer.objects.active=active
 assert bpy.ops.opendental.teeth_to_arch(mirror=True,link=True,limit=True,shift='2')=={'FINISHED'}
 path=bpy.context.object
 teeth=[bpy.data.objects[tooth.contour] for tooth in bpy.context.scene.odc_teeth]
 if attempt==0:
  first_path=path;first_teeth=teeth
 else:
  assert path==first_path, 'Repeated setup created another mirrored arch'
  assert teeth==first_teeth, 'Repeated setup duplicated restorations'
 for tooth in teeth:
  paths=[constraint for constraint in tooth.constraints if constraint.type=='FOLLOW_PATH']
  assert len(paths)==1 and paths[0].target==path
 assert len([obj for obj in bpy.context.scene.objects if obj.type=='CURVE'])==2
 assert len(bpy.data.curves)==2, [(data.name,data.users) for data in bpy.data.curves]
 assert len(path.data.splines)==1 and len(path.data.splines[0].points)==65
 bpy.context.view_layer.update()
 assert (teeth[0].matrix_world.translation-teeth[1].matrix_world.translation).length>.1
print('ODC_MIRRORED_ARCH_REPEAT_PASSED',bpy.app.version_string)
