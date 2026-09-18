#Python imports :
import math
from math import degrees, radians, pi
import time

#Blender Imports :
import bpy
import bmesh
from mathutils import Vector, Euler

#Addon Imports :

#Global variables : 

yellow_stone = [1.0, 0.36, 0.06, 1.0]

#Popup message box function :

def ShowMessageBox(message="", title="INFO", icon="INFO"):
    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


#######################################################################################
########################### Model Operations : Operators ##############################

#######################################################################################
#Join models operator :

class OPENDENTAL_OT_join_models(bpy.types.Operator):
    " Join Models "

    bl_idname = "opendental.join_models"
    bl_label = "Join Models :"

    def execute(self, context):

        if len(bpy.context.selected_objects) < 2:
            
            message = " Please select at least 2 objects to join !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
           
           bpy.ops.object.join()

           return {"FINISHED"}

#######################################################################################
# Separate models operator :

class OPENDENTAL_OT_separate_models(bpy.types.Operator):
    " Separate Models "

    bl_idname = "opendental.separate_models"
    bl_label = "Separate Models :"

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select the Model to separate!"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            
            bpy.ops.object.mode_set(mode="OBJECT")
            Model = bpy.context.view_layer.objects.active
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.separate(type='LOOSE')
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model


            return {"FINISHED"}

#######################################################################################
#Parent model operator :

class OPENDENTAL_OT_parent_models(bpy.types.Operator):
    " Parent Models "

    bl_idname = "opendental.parent_models"
    bl_label = "Link"

    def execute(self, context):

        parent = context.view_layer.objects.active
        selected_objects = context.selected_objects
        childs = selected_objects[1:]

        if len(selected_objects) < 2 or not parent in selected_objects :
            
            message = " Please select at least 2 objects to Link !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
           bpy.ops.object.mode_set(mode="OBJECT")
           bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
           bpy.ops.object.select_all(action='DESELECT')
           parent.select_set(True)
           #bpy.ops.object.hide_view_set(unselected=True)
           
           return {"FINISHED"}

#######################################################################################
#Unparent model operator :

class OPENDENTAL_OT_unparent_models(bpy.types.Operator):
    " Parent Models "

    bl_idname = "opendental.unparent_models"
    bl_label = "UnLink"

    def execute(self, context):

        parent = context.view_layer.objects.active
        selected_objects = context.selected_objects

        if not selected_objects :
            
            message = " Please select Model to UnLink !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
           bpy.ops.object.mode_set(mode="OBJECT")
           bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
           bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

           return {"FINISHED"}

#######################################################################################
#Align model to front operator :

class OPENDENTAL_OT_align_to_front(bpy.types.Operator):
    """Align Model To Front view"""

    bl_idname = "opendental.align_to_front"
    bl_label = "Align to Front"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and context.object is not None
                and context.object.select_get() and context.area is not None
                and context.area.type == 'VIEW_3D' and context.region_data is not None)

    def execute(self, context):

        if not bpy.context.selected_objects :
            
            message = " Please select Model to UnLink !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            Model = bpy.context.view_layer.objects.active

            # Get VIEW_rotation matrix  :

            view3d_rot_matrix = context.space_data.region_3d.view_rotation.to_matrix().to_4x4()

            # create a 90 degrees arround X_axis Euler :
            Eul_90x = Euler((radians(90), 0, 0), 'XYZ')

            # Euler to mattrix 4x4 :
            Eul_90x_matrix = Eul_90x.to_matrix().to_4x4()

            # Rotate Model :
            Model.matrix_world = Eul_90x_matrix @ view3d_rot_matrix.inverted() @ Model.matrix_world
            bpy.ops.view3d.view_all(center=True)
            bpy.ops.view3d.view_axis(type="FRONT")
            bpy.ops.wm.tool_set_by_id(name="builtin.cursor")

        return {"FINISHED"}

#######################################################################################
#Center model modal operator :

class OPENDENTAL_OT_center_Model(bpy.types.Operator):
    " Center Model to world origin "

    bl_idname = "opendental.center_model"
    bl_label = "Center Model :"

    yellow_stone = [1.0, 0.36, 0.06, 1.0]

    def modal(self, context, event):

        if not event.type in {"RET", "ESC"} :
            # allow navigation
            
            return {"PASS_THROUGH"}

        elif event.type == "RET":

            if event.value == ("PRESS"):

                if context.scene.cursor.location == (0, 0, 0) :

                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                
                else :

                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                    bpy.ops.view3d.snap_cursor_to_center()
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            bpy.ops.view3d.view_all(center=True)
            #bpy.ops.wm.tool_set_by_id(name="builtin.cursor")
            bpy.ops.wm.tool_set_by_id(name="builtin.select")

            return {"FINISHED"}

        elif event.type == ("ESC"):

            if event.value == ("PRESS"):

                bpy.ops.wm.tool_set_by_id(name="builtin.select")
            
                return {"CANCELLED"}


        return {"RUNNING_MODAL"}

    def invoke(self, context, event):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            if context.space_data.type == "VIEW_3D":

                bpy.ops.ed.undo_push()

                bpy.ops.object.mode_set(mode="OBJECT")
                Model = bpy.context.view_layer.objects.active
                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)

                bpy.ops.wm.tool_set_by_id(name="builtin.cursor")

                message = " Please move cursor to incisal Midline or to center of scene and click 'ENTER'!"
                ShowMessageBox(message=message, icon="COLORSET_02_VEC")

                context.window_manager.modal_handler_add(self)

                return {"RUNNING_MODAL"}

            else:

                self.report({"WARNING"}, "Active space must be a View3d")

                return {"CANCELLED"}

#######################################################################################
#Cursor to world origin operator :

class OPENDENTAL_OT_center_cursor(bpy.types.Operator):
    """Cursor to World Origin """

    bl_idname = "opendental.center_cursor"
    bl_label = "Center Cursor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context) :

        context.scene.cursor.location = (0.0, 0.0, 0.0)

        return {"FINISHED"}

#######################################################################################
#Decimate model operator :

