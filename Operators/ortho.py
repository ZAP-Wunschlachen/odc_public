'''
Created on Aug 18, 2016

@author: Patrick
some useful tidbits
http://blender.stackexchange.com/questions/44637/how-can-i-manually-calculate-bpy-types-posebone-matrix-using-blenders-python-ap?rq=1
http://blender.stackexchange.com/questions/1640/how-are-the-bones-assigned-to-the-vertex-groups-in-the-api?rq=1
http://blender.stackexchange.com/questions/46928/set-bone-constraints-via-python-api
http://blender.stackexchange.com/questions/40244/delete-bone-constraint-in-python
http://blender.stackexchange.com/questions/19602/child-of-constraint-set-inverse-with-python
http://blender.stackexchange.com/questions/28869/how-to-disable-loop-playback-of-animation
'''

#python imports :
import math

#Blender imports :
import bpy
import bmesh
from mathutils import Vector, Matrix, Color, Quaternion
from mathutils.bvhtree import BVHTree
from bpy_extras import view3d_utils

#Addon imports :
from ..Addon_utils.common_utilities import bversion
from ..Addon_utils.odcutils import get_settings, obj_list_from_lib, obj_from_lib

from .. import Operators

from ..Operators import common_drawing
from .. import Operators
from ..Operators import bgl_utils
from ..Operators.mesh_cut import cross_section_seed_ver1, bound_box, edge_loops_from_bmedges
from ..Operators.textbox import TextBox
from ..odcmenus import menu_utils as menu_utils
#TODO, better system for tooth # systems
TOOTH_NUMBERS = [11,12,13,14,15,16,17,18,
                 21,22,23,24,25,26,27,28,
                 31,32,33,34,35,36,37,38,
                 41,42,43,44,45,46,47,48]

def insertion_axis_draw_callback(self, context):
    self.help_box.draw()
    self.target_box.draw()
    bgl_utils.insertion_axis_callback(self,context)
 
def rapid_label_teeth_callback(self, context):
    self.help_box.draw()
    self.target_box.draw()
    
        
