"""Recover camera from known point correspondences and reject degenerate inputs."""
import sys, importlib
from pathlib import Path
import bpy, addon_utils, numpy as np
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
points=np.array([(x,y,z) for x in (-2,2) for y in (-2,2) for z in (-1,3)],dtype=float)
pixels=np.array([m.project_by_object_utils(camera,Vector(point)) for point in points])
for count in (6,8):
    P=m.projection_from_correspondences(points[:count],pixels[:count])
    q=(P @ np.column_stack((points,np.ones(len(points)))).T).T
    assert np.max(np.linalg.norm(q[:,:2]/q[:,2,None]-pixels,axis=1))<.001
    restored=m.get_blender_camera_from_3x4_P(P,1)
    for point,pixel in zip(points,pixels):
        actual=m.project_by_object_utils(restored,Vector(point))
        assert np.linalg.norm(np.array(actual)-pixel)<.01,(actual,pixel)
# Numerical conditioning: translated and rescaled coordinates.
large=points*1000+np.array((1e6,-2e6,3e6))
P=m.projection_from_correspondences(large,pixels)
q=(P @ np.column_stack((large,np.ones(len(large)))).T).T
assert np.max(np.linalg.norm(q[:,:2]/q[:,2,None]-pixels,axis=1))<.001
for world,image in [(points[:5],pixels[:5]),(points,pixels[:6]),(np.zeros((8,3)),pixels),
                    (np.column_stack((points[:,:2],np.zeros(8))),pixels),
                    (points,np.full((8,2),np.nan))]:
    try:m.projection_from_correspondences(world,image)
    except ValueError:pass
    else:raise AssertionError('Degenerate correspondences accepted')
print('ODC_IMAGE_CORRESPONDENCES_PASSED')
from types import SimpleNamespace
warnings=[]
state=SimpleNamespace(imgeditor_area=SimpleNamespace(spaces=SimpleNamespace(active=SimpleNamespace(image=SimpleNamespace(size=(800,600))))),points_3d=list(map(Vector,points)),pixel_coords=list(map(Vector,pixels)),
                      report=lambda levels,message:warnings.append(message))
objects_before=set(bpy.data.objects)
result=m.VIEW3D_OT_image_view3d_modal.build_matrix(state)
assert result is not None and result.type=='CAMERA'
assert len(set(bpy.data.objects)-objects_before)==1
state.pixel_coords=state.pixel_coords[:-1]
objects_before=set(bpy.data.objects)
assert m.VIEW3D_OT_image_view3d_modal.build_matrix(state) is None
assert warnings and set(bpy.data.objects)==objects_before
print('ODC_IMAGE_BUILD_MATRIX_PASSED')