class OPENDENTAL_OT_decimate_model(bpy.types.Operator):
    """ Decimate Model to ratio """  # TODO ratio poperty

    bl_idname = "opendental.decimate_model"
    bl_label = "Decimate Model"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        decimate_ratio = round(bpy.context.scene.ODC_modops_props.decimate_ratio, 2)

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            
            ###............... Decimate Model ....................###

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.modifier_add(type="DECIMATE")
            bpy.context.object.modifiers["Decimate"].ratio = decimate_ratio
            bpy.ops.object.modifier_apply(modifier="Decimate")

            return {"FINISHED"}


#######################################################################################
#Fill holes operator :

class OPENDENTAL_OT_fill(bpy.types.Operator):
    """fill edge or face """

    bl_idname = "opendental.fill"
    bl_label = "Fill Holes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            
            ####### Get model to clean ####### 
            bpy.ops.object.mode_set(mode="OBJECT")
            Model = bpy.context.view_layer.objects.active
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.edge_face_add()
            

            return {"FINISHED"}

#######################################################################################
#Retopo smooth operator :

class OPENDENTAL_OT_retopo_smooth(bpy.types.Operator):
    """Retopo sculpt for filled holes"""

    bl_idname = "opendental.retopo_smooth"
    bl_label = "Retopo Smooth"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode in {'OBJECT', 'SCULPT', 'EDIT_MESH'}
                and context.area is not None and context.area.type == 'VIEW_3D')

    def execute(self, context):
        model = context.object
        if any(mod.type == 'MULTIRES' for mod in model.modifiers):
            self.report({'WARNING'}, 'Dynamic topology cannot be used with a Multires modifier')
            return {'CANCELLED'}
        if context.mode != 'SCULPT':
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='SCULPT')
        if not model.use_dynamic_topology_sculpting:
            bpy.ops.sculpt.dynamic_topology_toggle()
        bpy.ops.brush.asset_activate(
            asset_library_type='ESSENTIALS',
            relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Density')
        sculpt = context.tool_settings.sculpt
        sculpt.use_symmetry_x = False
        sculpt.unified_paint_settings.use_unified_size = True
        sculpt.unified_paint_settings.size = 50
        brush = sculpt.brush
        brush.cursor_color_add = (0.3, 0.0, 0.7, 0.4)
        brush.strength = 0.5
        brush.auto_smooth_factor = 0.5
        brush.use_automasking_topology = True
        brush.use_frontface = True
        sculpt.detail_type_method = 'CONSTANT'
        sculpt.constant_detail_resolution = 16
        return {'FINISHED'}

#######################################################################################
#clean model operator :

class OPENDENTAL_OT_clean_model(bpy.types.Operator):
    """ Fill small and medium holes and remove small parts"""

    bl_idname = "opendental.clean_model"
    bl_label = "Clean Model"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode in {'OBJECT', 'EDIT_MESH'})

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            start = time.perf_counter()
            Fill_treshold = 400
            
            ####### Get model to clean ####### 
            bpy.ops.object.mode_set(mode="OBJECT")
            Model = bpy.context.view_layer.objects.active
            if Model.data.users > 1:
                Model.data = Model.data.copy()
            Model_name = Model.name
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            
            t1 = time.perf_counter()
            print(f"step 1 Done in {t1-start}")

            ####### Fill Holes #######
            
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.fill_holes(sides=Fill_treshold)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            

            ############ clean non_manifold borders ##############
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type='FACE')
            
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.select_less()
            bpy.ops.mesh.delete(type="VERT")
            
            t2 = time.perf_counter()
            print(f"step 2 Done in {t2-t1}")

            ####### Remove loose geometry #######
            
            # Keep the largest connected surface without separating/deleting objects.
            bpy.ops.object.mode_set(mode='OBJECT')
            bm = bmesh.new()
            try:
                bm.from_mesh(Model.data)
                remaining = set(bm.verts)
                components = []
                while remaining:
                    pending = [remaining.pop()]
                    component = set(pending)
                    while pending:
                        vertex = pending.pop()
                        for edge in vertex.link_edges:
                            neighbor = edge.other_vert(vertex)
                            if neighbor in remaining:
                                remaining.remove(neighbor)
                                component.add(neighbor)
                                pending.append(neighbor)
                    components.append(component)
                def size(component):
                    spans = [max(v.co[i] for v in component) - min(v.co[i] for v in component) for i in range(3)]
                    faces = {face for vertex in component for face in vertex.link_faces}
                    return (math.prod(spans), sum(face.calc_area() for face in faces), len(component))
                if components:
                    principal = max(components, key=size)
                    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in principal], context='VERTS')
                bm.to_mesh(Model.data)
            finally:
                bm.free()
            context.view_layer.objects.active = Model
            Model.select_set(True)

            t3 = time.perf_counter()
            print(f"step 3 Done in {t3-t2}")

            ####### Fill Holes #######

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.fill_holes(sides=Fill_treshold)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

            t4 = time.perf_counter()
            print(f"step 4 Done in {t4-t3}")

            ####### Relax borders #######
            
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            from .mesh_loop_tools import relax_selected
            relax_selected(Model.data, iterations=3)

            t5 = time.perf_counter()
            print(f"step 5 Done in {t5-t4}")


            ####### Make mesh consistent (face normals) #######
            
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bm = bmesh.from_edit_mesh(Model.data)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bmesh.update_edit_mesh(Model.data)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="OBJECT")

            t6 = time.perf_counter()
            print(f"step 6 Done in {t6-t5}")

            finish = time.perf_counter()
            print(f"Clean Model Done in {finish-start}")
            
            return {"FINISHED"}


#######################################################################################
############################ OPENDENTAL Cutting Tools operators #######################


################################# Curve cutting tool ##################################

#Curve cutting tool functions :

#######################################################################################
#Add curve function :

