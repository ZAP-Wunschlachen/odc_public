"""Verify real scene ray casting and axis world transforms under a scaled parent."""
import sys
import importlib
from pathlib import Path
import bpy
import addon_utils
from mathutils import Vector, Euler
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
place = importlib.import_module(f'{ROOT.name}.Operators.insertion_axis').place_axis
scene = bpy.context.scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_plane_add(size=20)
plane = bpy.context.object
master = bpy.data.objects.new('master_transform', None)
scene.collection.objects.link(master)
master.location = (3, 4, 5)
master.rotation_euler = (.2, .3, .4)
master.scale = (2, 3, 4)
scene.odc_props.master = master.name
tooth = scene.odc_teeth.add()
tooth.name = '25'
bpy.context.view_layer.update()
rotation = Euler((.1, .2, .3)).to_quaternion()
axis, hit = place(bpy.context, tooth, Vector((1, 2, 10)), Vector((0, 0, -1)), rotation, Vector((0, 0, 0)))
bpy.context.view_layer.update()
assert hit and axis.parent == master
assert (axis.matrix_world.translation - Vector((1, 2, 0))).length < 1e-5
assert axis.matrix_world.to_quaternion().rotation_difference(rotation).angle < 1e-5
assert (axis.matrix_world.to_scale() - Vector((1, 1, 1))).length < 1e-5
before = axis.matrix_world.translation.copy()
master.location.x += 2
bpy.context.view_layer.update()
assert (axis.matrix_world.translation - before - Vector((2, 0, 0))).length < 1e-5
# Misses use the view plane and reuse the same axis.
origin = Vector((100, 100, 10))
direction = Vector((.1, .2, -1)).normalized()
center = Vector((0, 0, 3))
reused, hit = place(bpy.context, tooth, origin, direction, rotation, center)
bpy.context.view_layer.update()
assert reused == axis and not hit
normal = rotation @ Vector((0, 0, 1))
assert abs((axis.matrix_world.translation - center).dot(normal)) < 1e-4
assert (axis.matrix_world.translation - origin).cross(direction).length < 1e-4
# Cancellation restores existing transforms/display and removes only created axes.
Session = importlib.import_module(f'{ROOT.name}.Operators.insertion_axis').AxisSession
session = Session(scene)
old_basis = axis.matrix_basis.copy()
old_inverse = axis.matrix_parent_inverse.copy()
axis.empty_display_type = 'CUBE'
axis.empty_display_size = 2
session.remember(tooth)
place(bpy.context, tooth, Vector((0, 0, 10)), Vector((0, 0, -1)), rotation, center)
new_tooth = scene.odc_teeth.add()
new_tooth.name = '26'
session.remember(new_tooth)
created, _ = place(bpy.context, new_tooth, Vector((0, 0, 10)), Vector((0, 0, -1)), rotation, center)
created_name = created.name
session.record_created(created)
unrelated = bpy.data.objects.new('unrelated_session_object', None)
scene.collection.objects.link(unrelated)
session.cancel()
assert created_name not in bpy.data.objects and new_tooth.axis == ''
assert tooth.axis == axis.name and axis.empty_display_type == 'CUBE'
assert axis.empty_display_size == 2
assert all(abs(axis.matrix_basis[r][c] - old_basis[r][c]) < 1e-6 for r in range(4) for c in range(4))
assert axis.matrix_parent_inverse == old_inverse
assert unrelated.name in bpy.data.objects
session.cancel()  # Cleanup is idempotent.
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_INSERTION_AXIS_PASSED', bpy.app.version_string)
