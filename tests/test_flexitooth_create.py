import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
u = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
for number in ('11', '16', '25', '36'):
    obj = u.obj_from_lib(u.get_settings().tooth_lib,number)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.opendental.flexitooth() == {'FINISHED'}
    hooks = [m for m in obj.modifiers if m.type == 'HOOK']
    assert len(hooks) > 0
    lap = next(m for m in obj.modifiers if m.type == 'LAPLACIANDEFORM')
    assert lap.is_bind
    assert all(mod.type == 'HOOK' for mod in list(obj.modifiers)[:len(hooks)])
    assert list(obj.modifiers)[len(hooks)] == lap
    bpy.context.view_layer.update()
    def coordinates():
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        points = [v.co.copy() for v in mesh.vertices]
        evaluated.to_mesh_clear()
        return points
    before = coordinates()
    hooks[0].object.location.x += .5
    bpy.context.view_layer.update()
    after = coordinates()
    assert max((a-b).length for a,b in zip(after,before)) > .01
    assert bpy.ops.opendental.flexitooth_keep() == {'FINISHED'}
    bpy.context.view_layer.update()
    kept = coordinates()
    assert max((a-b).length for a,b in zip(after,kept)) < 1e-4, (number, max((a-b).length for a,b in zip(after,kept)))
print('ODC_FLEXITOOTH_CREATE_PASSED',bpy.app.version_string)