def add_curve():

    # Prepare scene settings :
    bpy.ops.transform.select_orientation(orientation="GLOBAL")
    bpy.context.scene.tool_settings.use_snap = True
    bpy.context.scene.tool_settings.snap_elements = {"FACE"}
    bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
    
    # Get Model :
    bpy.ops.object.mode_set(mode="OBJECT")
    Model = bpy.context.view_layer.objects.active
    bpy.ops.object.select_all(action="DESELECT")
    Model.select_set(True)

    # Hide everything but model :
    bpy.ops.object.hide_view_set(unselected=True)

    # Deselect all vertices :
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")

    # ....Add Curve ....... :
    bpy.ops.curve.primitive_bezier_curve_add(
        radius=1, enter_editmode=False, align="CURSOR"
    )  

    # Set cutting_tool name :

    cutting_tool = bpy.context.view_layer.objects.active
    cutting_tool.name = "Cutting_curve"
    bpy.context.scene['odc_cutting_curve'] = cutting_tool
    curve = cutting_tool.data
    curve.name = "Cutting_curve"

    # Prepare curve and Set curve settings :
    bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.curve.select_all(action="DESELECT")
    curve.splines[0].bezier_points[0].select_control_point = True
    bpy.ops.curve.dissolve_verts()
    bpy.ops.curve.select_all(action="SELECT")
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

    bpy.context.object.data.dimensions = "3D"
    bpy.context.object.data.twist_smooth = 3
    bpy.ops.curve.handle_type_set(type="AUTOMATIC")
    bpy.context.object.data.bevel_depth = 0.3
    bpy.context.object.data.extrude = 0
    bpy.context.object.data.bevel_resolution = 10
    bpy.context.scene.tool_settings.curve_paint_settings.error_threshold = 1
    bpy.context.scene.tool_settings.curve_paint_settings.corner_angle = 1.5708
    bpy.context.scene.tool_settings.curve_paint_settings.depth_mode = "SURFACE"
    bpy.context.scene.tool_settings.curve_paint_settings.surface_offset = 0
    bpy.context.scene.tool_settings.curve_paint_settings.use_offset_absolute = True

    # Add color material :
    mat = bpy.data.materials.new("Blue_Metalica")
    mat.diffuse_color = [0.0, 0.0, 1.0, 0.9]
    mat.metallic = 0.7
    mat.roughness = 0.1

    curve.materials.append(mat)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.tool_set_by_id(name="builtin.cursor")
    bpy.context.space_data.overlay.show_outline_selected = False

    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].target = Model
    bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
    bpy.context.object.modifiers["Shrinkwrap"].use_apply_on_spline = True

#######################################################################################
#Delete last point function :

def get_cutting_curve():
    curve = bpy.context.scene.get('odc_cutting_curve')
    if curve is None or curve.name not in bpy.context.scene.objects:
        raise RuntimeError('Create a cutting curve first')
    return curve


def delete_last_point():

    cutting_tool = get_cutting_curve()
    curve = cutting_tool.data
    if not curve.splines or len(curve.splines[0].bezier_points) <= 1:
        return
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.dissolve_verts()
    curve.splines[0].bezier_points[0].select_control_point = True
    bpy.ops.object.mode_set(mode="OBJECT")

#######################################################################################
#Extrude to cursor function :
def extrude_to_cursor(context, event):
        
    cutting_tool = get_cutting_curve()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.curve.extrude(mode="INIT")
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
    bpy.ops.object.mode_set(mode="OBJECT")

#######################################################################################
#1st separate method function :

def first_separate_method() :

    Model_name = bpy.context.scene.ODC_modops_props.cutting_target
    Model = bpy.data.objects[Model_name]

    # Select intesecting vgroup + more :
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action="DESELECT")
    intersect_vgroup = Model.vertex_groups['intersect_vgroup']
    Model.vertex_groups.active_index = intersect_vgroup.index
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_split()

    # Separate by loose parts :

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

#######################################################################################
#2nd separate method function :

def Second_separate_method() :

    bpy.ops.object.mode_set(mode="OBJECT")
    selected_initial = list(bpy.context.selected_objects)
    bpy.ops.object.select_all(action="DESELECT")

    for obj in selected_initial :

        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Select intesecting vgroup + more :
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action="DESELECT")
        intersect_vgroup = obj.vertex_groups['intersect_vgroup']
        obj.vertex_groups.active_index = intersect_vgroup.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more()

        # Get selected unselected verts :
        
        mesh = obj.data
        polys = mesh.polygons
        bpy.ops.object.mode_set(mode="OBJECT")

        deselected_faces = [f.index for f in polys if f.select == False]

        selected_faces  = [f.index for f in polys if f.select == True]

        # Hide intesecting vgroup :
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.hide(unselected=False)
        
        # select a part :
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.object.mode_set(mode="OBJECT")
        polys[deselected_faces[0]].select = True
        bpy.ops.object.mode_set(mode = 'EDIT')

        bpy.ops.mesh.select_linked(delimit=set())
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.mesh.reveal()
        
        # ....Separate by selection.... :
        bpy.ops.mesh.separate(type="SELECTED")
        bpy.ops.object.mode_set(mode="OBJECT")

    resulting_parts = filter_loose_parts()# all visible objects are selected after func

    if resulting_parts == len(selected_initial) :
        return False
    else :
        return True

#######################################################################################
#Filter loose parts function :

def filter_loose_parts() :

    bpy.ops.object.mode_set(mode="OBJECT")
    selected_parts = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    surviving_parts = []
    bpy.ops.object.select_all(action="DESELECT")

    for obj in selected_parts :

        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        if obj.data.vertices :
            
            verts = obj.data.vertices
            
            bpy.ops.object.mode_set( mode="EDIT")

            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()
            
            bpy.ops.object.mode_set(mode="OBJECT")
            non_manifold_verts = [v for v in verts if v.select == True]
            
            if len(verts) < len(non_manifold_verts) * 2 :
                bpy.ops.object.delete(use_global=False, confirm=False)
            else :
                surviving_parts.append(obj)
                obj.select_set(False) 
            
        else :
            bpy.ops.object.delete(use_global=False, confirm=False)

    
    for obj in surviving_parts:
        obj.select_set(True)
    resulting_parts = len(surviving_parts)

    return resulting_parts


#######################################################################################
 #Curve cutting tool classes :
#######################################################################################

####################################################################################### 
#Make curve modal operator :
    
