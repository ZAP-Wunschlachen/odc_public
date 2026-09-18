#Python Imports
import math
from math import degrees, radians, pi

#Blender Imports
import bpy
from mathutils import Vector

#Addon Imports
from ..Addon_utils import odcutils

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
    """Calculates silhouette of object which surveys convexities AND concavities from the current view axis"""

    bl_idname = "opendental.blockout_model"
    bl_label = "Blockout Model From View"
    bl_options = {"REGISTER", "UNDO"}
    """
    world = bpy.props.BoolProperty(
        default=True,
        name="Use world coordinate for calculation...almost always should be true.",
    )
    smooth = bpy.props.BoolProperty(
        default=True,
        name="Smooth the outline.  Slightly less acuurate in some situations but more accurate in others.  Default True for best results",
    )
    
    @classmethod
    def poll(cls, context):
        # restoration exists and is in scene
        C0 = context.space_data is not None and context.space_data.type == "VIEW_3D"
        C1 = context.object != None
        if C1:
            C2 = context.object.type == "MESH"
        else:
            C2 = False
        return C0 and C1 and C2
    """
    def execute(self, context):
        
        Modelsprop = bpy.context.scene.UNDERCUTS_props.Modelsprop
        if "Preview" in Modelsprop:
            bmesh_fns.remove_undercuts(context, ob, view, self.world, self.smooth)
        elif "Solid" in Modelsprop:
            bpy.ops.opendental.view_blockout_undercuts_solid()
        return {"FINISHED"}


class OPENDENTAL_OT_blockout_model_solid(bpy.types.Operator): #produces watertight blockout mesh when supplied watertight mesh
    bl_idname = 'opendental.view_blockout_undercuts_solid'
    bl_label = "Blockout Model From Z-axis"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):

        extrude_z = -10
        
        if bpy.context.selected_objects == []:

            message = " Please select the Model to Blockout !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            if context.object.type != "MESH" :

                message = " Please select a valid Model (mesh object) !"
                ShowMessageBox(message=message, icon="COLORSET_02_VEC")

                return {"CANCELLED"}

            else :

                # ...........................Prepare scene settings : ..............................................

                # bpy.ops.view3d.snap_cursor_to_center()
                bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
                bpy.context.scene.tool_settings.transform_pivot_point = "ACTIVE_ELEMENT"
                bpy.context.scene.tool_settings.use_snap = False

                # Get active Object :..........................................................

                ob = bpy.context.view_layer.objects.active

                ###  PATRICKS TEST ###############################
                ##################################################
                if bpy.types.Scene.pre_surveyed == True:
                    world_view = context.scene.UNDERCUTS_view_props.survey_quaternion @ Vector((0,0,1))
                else:
                    world_view = context.space_data.region_3d.view_rotation @ Vector((0,0,1))

                local_view = ob.matrix_world.inverted().to_quaternion() @ world_view
                
                bpy.context.tool_settings.mesh_select_mode = (False, False, True)
                for v in ob.data.vertices:
                    v.select = False
                for ed in ob.data.edges:
                    ed.select = False
                    
                for f in ob.data.polygons:
                    if f.normal.dot(local_view) < -0.000001:
                        f.select = True
                    else:
                        f.select = False
                
                bpy.ops.object.mode_set(mode = 'EDIT')
                
                bpy.context.scene.transform_orientation_slots[0].type = "LOCAL"
                extrude_vec = extrude_z * local_view
                bpy.ops.mesh.extrude_region_move()
                bpy.ops.transform.translate(
                    value=(extrude_vec[0], extrude_vec[1], extrude_vec[2]), constraint_axis=(False, False, False)
                )
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")

                bpy.types.Scene.pre_surveyed = False

                # Rename Model_blocked :
                
                colorprop = context.scene.UNDERCUTS_view_props.colorprop

                if "_solid_base" in ob.name :
                    ob_name = ob.name
                    ob.name = ob_name.replace("_solid_base", "_")

                if f"_survey({colorprop})" in ob.name :
                    ob_name = ob.name
                    ob.name = ob_name.replace(f"_survey({colorprop})", "_")

                ob.name += "blocked"
                ob.data.name = f"{ob.name}_mesh"

        return {'FINISHED'}
        ### END PATRICK"S TEST   #########################
        ###################################################
    
def register():
    bpy.utils.register_class(OPENDENTAL_OT_survey_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.register_class(OPENDENTAL_OT_blockout_model_solid)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model_solid)
    bpy.utils.unregister_class(OPENDENTAL_OT_blockout_model)
    bpy.utils.unregister_class(OPENDENTAL_OT_survey_model)
