"""Configure the original directional contact projection with current modifiers."""
import bpy


def adjust(context, tooth, role, overlap):
    crown = bpy.data.objects.get(tooth.restoration) or bpy.data.objects.get(tooth.contour)
    target = bpy.data.objects.get(getattr(tooth, role))
    if crown is None or target is None or crown == target or crown.type != 'MESH' or target.type != 'MESH':
        return False
    name, axis, negative, offset = {
        'mesial': ('Mesial Contact', 'X', True, overlap),
        'distal': ('Distal Contact', 'X', False, -overlap),
        'opposing': ('Occlusion', 'Z', True, overlap),
    }[role]
    mod = next((m for m in crown.modifiers if m.type == 'SHRINKWRAP' and
                (m.name == name or m.name.startswith(name + '.'))), None)
    if mod is None:
        mod = crown.modifiers.new(name=name, type='SHRINKWRAP')
    mod.wrap_method = 'PROJECT'
    mod.use_negative_direction = negative
    mod.use_positive_direction = not negative
    mod.use_project_x = axis == 'X'
    mod.use_project_y = False
    mod.use_project_z = axis == 'Z'
    mod.offset = offset
    mod.target = target
    mod.vertex_group = ''
    mod.cull_face = 'OFF'
    mod.project_limit = 0
    if role != 'opposing' and target.name in {context.scene.odc_props.master, tooth.prep_model}:
        mod.vertex_group = 'Mesial Connector' if role == 'mesial' else 'Distal Connector'
        mod.cull_face = 'FRONT'
        mod.project_limit = .5
    return True
