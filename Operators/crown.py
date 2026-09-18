#Python imports :
import math
import time
import os


#Blender imports :
import bpy
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils

#Addon imports :
from ..Addon_utils import odcutils
from ..Addon_utils.odcutils import get_settings
from ..Addon_utils.common_utilities import bversion

from ..odcmenus import menu_utils as menu_utils
from ..odcmenus import button_data as button_data
from ..Operators import crown_methods, full_arch_methods, bgl_utils, classes
from ..Operators.curve import CurveDataManager
from .mesh_loop_tools import flatten_selected
from ..Operators.textbox import TextBox

'''
This module handles operators for the crown (and maybe bridge) functionality of ODC
The "meat" of the more complicated operator functions is in crown_methods.py
Some License might be in the source directory. Summary: don't be an asshole, but do whatever you want with this code
Author: Patrick Moore:  patrick.moore.bu@gmail.com
'''

#Global variables (should they be?)
global lib_teeth
global lib_teeth_enum
lib_teeth = []
lib_teeth_enum = []
    
class OPENDENTAL_OT_center_all_objects(bpy.types.Operator):
    '''Use With Caution especially if objects are parented.'''
    bl_idname = "opendental.center_objects"
    bl_label = "Center All Objects"
    bl_options = {'REGISTER','UNDO'}
    
    def execute(self,context):
        #sce = bpy.context.scene #2.79
        #gather all the objects
        objects = [ob for ob in bpy.context.scene.objects] #don't want this to update #2.79 sce.objects
        
        #put all their origins at their medianpoint
        bpy.ops.object.select_all(action='DESELECT')
        for ob in objects:
            #sce.objects.active_object = ob #2.79
            bpy.context.view_layer.objects.active = ob
            ob.hide_set(False)
            ob.select_set(state=True)
            bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY', center = 'BOUNDS')
            ob.select_set(state=False)
            
        #calculate the median point of all the objects
        Med = Vector((0,0,0))
        for ob in objects:
            Med += ob.location
        Med = 1/len(objects)*Med
        print(Med)
        
        #Move everyone
        bpy.ops.object.select_all(action = 'SELECT')
        bpy.ops.transform.translate(value = (-Med[0], -Med[1], -Med[2]))
        
        #celebrate                           
        return{'FINISHED'}
        
class OPENDENTAL_OT_set_master(bpy.types.Operator):
    ''''''
    bl_idname='opendental.set_master'
    bl_label="Set Master"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls,context):
        if not hasattr(context.scene, 'odc_props'): return False
        condition_1 = context.object is not None and context.object.type == 'MESH' and context.mode == 'OBJECT'
        return condition_1
    
    def execute(self, context):        
        
        if len(bpy.context.selected_editable_objects) > 1:
            bpy.ops.object.join()
        
        ob=bpy.context.object
        
        if ob:
            n = 5
            if len(ob.name) < 5:
                n = len(ob.name) - 1
            
            new_name = "Master_" + ob.name[0:n]
            ob.name = new_name
            
            bpy.context.scene.odc_props.master = ob.name
            odcutils.layer_management(context.scene.odc_teeth, debug = False)
            odcutils.material_management(context, [context.scene.odc_props])
        else:
            self.report({'WARNING'}, "Nothing is active...sometimes you need to right click again :-)")
        
        return{'FINISHED'}
        
class OPENDENTAL_OT_set_as_prep(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.set_as_prep'
    bl_label = "Set as Prep"
    bl_options = {'REGISTER','UNDO'}
    
    abutment: bpy.props.BoolProperty(name = "abutment", default = False)
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.mode in {'OBJECT', 'EDIT_MESH'}
                and hasattr(context.scene, 'odc_teeth')
                and len(context.scene.odc_teeth) > 0)

    def execute(self, context):
        import bmesh
        scene = context.scene
        source = context.object
        master = scene.objects.get(scene.odc_props.master)
        if master is None:
            self.report({'WARNING'}, "Set a master model first")
            return {'CANCELLED'}
        tooth = scene.odc_teeth[scene.odc_tooth_index]
        settings = get_settings()
        if context.mode == 'EDIT_MESH':
            # Extract only the active object's selected geometry. This also avoids
            # duplicating unrelated objects in Blender's multi-object edit mode.
            edit_mesh = bmesh.from_edit_mesh(source.data)
            if not any(v.select for v in edit_mesh.verts):
                self.report({'WARNING'}, "Select preparation geometry first")
                return {'CANCELLED'}
            bm = edit_mesh.copy()
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.select], context='VERTS')
            mesh = bpy.data.meshes.new(tooth.name + '_Prep')
            bm.to_mesh(mesh)
            bm.free()
            for material in source.data.materials:
                mesh.materials.append(material)
            prep = source.copy()
            prep.data = mesh
            scene.collection.objects.link(prep)
            bpy.ops.object.mode_set(mode='OBJECT')
        elif source == master:
            prep = source.copy()
            prep.data = source.data.copy()
            scene.collection.objects.link(prep)
        else:
            prep = source
        prep.name = tooth.name + '_Prep'
        tooth.prep_model = prep.name
        if not self.abutment:
            odcutils.parent_in_place(prep, master)
        bpy.ops.object.select_all(action='DESELECT')
        prep.hide_set(False)
        prep.select_set(True)
        context.view_layer.objects.active = prep
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        if settings.workflow == '0':
            master.hide_set(True)
            if context.area and context.area.type == 'VIEW_3D':
                bpy.ops.view3d.view_axis(type='TOP', align_active=True)
        elif settings.workflow in {'1', '2'}:
            prep.select_set(False)
            source.select_set(True)
            context.view_layer.objects.active = source
            bpy.ops.object.mode_set(mode='EDIT')
        odcutils.layer_management(scene.odc_teeth)
        return {'FINISHED'}

class OPENDENTAL_OT_set_mesial(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.set_mesial'
    bl_label = "Set Mesial"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and hasattr(context.scene, 'odc_teeth')
                and 0 <= context.scene.odc_tooth_index < len(context.scene.odc_teeth))

    def execute(self, context):
        #grab active tooth the old way
        sce=bpy.context.scene
        tooth = odcutils.active_tooth_from_index(sce)
        tooth.mesial = context.object.name
        
        self.report({'INFO'},'You Set The Mesial')
        return {'FINISHED'}
    
class OPENDENTAL_OT_set_distal(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.set_distal'
    bl_label = "Set Distal"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and hasattr(context.scene, 'odc_teeth')
                and 0 <= context.scene.odc_tooth_index < len(context.scene.odc_teeth))

    def execute(self, context):
        #grab active tooth the old way
        sce=bpy.context.scene
        tooth = odcutils.active_tooth_from_index(sce)
        tooth.distal = context.object.name
        self.report({'INFO'},'You Set The Distal')
        return {'FINISHED'}
    