class OPENDENTAL_OT_make_curve(bpy.types.Operator):
    """start curve cutting tool"""

    bl_idname = "opendental.make_curve"
    bl_label = "Make Curve"
    bl_options = {"REGISTER", "UNDO"}

    def modal(self, context, event):

        if event.type in {
            "MIDDLEMOUSE",
            "WHEELUPMOUSE",
            "WHEELDOWNMOUSE",
            "TAB",
        }:
            # allow navigation
            
            return {"PASS_THROUGH"}

        elif event.type == ("DEL"):
            if event.value == ("PRESS"):

                delete_last_point()
            
            return {"RUNNING_MODAL"}

        elif event.type == ("LEFTMOUSE"):

            if event.value == ("PRESS"):

                return {"PASS_THROUGH"}
            
            if event.value == ("RELEASE"):
                
                extrude_to_cursor(context, event)

        elif event.type == "RET":

            if event.value == ("PRESS"):

                cutting_tool = get_cutting_curve()
                if not cutting_tool.data.splines or len(cutting_tool.data.splines[0].bezier_points) < 3:
                    self.report({'WARNING'}, 'Place at least three curve points before confirming')
                    return {'RUNNING_MODAL'}
                bpy.ops.object.mode_set(mode="OBJECT")

                bpy.ops.object.select_all(action="DESELECT")
                cutting_tool.select_set(True)
                bpy.context.view_layer.objects.active = cutting_tool
                bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

                
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.curve.cyclic_toggle()
                
                bpy.context.object.data.bevel_depth = 0
                bpy.context.object.data.extrude = 2
                bpy.context.object.data.offset = -0.5

                bpy.ops.wm.tool_set_by_id(name="builtin.select")
                

                bpy.context.space_data.overlay.show_outline_selected = True
                
                return {"FINISHED"}
        
        elif event.type == ("RIGHTMOUSE"):
            
            return {"PASS_THROUGH"}
        
        
        elif event.type == ("ESC"):

            if event.value == ("PRESS"):

                cutting_tool = get_cutting_curve()
                bpy.ops.object.mode_set(mode="OBJECT")

                bpy.ops.object.select_all(action="DESELECT")
                cutting_tool.select_set(True)
                bpy.context.view_layer.objects.active = cutting_tool
                curve_data = cutting_tool.data
                del context.scene['odc_cutting_curve']
                bpy.data.objects.remove(cutting_tool, do_unlink=True)
                if curve_data.users == 0:
                    bpy.data.curves.remove(curve_data)

                Model_name = context.scene.ODC_modops_props.cutting_target
                Model = bpy.data.objects[Model_name]

                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                bpy.context.view_layer.objects.active = Model

                bpy.ops.wm.tool_set_by_id(name="builtin.select")
                bpy.context.space_data.overlay.show_outline_selected = True
            
                return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            if context.space_data.type == "VIEW_3D":

                # Assign Model name to cutting_target property :
                Model = bpy.context.view_layer.objects.active
                context.scene.ODC_modops_props.cutting_target = Model.name
                
                add_curve()

                context.window_manager.modal_handler_add(self)

                return {"RUNNING_MODAL"}

            else:

                self.report({"WARNING"}, "Active space must be a View3d")

                return {"CANCELLED"}

####################################################################################### 
#Curve cut operator :

class OPENDENTAL_OT_curve_cut(bpy.types.Operator):
    " Cut model and separate parts"

    bl_idname = "opendental.curve_cut"
    bl_label = "Cut Model"

    def execute(self, context):
            
        Model_name = context.scene.ODC_modops_props.cutting_target
        Model = bpy.data.objects[Model_name]
        cutting_tool = get_cutting_curve()
        import uuid
        Model['odc_curve_cut_session'] = uuid.uuid4().hex
        Model['odc_curve_cut_original_name'] = Model.name

        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.context.scene.tool_settings.use_snap = False
        bpy.ops.view3d.snap_cursor_to_center()


        # Get cutting_tool:

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        cutting_tool.select_set(True)
        bpy.context.view_layer.objects.active = cutting_tool

        # Change bevel_depht to 0 to have flate curve :
        bpy.context.object.data.bevel_depth = 0
        

        # convert curve (cutting_tool )to mesh :

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.convert(target="MESH")
        
        # Make vertex group :
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        #bpy.ops.mesh.subdivide(number_cuts=1)
        
        curve_vgroup = cutting_tool.vertex_groups.new(name="curve_vgroup")
        bpy.ops.object.vertex_group_assign()

        bpy.ops.object.mode_set(mode="OBJECT")
                    
        # Get model_trim :

        bpy.ops.object.select_all(action="DESELECT")
        Model.select_set(True)
        bpy.context.view_layer.objects.active = Model

        # deselect all vertices :

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bm = bmesh.from_edit_mesh(Model.data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bmesh.update_edit_mesh(Model.data)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        # delete old vertex groups :
        Model.vertex_groups.clear()

        # Join curve to Model :
        if 'odc_cutting_curve' in context.scene:
            del context.scene['odc_cutting_curve']
        cutting_tool.select_set(True)
        bpy.ops.object.join()

        # intersect make vertex group :

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.intersect()
        
        intersect_vgroup = Model.vertex_groups.new(name="intersect_vgroup")
        bpy.ops.object.vertex_group_assign()

        Model.select_set(False)

        if bpy.context.selected_objects :
            bpy.ops.object.hide_view_set(unselected=False)
            
        Model.select_set(True)
        
        # delete curve_vgroup :
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action="DESELECT")
        curve_vgroup = Model.vertex_groups['curve_vgroup']
        
        
        Model.vertex_groups.active_index = curve_vgroup.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.delete(type='FACE')

        # 1st methode :
        first_separate_method() 
        
        # Filtring loose parts :
        resulting_parts = filter_loose_parts()

        if resulting_parts > 1 :

            print("Cutting done with first method")

        else :

            # Select Model :
            Model = bpy.data.objects[Model_name]
            bpy.context.view_layer.objects.active = Model 
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)

            bol = True

            while bol :
                bol = Second_separate_method()

            # Filtring loose parts :
            resulting_parts = filter_loose_parts()
            print("Cutting done with second method")

        
        # Remove Blue material :

        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            if obj.active_material and 'Blue_Metalica' in obj.active_material.name:
                bpy.ops.object.material_slot_remove()

        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.wm.tool_set_by_id(name="builtin.select")
            
        return {"FINISHED"}

####################################################################################### 
#Trim model operator :

