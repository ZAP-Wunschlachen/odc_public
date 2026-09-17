"""Reproduce the shutdown report without importing or enabling ODC."""
import bpy
from pathlib import Path
path = Path(__file__).resolve().parents[1] / 'Resources/data/odc_tooth_library.blend'
with bpy.data.libraries.load(str(path)) as (source, destination):
    destination.objects = ['16']
obj = destination.objects[0]
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.object.mode_set(mode='OBJECT')
print('ASSET_EDITMODE_PROBE_DONE', flush=True)
