"""World-space placement shared by the interactive insertion-axis tool."""
import bpy
from mathutils import Matrix, Vector


def place_axis(context, tooth, origin, direction, rotation, view_center):
    direction = direction.normalized()
    hit, location, *_ = context.scene.ray_cast(
        context.evaluated_depsgraph_get(), origin, direction)
    if not hit:
        normal = rotation @ Vector((0, 0, 1))
        denominator = direction.dot(normal)
        if abs(denominator) < 1e-8:
            location = view_center.copy()
        else:
            location = origin + direction * ((view_center - origin).dot(normal) / denominator)
    axis = context.scene.objects.get(tooth.axis) if tooth.axis else None
    if axis is None:
        axis = bpy.data.objects.new(tooth.name + '_Axis', None)
        context.scene.collection.objects.link(axis)
        tooth.axis = axis.name
        axis.parent = context.scene.objects.get(context.scene.odc_props.master)
    axis.empty_display_type = 'SINGLE_ARROW'
    axis.empty_display_size = 10
    axis.rotation_mode = 'QUATERNION'
    # Reset parent inverse to cancel all parent transforms, including nonuniform
    # scale, at placement time. Subsequent master movement still moves the axis.
    axis.matrix_parent_inverse = axis.parent.matrix_world.inverted() if axis.parent else Matrix.Identity(4)
    axis.matrix_basis = Matrix.LocRotScale(location, rotation, Vector((1, 1, 1)))
    return axis, hit