class OPENDENTAL_OT_set_opposing(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.set_opposing'
    bl_label = "Set Opposing"
    bl_options = {'REGISTER','UNDO'}
    
    for_all: bpy.props.BoolProperty(default = True)
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and hasattr(context.scene, 'odc_props'))

    def execute(self, context):
        #grab active tooth the old way
        
        if self.for_all:
            for tooth in context.scene.odc_teeth:
                tooth.opposing = context.object.name
            
            context.scene.odc_props.opposing = context.object.name
        else:
            sce = context.scene
            if not 0 <= sce.odc_tooth_index < len(sce.odc_teeth):
                self.report({'WARNING'}, 'Plan and select a tooth first')
                return {'CANCELLED'}
            tooth = odcutils.active_tooth_from_index(sce)
            tooth.opposing = context.object.name
        self.report({'INFO'},'You Set The Opposing')
        return {'FINISHED'}
    
           
class ViewToZ(bpy.types.Operator):
    '''Aligns the local coordinates of the acive object with the view'''
    bl_idname = "view3d.view_to_z"
    bl_label = "View to Z"
    bl_options = {'REGISTER','UNDO'}

    keep_orientation: bpy.props.BoolProperty(default = False, name = "Keep Orientation")
    
    def execute(self, context):
        bpy.ops.object.select_all(action = 'DESELECT')
        ob = bpy.context.object
        ob.select = True
        
        #necessary because I don't want to have to wory
        #about what the transform orientation might be
       # bpy.ops.object.transform_apply(rotation = True)
        
        #this is what the view rotation is reported as
        #so for convenience I will just make the object
        #use it
        #ob.rotation_mode = 'QUATERNION'
        
        #gather info
        space = bpy.context.space_data
        region = space.region_3d        
        vrot = region.view_rotation       
        #align = vrot.inverted()
        
        odcutils.reorient_object(ob,vrot)    
        #rotate the object the inverse of the view rotation
        #ob.rotation_quaternion = align
        
        #if we want to keep the rotatio nof the object in
        #the scene and essentially just set the object's
        #local coordinates to the view...then do this.      
        if self.keep_orientation:
            bpy.ops.object.transform_apply(rotation = True)
            ob.rotation_quaternion = vrot   
                
        return {'FINISHED'}
def insertion_axis_draw_callback(self, context):
    self.help_box.draw()
    self.target_box.draw()
    
    bgl_utils.insertion_axis_callback(self,context)

