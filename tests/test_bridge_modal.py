import sys
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
m = importlib.import_module(f'{ROOT.name}.Operators.bridge_methods')
bm = bmesh.new()
for x in (-2,2):
    vertices = bmesh.ops.create_cube(bm, size=2)['verts']
    bmesh.ops.translate(bm, verts=vertices, vec=Vector((x,0,0)))
mesh = bpy.data.meshes.new('Connector fixture')
bm.to_mesh(mesh)
bm.free()
obj = bpy.data.objects.new('Connector fixture', mesh)
bpy.context.scene.collection.objects.link(obj)
for name, x in (('A',-1),('B',1)):
    group = obj.vertex_groups.new(name=name)
    group.add([v.index for v in mesh.vertices if abs(v.co.x-x)<1e-6],1,'REPLACE')
obj.vertex_groups.new(name='Connectors')
import os
import traceback
bridge = bpy.context.scene.odc_bridges.add()
bridge.name = '24x25'
bridge.tooth_string = '24:25'
bridge.bridge = obj.name
obj.vertex_groups['A'].name = '24_Distal Connector'
obj.vertex_groups['B'].name = '25_Mesial Connector'
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
u.get_settings().behavior = '0'
original_mesh = obj.data
original_coordinates = [tuple(v.co) for v in obj.data.vertices]
original_mesh_count = len(bpy.data.meshes)
phase = 0
window = area = region = None
def send(kind):
    for value in ('PRESS','RELEASE'):
        window.event_simulate(type=kind,value=value,x=region.x+region.width//2,y=region.y+region.height//2)
def run():
    global phase,window,area,region
    try:
        if phase == 0:
            window = bpy.context.window
            area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=window,area=area,region=region):
                bridge.tooth_string = '24'
                assert bpy.ops.opendental.bridge_individual('INVOKE_DEFAULT') == {'CANCELLED'}
                assert not any(op.bl_idname == 'OPENDENTAL_OT_bridge_individual' for op in window.modal_operators)
                bridge.tooth_string = '24:25'
                assert bpy.ops.opendental.bridge_individual('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('SPACE')
        elif phase == 1:
            assert len(obj.data.vertices) > 16
            send('ESC')
        elif phase == 2:
            assert obj.data == original_mesh
            assert [tuple(v.co) for v in obj.data.vertices] == original_coordinates
            assert len(bpy.data.meshes) == original_mesh_count
            assert not any(op.bl_idname == 'OPENDENTAL_OT_bridge_individual' for op in window.modal_operators)
            with bpy.context.temp_override(window=window,area=area,region=region):
                assert bpy.ops.opendental.bridge_individual('INVOKE_DEFAULT') == {'RUNNING_MODAL'}
            send('SPACE')
        elif phase == 3:
            assert len(obj.data.vertices) > 16
            send('RET')
        elif phase == 4:
            assert len(obj.data.vertices) > 16
            assert len(bpy.data.meshes) == original_mesh_count
            assert not any(op.bl_idname == 'OPENDENTAL_OT_bridge_individual' for op in window.modal_operators)
            print('ODC_BRIDGE_MODAL_PASSED',flush=True)
            bpy.ops.wm.quit_blender()
            return None
        phase += 1
        return .7
    except Exception:
        traceback.print_exc()
        os._exit(1)
bpy.app.timers.register(run,first_interval=2)
