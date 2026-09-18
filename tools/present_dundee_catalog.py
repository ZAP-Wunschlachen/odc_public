"""Add deterministic asset categories, rendered thumbnails and a review scene."""
import argparse
import json
import math
from pathlib import Path
import sys
import uuid
import bpy
from mathutils import Vector, Matrix, Quaternion

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--library',required=True,type=Path)
p.add_argument('--previews',required=True,type=Path)
p.add_argument('--overview',required=True,type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.library=a.library.resolve();a.previews=a.previews.resolve();a.overview=a.overview.resolve()
a.previews.mkdir(parents=True,exist_ok=True);a.overview.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.library))
s=bpy.context.scene
objects=sorted(list(s.objects),key=lambda o:o.name)
assert {o.name for o in objects}=={f'{q}{n}' for q in (1,2,3,4) for n in range(1,9)}
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=256;s.render.resolution_y=256;s.render.resolution_percentage=100
s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.79,.76,.69)
s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
s.display.shading.curvature_ridge_factor=.5;s.display.shading.curvature_valley_factor=.6
s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Dundee Neutral');s.world.color=(.025,.035,.05)
camdata=bpy.data.cameras.new('Preview camera');cam=bpy.data.objects.new('Preview camera',camdata)
s.collection.objects.link(cam);s.camera=cam;camdata.type='ORTHO'
catalogs={}
for ob in objects:ob.hide_render=True
for ob in objects:
 fdi=int(ob.name);family=ob['Tooth family'];jaw=ob['Jaw'];path='Dundee/'+jaw+'/'+family
 cid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/ZAP-Wunschlachen/odc_public/dundee/'+jaw+'/'+family))
 ob.asset_data.catalog_id=cid;catalogs[path]=cid
 if fdi in (31,32,41,42):
  ob['Source identification review']='Author title and internal LL1/LL2 node labels conflict; catalogue follows author title. Anatomical identity requires review.'
  ob.asset_data.tags.new('identity-review')
  ob.asset_data.description+=' Source identification conflict: author title versus LL1/LL2 node labels; review identity.'
 v=[v.co for v in ob.data.vertices];low=Vector(tuple(min(q[k] for q in v) for k in range(3)));high=Vector(tuple(max(q[k] for q in v) for k in range(3)));center=(low+high)/2
 sign=-1 if fdi//10 in (2,4) else 1
 direction=Vector((.75,sign,1)).normalized();cam.location=center+50*direction;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
 camdata.ortho_scale=max(high-low)*1.35;ob.hide_render=False
 pathpng=a.previews/(ob.name+'.png');s.render.filepath=str(pathpng)
 bpy.ops.render.render(write_still=True)
 with bpy.context.temp_override(id=ob):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(pathpng))
 assert ob.preview.image_size[0]>0
 ob.hide_render=True
 print('PREVIEW',ob.name,flush=True)
for ob in objects:ob.hide_render=False
bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(camdata);s.camera=None
s.render.filepath='//'
# Runtime must contain only the 32 callable FDI mesh names.
assert len(bpy.data.objects)==32
bpy.ops.wm.save_as_mainfile(filepath=str(a.library))
cattext='# Blender Asset Catalog Definition File\nVERSION 1\n\n'
for path,cid in sorted(catalogs.items()):cattext+=f'{cid}:{path}:{path.replace("/","-")}\n'
(a.library.parent/'blender_assets.cats.txt').write_text(cattext)
# The review file is deliberately separate: labels and layout are not runtime assets.
s.name='Dundee | 32 Kronenvorlagen'
rows=[(list(range(18,10,-1)),'OBERKIEFER RECHTS  |  gespiegelt'),
      (list(range(21,29)),'OBERKIEFER LINKS  |  Originalformen'),
      (list(range(48,40,-1)),'UNTERKIEFER RECHTS  |  gespiegelt'),
      (list(range(31,39)),'UNTERKIEFER LINKS  |  Originalformen')]
labels=bpy.data.collections.new('Beschriftung');s.collection.children.link(labels)
def text_obj(name,body,position,size,color=(.8,.83,.88,1)):
 data=bpy.data.curves.new(name,'FONT');data.body=body;data.size=size;data.align_x='LEFT'
 ob=bpy.data.objects.new(name,data);labels.objects.link(ob);ob.location=position;ob.color=color
 return ob