class OPENDENTAL_OT_insertion_axis(bpy.types.Operator):
    """Set the insertion axis of the preps from view"""
    bl_idname = "opendental.insertion_axis"
    bl_label = "Insertion Axis"
    bl_options = {'REGISTER','UNDO'}
    
    def set_axis(self, context, event):
        tooth = context.scene.odc_teeth[self.target]
        from .insertion_axis import place_axis
        coord = (event.mouse_region_x, event.mouse_region_y)
        rv3d = context.space_data.region_3d
        direction = view3d_utils.region_2d_to_vector_3d(context.region, rv3d, coord)
        origin = view3d_utils.region_2d_to_origin_3d(context.region, rv3d, coord)
        self.axis_session.remember(tooth)
        previous = context.scene.objects.get(tooth.axis) if tooth.axis else None
        axis, _ = place_axis(context, tooth, origin, direction, rv3d.view_rotation, rv3d.view_location)
        if previous is None:
            self.axis_session.record_created(axis)
        self.align = rv3d.view_rotation.inverted()

    def advance_next_prep(self,context):
        self.target_index = (self.target_index + 1) % len(self.units)
        self.target = self.units[self.target_index]
        self.message = "Set axis for %s" % self.units[self.target_index]
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        tooth = context.scene.odc_teeth[self.target]
        
        for obj in context.view_layer.objects:
            obj.select_set(False)
        if tooth.prep_model in bpy.data.objects:
            bpy.data.objects[tooth.prep_model].select_set(True)
            context.space_data.region_3d.view_location = bpy.data.objects[tooth.prep_model].matrix_world.translation
              
    def select_prev_unit(self,context):
        self.target_index = (self.target_index - 1) % len(self.units)
        self.target = self.units[self.target_index]
        self.message = "Set axis for %s" % self.units[self.target_index]
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        tooth = context.scene.odc_teeth[self.target]
        
        for obj in context.view_layer.objects:
            obj.select_set(False)
        if tooth.prep_model in bpy.data.objects:
            bpy.data.objects[tooth.prep_model].select_set(True)
            context.space_data.region_3d.view_location = bpy.data.objects[tooth.prep_model].matrix_world.translation
                       
    def update_selection(self,context):
        selection_targets = odcutils.tooth_selection(context)        
        if not selection_targets or selection_targets[0].name not in self.units:
            return
        self.target_index = self.units.index(selection_targets[0].name)
        self.target = self.units[self.target_index]
        self.message = "Set axis for %s" % self.units[self.target_index]
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        
    def modal_main(self, context, event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        if event.type in {'RIGHTMOUSE'} and event.value == 'PRESS':
            self.update_selection(context)
            return 'pass'
        
        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            self.update_selection(context)
            if len(context.selected_objects):
                context.space_data.region_3d.view_location = context.selected_objects[0].location
            return 'main'
        
        elif event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            #raycast to check a hit?
            self.set_axis(context, event)
            self.advance_next_prep(context)
            return 'main'
        
        elif event.type in {'DOWN_ARROW'} and event.value == 'PRESS':
            self.select_prev_unit(context)
            return 'main'
        
        elif event.type in {'UP_ARROW'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'main'
        
        elif event.type == 'SPACE' and event.value == 'PRESS':
            self.set_axis(context, event)
            return 'main'
            
        elif event.type in {'ESC'}:
            #keep track of and delete new objects? reset old transforms?
            return'cancel'
        
        elif event.type in {'RET'} and event.value == 'PRESS':
            return 'finish'
        
        return 'main'
        
    def modal_nav(self, event):
        events_nav = {'MIDDLEMOUSE', 'WHEELINMOUSE','WHEELOUTMOUSE', 'WHEELUPMOUSE','WHEELDOWNMOUSE'} #TODO, better navigation, another tutorial
        handle_nav = False
        handle_nav |= event.type in events_nav

        if handle_nav: 
            return 'nav'
        return ''

    def modal(self, context, event):
        context.area.tag_redraw()

        FSM = {}    
        FSM['main']    = self.modal_main
        FSM['pass']    = self.modal_main
        FSM['nav']     = self.modal_nav
        
        nmode = FSM[self.mode](context, event)

        if nmode == 'nav': 
            return {'PASS_THROUGH'}
        
        if nmode in {'finish','cancel'}:
            if nmode == 'cancel':
                self.axis_session.cancel()
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        if nmode == 'pass':
            self.mode = 'main'
            return {'PASS_THROUGH'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}
     
    def invoke(self, context, event):
        settings = get_settings()
        dbg = settings.debug
        odcutils.scene_verification(context.scene, debug = dbg)
        if context.space_data is None or context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, 'Active space must be a View3d')
            return {'CANCELLED'}
        from .insertion_axis import AxisSession
        self.axis_session = AxisSession(context.scene)
        
        if context.space_data.region_3d.is_perspective:
            #context.space_data.region_3d.is_perspective = False
            bpy.ops.view3d.view_persportho()
            
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        
        else:
            
            #gather all the teeth in the scene
            self.units = [tooth.name for tooth in context.scene.odc_teeth]

            if not self.units:
                self.report({'ERROR'}, "Yikes, there are no working teeth in the sceen!")
                return {'CANCELLED'}
            
            selection_targets = odcutils.tooth_selection(context)
            if selection_targets:
                self.target = selection_targets[0].name
            else:
                self.target = self.units[0]
        
            self.target_index = self.units.index(self.target)
            self.message = "Set axis for %s" %self.units[self.target_index]
            

        help_txt = "Right click to select a prep \n View path of insertion \n Up Arrow and Dn Arrow to select different units \n Left click in middle of prep to set axis \n Enter to finish \n ESC to cancel"
        self.help_box = TextBox(context,500,500,300,200,10,20,help_txt)
        self.help_box.fit_box_width_to_text_lines()
        self.help_box.fit_box_height_to_text_lines()
        self.help_box.snap_to_corner(context, corner = [1,1])
        
        aspect, mid = menu_utils.view3d_get_size_and_mid(context)
        self.target_box = TextBox(context,mid[0],aspect[1]-20,300,200,10,20,self.message)
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        self.target_box.fit_box_height_to_text_lines()
        
        self.mode = 'main'
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(insertion_axis_draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}
    

    
class CBGetCrownForm(bpy.types.Operator):
    '''Inserts a crown form from the tooth library at the cursor location'''
    bl_idname = 'opendental.get_crown_form'
    bl_label = "Get Crown Form"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "ob_list"

    _library_items = []

    def item_cb(self, context):
        # Retain enum strings for Blender and support execution without a popup.
        names = [obj.name for obj in self.objs]
        if not names:
            try:
                names = odcutils.obj_list_from_lib(get_settings().tooth_lib, exclude='_')
            except (OSError, RuntimeError):
                names = []
        CBGetCrownForm._library_items = [(name, name, '') for name in names]
        return CBGetCrownForm._library_items

    objs: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    ob_list: bpy.props.EnumProperty(name="Tooth Library Objects", description="A List of the tooth library", items=item_cb)
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        #here we grab the asset library from the addon prefs
        libpath = settings.tooth_lib
        
        #a list of all objects in the asset library
        assets = odcutils.obj_list_from_lib(libpath, exclude = '_')
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
        #context.window_manager.invoke_search_popup(self.ob_list)
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        
        #TODO:...make this work for multiple teeth
        #TODO:...incorporate with teeth on curve
        sce = context.scene
        settings = get_settings()
        tooth = None
        tooth_candidates = odcutils.tooth_selection(context)
        if tooth_candidates:
            tooth = tooth_candidates[0]
            if not tooth:
                self.report({'WARNING'},"I'm not sure which tooth you want, guessing based on active tooth in list")
                tooth = sce.odc_teeth[sce.odc_tooth_index]
        
        if tooth is None:
            self.report({'WARNING'}, "No planned teeth, inserting object anyway")

        try:
            ob = odcutils.obj_from_lib(settings.tooth_lib, self.ob_list)
        except (OSError, RuntimeError, ValueError) as error:
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        sce.collection.objects.link(ob)
        ob.location = sce.cursor.location
        # Do not discard the previous restoration until its replacement loaded.
        if tooth is not None and tooth.restoration:
            old_ob = bpy.data.objects.get(tooth.restoration)
            if old_ob is not None:
                bpy.data.objects.remove(old_ob, do_unlink=True)

        if tooth != None:
            
            ob.name = tooth.name + "_FullContour"
            tooth.contour = ob.name
            ob.rotation_mode = 'QUATERNION'
        
            #align with the insertion axis
            axis = sce.objects.get(tooth.axis) if tooth.axis else None
            if axis is None:
                self.report({'WARNING'}, "No insertion axis set, can't align tooth properly, may cause problem later!")
            else:
                rot = axis.matrix_world.to_quaternion()
                ob.rotation_quaternion = rot
        
        
        
        
        
            if tooth.rest_type == '0' or tooth.rest_type == '1':
                tooth.restoration = ob.name
        
            if tooth.rest_type == '1':
                print('pontic!')
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True)
                context.view_layer.objects.active = ob
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_non_manifold()
                flatten_selected(ob.data)
                bpy.ops.transform.translate(value = (0,0,-1))
            
                bpy.ops.object.mode_set(mode= 'OBJECT')
                eds = [ed for ed in ob.data.edges if ed.select]
                odcutils.fill_loop_scale(ob, eds, .3, debug = False)
            
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_more()
                bpy.ops.mesh.select_more()
            
                #new vertex group for smoothin after multires.
                n = len(ob.vertex_groups)
                bpy.ops.object.vertex_group_assign_new()
                ob.vertex_groups[n].name = 'Smooth'
            
                bpy.ops.mesh.remove_doubles()
                #this operator causes multires data to get screwed up!
                #bpy.ops.mesh.relax(iterations=10)
                #dont do this either...we will make new functions
                #to control the bottom of the pontic
                #bpy.ops.mesh.vertices_smooth(repeat = 5)
                bpy.ops.object.mode_set(mode='OBJECT')
            
                #add a smooth modifier to attempt to mitigate
                #the funky result when changing base mesh topology
                n = len(ob.modifiers)
                bpy.ops.object.modifier_add(type = 'SMOOTH')
                mod = ob.modifiers[n]
                mod.name = 'Smooth'        
                mod.vertex_group = 'Smooth'
                mod.iterations = 30
                mod.factor = 2    
            
        #fill the bottom if it's a pontic
        
        #layer management
        odcutils.layer_management(sce.odc_teeth)
        #odcutils.transform_management(tooth,sce)
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_seat_to_margin(bpy.types.Operator):
    '''
    Adapts the open edge of the crown to the marked margin.
    '''
    bl_idname = 'opendental.seat_to_margin'
    bl_label = "Seat to Margin"
    bl_options = {'REGISTER','UNDO'}
    
    influence: bpy.props.FloatProperty(name="Nearby Influence", description="", default=1, min=.1, max=2, step=2, precision=1, options={'ANIMATABLE'})
    
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        
        tooth = odcutils.tooth_selection(context)[0]  #TODO:...make this poll work for all selected teeth...
        condition_1 = tooth.contour in bpy.data.objects
        condition_2 = tooth.margin in bpy.data.objects
        condition_3 = tooth.pmargin in bpy.data.objects
                
        return condition_1 and condition_2 and condition_3
    
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        odcutils.layer_management(context.scene.odc_teeth, debug = False)
        

        
        #TODO: Scene Preservation recording
        teeth = odcutils.tooth_selection(context)
        
        not_valid = []
        for tooth in teeth:
            if tooth.rest_type == 1: continue
            condition_1 = tooth.contour in bpy.data.objects
            condition_2 = tooth.margin in bpy.data.objects
            condition_3 = tooth.pmargin in bpy.data.objects
            if not (condition_1 and condition_2 and condition_3):
                reason = 'Tooth #' + tooth.name + ' can not seat because...'
                if not condition_1:
                    reason += 'No full contour, please "Get Crown Form."  '
                if not condition_2:
                    reason += 'No margin, please "Mark Margin."  '
                if not condition_3:
                    reason += 'Margin still provisional, please "Accept Margin."'
                    
                not_valid.append(reason)
            
        if len(not_valid):
            for reason in not_valid:
                self.report({'INFO'}, reason)
                    
        for tooth in teeth:
            sce = bpy.context.scene
            
            condition_1 = tooth.contour in bpy.data.objects
            condition_2 = tooth.margin in bpy.data.objects
            condition_3 = tooth.pmargin in bpy.data.objects
            
            if not (condition_1 and condition_2 and condition_3):
                continue
            crown_methods.seat_to_margin_improved(context, sce, tooth, influence = self.influence, debug = dbg) #TODO: debug stuff
  

        return {'FINISHED'}
    