class OPENDENTAL_OT_add_bone_roots(bpy.types.Operator):
    """Set the axis and direction of the roots for crowns from view"""
    bl_idname = "opendental.add_bone_roots"
    bl_label = "Add bone roots"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.mode != 'OBJECT':
            return False
        else:
            return True
        
    def set_axis(self, context, event):
        
        if not self.target:
            return
        
        coord = (event.mouse_region_x, event.mouse_region_y)
        v3d = context.space_data
        rv3d = v3d.region_3d
        view_vector = view3d_utils.region_2d_to_vector_3d(context.region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        res, loc, no, ind, obj, mx = context.scene.ray_cast(context.evaluated_depsgraph_get(), ray_origin, view_vector)

        if not res or obj != self.target:
            return

        empty_name = self.target.name + 'root_empty'
        if empty_name in context.scene.objects:
            ob = context.scene.objects[empty_name]
            ob.empty_display_type = 'SINGLE_ARROW'
            ob.empty_display_size = 10
        else:
            ob = bpy.data.objects.new(empty_name, None)
            ob.empty_display_type = 'SINGLE_ARROW'
            ob.empty_display_size = 10
            context.collection.objects.link(ob)
            
        ob.location = loc
        if ob.rotation_mode != 'QUATERNION':
            ob.rotation_mode = 'QUATERNION'
            
        vrot = rv3d.view_rotation    
        ob.rotation_quaternion = vrot
                   
    def advance_next_prep(self,context):
        if self.target == None:
            self.target = self.units[0]
            
        ind = self.units.index(self.target)
        prev = int(math.fmod(ind + 1, len(self.units)))
        self.target = self.units[prev]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

        for obj in context.scene.objects:
            obj.select_set(False)
        
        self.target.select_set(True)
        context.space_data.region_3d.view_location = self.target.location
        
              
    def select_prev_unit(self,context):
        if self.target == None:
            self.target = self.units[0]
            
        ind = self.units.index(self.target)
        prev = int(math.fmod(ind - 1, len(self.units)))
        self.target = self.units[prev]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

        for obj in context.scene.objects:
            obj.select_set(False)
        
        self.target.select_set(True)
        context.space_data.region_3d.view_location = self.target.location
                       
    def update_selection(self,context):
        if not len(context.selected_objects):
            self.message = "Right Click to Select"
            self.target = None
            return
        
        if context.selected_objects[0] not in self.units:
            self.message = "Selected Object must be tooth"      
            self.target = None
            return

        self.target = context.selected_objects[0]
        self.message = "Set axis for %s" % self.target.name
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
        
    def empties_to_bones(self,context):
        bpy.ops.object.select_all(action = 'DESELECT')
        
        arm_ob = bpy.data.objects['Roots']
        arm_ob.hide_set(False)
        arm_ob.select_set(True)
        context.view_layer.objects.active = arm_ob
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        for ob in self.units:
            e = context.scene.objects.get(ob.name + 'root_empty')
            b = arm_ob.data.edit_bones.get(ob.name + 'root')
            
            if e != None and b != None:
                local = arm_ob.matrix_world.inverted() @ e.matrix_world
                Z = local.to_3x3() @ Vector((0,0,1))
                Z.normalize()
                b.tail = local.translation
                b.head = local.translation - 16 * Z
                b.align_roll(local.to_3x3() @ Vector((0,1,0)))
                b.head_radius = 1.5
                b.tail_radius = 2.5
                bpy.data.objects.remove(e, do_unlink=True)
            else:
                print('missing bone or empty')
                    
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
           
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
            self.set_axis(context, event)
            self.advance_next_prep(context)
            return 'main'
        
        elif event.type in {'DOWN_ARROW'} and event.value == 'PRESS':
            self.select_prev_unit(context)
            return 'main'
        
        elif event.type in {'UP_ARROW'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'main'
                    
        elif event.type in {'ESC'}:
            #keep track of and delete new objects? reset old transforms?
            return'cancel'
        
        elif event.type in {'RET'} and event.value == 'PRESS':
            self.empties_to_bones(context)
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
                self.restore_roots(context)
            #clean up callbacks
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'} if nmode == 'finish' else {'CANCELLED'}
        if nmode == 'pass':
            self.mode = 'main'
            return {'PASS_THROUGH'}
        
        if nmode: self.mode = nmode
        
        return {'RUNNING_MODAL'}
     
    def restore_roots(self, context):
        arm = context.scene.objects.get('Roots')
        if arm is not None:
            context.view_layer.objects.active = arm
            arm.select_set(True)
            if self._original_arm is None:
                data = arm.data
                bpy.data.objects.remove(arm, do_unlink=True)
                if data.users == 0:
                    bpy.data.armatures.remove(data)
            else:
                bpy.ops.object.mode_set(mode='EDIT')
                for bone in list(arm.data.edit_bones):
                    if bone.name not in self._original_bones:
                        arm.data.edit_bones.remove(bone)
                bpy.ops.object.mode_set(mode='OBJECT')
        for unit in self.units:
            name = unit.name + 'root_empty'
            axis = context.scene.objects.get(name)
            previous = self._original_axes.get(name)
            if axis is not None and previous is None:
                bpy.data.objects.remove(axis, do_unlink=True)
            elif axis is not None:
                axis.matrix_world, axis.empty_display_type, axis.empty_display_size = previous

    def invoke(self, context, event):
        settings = get_settings()
        dbg = settings.debug
        
        if not context.space_data or context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, 'Active space must be a View3d')
            return {'CANCELLED'}
        if context.space_data.region_3d.is_perspective:
            #context.space_data.region_3d.is_perspective = False
            bpy.ops.view3d.view_persportho()
            
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

        #gather all the teeth in the scene TODO, keep better track
        self.units = []
        
        for i in TOOTH_NUMBERS:
            ob = context.scene.objects.get(str(i))
            if ob != None and not ob.hide_get():
                self.units.append(ob)
            
        if not len(self.units):
            self.report({'ERROR'}, "There are no teeth in the scene!, Teeth must be named 2 digits eg 11 or 46")
            return {'CANCELLED'}
        
        self.target = self.units[0]
        self.message = "Set axis for %s" %self.target.name
            
        self._original_arm = context.scene.objects.get('Roots')
        self._original_bones = set(self._original_arm.data.bones.keys()) if self._original_arm else set()
        self._original_axes = {}
        for unit in self.units:
            axis = context.scene.objects.get(unit.name + 'root_empty')
            if axis is not None:
                self._original_axes[axis.name] = (axis.matrix_world.copy(), axis.empty_display_type, axis.empty_display_size)

        #check for an armature
        bpy.ops.object.select_all(action = 'DESELECT')
        if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode = 'OBJECT')
                
        if context.scene.objects.get('Roots'):
            root_arm = context.scene.objects.get('Roots')
            root_arm.select_set(True)
            root_arm.hide_set(False)
            context.view_layer.objects.active = root_arm
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            for ob in self.units:
                if ob.name + 'root' not in root_arm.data.bones:
                    bpy.ops.armature.bone_primitive_add(name = ob.name + 'root')
            
        else:
            root_data = bpy.data.armatures.new('Roots')
            root_arm = bpy.data.objects.new('Roots',root_data)
            context.collection.objects.link(root_arm)
            
            root_arm.select_set(True)
            context.view_layer.objects.active = root_arm
            bpy.ops.object.mode_set(mode = 'EDIT')
            
            for ob in self.units:
                bpy.ops.armature.bone_primitive_add(name = ob.name + 'root')
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        root_arm.select_set(False)
        self.units[0].select_set(True)
            
        help_txt = "Right click to select a tooth \n Align View with root, mes and distal\n Up Arrow and Dn Arrow to select different units \n Left click in middle of prep to set axis \n Enter to finish \n ESC to cancel"
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