class OPENDENTAL_OT_trim_model(bpy.types.Operator):
    """Keep selected curve-cut pieces and remove only their unselected siblings."""
    bl_idname = 'opendental.trim_model'
    bl_label = 'Trim Model'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.object is not None

    def execute(self, context):
        model = context.object
        session = model.get('odc_curve_cut_session')
        if not session or not model.select_get():
            self.report({'WARNING'}, 'Select a part from a curve-cut operation')
            return {'CANCELLED'}
        parts = [obj for obj in context.scene.objects if obj.get('odc_curve_cut_session') == session]
        keep = [obj for obj in parts if obj.select_get()]
        original_name = model.get('odc_curve_cut_original_name', model.name)
        for obj in parts:
            if obj not in keep:
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        model.name = original_name
        model.data.name = original_name + '_mesh'
        context.scene.ODC_modops_props.cutting_target = model.name
        for obj in keep:
            del obj['odc_curve_cut_session']
            if 'odc_curve_cut_original_name' in obj:
                del obj['odc_curve_cut_original_name']
            for vertex in obj.data.vertices:
                vertex.select = False
            for edge in obj.data.edges:
                edge.select = False
            for face in obj.data.polygons:
                face.select = False
        context.view_layer.objects.active = model
        return {'FINISHED'}

#######################################################################################

############################### Square cutting tool ####################################

#Square cutting tool functions :

