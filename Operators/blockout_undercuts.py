#Python Imports
import math
from math import degrees, radians, pi

#Blender Imports
import bpy
import bmesh
from mathutils import Vector, Quaternion

#Addon Imports
from ..Addon_utils import odcutils
from . import bmesh_fns

#Popup message box function :

def ShowMessageBox(message="", title="INFO", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


color = {
    "No color selected": [1.0, 0.9, 0.8, 1],
    "Green": [0, 1.0, 0.0, 1],
    "Blue": [0.0, 0.02, 0.19, 1],
    "Violet": [0.16, 0.0, 0.19, 1],
    "Pink": [1.0, 0.3, 1.0, 1],
}


class OPENDENTAL_OT_survey_model(bpy.types.Operator):
    """Calculates silhouette of object which surveys convexities AND concavities from the current view axis"""

    bl_idname = "opendental.view_silhouette_survey"
    bl_label = "Survey Model From View"
    bl_options = {"REGISTER", "UNDO"}

    world: bpy.props.BoolProperty(
        default=True,
        name="Use world coordinate for calculation...almost always should be true.",
    )
    smooth: bpy.props.BoolProperty(
        default=True,
        name="Smooth the outline.  Slightly less acuurate in some situations but more accurate in others.  Default True for best results",
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and context.object is not None
                and context.object.type == 'MESH' and context.object.select_get()
                and context.area is not None and context.area.type == 'VIEW_3D'
                and context.region_data is not None)

    def execute(self, context):
        props = context.scene.UNDERCUTS_view_props
        color_name = props.colorprop
        if color_name == 'No color selected':
            self.report({'WARNING'}, 'Choose a survey color first')
            return {'CANCELLED'}
        source = context.object
        original = source.get('odc_survey_source')
        if isinstance(original, bpy.types.Object) and original.name in context.scene.objects:
            source = original
        previous = [obj for obj in context.scene.objects
                    if obj.get('odc_survey_source') == source
                    and obj.get('odc_survey_color') == color_name]
        context.view_layer.update()
        survey = source.copy()
        survey.data = source.data.copy()
        survey.name = source.name + '_survey(' + color_name + ')'
        context.collection.objects.link(survey)
        survey.hide_viewport = False
        survey['odc_survey_source'] = source
        survey['odc_survey_color'] = color_name
        survey.vertex_groups.clear()
        survey.data.materials.clear()
        for name, rgba in (('my_Neutral', (.8,.8,.8,1)),
                           ('survey_materiel(' + color_name + ')', color[color_name])):
            material = bpy.data.materials.get(name)
            if material is None:
                material = bpy.data.materials.new(name)
                material.diffuse_color = rgba
                material.roughness = .4
            survey.data.materials.append(material)
        context.view_layer.update()
        rotation = context.region_data.view_rotation.copy()
        direction = rotation @ Vector((0,0,1))
        local = (survey.matrix_world.inverted().to_3x3() @ direction).normalized()
        vertices = set()
        for face in survey.data.polygons:
            face.material_index = int(face.normal.dot(local) < -1e-6)
            if face.material_index:
                vertices.update(face.vertices)
        group = survey.vertex_groups.new(name='my_survey_vgroup(' + color_name + ')')
        if vertices:
            group.add(list(vertices), 1, 'REPLACE')
        try:
            silhouette = odcutils.silouette_brute_force(context, survey, direction, self.world, self.smooth)
        except Exception:
            mesh = survey.data
            bpy.data.objects.remove(survey, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            raise
        silhouette['odc_survey_owner'] = survey
        for old in previous:
            owned = [obj for obj in context.scene.objects if obj.get('odc_survey_owner') == old]
            for obj in owned + [old]:
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        props.survey_quaternion = rotation
        context.scene.pre_surveyed = True
        for obj in context.selected_objects:
            obj.select_set(False)
        source.hide_set(True)
        survey.hide_set(False)
        silhouette.hide_set(False)
        survey.select_set(True)
        context.view_layer.objects.active = survey
        return {'FINISHED'}

class OPENDENTAL_OT_blockout_model(bpy.types.Operator):
    """Run preview or solid undercut removal using the selected insertion axis."""
    bl_idname = "opendental.blockout_model"
    bl_label = "Blockout Model From View"
    bl_options = {"REGISTER", "UNDO"}

    world: bpy.props.BoolProperty(name="World coordinates", default=True)
    smooth: bpy.props.BoolProperty(name="Smooth boundary", default=True)

    @classmethod
    def poll(cls, context):
        return OPENDENTAL_OT_survey_model.poll(context)

    def execute(self, context):
        if context.scene.UNDERCUTS_props.Modelsprop == 'Solid':
            return bpy.ops.opendental.view_blockout_undercuts_solid()
        rotation = (Quaternion(context.scene.UNDERCUTS_view_props.survey_quaternion)
                    if context.scene.pre_surveyed else context.region_data.view_rotation)
        view = rotation @ Vector((0, 0, 1))
        bmesh_fns.remove_undercuts(context, context.object, view, self.world, self.smooth)
        return {'FINISHED'}


class OPENDENTAL_OT_blockout_model_solid(bpy.types.Operator): #produces watertight blockout mesh when supplied watertight mesh
    bl_idname = 'opendental.view_blockout_undercuts_solid'
    bl_label = "Blockout Model From Z-axis"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        return OPENDENTAL_OT_survey_model.poll(context)

    def execute(self, context):
        ob = context.object
        bm = bmesh.new()
        try:
            bm.from_mesh(ob.data)
            if not bm.faces or any(not edge.is_manifold for edge in bm.edges):
                self.report({'WARNING'}, 'Solid blockout requires a closed mesh')
                return {'CANCELLED'}
        finally:
            bm.free()
        rotation = (Quaternion(context.scene.UNDERCUTS_view_props.survey_quaternion)
                    if context.scene.pre_surveyed else context.region_data.view_rotation)
        direction = rotation @ Vector((0, 0, 1))
        if direction.length_squared < 1e-12 or abs(ob.matrix_world.determinant()) < 1e-12:
            self.report({'WARNING'}, 'Use a valid survey axis and nonzero object scale')
            return {'CANCELLED'}
        direction.normalize()
        local = (ob.matrix_world.inverted().to_3x3() @ direction).normalized()
        faces = [face.index for face in ob.data.polygons if face.normal.dot(local) < -1e-6]
        if not faces:
            self.report({'WARNING'}, 'No backward-facing faces found')
            return {'CANCELLED'}
        original = ob.data
        working = original.copy()
        selected = list(context.selected_objects)
        settings = context.tool_settings
        tool_state = (context.scene.transform_orientation_slots[0].type,
                      settings.transform_pivot_point, settings.use_snap,
                      tuple(settings.mesh_select_mode))
        ob.data = working
        try:
            bpy.ops.object.select_all(action='DESELECT')
            ob.select_set(True)
            settings.use_snap = False
            settings.mesh_select_mode = (False, False, True)
            for vertex in working.vertices:
                vertex.select = False
            for edge in working.edges:
                edge.select = False
            chosen = set(faces)
            for face in working.polygons:
                face.select = face.index in chosen
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={
                'value': tuple(-10 * direction), 'orient_type': 'GLOBAL'})
            bpy.ops.object.mode_set(mode='OBJECT')
            if bpy.ops.opendental.remesh_model('EXEC_DEFAULT') != {'FINISHED'}:
                raise RuntimeError('Remeshing was cancelled')
            bm = bmesh.new()
            try:
                bm.from_mesh(ob.data)
                if not bm.faces or any(not edge.is_manifold for edge in bm.edges):
                    raise ValueError('Remeshing did not produce a closed blockout')
            finally:
                bm.free()
        except Exception as error:
            if ob.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            failed = ob.data
            ob.data = original
            for mesh in {failed, working}:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            bpy.ops.object.select_all(action='DESELECT')
            for item in selected:
                item.select_set(True)
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        finally:
            context.scene.transform_orientation_slots[0].type = tool_state[0]
            settings.transform_pivot_point = tool_state[1]
            settings.use_snap = tool_state[2]
            settings.mesh_select_mode = tool_state[3]
        if original.users == 0:
            bpy.data.meshes.remove(original)
        if working != ob.data and working.users == 0:
            bpy.data.meshes.remove(working)
        # A finished blockout is no longer a replaceable survey preview.
        owned = [item for item in context.scene.objects if item.get('odc_survey_owner') == ob]
        for item in owned:
            mesh = item.data
            bpy.data.objects.remove(item, do_unlink=True)
            if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for key in ('odc_survey_source', 'odc_survey_color'):
            if key in ob:
                del ob[key]
        ob.name += '_blocked'
        ob.data.name = ob.name + '_mesh'
        context.scene.pre_surveyed = False
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OPENDENTAL_OT_survey_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model_solid)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model_solid)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_survey_model)