class OPENDENTAL_OT_fast_label_teeth(bpy.types.Operator):
    """Label teeth by clicking on them"""
    bl_idname = "opendental.fast_label_teeth"
    bl_label = "Fast Label Teeth"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.mode != 'OBJECT':
            return False
        else:
            return True
        
    def set_axis(self, context, event):
        
            
        coord = (event.mouse_region_x, event.mouse_region_y)
        v3d = context.space_data
        rv3d = v3d.region_3d
        view_vector = view3d_utils.region_2d_to_vector_3d(context.region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(context.region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 1000)
        res, loc, no, ind, obj, mx = context.scene.ray_cast(context.evaluated_depsgraph_get(), ray_origin, view_vector)

        if res:
            existing = bpy.data.objects.get(str(self.target))
            if existing is not None and existing != obj:
                self.report({'WARNING'}, 'Tooth number %s is already assigned' % self.target)
                return False
            if obj not in self._labels_before:
                self._labels_before[obj] = (obj.name, obj.show_name)
            obj.name = str(self.target)
            for ob in context.view_layer.objects:
                ob.select_set(False)
            obj.select_set(True)
            obj.show_name = True
            context.view_layer.objects.active = obj
            return True
        else:
            return False       
    def advance_next_prep(self,context):
        
        def next_ind(n):
            if math.fmod(n, 10) < 7:
                return n + 1
            elif math.fmod(n, 10) == 7:
                if n == 17: return 21
                elif n== 27: return 31
                elif n == 37: return 41
                elif n == 47: return 11
           
            
        self.target = next_ind(self.target)
        self.message = "Click on tooth % i" % self.target
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()

              
    def select_prev_unit(self,context):
        
        
        def prev_ind(n):
            if math.fmod(n, 10) > 1:
                return n - 1
            elif math.fmod(n, 10) == 1:
                if n == 11: return 47
                elif n== 21: return 17
                elif n == 31: return 27
                elif n == 41: return 37
                
                
        self.target = prev_ind(self.target)
       
        self.message = "Click on tooth %i" % self.target
        self.target_box.raw_text = self.message
        self.target_box.format_and_wrap_text()
        self.target_box.fit_box_width_to_text_lines()
    
           
    def modal_main(self, context, event):
        # general navigation
        nmode = self.modal_nav(event)
        if nmode != '':
            return nmode  #stop here and tell parent modal to 'PASS_THROUGH'

        if event.type in {'RIGHTMOUSE'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'pass'
        
        elif event.type in {'LEFTMOUSE'} and event.value == 'PRESS':
            res = self.set_axis(context, event)
            if res:
                self.advance_next_prep(context)
            return 'main'
        
        elif event.type in {'DOWN_ARROW'} and event.value == 'PRESS':
            self.select_prev_unit(context)
            return 'main'
        
        elif event.type in {'UP_ARROW'} and event.value == 'PRESS':
            self.advance_next_prep(context)
            return 'main'
                    
        elif event.type in {'ESC'}:
            #keep track of and delete new objects? reset old transforms?
            return'cancel'
        
        elif event.type in {'RET'} and event.value == 'PRESS':
            #self.empties_to_bones(context)
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
                # Free all session labels before restoring names to avoid suffixes.
                for obj in self._labels_before:
                    obj.name = '__ODC_LABEL_RESTORE__'
                for obj, (name, show_name) in self._labels_before.items():
                    obj.name = name
                    obj.show_name = show_name
            else:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in self._labels_before:
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                    obj.select_set(False)
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
        
        if not context.space_data or context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, 'Active space must be a View3d')
            return {'CANCELLED'}
        if context.space_data.region_3d.is_perspective:
            #context.space_data.region_3d.is_perspective = False
            bpy.ops.view3d.view_persportho()
            
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

        #gather all the teeth in the scene TODO, keep better track

        
        
        
        self._labels_before = {}
        self.target = 11
        self.message = "Set axis for " + str(self.target)
            
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
                
        #check for an armature
        bpy.ops.object.select_all(action = 'DESELECT')
            
        help_txt = "Left click on the tooth indicated to label it. Right click skip a tooth \n Up or Dn Arrow to change label\n Enter to finish \n ESC to cancel"
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
        self._handle = bpy.types.SpaceView3D.draw_handler_add(rapid_label_teeth_callback, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}
    
class OPENDENTAL_OT_simple_ortho_base(bpy.types.Operator):
    """Simple ortho base with height 5 - 50mm """
    bl_idname = "opendental.simple_base"
    bl_label = "Simple model base"
    bl_options = {'REGISTER', 'UNDO'}
    
    base_height: bpy.props.FloatProperty(name = 'Base Height', default = 10, min = -50, max = 50,  description = 'Base height added in mm')
    
    @classmethod
    def poll(cls, context):
        if context.mode == "OBJECT" and context.object != None and context.object.type == 'MESH':
            return True
        else:
            return False
        
    def execute(self, context):
        
        bme = bmesh.new()
        bme.from_mesh(context.object.data)
        
        bme.verts.ensure_lookup_table()
        bme.edges.ensure_lookup_table()
        bme.faces.ensure_lookup_table()
        
        non_man_eds = [ed.index for ed in bme.edges if ed.is_boundary]
        loops = edge_loops_from_bmedges(bme, non_man_eds)
                
                
        closed_loops = [loop for loop in loops if len(loop) >= 4 and loop[0] == loop[-1]]
        if not closed_loops:
            bme.free()
            self.report({'WARNING'}, 'The model needs a closed boundary loop for a base')
            return {'CANCELLED'}
        biggest_loop = max(closed_loops, key=len)

        biggest_loop.pop()
        
        com = Vector((0,0,0))
        for vind in biggest_loop:
            com += bme.verts[vind].co
        com *= 1/len(biggest_loop)
        
        for vind in biggest_loop:
            bme.verts[vind].co[2] = com[2] + self.base_height
        
        bme.faces.new([bme.verts[vind] for vind in biggest_loop])
        bmesh.ops.recalc_face_normals(bme, faces = bme.faces)
        bme.to_mesh(context.object.data)
        bme.free()
        context.object.data.update()
        return {'FINISHED'}
    
class OPENDENTAL_OT_setup_root_parenting(bpy.types.Operator):
    """Prepares model for gingival simulation"""
    bl_idname = "opendental.set_roots_parents"
    bl_label = "Set Root Parents"
    bl_options = {'REGISTER','UNDO'}
    
    link_to_cast: bpy.props.BoolProperty(default = False)
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        
        #make sure we don't mess up any animations!
        context.scene.frame_set(0)
        
        max_ob = context.scene.objects.get('UpperJaw')
        man_ob = context.scene.objects.get('LowerJaw')
        arm_ob = context.scene.objects.get('Roots')
        
        if not self.link_to_cast:
            max_ob = None
            man_ob = None
            
        if arm_ob == None:
            self.report({'ERROR'}, "You need a 'Roots' armature, pease add one or see wiki")
            return {'CANCELLED'}
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
            
        context.view_layer.objects.active = arm_ob
        arm_ob.hide_set(False)
        arm_ob.select_set(True)
            
        #create a vertex group for every maxillary bone
        for bone in arm_ob.data.bones:
            if bone.name.startswith('1') or bone.name.startswith('2'):
                jaw_ob = max_ob
            else:
                jaw_ob = man_ob
                
            if jaw_ob != None:
            
                if bone.name not in jaw_ob.vertex_groups:
                    vg = jaw_ob.vertex_groups.new(name = bone.name)
                else:
                    vg = jaw_ob.vertex_groups[bone.name]
                #make all members, weight at 0    
                vg.add([i for i in range(0,len(jaw_ob.data.vertices))], 0, type = 'REPLACE')
                
            tooth = context.scene.objects.get(bone.name[0:2])
            if tooth == None: continue
            
            if jaw_ob != None:
                if tooth.name+'_prox' in jaw_ob.modifiers:
                    mod = jaw_ob.modifiers.get(tooth.name + '_prox')
                else:
                    mod = jaw_ob.modifiers.new(tooth.name + '_prox', 'VERTEX_WEIGHT_PROXIMITY')
                    
                mod.target = tooth
                mod.vertex_group = bone.name
                mod.proximity_mode = 'GEOMETRY'
                mod.min_dist = 10
                mod.max_dist = 0
                mod.falloff_type = 'SHARP'
                mod.show_expanded = False
            
            pbone = arm_ob.pose.bones[bone.name]
            
            if 'Child Of' in pbone.constraints:
                cons = pbone.constraints['Child Of']
                cons.target = tooth
            else:
                cons = pbone.constraints.new(type = 'CHILD_OF')
                cons.target = tooth
                    
                arm_ob.data.bones.active = pbone.bone
                pbone.select = True
                bpy.ops.object.mode_set(mode = 'POSE')
                with context.temp_override(constraint=cons):
                    bpy.ops.constraint.childof_set_inverse(constraint=cons.name, owner='BONE')
                bpy.ops.object.mode_set(mode = 'OBJECT')
            
        if max_ob != None:
            if 'Armature' in max_ob.modifiers:
                mod = max_ob.modifiers['Armature']
                max_ob.modifiers.remove(mod)
            mod = max_ob.modifiers.new('Armature', type = 'ARMATURE')
            mod.object = arm_ob
            mod.use_vertex_groups = True
        
        if man_ob != None:
            if 'Armature' in man_ob.modifiers:
                mod = man_ob.modifiers['Armature']
                man_ob.modifiers.remove(mod)
            mod = man_ob.modifiers.new('Armature', type = 'ARMATURE')
            mod.object = arm_ob
            mod.use_vertex_groups = True       
        return {'FINISHED'}

class OPENDENTAL_OT_adjust_roots(bpy.types.Operator):
    """Adjust root bones in edit_mode before moving teeth"""
    bl_idname = "opendental.adjust_bone_roots"
    bl_label = "Adjust Roots"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        arm = context.view_layer.objects.get('Roots')
        return arm is not None and arm.type == 'ARMATURE' and context.mode in {'OBJECT', 'EDIT_ARMATURE'}

    def execute(self, context):
        context.scene.frame_set(0)
        arm = context.view_layer.objects.get('Roots')
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        arm.hide_set(False)
        arm.select_set(True)
        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class OPENDENTAL_OT_set_treatment_keyframe(bpy.types.Operator):
    """Sets a treatment stage at this frame"""
    bl_idname = "opendental.set_treatment_keyframe"
    bl_label = "Set Treatment Keyframe"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):



        #find obs
        obs = []
        for num in TOOTH_NUMBERS:
            ob = context.view_layer.objects.get(str(num))
            if ob != None and ob.visible_get(view_layer=context.view_layer):
                obs.append(ob)
                continue

            for ob in context.view_layer.objects:
                if ob.name.startswith(str(num)) and ob.visible_get(view_layer=context.view_layer):
                    obs.append(ob)

        if not obs:
            self.report({'WARNING'}, 'No visible teeth found for treatment keyframes')
            return {'CANCELLED'}
        for ob in obs:
            ob.keyframe_insert(data_path='location', group='Treatment')
            rotation_path = {'QUATERNION': 'rotation_quaternion',
                             'AXIS_ANGLE': 'rotation_axis_angle'}.get(ob.rotation_mode, 'rotation_euler')
            ob.keyframe_insert(data_path=rotation_path, group='Treatment')
        return {'FINISHED'}