#######################################################################################
#Add square cutter function :
def add_square_cutter(context) :

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

    Model = bpy.context.view_layer.objects.active
    loc = Model.location.copy()# get model location
    view_rotation = context.space_data.region_3d.view_rotation

    view3d_rot_matrix = view_rotation.to_matrix().to_4x4()# get v3d rotation matrix 4x4

    # Add cube :
    bpy.ops.mesh.primitive_cube_add(size=120, enter_editmode=False )

    frame = bpy.context.view_layer.objects.active
    frame.name = "my_frame_cutter"
    frame['odc_square_target'] = Model


    # Reshape and align cube :

    frame.matrix_world = view3d_rot_matrix 

    frame.location = loc

    bpy.context.object.display_type = 'WIRE'
    bpy.context.object.scale[1] = 0.5
    bpy.context.object.scale[2] = 2

    # Subdivide cube 10 iterations 3 times :

    bpy.ops.object.select_all(action="DESELECT")
    frame.select_set(True)
    bpy.context.view_layer.objects.active = frame

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.mesh.subdivide(number_cuts=6)

    # Make cube normals consistent :

    bm = bmesh.from_edit_mesh(frame.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.update_edit_mesh(frame.data)
    bpy.ops.mesh.select_all(action="DESELECT")
    
    bpy.ops.object.mode_set(mode="OBJECT")
    
    # Select frame :

    bpy.ops.object.select_all(action="DESELECT")
    frame.select_set(True)
    bpy.context.view_layer.objects.active = frame


#######################################################################################

#Square cutting tool operators :

#######################################################################################
#Square cut modal operator :

class OPENDENTAL_OT_square_cut(bpy.types.Operator):
    """Align the view, then create a cutter for the active model."""
    bl_idname = 'opendental.square_cut'
    bl_label = 'Square Cut'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and context.object is not None
                and context.object.type == 'MESH' and context.area is not None
                and context.area.type == 'VIEW_3D' and context.region_data is not None)

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            return {'CANCELLED'}
        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            model = context.scene.objects.get(self.target_name)
            if model is None:
                self.report({'WARNING'}, 'The cutting target no longer exists')
                return {'CANCELLED'}
            for obj in context.selected_objects:
                obj.select_set(False)
            model.hide_set(False)
            model.select_set(True)
            context.view_layer.objects.active = model
            context.scene.ODC_modops_props.cutting_target = model.name
            bpy.ops.object.hide_view_set(unselected=True)
            context.tool_settings.use_snap = False
            add_square_cutter(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        self.target_name = context.object.name
        ShowMessageBox(message="Align the cutting view, then press Enter. Escape cancels.", icon='COLORSET_02_VEC')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

#######################################################################################
#Square cut confirm operator :

def square_cut_pair(context):
    frame = context.object
    if frame is None or frame.get('odc_square_target') is None:
        candidates = [ob for ob in context.scene.objects if ob.get('odc_square_target') is not None]
        frame = candidates[0] if len(candidates) == 1 else None
    target = frame.get('odc_square_target') if frame is not None else None
    if target is None or target.name not in context.scene.objects or target.type != 'MESH':
        return None, None
    return frame, target


class OPENDENTAL_OT_square_cut_confirm(bpy.types.Operator):
    """Apply the square cutter to its recorded target."""
    bl_idname = 'opendental.square_cut_confirm'
    bl_label = 'Trim'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        frame, model = square_cut_pair(context)
        if frame is None:
            self.report({'WARNING'}, 'Select a square cutter with a valid model target')
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        if model.data.users > 1:
            model.data = model.data.copy()
        for ob in context.selected_objects:
            ob.select_set(False)
        model.hide_set(False)
        model.select_set(True)
        context.view_layer.objects.active = model
        bm = bmesh.new()
        try:
            bm.from_mesh(model.data)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(model.data)
        finally:
            bm.free()
        modifier = model.modifiers.new('Square Cut', 'BOOLEAN')
        modifier.operation = 'INTERSECT' if context.scene.ODC_modops_props.cutting_mode == 'Keep inner' else 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = frame
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError as error:
            model.modifiers.remove(modifier)
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        bm = bmesh.new()
        try:
            bm.from_mesh(model.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            bm.to_mesh(model.data)
        finally:
            bm.free()
        model.select_set(False)
        frame.select_set(True)
        context.view_layer.objects.active = frame
        return {'FINISHED'}


class OPENDENTAL_OT_square_cut_exit(bpy.types.Operator):
    """Remove the square cutter and return to its target."""
    bl_idname = 'opendental.square_cut_exit'
    bl_label = 'Exit'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        frame, model = square_cut_pair(context)
        if frame is None:
            self.report({'WARNING'}, 'Select a square cutter with a valid model target')
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        mesh = frame.data
        bpy.data.objects.remove(frame, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        for ob in context.selected_objects:
            ob.select_set(False)
        model.hide_set(False)
        model.select_set(True)
        context.view_layer.objects.active = model
        return {'FINISHED'}

#######################################################################################
############################# Model base tools ########################################

#######################################################################################
#model solid base operator :

class OPENDENTAL_OT_model_base(bpy.types.Operator):
    """Make a model base from top user view prspective"""

    bl_idname = "opendental.model_base"
    bl_label = "Create a solid base Dental Model."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode == 'OBJECT' and context.area is not None
                and context.area.type == 'VIEW_3D' and context.region_data is not None)

    def execute(self, context):

        base_height_prop = context.scene.ODC_modops_props.base_height
        base_height = round(base_height_prop, 2)
        show_box = bpy.context.scene.ODC_modops_props.show_box

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            
            # Prepare scene settings :

            bpy.ops.view3d.snap_cursor_to_center()
            bpy.ops.transform.select_orientation(orientation="GLOBAL")
            bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            ####### Duplicate Model #######
                        
            # Get active Object :

            Model = bpy.context.view_layer.objects.active

            # Duplicate Model to Model_Base :

            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.view_layer.objects.active = Model
            bpy.ops.object.duplicate_move()

            # Rename Model_Base :

            Model_base = bpy.context.view_layer.objects.active
            Model_base.name = f"{Model.name}_solid_base"
            mesh_base = Model_base.data
            mesh_base.name = f"{Model.name}_solid_base_mesh"

            bpy.ops.object.select_all(action="DESELECT")
            Model_base.select_set(True)
            bpy.context.view_layer.objects.active = Model_base

            
            ####### Flip Model_Base to top view #######

            view_rotation = context.space_data.region_3d.view_rotation
            view3d_rot_matrix = view_rotation.to_matrix().to_4x4()

            flip_matrix = view3d_rot_matrix.inverted()
            unflip_matrix = view3d_rot_matrix

            Model_base.matrix_world = flip_matrix @ Model_base.matrix_world
            
            # Select base boarder :
                        
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            # Relax border loop :
            bpy.ops.mesh.remove_doubles(threshold=0.1)
            from .mesh_loop_tools import relax_selected
            relax_selected(Model_base.data, iterations=3)

            # Make some calcul of average z_cordinate of border vertices :

            bpy.ops.object.mode_set(mode="OBJECT") 
            obj = bpy.context.view_layer.objects.active
            obj_mx = obj.matrix_world.copy()
            verts = obj.data.vertices           
            global_z_cords = [(obj_mx @ v.co)[2] for v in verts]

            max_z = max(global_z_cords)
            min_z = min(global_z_cords)
            offset = max_z - min_z

            print (f"max_z = {max_z}")
            print (f"min_z = {min_z}")
            print (f"offset = {offset}")

            # Border_2 = Extrude 1st border loop no translation :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.extrude_region_move()

            # change Border2 vertices zco to min_z - base_height  :

            bpy.ops.object.mode_set(mode="OBJECT") 
            selected_verts = [v for v in verts if v.select == True ]

            for v in selected_verts :
                global_v_co = obj_mx @ v.co 
                v.co = obj_mx.inverted() @ Vector((global_v_co[0], global_v_co[1], min_z - base_height))
            #Store Base location :
            context.scene.ODC_modops_props.base_location_prop = (0,0,min_z - base_height)
            # fill base :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.fill(use_beauty=False)

            # Repare geometry resuting from precedent operation :

            bpy.ops.mesh.dissolve_limited()

            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.fill_holes(sides=100)

            bpy.ops.mesh.select_all(action="SELECT")
            bm = bmesh.from_edit_mesh(Model_base.data)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bmesh.update_edit_mesh(Model_base.data)
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="OBJECT")

            # Hide everything but Model_base :

            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.shade_flat()
            bpy.ops.object.hide_view_set(unselected=True)

            # Model_base matrix_world reset :

            Model_base.matrix_world = unflip_matrix @ Model_base.matrix_world

           
            # Result Check :

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.mode_set(mode="OBJECT")
            verts = Model_base.data.vertices 
            selected_verts =  [v for v in verts if v.select] 
            
            if not selected_verts :

                bpy.context.object.show_name = True

                if show_box == True :
                    message = " Model Base created !"
                    ShowMessageBox(message=message, icon="COLORSET_03_VEC")

                print ("base operation done in 1st check")
                return {"FINISHED"}

            else :

                bpy.ops.object.mode_set(mode="OBJECT")

                bpy.ops.object.select_all(action="DESELECT")
                Model_base.select_set(True)
                bpy.context.view_layer.objects.active = Model_base

                bpy.ops.object.delete(use_global=False, confirm=False)

                bpy.ops.object.hide_view_clear()
                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                bpy.context.view_layer.objects.active = Model

                bpy.ops.object.hide_view_set(unselected=True)

                if show_box == True :
                    message = " Operation failed ! Please change view orientation and retry (clean trimed Model)!"
                    ShowMessageBox(message=message, icon="COLORSET_01_VEC")

            return {"FINISHED"}

#######################################################################################
#Hollow model operator :

class OPENDENTAL_OT_hollow_model(bpy.types.Operator):
    """Create a hollow Dental Model from closed Model """

    bl_idname = "opendental.hollow_model"
    bl_label = "Hollow Model"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode == 'OBJECT' and context.area is not None
                and context.area.type == 'VIEW_3D')

    def execute(self, context) :

        show_box = bpy.context.scene.ODC_modops_props.show_box

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            
            Model = bpy.context.view_layer.objects.active
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.mode_set(mode="OBJECT")
            verts = Model.data.vertices 
            selected_verts =  [v for v in verts if v.select]

            if selected_verts :

                message = " Invalid mesh! Can't hollow Open mesh!"
                ShowMessageBox(message=message, icon="COLORSET_01_VEC")


                return {"CANCELLED"}

            else :

                # Prepare scene settings :

                bpy.ops.view3d.snap_cursor_to_center()
                bpy.ops.transform.select_orientation(orientation="GLOBAL")
                bpy.context.scene.tool_settings.transform_pivot_point = "INDIVIDUAL_ORIGINS"
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.context.scene.tool_settings.use_snap = False
                bpy.context.scene.tool_settings.use_proportional_edit_objects = False
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')


                ####### Duplicate Model #######
                        
                # Get active Object :

                Model = bpy.context.view_layer.objects.active

                # Duplicate Model to Model_hollow:

                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                bpy.context.view_layer.objects.active = Model
                bpy.ops.object.duplicate_move()

                # Rename Model_hollow....

                Model_hollow = bpy.context.view_layer.objects.active
                
                model_name = Model.name

                if "solid_base" in model_name :
                    Model_hollow.name = model_name.replace("solid_base", "hollow")
                else :
                    Model_hollow.name = model_name + "_hollow"

                # Duplicate Model_hollow and make a low resolution duplicate :

                bpy.ops.object.duplicate_move()

                # Rename Model_lowres :

                Model_lowres = bpy.context.view_layer.objects.active
                Model_lowres.name = "Model_lowres"
                mesh_lowres = Model_lowres.data
                mesh_lowres.name = "Model_lowres_mesh"

                # Get Model_lowres :

                bpy.ops.object.select_all(action="DESELECT")
                Model_lowres.select_set(True)
                bpy.context.view_layer.objects.active = Model_lowres

                # remesh Model_lowres 1.0 mm :

                bpy.context.object.data.use_remesh_preserve_volume = True
                bpy.context.object.data.use_remesh_fix_poles = True
                bpy.context.object.data.remesh_voxel_size = 1
                bpy.ops.object.voxel_remesh()
                for polygon in bpy.context.object.data.polygons:
                    polygon.use_smooth = True
                
                # Add Metaballs :

                obj = bpy.context.view_layer.objects.active

                loc, rot, scale = obj.matrix_world.decompose()

                verts = obj.data.vertices
                vcords = [obj.matrix_world @ v.co for v in verts]
                mball_elements_cords = [ vco - vcords[0] for vco in vcords[1:]]

                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")

                thikness = 2.5
                radius = thikness * 5/8

                bpy.ops.object.metaball_add(type='BALL', radius=radius, enter_editmode=False, location= vcords[0])

                Mball_object = bpy.context.view_layer.objects.active
                index = 1
                while bpy.data.objects.get(f'ODC Hollow Envelope {index}'):
                    index += 1
                Mball_object.name = f'ODC Hollow Envelope {index}'
                mball = Mball_object.data
                mball.resolution = 0.6
                bpy.context.object.data.update_method = 'FAST'

                for i in range(len(mball_elements_cords)) :
                    element = mball.elements.new()
                    element.co = mball_elements_cords[i]
                    element.radius = radius*2

                bpy.ops.object.convert(target='MESH')

                Mball_object = bpy.context.view_layer.objects.active
                Mball_object.name = "Mball_object"
                mball_mesh = Mball_object.data
                mball_mesh.name = "Mball_object_mesh"

                # Make boolean intersect operation :

                bpy.ops.object.select_all(action="DESELECT")
                Model_hollow.select_set(True)
                bpy.context.view_layer.objects.active = Model_hollow

                modifier = Model_hollow.modifiers.new('Hollow Envelope', 'BOOLEAN')
                modifier.operation = 'INTERSECT'
                modifier.solver = 'EXACT'
                modifier.object = Mball_object
                bpy.ops.object.modifier_apply(modifier=modifier.name)

                # Delet Model_lowres and Mball_object:

                bpy.ops.object.select_all(action="DESELECT")
                Model_lowres.select_set(True)
                bpy.context.view_layer.objects.active = Model_lowres
                Mball_object.select_set(True)

                bpy.ops.object.delete(use_global=False, confirm=False)
                

                # Hide everything but hollow model + Model :

                bpy.ops.object.select_all(action="DESELECT")
                Model.select_set(True)
                Model_hollow.select_set(True)
                bpy.context.view_layer.objects.active = Model_hollow
                bpy.ops.object.shade_flat()
                bpy.ops.object.hide_view_set(unselected=True)
                Model.select_set(False)
           
                if show_box == True :

                    message = "You can trim hollowed Model using cutting tools !"
                    ShowMessageBox(message=message, icon="COLORSET_03_VEC")
                
                return {"FINISHED"}


