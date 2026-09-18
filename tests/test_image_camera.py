"""Camera projection round-trip checked against Blender's own projection."""
import sys, importlib
from pathlib import Path
import bpy, addon_utils
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
m=importlib.import_module(f'{ROOT.name}.Operators.image_object_registration')
scene=bpy.context.scene
scene.render.resolution_x=800
scene.render.resolution_y=600
scene.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(3,-4,15),rotation=(.1,.2,.3))
camera=bpy.context.object
camera.data.lens=45
camera.data.sensor_fit='HORIZONTAL'
bpy.context.view_layer.update()
P,K,RT=m.get_3x4_P_matrix_from_blender(camera)
points=[Vector(p) for p in [(0,0,0),(1,2,3),(-2,1,1),(2,-1,-2)]]
expected=[]
for point in points:
    q=P @ point.to_4d()
    pixel=Vector((q.x/q.z,q.y/q.z))
    actual=m.project_by_object_utils(camera,point)
    assert (pixel-actual).length<.001,(pixel,actual)
    expected.append(actual)
restored=m.get_blender_camera_from_3x4_P(P,1)
for point,pixel in zip(points,expected):
    actual=m.project_by_object_utils(restored,point)
    assert (pixel-actual).length<.01,(pixel,actual)
assert (restored.matrix_world.translation-camera.matrix_world.translation).length<1e-4
assert scene.camera==restored
print('ODC_IMAGE_CAMERA_PASSED')
for fit in ('HORIZONTAL','VERTICAL','AUTO'):
    for width,height in ((800,600),(600,800)):
        for aspect in ((1,1),(2,1),(1,2)):
            scene.render.resolution_x=width
            scene.render.resolution_y=height
            scene.render.resolution_percentage=75
            scene.render.pixel_aspect_x,scene.render.pixel_aspect_y=aspect
            camera.data.sensor_fit=fit
            camera.data.shift_x=.12
            camera.data.shift_y=-.08
            bpy.context.view_layer.update()
            P,_,_=m.get_3x4_P_matrix_from_blender(camera)
            for point in points:
                q=P @ point.to_4d()
                pixel=Vector((q.x/q.z,q.y/q.z))
                actual=m.project_by_object_utils(camera,point)
                assert (pixel-actual).length<.002,(fit,width,height,aspect,pixel,actual)
print('ODC_IMAGE_CAMERA_SENSOR_FITS_PASSED')