class OPENDENTAL_OT_maxillary_view(bpy.types.Operator):
    '''Will hide all non maxillary objects'''
    bl_idname = "opendental.show_max_teeth"
    bl_label = "Show Maxillary Teeth"
    bl_options = {'REGISTER','UNDO'}

    show_master: bpy.props.BoolProperty(default = False)

    def execute(self, context):
        for ob in context.view_layer.objects:
            if ob.name.startswith('1') or ob.name.startswith('2'):
                ob.hide_set(False)

            elif ('upper' in ob.name or 'Upper' in ob.name) and self.show_master:
                ob.hide_set(False)
            elif ('maxil' in ob.name or 'Maxil' in ob.name) and self.show_master:
                ob.hide_set(False)
            else:
                ob.hide_set(True)
        return {'FINISHED'}

class OPENDENTAL_OT_mandibular_view(bpy.types.Operator):
    '''Will hide all non mandibuar objects'''
    bl_idname = "opendental.show_man_teeth"
    bl_label = "Show Mandibular Teeth"
    bl_options = {'REGISTER','UNDO'}

    show_master: bpy.props.BoolProperty(default = False)

    def execute(self, context):
        for ob in context.view_layer.objects:
            if ob.name.startswith('3') or ob.name.startswith('4'):
                ob.hide_set(False)

            elif ('lower' in ob.name or 'Lower' in ob.name) and self.show_master:
                ob.hide_set(False)
            elif ('mand' in ob.name or 'Mand' in ob.name) and self.show_master:
                ob.hide_set(False)
            else:
                ob.hide_set(True)
        return {'FINISHED'}