class OPENDENTAL_OT_solid_hollow_models(bpy.types.Operator):
    """Create a solid and hollow trimed, Dental Models from dental clean mesh """

    bl_idname = "opendental.solid_hollow_models"
    bl_label = "Solid Hollow Models"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode == 'OBJECT' and context.area is not None
                and context.area.type == 'VIEW_3D' and context.region_data is not None)

    def execute(self, context):
        props = context.scene.ODC_modops_props
        height, show_box = props.base_height, props.show_box
        try:
            return self.build_models(context)
        finally:
            props.base_height = height
            props.show_box = show_box

    def build_models(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:
            # Start counter :
            start = time.perf_counter()

            bpy.context.scene.ODC_modops_props.show_box = False
            context.scene.ODC_modops_props.base_height += 3
            
            if bpy.ops.opendental.model_base() != {'FINISHED'}:
                return {'CANCELLED'}
            bpy.context.object.show_name = True
            Model_solid_base = bpy.context.active_object

            if bpy.ops.opendental.hollow_model() != {'FINISHED'}:
                return {'CANCELLED'}
            bpy.context.object.show_name = True
            Model_hollow = bpy.context.active_object

            # flip/Unflip matrix :
            view_rotation = context.space_data.region_3d.view_rotation
            view3d_rot_matrix = view_rotation.to_matrix().to_4x4()

            flip_matrix = view3d_rot_matrix.inverted()
            unflip_matrix = view3d_rot_matrix

            # Get location values :
            base_location = context.scene.ODC_modops_props.base_location_prop

            # Cut plane location :
            plane_z_loc = base_location[2] + 3
            plane_loc = (0, 0, plane_z_loc)


            ##################### Cut Model_hollow to height : #################################

            # Get Model_hollow :(Just we ensure)
            bpy.ops.object.select_all(action="DESELECT")
            Model_hollow.select_set(True)
            bpy.context.view_layer.objects.active = Model_hollow

            # Flip Model_hollow to top view :
            Model_hollow.matrix_world = flip_matrix @ Model_hollow.matrix_world

            # Trim Model_hollow using bisect tool :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.bisect(plane_co=plane_loc, plane_no=(0,0,-1), use_fill=True, clear_inner=False, clear_outer=True)

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode="OBJECT")

            # Model_hollow matrix_world reset :
            Model_hollow.matrix_world = unflip_matrix @ Model_hollow.matrix_world
            Model_hollow.name += '_base'


            ################## Cut Model_solid_base to height ########################### :
            # Get Model_solid_base :
            bpy.ops.object.select_all(action="DESELECT")
            Model_solid_base.select_set(True)
            bpy.context.view_layer.objects.active = Model_solid_base

            # Flip Model_solid_base to top view :
            Model_solid_base.matrix_world = flip_matrix @ Model_solid_base.matrix_world
            
            # Trim Model_solid_base using bisect tool :
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.bisect(plane_co=plane_loc, plane_no=(0,0,-1), use_fill=True, clear_inner=False, clear_outer=True)

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode="OBJECT")

            # Model_solid_base matrix_world reset :
            Model_solid_base.matrix_world = unflip_matrix @ Model_solid_base.matrix_world


            # Select Model solid base :
            bpy.ops.object.select_all(action="DESELECT")
            Model_solid_base.select_set(True)
            bpy.context.view_layer.objects.active = Model_solid_base
            
            #Restore base_height user value :
            context.scene.ODC_modops_props.base_height -= 3

            #stop counter :
            finish = time.perf_counter()

            print(f'Making model solide base and model hollow base finished in {finish-start} second(s)')

            message = " Model solide and hollow base created !"
            ShowMessageBox(message=message, icon="COLORSET_03_VEC")
            
            return {"FINISHED"}

           