class OPENDENTAL_OT_calculate_inside(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.calculate_inside'
    bl_label = "Calculate Intaglio"
    bl_options = {'REGISTER','UNDO'}
    
    holy_zone: bpy.props.FloatProperty(name="Holy Zone Width", description="", default=.4, min=.2, max=2, step=5, precision=1, options={'ANIMATABLE'})
    chamfer: bpy.props.FloatProperty(name="Chamfer", description="0 = shoulder 1 = feather", default=.2, min=0, max=1, step=2, precision=2, options={'ANIMATABLE'})
    gap: bpy.props.FloatProperty(name="Gap Thickness", description="thickness required for cement", default=0.07, min=.01, max=.5, step=2, precision=2, options={'ANIMATABLE'})
    no_undercuts: bpy.props.BoolProperty(name="No Undercuts", description="Uncheck if there are significant undercuts", default=True)

    @classmethod
    def poll(cls,context):
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        
        tooth = odcutils.tooth_selection(context)[0]  #TODO:...make this poll work for all selected teeth...
        condition_1 = tooth.contour in bpy.data.objects
        condition_2 = tooth.margin in bpy.data.objects
        condition_3 = tooth.pmargin in bpy.data.objects
        
        return condition_1 and condition_2 and condition_3
        
    def invoke(self, context, event): 
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        

        
        context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
            
        sce=bpy.context.scene        
        #master = sce.master_model
        
        #exclude = ["mesial_model","distal_model"]
        candidates = odcutils.tooth_selection(context)
        
        for tooth in candidates:
            if tooth.rest_type == '1': continue  #pontic
            if any(not context.scene.objects.get(getattr(tooth, field)) for field in ('prep_model', 'axis', 'contour', 'margin', 'pmargin')):
                self.report({'WARNING'}, 'Assign preparation, axis, crown and accepted margin first')
                return {'CANCELLED'}
            if self.no_undercuts:         
                crown_methods.calc_intaglio(context, sce, tooth, self.chamfer, self.gap, self.holy_zone, debug = dbg) #TODO: institude global debug for addon
            else:
                crown_methods.calc_intaglio2(context, sce, tooth, self.chamfer, self.gap, self.holy_zone, debug =dbg)
        odcutils.layer_management(candidates)
        #TODO: good logging print("Finished operationt %s on tooth %s in 3 seconds /n again" % (self.bl_label, tooth.name) )        
        return {'FINISHED'}
    
class OPENDENTAL_OT_crown_cervical_convergence(bpy.types.Operator):
    '''Changes the angle of cervical convergence for the crown relative to insertion axis /n (unfortunately not to tangent of prep)'''
    bl_idname = "opendental.cervical_convergence"
    bl_label = "Angle Cervical Convergence"
    bl_options = {'REGISTER','UNDO'}

    ang: bpy.props.FloatProperty(name="Angle", description="", default=math.pi/12, min=0, options={'ANIMATABLE'}, subtype='ANGLE', unit='ROTATION')
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        
        tooth = odcutils.tooth_selection(context)[0]  #TODO: make this poll work for all selected teeth...
        condition_1 = tooth.contour and tooth.contour in bpy.data.objects #TODO: make this restoration when that property implemented
        condition_2 = tooth.axis and tooth.axis in bpy.data.objects        
        return condition_1 and condition_2

    
    #def modal(self,context): #TODO: modal code for cervical convergence
        
    #def draw(self,context): #TODO: draw code for cervical convergence
    
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        tooth = odcutils.tooth_selection(context)[0]
        
        angle = self.ang
        crown_methods.cervical_convergence_improved(context, tooth, angle, selected = False, debug = dbg)
        
        odcutils.layer_management(context.scene.odc_teeth, debug = False)
        return{'FINISHED'}
        
    def draw(self, context):
        
        layout = self.layout
        row = layout.row()       
        row.prop(self, "ang")
        
class OPENDENTAL_make_solid_restoration(bpy.types.Operator):
    '''
    joins the shell and intaglio to make a millable/printable watertight mesh
    '''
    bl_idname = 'opendental.make_solid_restoration'
    bl_label = "Make Solid Restoration"
    bl_options = {'REGISTER','UNDO'}
    
    method: bpy.props.IntProperty(default = 1)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not hasattr(context.scene, 'odc_props'): return False
        if not len(context.scene.odc_teeth): return False
        if not len(odcutils.tooth_selection(context)): return False
        tooth = odcutils.tooth_selection(context)[0]  #TODO: make this poll work for all selected teeth...
        condition_1 = tooth.contour and tooth.contour in bpy.data.objects #TODO: make this restoration when that property implemented
        condition_2 = tooth.intaglio and tooth.intaglio in bpy.data.objects        
        return condition_1 and condition_2
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        teeth = odcutils.tooth_selection(context)
        
        for tooth in teeth:
            if self.method == 0:
                crown_methods.make_solid_restoration(context, tooth, debug = dbg)
            else:
                crown_methods.make_solid_restoration2(context, tooth, debug = dbg)
        
        odcutils.layer_management(context.scene.odc_teeth, debug = False)
            
        return {'FINISHED'}
           
class OPENDENTAL_OT_plan_restorations(bpy.types.Operator):
    '''Select Multiple Interestingly Shaped Buttons'''
    bl_idname = "opendental.plan_restorations"
    bl_label = "Plan Restorations"

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'MOUSEMOVE':
            #check to see what button the mouse is over if any
            self.mouse = (event.mouse_region_x, event.mouse_region_y)
            for i in range(0,len(button_data.tooth_button_data)):
                self.tooth_button_hover[i] = bgl_utils.point_inside_loop(button_data.tooth_button_data[i],self.mouse,self.menu_width, self.menu_loc)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.mouse = (event.mouse_region_x, event.mouse_region_y)
            
            
            #determine if we are clicking on a toth
            for i in range(0,len(button_data.tooth_button_data)):
                #check every tooth
                self.tooth_button_hover[i] = bgl_utils.point_inside_loop(button_data.tooth_button_data[i],self.mouse,self.menu_width, self.menu_loc)
                #if we have clicked on it, add it to the current restoration type list
                if self.tooth_button_hover[i]:
                    if button_data.tooth_button_names[i] not in self.rest_lists[self.rest_index]:
                        print(self.rest_lists[self.rest_index])      
                        self.rest_lists[self.rest_index].append(button_data.tooth_button_names[i])
                    else:
                        self.rest_lists[self.rest_index].remove(button_data.tooth_button_names[i])

            #no buttons are hovered, this is equiv to enter...
            if True not in self.tooth_button_hover:
                for i in range(0,len(button_data.rest_button_data)):
                    self.rest_button_select[i] = bgl_utils.point_inside_loop(button_data.rest_button_data[i],self.mouse,.5*self.menu_width, self.rest_menu_loc)
                    
                    if self.rest_button_select[i]:
                        self.rest_index = i 
                
                if True not in self.rest_button_select:
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    self.ret_selected = [button_data.tooth_button_names[i] for i in range(0,len(button_data.tooth_button_data)) if self.tooth_button_select[i]]
                    self.execute(context)
                    return {'FINISHED'}
            

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.mouse = (event.mouse_region_x, event.mouse_region_y)
            for i in range(0,len(button_data.tooth_button_data)):
                self.tooth_button_hover[i] = bgl_utils.point_inside_loop(button_data.tooth_button_data[i],self.mouse,self.menu_width, self.menu_loc)
                if self.tooth_button_hover[i]:
                    self.tooth_button_select[i] = False

            #no buttons are hovered, this is equiv to quiting...
            if True not in self.tooth_button_hover:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'CANCELLED'}
            
        elif event.type == 'RET' and event.value == 'PRESS':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.ret_selected = [button_data.tooth_button_names[i] for i in range(0,len(button_data.tooth_button_data)) if self.tooth_button_select[i]]
            self.execute(context)
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(bgl_utils.draw_callback_tooth_select, (self, context), 'WINDOW', 'POST_PIXEL')

            self.mouse = (0,0)
            
            #keep track of which teeth are selected and which one the mouse is over
            self.tooth_button_select = [False]*len(button_data.tooth_button_data)
            self.tooth_button_hover = [False]*len(button_data.tooth_button_data)
            
            
            #keep track of which rest type is selected
            self.rest_button_select = [False]*5 #keep in mind we only want a subset of them!
            self.rest_button_select[0] = True #make something default
            self.rest_button_hover = [False]*5 #don't think I need this....
            self.rest_index = 0
            
            #form lists for each rest_type
            self.rest_lists = [[],[],[],[],[]] #contour, pontic, coping, anatomic coping, implant

            
            region = bpy.context.region
            rv3d = bpy.context.space_data.region_3d
    
            width = region.width
            height = region.height
            mid = (width/2,height/2)
    
            #need to check height available..whatev
            #menu_width is also our scale!
            self.menu_aspect = 0.5824333739982135
            self.menu_width = .8*width
            self.menu_height = self.menu_width/self.menu_aspect
            if self.menu_height > height:
                self.menu_width = self.menu_aspect*.8*height
                self.menu_height = self.menu_width/self.menu_aspect
            #origin of menu is bottom left corner
            self.menu_loc = (.5*(width - self.menu_width), .5*(height - self.menu_height)) #for now
            
            #middle menu
            self.rest_menu_loc = (self.menu_loc[0] + self.menu_width*.25, self.menu_loc[1] + self.menu_height*.25/self.menu_aspect)

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
        
    def execute(self,context):
        for i in range (0,4):
            for tooth_name in self.rest_lists[i]:
                bpy.ops.opendental.add_tooth_restoration('EXEC_DEFAULT',name = str(tooth_name), rest_type = str(i))
        for tooth_name in self.rest_lists[4]:
            print('adding an implant at %s' % tooth_name)
            bpy.ops.opendental.add_implant_restoration('EXEC_DEFAULT',name = str(tooth_name))  