class OPENDENTAL_OT_right_view(bpy.types.Operator):
    '''Will hide all non right tooth objects'''
    bl_idname = "opendental.show_right_teeth"
    bl_label = "Show Right Teeth"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        for ob in context.view_layer.objects:
            if ob.name.startswith('1') or ob.name.startswith('4'):
                ob.hide_set(False)
            else:
                ob.hide_set(True)
        return {'FINISHED'}


class OPENDENTAL_OT_left_view(bpy.types.Operator):
    '''Will hide all non left toot objects'''
    bl_idname = "opendental.show_left_teeth"
    bl_label = "Show Left Teeth"
    bl_options = {'REGISTER','UNDO'}

    def execute(self, context):
        for ob in context.view_layer.objects:
            if ob.name.startswith('2') or ob.name.startswith('3'):
                ob.hide_set(False)
            else:
                ob.hide_set(True)
        return {'FINISHED'}

class OPENDENTAL_OT_physics_scene(bpy.types.Operator):
    """Copy selected meshes into a separate physics scene."""
    bl_idname = "opendental.add_physics_scene"
    bl_label = "Physics Scene for Simulation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.window is not None and context.mode == 'OBJECT'
                and context.scene.name != 'Physics Sim'
                and any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        source_scene = context.scene
        sources = [(obj, obj.matrix_world.copy()) for obj in context.selected_objects if obj.type == 'MESH']
        scene = bpy.data.scenes.get('Physics Sim') or bpy.data.scenes.new('Physics Sim')
        # Remove only our previous copies; unrelated scene objects are preserved.
        physics_collection = scene.rigidbody_world.collection if scene.rigidbody_world else None
        for obj in sorted(scene.objects, key=lambda item: item.type == 'MESH'):
            if obj.get('odc_physics_copy'):
                for collection in list(obj.users_collection):
                    if (collection == scene.collection or collection == physics_collection
                            or collection in scene.collection.children_recursive):
                        collection.objects.unlink(obj)
                if obj.users == 0:
                    bpy.data.objects.remove(obj)
        scene['odc_source_scene'] = source_scene
        copies = []
        for source, world in sources:
            obj = source.copy()
            obj['odc_physics_copy'] = True
            obj['odc_source_object'] = source
            obj.parent = None
            obj.constraints.clear()
            obj.animation_data_clear()
            obj.matrix_world = world
            scene.collection.objects.link(obj)
            copies.append(obj)
        context.window.scene = scene
        scene.frame_set(0)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in copies:
            obj.hide_set(False)
            obj.select_set(True)
        context.view_layer.objects.active = copies[0]
        return {'FINISHED'}