#######################################################################################
#Remesh model operator : todo add factor property default to 0.1

class OPENDENTAL_OT_remesh_model(bpy.types.Operator):
    """ Rmesh Model - remesh alogorythm remove any internal intersecting topology and make quad polygons """

    bl_idname = "opendental.remesh_model"
    bl_label = "Remesh Model"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            # get model to clean :
            bpy.ops.object.mode_set(mode="OBJECT")
            Model = bpy.context.view_layer.objects.active
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)
            bpy.context.object.data.remesh_voxel_size = 0.1
            bpy.ops.object.voxel_remesh()
            for polygon in Model.data.polygons:
                polygon.use_smooth = True
            
            bpy.ops.object.mode_set(mode="OBJECT")
            

            return {"FINISHED"}

#######################################################################################
#Model Add color operator :

class OPENDENTAL_OT_model_color(bpy.types.Operator):
    """Add color material """

    bl_idname = "opendental.model_color"
    bl_label = "Model Color"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context) :

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            Model = context.view_layer.objects.active
            if Model.material_slots :

                for _ in Model.material_slots :
                
                    bpy.ops.object.material_slot_remove()

            
            model_color = bpy.data.materials.new("ODC_Model_material")
            model_color.diffuse_color = [0.8, 0.8, 0.8, 1.0]
            Model.data.materials.append(model_color)



        return {"FINISHED"}

#######################################################################################
#Model Remove color operator :

class OPENDENTAL_OT_model_remove_color(bpy.types.Operator):
    """Remove Model color material """

    bl_idname = "opendental.remove_model_color"
    bl_label = "Remove Color"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context) :

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else:

            Model = context.view_layer.objects.active
            if Model.material_slots :

                for _ in Model.material_slots :
                
                    bpy.ops.object.material_slot_remove()

        return {"FINISHED"}

#######################################################################################
#Model Add offset operator :

class OPENDENTAL_OT_add_offset(bpy.types.Operator):
    """ Add offset to mesh """

    bl_idname = "opendental.add_offset"
    bl_label = "Offset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context) :

        if bpy.context.selected_objects == []:

            message = " Please select Model !"
            ShowMessageBox(message=message, icon="COLORSET_02_VEC")

            return {"CANCELLED"}

        else :
            offset_prop = context.scene.ODC_modops_props.offset
            offset = round(offset_prop, 2)

            bpy.ops.object.mode_set(mode="OBJECT")
            Model = context.view_layer.objects.active
            bpy.ops.object.select_all(action="DESELECT")
            Model.select_set(True)

            bpy.ops.object.duplicate_move()

            # Rename Model_Base :

            Model_offset = bpy.context.view_layer.objects.active
            Model_offset.name = f"{Model.name}_offset_{offset}mm"
            mesh_offset = Model_offset.data
            mesh_offset.name = f"{Model.name}_offset_{offset}mm_mesh"

            bpy.ops.object.select_all(action="DESELECT")
            Model_offset.select_set(True)
            bpy.context.view_layer.objects.active = Model_offset

            bpy.ops.object.modifier_add(type='DISPLACE')
            bpy.context.object.modifiers["Displace"].strength = offset
            bpy.context.object.modifiers["Displace"].mid_level = 0.0
            bpy.ops.object.modifier_apply(modifier="Displace")


        return {"FINISHED"}

classes = [ OPENDENTAL_OT_join_models,
            OPENDENTAL_OT_separate_models,
            OPENDENTAL_OT_parent_models,
            OPENDENTAL_OT_unparent_models,
            OPENDENTAL_OT_align_to_front,
            OPENDENTAL_OT_center_Model,
            OPENDENTAL_OT_center_cursor,
            OPENDENTAL_OT_decimate_model, 
            OPENDENTAL_OT_clean_model,
            OPENDENTAL_OT_fill, 
            OPENDENTAL_OT_retopo_smooth,
            OPENDENTAL_OT_make_curve,
            OPENDENTAL_OT_curve_cut,
            OPENDENTAL_OT_trim_model,
            OPENDENTAL_OT_square_cut,
            OPENDENTAL_OT_square_cut_confirm,
            OPENDENTAL_OT_square_cut_exit,
            OPENDENTAL_OT_model_base, 
            OPENDENTAL_OT_hollow_model,
            OPENDENTAL_OT_solid_hollow_models, 
            OPENDENTAL_OT_remesh_model,
            OPENDENTAL_OT_model_color, 
            OPENDENTAL_OT_model_remove_color,
            OPENDENTAL_OT_add_offset,            
] 
    
def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
   
