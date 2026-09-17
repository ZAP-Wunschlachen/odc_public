import sys
from pathlib import Path
import bpy
import addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.curve.primitive_bezier_circle_add(radius=4)
curve = bpy.context.object
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
parent = bpy.data.objects.new('Parent', None)
bpy.context.scene.collection.objects.link(parent)
parent.location = (3,4,5)
parent.rotation_euler = (.2,.3,.4)
obj.parent = parent
constraint = obj.constraints.new('FOLLOW_PATH')
constraint.name = 'Renamed arch path'
constraint.target = curve
constraint.use_fixed_location = True
constraint.offset_factor = .3
constraint.use_curve_follow = True
bpy.context.view_layer.update()
before = obj.matrix_world.copy()
bpy.context.view_layer.objects.active = curve
assert bpy.ops.opendental.arch_plan_keep() == {'FINISHED'}
assert not obj.constraints
assert obj.parent == parent
assert max(abs(obj.matrix_world[i][j]-before[i][j]) for i in range(4) for j in range(4)) < 1e-5
assert bpy.ops.opendental.arch_plan_keep() == {'FINISHED'}
assert max(abs(obj.matrix_world[i][j]-before[i][j]) for i in range(4) for j in range(4)) < 1e-5
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_KEEP_ARCH_PLAN_PASSED', bpy.app.version_string)