class OPENDENTAL_OT_physics_setup(bpy.types.Operator):
    '''Make objects rigid bodies for physics simulation'''
    bl_idname = "opendental.physics_sim_setup"
    bl_label = "Setup Physics for Simulation"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def execute(self, context):

        context.scene.use_gravity = False
        #clear existing rigidbody
        if context.scene.rigidbody_world:
            bpy.ops.rigidbody.world_remove()
            bpy.ops.rigidbody.world_add()
        else:
            bpy.ops.rigidbody.world_add()

        #potentially adjust these values
        rbw = context.scene.rigidbody_world
        rbw.solver_iterations = 15
        rbw.point_cache.frame_end = 500 #more time for sim.
        context.scene.frame_end = 500
        context.scene.frame_set(0)

        obs = [ob for ob in context.selected_objects if ob.type == 'MESH' and not ob.get('odc_movement_reference')]
        bpy.ops.object.select_all(action = 'DESELECT')

        for ob in obs:
            context.view_layer.objects.active = ob
            ob.select_set(True)
            if not ob.rigid_body:
                bpy.ops.rigidbody.object_add()
            else:
                bpy.ops.rigidbody.object_remove()
                bpy.ops.rigidbody.object_add()


            ob.lock_rotations_4d = True
            ob.lock_rotation[0] = True
            ob.lock_rotation[1] = True
            ob.lock_rotation[2] = True
            ob.lock_rotation_w = True

            rb = ob.rigid_body
            rb.friction = .1
            rb.use_margin = True
            rb.collision_margin = .05
            rb.collision_shape = 'CONVEX_HULL'
            rb.restitution = 0
            rb.linear_damping = 1
            rb.angular_damping = .9
            rb.mass = 3
            ob.select_set(False)

        return {'FINISHED'}

@bpy.app.handlers.persistent
def update_tooth_forcefields(scene, depsgraph=None):
    """Use the preceding evaluated pose without a dependency on the rigid-body solve.

    Parenting an effector to its own simulated body introduces a depsgraph cycle.
    Update before each frame instead; rewinding to the cache start restores the
    body's input transform. Sequential playback supplies the previous frame pose.
    """
    if not scene.rigidbody_world:
        return
    start = scene.rigidbody_world.point_cache.frame_start
    graph = scene.view_layers[0].depsgraph
    for field in scene.objects:
        if not field.get('odc_tooth_forcefield'):
            continue
        body = field.get('odc_forcefield_body')
        if not isinstance(body, bpy.types.Object) or body.name not in scene.objects:
            # An orphan must not attract the surviving teeth from its last pose.
            if field.field is not None and field.field.type != 'NONE':
                field.field.type = 'NONE'
            continue
        world = (body.matrix_world if scene.frame_current <= start
                 else body.evaluated_get(graph).matrix_world)
        field.matrix_world = world.copy()


class OPENDENTAL_OT_add_forcefields(bpy.types.Operator):
    '''Add forcefields to selected objects'''
    bl_idname = "opendental.add_forcefields"
    bl_label = "Add Forcefields All"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        bpy.ops.object.select_all(action = 'DESELECT')

        for ob in obs:
            if ob.type != 'MESH' or ob.get('odc_movement_reference'): continue
            empty = next((item for item in context.scene.objects
                          if item.get('odc_tooth_forcefield')
                          and (item.get('odc_forcefield_body') == ob or item.parent == ob)), None)
            if empty is None:
                empty = bpy.data.objects.new(ob.name[0:2] + 'force', None)
                context.scene.collection.objects.link(empty)
                empty['odc_tooth_forcefield'] = True
                empty['odc_physics_copy'] = True
            context.view_layer.objects.active = empty
            empty.parent = None
            empty['odc_forcefield_body'] = ob
            empty.matrix_world = ob.matrix_world.copy()
            empty.select_set(True)
            if empty.field is None or empty.field.type == 'NONE':
                bpy.ops.object.forcefield_toggle()
            empty.field.strength = -1000
            empty.field.falloff_type = 'SPHERE'
            empty.field.use_radial_min = True
            empty.field.use_radial_max = True
            empty.field.radial_min = ob.dimensions[0]/1.8
            empty.field.radial_max = 10
            # Tag effector relations after forcefield_toggle creates the settings.
            empty.field.type = 'FORCE'
            empty.select_set(False)

        context.view_layer.update()
        return {'FINISHED'}