class OPENDENTAL_OT_prep_from_crown(bpy.types.Operator):
    '''
    Use to make temp crown or custom abutment \n
    Operator will calculate a shoulder prep of specified width
    from a margin and crown form or from a crown form
    with non manifold edge
    '''
    bl_idname = 'opendental.prep_from_crown'
    bl_label = "Prep From Crown"
    bl_options = {'REGISTER','UNDO'}
    
    margin_width: bpy.props.FloatProperty(name="Chamfer Depth", description="", default=.5, min=.1, max=2, step=5, precision=2, options={'ANIMATABLE'})
    reduction: bpy.props.FloatProperty(name="Occlusal Reduction", description="", default=.5, min=.1, max=4, step=5, precision=2, options={'ANIMATABLE'})
    make_inside: bpy.props.BoolProperty(name="Make Inside", description = "Use if making prefab temp shell", default = True)

    
    @classmethod
    def poll(cls, context):
        if not hasattr(context.scene, 'odc_props'): return False
        settings = get_settings()
        dbg = settings.debug
        if len(context.scene.odc_teeth) and len(odcutils.tooth_selection(context)): 
            return True
        
        elif len(context.selected_objects) and dbg > 1:
            return True
        
        else:
            return False
        #1  the user has selected a random object and wants to do this thing to it
        
        #2 the obect is a restoration in a bridge
        
        #3 the object is a dx waxup going to be turned into a stent.
        #restoration exists and is in scene
        
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        teeth = odcutils.tooth_selection(context)
        
        
        [ob_sets, tool_sets, space_sets] = odcutils.scene_preserv(context, debug=dbg)
        
        if len(teeth):
            for tooth in teeth:
                if tooth.contour and tooth.contour in bpy.data.objects:
                    if tooth.rest_type == '1': continue #pontics!
                    
                    shell = bpy.data.objects[tooth.contour]
                    
                    #TODO....view axis vs z axis of object
                    if tooth.axis and tooth.axis in bpy.data.objects:
                        axis = bpy.data.objects[tooth.axis]
                        axis_mx = axis.matrix_world #TODO, insetion axis?
                        
                    else:
                        axis_mx = shell.matrix_world
                    
                    
                    #else:
                        #margin = None
                            
                    prep = crown_methods.prep_from_shell(context, shell, axis_mx, shoulder_width = self.margin_width, reduction = self.reduction, base_res = self.margin_width/2, margin_loop = None, debug = dbg)
                    prep.show_in_front = True
                    prep.name = tooth.name + "_GenPrep"
                    
                    mod = prep.modifiers.new('Margin','SHRINKWRAP')
                    mod.wrap_method = 'NEAREST_SURFACEPOINT'
                    mod.vertex_group = 'Margin'    
                    
                    if tooth.margin and tooth.margin in bpy.data.objects:
                        margin = bpy.data.objects[tooth.margin]
                        mod.target = margin
                    else:
                        mod.target = shell
                            
                    
                    if self.make_inside:
                        tooth.intaglio = prep.name
                       
                            
        elif len(context.selected_objects) and dbg > 1:
            for ob in context.selected_objects:
                if ob.type == 'MESH':
                    print('did we tr?')
                    prep = crown_methods.prep_from_shell(context, ob, ob.matrix_world, 
                                                         shoulder_width = self.margin_width, reduction = self.reduction, 
                                                         base_res = self.margin_width/2, margin_loop = None, debug = dbg)
                    prep.show_in_front = True
                    prep.name = ob.name + "_GenPrep"
                              
        odcutils.scene_reconstruct(context, ob_sets, tool_sets, space_sets, debug=dbg)
        odcutils.layer_management(context.scene.odc_teeth, debug = False)
        return {'FINISHED'}