for row,(numbers,title) in enumerate(rows):
 y=39-row*26
 text_obj('Zeile '+str(row),title,(-66,y+10,0),1.7)
 for col,fdi in enumerate(numbers):
  ob=bpy.data.objects[str(fdi)];ob.asset_clear();x=-59.5+col*17
  center=sum((Vector(c) for c in ob.bound_box),Vector())/8
  sign=-1 if fdi//10 in (2,4) else 1
  ob.matrix_world=Matrix.Translation((x,y,2))@Matrix.Rotation(math.pi if sign>0 else 0,4,'Z')@Matrix.Rotation(sign*math.radians(42),4,'X')@Matrix.Translation(-center)
  text_obj('FDI_'+str(fdi),str(fdi)+(' *' if fdi in (31,32,41,42) else ''),(x-2,y-9,0),2)
text_obj('Titel','DUNDEE  /  KRONENBIBLIOTHEK',(-66,57,0),3.2)
text_obj('Untertitel','32 FDI-Positionen  /  Wurzeln entfernt  /  Anatomie erhalten',(-66,52.5,0),1.6)
text_obj('Hinweis','* 31/32 und 41/42: Quellenbenennung widerspruechlich; Zuordnung fachlich pruefen.',(-66,-58,0),1.2)
text_obj('Lizenz','University of Dundee, School of Dentistry  /  CC BY 4.0  /  Bearbeitung: ZAP-Wunschlachen',(-66,-61,0),1.1)
text_obj('Gebrauch','Nominale Startgroessen. Rand, Einschubrichtung, Spacer und Materialprofil je Fall festlegen.',(-66,-64,0),1.1)
guide=bpy.data.texts.new('START_HIER.txt')
guide.write('DUNDEE KRONENBIBLIOTHEK\n\nDiese Datei zeigt alle32 vorbereiteten Kronen. Auswahl: FDI-Objekte im Outliner.\nNummern 31/32 sowie Spiegel41/42 folgen den Autor-Titeln; widerspruechliche interne LL1/LL2-Labels bleiben zu pruefen.\n\nProduktivbibliothek: odc_public/Resources/data/odc_tooth_library.blend\nCEJ: offener Halsrand; CervicalBlend: weich auslaufende Anpassungsgewichte; AnatomyProtected: obere Anatomie.\nWeitere Gruppen: Kontakt-/Verbinderflaechen, Hoecker, Fissuren, Inzisalkanten.\nZementspalt und Innenflaeche werden am Patientenfall erstellt.\n\nQuellen: University of Dundee, School of Dentistry. Lizenz CC BY4.0.\nOriginale, Hashes, Detailquellen und Vorbereitungsrezept liegen im Repository unter Resources/dundee und tools.\n')
s.display.shading.color_type='OBJECT'
for ob in objects:ob.color=(.82,.79,.71,1)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.region_3d.view_rotation=Quaternion((1,0,0,0));sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_location=(0,-3,0);sp.region_3d.view_distance=175
   sp.overlay.show_floor=False;sp.overlay.show_axis_x=False;sp.overlay.show_axis_y=False;sp.overlay.show_extras=False;sp.clip_end=5000
   sp.shading.type='SOLID';sp.shading.light='STUDIO';sp.shading.color_type='OBJECT';sp.shading.show_shadows=True;sp.shading.show_cavity=True;sp.shading.cavity_type='BOTH'
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=bpy.data.objects['25']
# Render the same overview for quick review.
camdata=bpy.data.cameras.new('Uebersicht');cam=bpy.data.objects.new('Uebersicht',camdata);s.collection.objects.link(cam)
cam.location=(0,-3,220);cam.rotation_euler=(0,0,0);camdata.type='ORTHO';camdata.ortho_scale=145;s.camera=cam
s.render.resolution_x=1800;s.render.resolution_y=1650;s.render.filepath=str(a.overview.with_suffix('.png'))
bpy.ops.render.render(write_still=True);cam.hide_set(True)
s.render.filepath='//'
bpy.ops.wm.save_as_mainfile(filepath=str(a.overview))
print('PRESENTATION_READY',str(a.overview),flush=True)