class OPENDENTAL_OT_limit_movements(bpy.types.Operator):
    '''Add constraints to limit movements in simulation'''
    bl_idname = "opendental.limit_physics_movements"
    bl_label = "Limit Physics Movements"
    bl_options = {'REGISTER','UNDO'}

    buc_ling: bpy.props.FloatProperty(name = 'Facial/Lingual', default = 2)
    mes_dis: bpy.props.FloatProperty(name = 'Mesial/Distal', default = 2)
    occlusal: bpy.props.FloatProperty(name = 'Occluso/Gingival', default = 0)

    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=300)


    def execute(self, context):

        context.scene.frame_set(0)
        obs = [ob for ob in context.selected_objects]

        #bpy.ops.object.select_all(action = 'DESELECT')

        for ob in obs:
            if ob.type != 'MESH' or ob.get('odc_movement_reference'): continue

            limit = ob.constraints.get('Limit Location')
            if limit is None:
                limit = ob.constraints.new('LIMIT_LOCATION')
            reference = limit.space_object if limit.owner_space == 'CUSTOM' else None
            previous_reference = reference
            upgrade = (reference is not None and reference.get('odc_movement_reference')
                       and reference.type == 'EMPTY' and ob.rigid_body is not None)
            if reference is None or not reference.get('odc_movement_reference') or upgrade:
                world = reference.matrix_world.copy() if upgrade else ob.matrix_world.copy()
                reference_mesh = None
                if ob.rigid_body is not None:
                    reference_mesh = bpy.data.meshes.new(ob.name + ' Movement Anchor')
                    reference_mesh.from_pydata([(0, 0, 0), (.001, 0, 0), (0, .001, 0), (0, 0, .001)],
                                              [], [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
                reference = bpy.data.objects.new(ob.name + ' Movement Axes', reference_mesh)
                reference['odc_movement_reference'] = True
                reference['odc_physics_copy'] = True
                context.scene.collection.objects.link(reference)
                reference.matrix_world = Matrix.LocRotScale(world.translation, world.to_quaternion(), Vector((1,1,1)))
                reference.hide_render = True
                reference.hide_set(True)
            limit.space_object = reference
            if upgrade:
                users = bpy.data.user_map(subset={previous_reference}).get(previous_reference, set())
                if all(isinstance(user, (bpy.types.Collection, bpy.types.Scene)) for user in users):
                    bpy.data.objects.remove(previous_reference, do_unlink=True)

            limit.use_min_x = True
            limit.use_min_y = True
            limit.use_min_z = True
            limit.use_max_x = True
            limit.use_max_y = True
            limit.use_max_z = True
            limit.use_transform_limit = False

            limit.owner_space = 'CUSTOM'
            limit.min_x, limit.max_x = -self.mes_dis, self.mes_dis
            limit.min_y, limit.max_y = -self.buc_ling, self.buc_ling
            limit.min_z, limit.max_z = -self.occlusal, self.occlusal

            # Bullet ignores object transform constraints on active bodies.
            # Use the same stationary local axes as a world-anchored joint.
            if ob.rigid_body is not None:
                if reference.rigid_body_constraint is None:
                    active = context.view_layer.objects.active
                    selected = list(context.selected_objects)
                    for selected_object in selected:
                        selected_object.select_set(False)
                    reference.hide_set(False)
                    reference.select_set(True)
                    context.view_layer.objects.active = reference
                    try:
                        bpy.ops.rigidbody.object_add(type='PASSIVE')
                        reference.rigid_body.collision_collections = (False,) * 20
                        bpy.ops.rigidbody.constraint_add(type='GENERIC')
                    finally:
                        reference.select_set(False)
                        reference.hide_set(True)
                        for selected_object in selected:
                            selected_object.select_set(True)
                        context.view_layer.objects.active = active
                reference.hide_set(False)
                reference.display_type = 'WIRE'
                joint = reference.rigid_body_constraint
                joint.object1 = ob
                joint.object2 = reference
                joint.enabled = True
                for axis, distance in (('x', self.mes_dis), ('y', self.buc_ling), ('z', self.occlusal)):
                    setattr(joint, 'use_limit_lin_' + axis, True)
                    setattr(joint, 'limit_lin_' + axis + '_lower', -distance)
                    setattr(joint, 'limit_lin_' + axis + '_upper', distance)
        return {'FINISHED'}

class OPENDENTAL_OT_unlimit_movements(bpy.types.Operator):
    '''Removes limitations'''
    bl_idname = "opendental.unlimit_physics_movements"
    bl_label = "Unlimit Physics Movements"
    bl_options = {'REGISTER','UNDO'}

    buc_ling: bpy.props.FloatProperty(name = 'Facial/Lingual', default = 2)
    mes_dis: bpy.props.FloatProperty(name = 'Mesial/Distal', default = 2)
    occlusal: bpy.props.FloatProperty(name = 'Occluso/Gingival', default = 0)

    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    def invoke(self,context,event):
        return context.window_manager.invoke_props_dialog(self, width=300)


    def execute(self, context):

        context.scene.frame_set(0)
        obs = [ob for ob in context.selected_objects]

        #bpy.ops.object.select_all(action = 'DESELECT')

        for ob in obs:

            if ob.type != 'MESH' or ob.get('odc_movement_reference'): continue

            if 'Limit Location' in ob.constraints:
                limit = ob.constraints['Limit Location']
                reference = limit.space_object
                ob.constraints.remove(limit)
                if reference and reference.get('odc_movement_reference'):
                    if reference.rigid_body_constraint is not None:
                        reference.rigid_body_constraint.enabled = False
                        reference.rigid_body_constraint.object2 = None
                    users = bpy.data.user_map(subset={reference}).get(reference, set())
                    if all(isinstance(user, (bpy.types.Collection, bpy.types.Scene)) for user in users):
                        mesh = reference.data
                        bpy.data.objects.remove(reference, do_unlink=True)
                        if mesh is not None and mesh.users == 0:
                            bpy.data.meshes.remove(mesh)
        return {'FINISHED'}

class OPENDENTAL_OT_lock_movements(bpy.types.Operator):
    '''Prevent Selected Teeth from moving in any direction '''
    bl_idname = "opendental.lock_physics_movements"
    bl_label = "Lock Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        
        for ob in obs:
            if ob.type != 'MESH' or ob.get('odc_movement_reference'): continue
            ob.lock_location[0], ob.lock_location[1], ob.lock_location[2] = True, True, True

        return {'FINISHED'}    

class OPENDENTAL_OT_unlock_movements(bpy.types.Operator):
    '''Allows Selected Teeth to move in any direction '''
    bl_idname = "opendental.unlock_physics_movements"
    bl_label = "Unlock Physics Movements"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        obs = [ob for ob in context.selected_objects]
        
        for ob in obs:
            if ob.type != 'MESH' or ob.get('odc_movement_reference'): continue
            ob.lock_location[0], ob.lock_location[1], ob.lock_location[2] = False, False, False

        return {'FINISHED'} 

class OPENDENTAL_OT_keep_simulation_result(bpy.types.Operator):
    '''Kepe results of simulation at current frame, and apply back to design scene '''
    bl_idname = "opendental.keep_simulation_results"
    bl_label = "Keep Simulation Results"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(self,context):
        if context.scene.name == 'Physics Sim':
            return True
        else:
            return False
    
    def execute(self, context):
        scene = context.scene.get('odc_source_scene')
        if not isinstance(scene, bpy.types.Scene):
            self.report({'WARNING'}, 'The simulation has no recorded source scene')
            return {'CANCELLED'}
        depsgraph = context.evaluated_depsgraph_get()
        results = []
        for obj in context.scene.objects:
            source = obj.get('odc_source_object')
            if isinstance(source, bpy.types.Object) and source.name in scene.objects:
                results.append((source, obj.evaluated_get(depsgraph).matrix_world.copy()))
        if not results:
            self.report({'WARNING'}, 'No surviving source objects were found')
            return {'CANCELLED'}
        context.window.scene = scene
        for source, world in results:
            source.matrix_world = world
        context.view_layer.update()
        return {'FINISHED'}


def register():
    if update_tooth_forcefields not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(update_tooth_forcefields)
    bpy.utils.register_class(OPENDENTAL_OT_mandibular_view)
    bpy.utils.register_class(OPENDENTAL_OT_maxillary_view)
    bpy.utils.register_class(OPENDENTAL_OT_left_view)
    bpy.utils.register_class(OPENDENTAL_OT_right_view)
    bpy.utils.register_class(OPENDENTAL_OT_add_bone_roots)
    bpy.utils.register_class(OPENDENTAL_OT_fast_label_teeth)
    bpy.utils.register_class(OPENDENTAL_OT_adjust_roots)
    bpy.utils.register_class(OPENDENTAL_OT_setup_root_parenting)
    bpy.utils.register_class(OPENDENTAL_OT_set_treatment_keyframe)
    bpy.utils.register_class(OPENDENTAL_OT_keep_simulation_result)
    bpy.utils.register_class(OPENDENTAL_OT_unlock_movements)
    bpy.utils.register_class(OPENDENTAL_OT_lock_movements)
    bpy.utils.register_class(OPENDENTAL_OT_limit_movements)
    bpy.utils.register_class(OPENDENTAL_OT_unlimit_movements)
    bpy.utils.register_class(OPENDENTAL_OT_add_forcefields)
    bpy.utils.register_class(OPENDENTAL_OT_physics_setup)
    bpy.utils.register_class(OPENDENTAL_OT_physics_scene)
    bpy.utils.register_class(OPENDENTAL_OT_simple_ortho_base)
    
    
    
def unregister():
    if update_tooth_forcefields in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(update_tooth_forcefields)
    bpy.utils.unregister_class(OPENDENTAL_OT_simple_ortho_base)
    bpy.utils.unregister_class(OPENDENTAL_OT_physics_scene)
    bpy.utils.unregister_class(OPENDENTAL_OT_physics_setup)
    bpy.utils.unregister_class(OPENDENTAL_OT_add_forcefields)
    bpy.utils.unregister_class(OPENDENTAL_OT_unlimit_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_limit_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_lock_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_unlock_movements)
    bpy.utils.unregister_class(OPENDENTAL_OT_keep_simulation_result)
    bpy.utils.unregister_class(OPENDENTAL_OT_set_treatment_keyframe)
    bpy.utils.unregister_class(OPENDENTAL_OT_setup_root_parenting)
    bpy.utils.unregister_class(OPENDENTAL_OT_adjust_roots)
    bpy.utils.unregister_class(OPENDENTAL_OT_fast_label_teeth)
    bpy.utils.unregister_class(OPENDENTAL_OT_add_bone_roots)
    bpy.utils.unregister_class(OPENDENTAL_OT_right_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_left_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_maxillary_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_mandibular_view)
    
if __name__ == "__main__":
    register()