class OPENDENTAL_OT_lattice_deform(bpy.types.Operator):
    '''
    Will add a lattice modifier to an object
    Use "Keep Shape" after modifying the lattice
    Make sure there aren't any existing lattice modifiers
    '''
    bl_idname = 'opendental.lattice_deform'
    bl_label = "Crown Lattice"
    bl_options = {'REGISTER','UNDO'}
    
    
    @classmethod
    def poll(cls, context):
        condition0 = context.mode == 'OBJECT'
        condition1 = context.object and context.object.type == 'MESH'
        
        return condition0 and condition1
    
    def execute(self, context):
        
        for ob in context.selected_objects:
            mods = [mod.type for mod in ob.modifiers]
            if 'LATTICE' in mods:
                self.report({'WARNING'}, 'There are lattice modifiers in' + ob.name +'.  Please apply or remove them') 
             
            else:
                if ob.type == 'MESH':
                    odcutils.bbox_to_lattice(context.scene, ob)
            
        
        return {'FINISHED'}
    
class OPENDENTAL_OT_pointic_from_crown(bpy.types.Operator):
    '''
    will close the bottom of and shape a pontic from a crown form.
    '''
    bl_idname = 'opendental.pontic_from_crown'
    bl_label = "Pontic From Crown"
    bl_options = {'REGISTER','UNDO'}
    
    p_types=['OVATE',
            'TISSUE',
            'PRESCULPT']
            
    p_enum = []
    for index, type in enumerate(p_types):
        p_enum.append((str(index), p_types[index], str(index)))
    p_type: bpy.props.EnumProperty(name="Pontic Type", description="How To Shape the pontic", items=p_enum, default='0')
    offset: bpy.props.FloatProperty(name="Tissue spacer", description="", default=1, min=-1, max=4, step=2, precision=1, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        settings = get_settings()
        dbg = settings.debug
        #modes we may want to use this.
        teeth = odcutils.tooth_selection(context)
        
        if len(teeth):
            return True
        
        elif len(context.selected_objects) and dbg > 1:
            return True
        
        else:
            return False
        #1  the user has selected a random object and wants to do this thing to it
        
        #2 the obect is a restoration in a bridge
        
        #3 the object is a dx waxup going to be turned into a stent.
        #restoration exists and is in scene
        
    def execute(self, context):
        settings = get_settings()
        dbg = settings.debug
        teeth = odcutils.tooth_selection(context)
        
        [ob_sets, tool_sets, space_sets] = odcutils.scene_preserv(context, debug=dbg)
        
        if len(teeth):
            for tooth in teeth:
                if tooth.contour and tooth.contour in bpy.data.objects:
                    shell = bpy.data.objects[tooth.contour]
                    tooth.rest_type = '1'  #change the rest type to pontic
                    crown_methods.pontificate(context, tooth, shell, self.p_types[int(self.p_type)], self.offset)
                       
                            
                        
        odcutils.scene_reconstruct(context, ob_sets, tool_sets, space_sets, debug=dbg)

        return {'FINISHED'}
    
class OPENDENTAL_OT_manufacture_restoration(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.manufacture_restoration'
    bl_label = "Manufacture Restoration"
    
    
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(odcutils.tooth_selection(context))

    def execute(self, context):
        import bmesh
        teeth = odcutils.tooth_selection(context)
        pairs = []
        for tooth in teeth:
            shell = context.scene.objects.get(tooth.restoration) or context.scene.objects.get(tooth.contour)
            inside = context.scene.objects.get(tooth.intaglio)
            if shell is None or inside is None or shell.type != 'MESH' or inside.type != 'MESH':
                self.report({'WARNING'}, 'Each selected tooth needs a mesh restoration and intaglio')
                return {'CANCELLED'}
            pairs.append((tooth, shell, inside))
        prepared = []
        try:
            for tooth, shell, inside in pairs:
                bm = bmesh.new()
                try:
                    for source in (shell, inside):
                        evaluated = source.evaluated_get(context.evaluated_depsgraph_get())
                        mesh = bpy.data.meshes.new_from_object(evaluated)
                        try:
                            mesh.transform(source.matrix_world)
                            bm.from_mesh(mesh)
                        finally:
                            bpy.data.meshes.remove(mesh)
                    boundary = [edge for edge in bm.edges if edge.is_boundary]
                    if not boundary:
                        raise ValueError('Restoration and intaglio need open margin loops')
                    bmesh.ops.bridge_loops(bm, edges=boundary)
                    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
                    if not bm.faces or not all(edge.is_manifold for edge in bm.edges):
                        raise ValueError('The margin loops could not be joined into a closed restoration')
                    mesh = bpy.data.meshes.new(tooth.name + '_Solid Crown')
                    bm.to_mesh(mesh)
                    prepared.append((tooth, mesh))
                finally:
                    bm.free()
        except (ValueError, RuntimeError) as error:
            for _, mesh in prepared:
                bpy.data.meshes.remove(mesh)
            self.report({'WARNING'}, str(error))
            return {'CANCELLED'}
        for selected in context.selected_objects:
            selected.select_set(False)
        for tooth, mesh in prepared:
            output = bpy.data.objects.new(tooth.name + '_Solid Crown', mesh)
            context.collection.objects.link(output)
            tooth.solid = output.name
            output.select_set(True)
            context.view_layer.objects.active = output
        return {'FINISHED'}
                
               
        '''
        #first weld all the very close verts at the resoution of the margin resolution
        bpy.ops.mesh.remove_doubles(mergedist = .025)
        bpy.ops.mesh.select_all(action = 'DESELECT')
        
        #select any remaining non manifold edges and try again after subdividing and using a larger merge
        bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]        
        bpy.ops.mesh.select_non_manifold()
        bpy.ops.mesh.subdivide()
        bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False] 
        bpy.ops.mesh.remove_doubles(mergedist = .03)
        
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.mesh.select_non_manifold()
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        sel_verts = [v.index for v in me.vertices if v.select]
        
        #if we still have non manifold, it's time to get desperate
        if len(sel_verts):
            
            #repeat
            bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]        
            bpy.ops.mesh.subdivide()
            bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
            bpy.ops.mesh.remove_doubles(mergedist = .05)
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.mesh.select_non_manifold()
        
        
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')        
        sel_verts = [v.index for v in me.vertices if v.select]
        
        if len(sel_verts):
            
            #repeat
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.mesh.select_non_manifold()
        
            bpy.ops.mesh.subdivide()
            bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
            bpy.ops.mesh.remove_doubles(mergedist = .1)
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.mesh.select_non_manifold()
            
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.mode_set(mode = 'EDIT')        
        sel_verts = [v.index for v in me.vertices if v.select]
        
        if len(sel_verts):
            
            #repeat
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.context.scene.tool_settings.mesh_select_mode = [False, True, False]
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.mesh.select_non_manifold()
        
            bpy.ops.mesh.subdivide()
            bpy.context.scene.tool_settings.mesh_select_mode = [True, False, False]
            bpy.ops.mesh.remove_doubles(mergedist = .2)
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.mesh.select_non_manifold()    
        
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.normals_make_consistent()
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for a in bpy.context.window.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        if not s.local_view:
                            bpy.ops.view3d.localview()
        '''        
      
class OPENDENTAL_OT_assess_contacts(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.asses_contacts'
    bl_label = "Asses Contacts"
    bl_options = {'REGISTER','UNDO'}
    
    min_d: bpy.props.FloatProperty(name="Touching", description="", default=0, min=0, max=1, step=5, precision=2, options={'ANIMATABLE'})
    max_d: bpy.props.FloatProperty(name="Max D", description="", default=.5, min=.1, max=2, step=5, precision=2, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context)
        if not teeth:
            return False
        tooth = teeth[0]
        condition_1 = tooth.mesial and tooth.mesial in bpy.data.objects #TODO: make this restoration when that property implemented
        condition_2 = tooth.distal and tooth.distal in bpy.data.objects
        condition_3 = tooth.opposing and tooth.opposing in bpy.data.objects
        condition_4 = tooth.contour and tooth.contour in bpy.data.objects
        condition_5 = tooth.restoration and tooth.restoration in bpy.data.objects
        return condition_1 or condition_2 or condition_3 or condition_4 or condition_5
            
    def execute(self, context):
        
        if self.max_d <= self.min_d:
            self.report({'WARNING'}, 'Maximum distance must exceed minimum distance')
            return {'CANCELLED'}
        changed = False
        for tooth in odcutils.tooth_selection(context):
            changed |= crown_methods.check_contacts(context, tooth, self.min_d, self.max_d)
        if not changed:
            self.report({'WARNING'}, 'Assign a restoration and a contact target first')
            return {'CANCELLED'}
        return {'FINISHED'}

class OPENDENTAL_OT_grind_contacts(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.grind_contacts'
    bl_label = "Grind Contacts"
    bl_options = {'REGISTER','UNDO'}
    
    mesial: bpy.props.BoolProperty(default = True)
    distal: bpy.props.BoolProperty(default = True)
    overlap: bpy.props.FloatProperty(name='Offset', default = .04)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not len(odcutils.tooth_selection(context)): return False
        tooth = odcutils.tooth_selection(context)[0]  #TODO: make this poll work for all selected teeth...
        condition_1 = tooth.mesial and tooth.mesial in bpy.data.objects #TODO: make this restoration when that property implemented
        condition_2 = tooth.distal and tooth.distal in bpy.data.objects
        condition_3 = tooth.opposing and tooth.opposing in bpy.data.objects
        condition_4 = tooth.contour and tooth.contour in bpy.data.objects
        condition_5 = tooth.restoration and tooth.restoration in bpy.data.objects
        
        
        return (condition_1 or condition_2 or condition_3) and (condition_4 or condition_5)
            
    def execute(self, context):
        from .contact_adjustment import adjust
        changed = False
        for tooth in odcutils.tooth_selection(context):
            if self.mesial:
                changed |= adjust(context, tooth, 'mesial', self.overlap)
            if self.distal:
                changed |= adjust(context, tooth, 'distal', self.overlap)
        if not changed:
            self.report({'WARNING'}, 'Assign a restoration and the requested contact target first')
            return {'CANCELLED'}
        return {'FINISHED'}

class OPENDENTAL_OT_grind_occlusion(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.grind_occlusion'
    bl_label = "Grind Occlusion"
    bl_options = {'REGISTER','UNDO'}
    

    overlap: bpy.props.FloatProperty(name='Offset', default = .05)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        if not len(odcutils.tooth_selection(context)): return False
        tooth = odcutils.tooth_selection(context)[0]  #TODO: make this poll work for all selected teeth...
        condition_3 = tooth.opposing and tooth.opposing in bpy.data.objects
        condition_4 = tooth.contour and tooth.contour in bpy.data.objects
        condition_5 = tooth.restoration and tooth.restoration in bpy.data.objects
        
        
        return condition_3 and (condition_4 or condition_5)
            
    def execute(self, context):
        from .contact_adjustment import adjust
        changed = False
        for tooth in odcutils.tooth_selection(context):
            changed |= adjust(context, tooth, 'opposing', self.overlap)
        if not changed:
            self.report({'WARNING'}, 'Assign a restoration and the requested contact target first')
            return {'CANCELLED'}
        return {'FINISHED'}

class OPENDENTAL_OT_teeth_arch(bpy.types.Operator):
    ''''''
    bl_idname = 'opendental.teeth_to_arch'
    bl_label = "Teeth to Arch"
    bl_options = {'REGISTER','UNDO'}
    
    arch_enum = []
    arch_types = ['MAX','MAND','LR','LL','LA','UR','UL','UA']
    for index, type in enumerate(arch_types):
        arch_enum.append((str(index), arch_types[index], str(index)))
    
    shift_enum = []
    shifts = ['BUCCAL', 'FOSSA', 'BODY']
    for index, type in enumerate(shifts):
        shift_enum.append((str(index), shifts[index], str(index)))
        
    arch_type: bpy.props.EnumProperty(
        name="Arch", 
        description="What Segment of the mouth does this curve represent?", 
        items=arch_enum, 
        default='0',
        options={'ANIMATABLE'})
    
    shift: bpy.props.EnumProperty(
        name="Arch", 
        description="What Segment of the mouth does this curve represent?", 
        items=shift_enum, 
        default='0',
        options={'ANIMATABLE'})
    
    mirror: bpy.props.BoolProperty(
        name = "Mirror", 
        description = "If checked, will mirror the arch and place teeth on contralateral side",
        default = False)
            
    reverse: bpy.props.BoolProperty(
        name = "Reverse", 
        description = "Check this if the teeth come in ordered the wrong way...not if they are flipped over",
        default = False)
            
    link: bpy.props.BoolProperty(
        name = "Link", 
        description = "If checked, sets the teeth as the restoration for working teeth",
        default = False)
        
    limit: bpy.props.BoolProperty(
        name = "Limit", 
        description = "If checked, only inserts teeth from the working teeth",
        default = False)
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        return context.object is not None and context.object.type == 'CURVE' and context.mode == 'OBJECT'
    
    def invoke(self,context,event):
        
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}       
    def execute(self, context):
        settings = get_settings()
        
        ob = context.object
        quad = self.arch_types[int(self.arch_type)]
        shift = self.shifts[int(self.shift)]
        settings = get_settings()
        dbg = settings.debug
        
        
        full_arch_methods.teeth_to_curve(context, ob, quad,settings.tooth_lib, 
                                    shift = shift,
                                    limit = self.limit,
                                    link = self.link,
                                    reverse = self.reverse,
                                    mirror = self.mirror, 
                                    debug = dbg)
 
        
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = ob
        ob.select_set(True)
        #go into weight paint mode?
        
        odcutils.layer_management(context.scene.odc_teeth, debug = True)
        return {'FINISHED'}

class OPENDENTAL_OT_occlusal_scheme_to_curve(bpy.types.Operator):
    '''
    applies an entire tooth library to a bezier curve
    '''
    bl_idname = 'opendental.occlusal_scheme'
    bl_label = "Arch Plan Occlusion"
    bl_options = {'REGISTER','UNDO'}
    
    
    mirror: bpy.props.BoolProperty(
        name = "Mirror", 
        description = "If checked, will mirror the arch and place teeth on contralateral side",
        default = False)
            
    reverse: bpy.props.BoolProperty(
        name = "Reverse", 
        description = "Check this if the teeth come in ordered the wrong way...not if they are flipped over",
        default = False)
            
    link: bpy.props.BoolProperty(
        name = "Link", 
        description = "If checked, sets the teeth as the restoration for working teeth",
        default = False)
        
    
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        return context.object is not None and context.object.type == 'CURVE' and context.mode == 'OBJECT'
    
    def invoke(self,context,event):
        
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}       
    def execute(self, context):
        settings = get_settings()
        
        ob = context.object
        settings = get_settings()

        full_arch_methods.occlusal_scheme_to_curve(context,
                                                   ob, 
                                                   settings.tooth_lib, 
                                                   teeth = [], 
                                                   link = self.link,
                                                   flip = False, 
                                                   reorient = True)
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = ob
        ob.select_set(True)
        #go into weight paint mode?
        
        odcutils.layer_management(context.scene.odc_teeth, debug = True)
        return {'FINISHED'}
    
       
def post_register2():
    #until we get access to addon prefs at register...:-( what we gonna do!?
    #bpy.utils.register_class(CBGetCrownForm)
    print('not needed')
           
def register():
    bpy.utils.register_class(OPENDENTAL_OT_set_master)
    bpy.utils.register_class(OPENDENTAL_OT_center_all_objects)
    bpy.utils.register_class(OPENDENTAL_OT_plan_restorations)
    bpy.utils.register_class(OPENDENTAL_OT_set_as_prep)
    bpy.utils.register_class(OPENDENTAL_OT_set_opposing)
    bpy.utils.register_class(OPENDENTAL_OT_set_mesial)
    bpy.utils.register_class(OPENDENTAL_OT_set_distal)
    
    bpy.utils.register_class(OPENDENTAL_OT_insertion_axis)
    bpy.utils.register_class(OPENDENTAL_OT_seat_to_margin)
    bpy.utils.register_class(OPENDENTAL_OT_calculate_inside)
    bpy.utils.register_class(OPENDENTAL_OT_prep_from_crown)
    bpy.utils.register_class(OPENDENTAL_OT_grind_contacts)
    bpy.utils.register_class(OPENDENTAL_OT_grind_occlusion)
    bpy.utils.register_class(OPENDENTAL_OT_crown_cervical_convergence)
    bpy.utils.register_class(OPENDENTAL_make_solid_restoration)
    bpy.utils.register_class(OPENDENTAL_OT_manufacture_restoration)
    bpy.utils.register_class(OPENDENTAL_OT_assess_contacts)
    bpy.utils.register_class(OPENDENTAL_OT_teeth_arch)
    bpy.utils.register_class(OPENDENTAL_OT_occlusal_scheme_to_curve)
    bpy.utils.register_class(ViewToZ)
    bpy.utils.register_class(CBGetCrownForm)
    bpy.utils.register_class(OPENDENTAL_OT_pointic_from_crown)
    bpy.utils.register_class(OPENDENTAL_OT_lattice_deform)
    
    #bpy.utils.register_module(__name__)
   
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_lattice_deform)
    bpy.utils.unregister_class(OPENDENTAL_OT_pointic_from_crown)
    bpy.utils.unregister_class(CBGetCrownForm)
    bpy.utils.unregister_class(ViewToZ)
    bpy.utils.unregister_class(OPENDENTAL_OT_occlusal_scheme_to_curve)
    bpy.utils.unregister_class(OPENDENTAL_OT_teeth_arch)
    bpy.utils.unregister_class(OPENDENTAL_OT_assess_contacts)
    bpy.utils.unregister_class(OPENDENTAL_OT_manufacture_restoration)
    bpy.utils.unregister_class(OPENDENTAL_make_solid_restoration)
    bpy.utils.unregister_class(OPENDENTAL_OT_crown_cervical_convergence)
    bpy.utils.unregister_class(OPENDENTAL_OT_grind_occlusion)
    bpy.utils.unregister_class(OPENDENTAL_OT_grind_contacts)
    bpy.utils.unregister_class(OPENDENTAL_OT_prep_from_crown)
    bpy.utils.unregister_class(OPENDENTAL_OT_calculate_inside)
    bpy.utils.unregister_class(OPENDENTAL_OT_seat_to_margin)
    bpy.utils.unregister_class(OPENDENTAL_OT_insertion_axis)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_distal)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_mesial)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_opposing)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_as_prep)
    bpy.utils.unregister_class(OPENDENTAL_OT_plan_restorations)
    bpy.utils.unregister_class(OPENDENTAL_OT_center_all_objects)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_master)

    
if __name__ == "__main__":
    register()