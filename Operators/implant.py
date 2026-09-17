'''
Created on Nov 20, 2012
#test commit tracker
Implant functions and operators

Some License might be in the source directory. Summary: don't be an asshole, but do whatever you want with this code
Author: Patrick Moore:  patrick.moore.bu@gmail.com
'''

#Python imports :
import os

#Blender imports :
import bpy
from mathutils import Vector, Matrix

#Addon imports : 
from .. import Addon_utils
from ..Addon_utils import odcutils
from ..Addon_utils.odcutils import get_settings
from .. import Operators
from ..Operators import implant_utils
#Global variables (should they be?)
global lib_imp
global lib_imp_enum
lib_implants = []
lib_imp_enum = []

class OPENDENTAL_OT_implant_slice_view(bpy.types.Operator):
    '''Gives 3 orthogonal slices and one obliqe slice'''
    bl_idname = "opendental.slice_view"
    bl_label = "Slice View"
    bl_options = {'REGISTER','UNDO'}
    
    thickness: bpy.props.FloatProperty(name="Slice Thickness", description="view slice thickenss", default=1, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D' and context.region is not None and context.region.type == 'WINDOW'

    def execute(self,context):
        
        view = bpy.context.space_data
        
        view.clip_end = view.clip_start + self.thickness
        
        if not view.region_quadviews:
            bpy.ops.screen.region_quadview()
            view.lock_cursor = True
                           
        return{'FINISHED'}
  
class OPENDENTAL_OT_implant_normal_view(bpy.types.Operator):
    '''Returns view from quad view to normal'''
    bl_idname = "opendental.normal_view"
    bl_label = "Normal View"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D' and context.region is not None and context.region.type == 'WINDOW'

    def execute(self,context):
        
        view = bpy.context.space_data        
        view.clip_end = view.clip_start + 10000
        
        
        if view.region_quadviews:
            bpy.ops.screen.region_quadview()
            view.lock_cursor = False
                           
        return{'FINISHED'}
        
class OPENDENTAL_OT_implant_from_contour(bpy.types.Operator):
    '''
    Places an implant down the axis of a already planned crown..
    '''
    bl_idname = 'opendental.implant_from_crown'
    bl_label = "Place Implants from Crowns"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "imp"
    
    
    _enum_items = []

    def item_cb(self, context):
        type(self)._enum_items = [(name, name, '') for name in
            odcutils.obj_list_from_lib(get_settings().imp_lib, exclude='_')]
        return type(self)._enum_items

    objs: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    imp: bpy.props.EnumProperty(name="Implant Library Objects",
                                 description="A List of the tooth library", 
                                 items=item_cb)
    depth: bpy.props.IntProperty(name = 'Depth', description = "milimeters below CEJ to place implant", default = 5)
    hardware: bpy.props.BoolProperty(name="Include Hardware", default=True)
    @classmethod
    def poll(cls, context):
        #restoration exists and is in scene
        teeth = odcutils.tooth_selection(context) #TODO:...make this poll work for all selected teeth...
        condition = False
        if teeth and len(teeth)>0:
            condition = True
             
        return condition
    
    def invoke(self,context,event):
        self.objs.clear()
        #here we grab the asset library from the addon prefs
        settings = get_settings()
        libpath = settings.imp_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = '_')
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
        #context.window_manager.invoke_search_popup(self.ob_list)
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self,context):
        settings = get_settings()
        dbg = settings.debug
        #TODO: Scene Preservation recording
        teeth = odcutils.tooth_selection(context)
        sce = bpy.context.scene
        
        
        for tooth in teeth:
            
            #see if there is a corresponding implant
            if tooth.name in sce.odc_implants:
                contour = bpy.data.objects.get(tooth.contour)
                Z  = Vector((0,0,-1))
                if contour:
                    
                    if tooth.axis:
                        Axis = bpy.data.objects.get(tooth.axis)
                        if Axis:
                            neg_z = Axis.matrix_world.to_quaternion() @ Z
                            rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                        else:
                            neg_z = contour.matrix_world.to_quaternion() @ Z
                            rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                    else:
                        neg_z = contour.matrix_world.to_quaternion() @ Z
                        rot_diff = odcutils.rot_between_vecs(Vector((0,0,1)), neg_z)
                    mx = contour.matrix_world
                    x = mx[0][3]
                    y = mx[1][3]
                    z = mx[2][3]
                    
                    #CEJ Location
                    new_loc = odcutils.box_feature_locations(contour, Vector((0,0,-1)))
                    
                    Imp = implant_utils.place_implant(context, sce.odc_implants[tooth.name], new_loc, rot_diff, self.imp, hardware = self.hardware)
                    
                    #reposition platform below CEJ
                    context.view_layer.update()
                    world_mx = Imp.matrix_world.copy()
                    length = max(v[2] for v in Imp.bound_box)-min(v[2] for v in Imp.bound_box)
                    delta = (length + self.depth) * (world_mx.to_quaternion() @ Vector((0,0,1)))
                    
                    world_mx[0][3] += delta[0]
                    world_mx[1][3] += delta[1]
                    world_mx[2][3] += delta[2]
                    Imp.matrix_world = world_mx
                    context.view_layer.update()
        
        odcutils.layer_management(sce.odc_implants, debug = False)
        
        return {'FINISHED'}
        
class OPENDENTAL_OT_place_implant(bpy.types.Operator):
    '''Places Implant or swaps existing implant with new implant of your choice'''
    bl_idname = "opendental.place_implant"
    bl_label = "Place Implant"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "imp"

    _enum_items = []

    def item_cb(self, context):
        type(self)._enum_items = [(name, name, '') for name in
            odcutils.obj_list_from_lib(get_settings().imp_lib, exclude='_')]
        return type(self)._enum_items

    objs: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    imp: bpy.props.EnumProperty(name="Implant Library Objects",
                                 description="A List of the tooth library", 
                                 items=item_cb)
    hardware: bpy.props.BoolProperty(name="Include Hardware", default=False)
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and hasattr(context.scene, 'odc_implants')
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.imp_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = '_')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        spaces = odcutils.implant_selection(context)
        if not spaces:
            implant = odcutils.obj_from_lib(settings.imp_lib, self.imp)
            context.collection.objects.link(implant)
            implant.matrix_world = Matrix.Translation(context.scene.cursor.location)
            return {'FINISHED'}
        for space in spaces:
            old = bpy.data.objects.get(space.implant)
            if old is None:
                orientation = Matrix.Identity(4).to_quaternion()
                platform = context.scene.cursor.location.copy()
            else:
                orientation = old.matrix_world.to_quaternion()
                length = max(v[2] for v in old.bound_box)-min(v[2] for v in old.bound_box)
                platform = old.matrix_world @ Vector((0, 0, -length))
            implant = implant_utils.place_implant(context, space, platform, orientation,
                                                  self.imp, hardware=self.hardware)
            context.view_layer.update()
            length = max(v[2] for v in implant.bound_box)-min(v[2] for v in implant.bound_box)
            matrix = implant.matrix_world.copy()
            matrix.translation = platform + orientation @ Vector((0, 0, length))
            implant.matrix_world = matrix
            context.view_layer.update()
        odcutils.layer_management(context.scene.odc_implants, debug=settings.debug)
        return {'FINISHED'}

class OPENDENTAL_OT_place_sleeve(bpy.types.Operator):
    '''Places or replace guide sleeve at specified depth'''
    bl_idname = "opendental.place_guide_sleeve"
    bl_label = "Place Sleeve"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "drill"

    _enum_items = []

    def item_cb(self, context):
        type(self)._enum_items = [(name, name, '') for name in
            odcutils.obj_list_from_lib(get_settings().drill_lib, exclude='Drill')]
        return type(self)._enum_items

    objs: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    drill: bpy.props.EnumProperty(name="Drill/Sleeve Library",
                                 description="A List of the items library", 
                                 items=item_cb)
    
    depth: bpy.props.FloatProperty(name="Depth", description="Top edge to apex of implant", default=20, min=0, max=30, step=5, precision=2, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(odcutils.implant_selection(context))
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.drill_lib
        assets = odcutils.obj_list_from_lib(libpath, exclude = 'Drill')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        spaces = odcutils.implant_selection(context)
        for space in spaces:
            implant = bpy.data.objects.get(space.implant)
            if implant is None or context.view_layer.objects.get(implant.name) != implant:
                self.report({'WARNING'}, 'Assign an implant in the current view layer first')
                return {'CANCELLED'}
        for space in spaces:
            implant = bpy.data.objects[space.implant]
            previous = bpy.data.objects.get(space.sleeve)
            sleeve = odcutils.obj_from_lib(settings.drill_lib, self.drill)
            context.collection.objects.link(sleeve)
            orientation = implant.matrix_world.to_quaternion()
            sleeve.rotation_mode = 'QUATERNION'
            sleeve.rotation_quaternion = orientation
            sleeve.location = implant.matrix_world.translation + orientation @ Vector((0, 0, -self.depth))
            sleeve.name = space.name + '_Sleeve'
            context.view_layer.update()
            odcutils.parent_in_place(sleeve, implant)
            space.sleeve = sleeve.name
            if previous is not None and previous != implant:
                mesh = previous.data if previous.type == 'MESH' else None
                bpy.data.objects.remove(previous, do_unlink=True)
                if mesh is not None and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        odcutils.layer_management(context.scene.odc_implants, debug=settings.debug)
        return {'FINISHED'}

class OPENDENTAL_OT_place_drill(bpy.types.Operator):
    '''Places or replaces drill at specified depth'''
    bl_idname = "opendental.place_drill"
    bl_label = "Place Drill"
    bl_options = {'REGISTER','UNDO'}
    bl_property = "drill"

    _enum_items = []

    def item_cb(self, context):
        type(self)._enum_items = [(name, name, '') for name in
            odcutils.obj_list_from_lib(get_settings().drill_lib, include='Drill', exclude='Sleeve')]
        return type(self)._enum_items

    objs: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    drill: bpy.props.EnumProperty(name="Drill Library",
                                 description="A List of the items library", 
                                 items=item_cb)
    
    depth: bpy.props.FloatProperty(name="Depth", description="Distance tip of drill to implant apex", default=0, min=-4, max=10, step=5, precision=2, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(odcutils.implant_selection(context))
        
    def invoke(self, context, event): 
        self.objs.clear()
        settings = get_settings()
        libpath = settings.drill_lib
        assets = odcutils.obj_list_from_lib(libpath, include = 'Drill', exclude = 'Sleeve')
       
        for asset_object_name in assets:
            self.objs.add().name = asset_object_name
           
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
    
    def execute(self, context):
        settings = get_settings()
        spaces = odcutils.implant_selection(context)
        for space in spaces:
            implant = bpy.data.objects.get(space.implant)
            if implant is None or context.view_layer.objects.get(implant.name) != implant:
                self.report({'WARNING'}, 'Assign an implant in the current view layer first')
                return {'CANCELLED'}
        for space in spaces:
            implant = bpy.data.objects[space.implant]
            previous = bpy.data.objects.get(space.drill)
            drill = odcutils.obj_from_lib(settings.drill_lib, self.drill)
            context.collection.objects.link(drill)
            orientation = implant.matrix_world.to_quaternion()
            drill.rotation_mode = 'QUATERNION'
            drill.rotation_quaternion = orientation
            drill.location = implant.matrix_world.translation + orientation @ Vector((0, 0, -self.depth))
            drill.name = space.name + '_' + self.drill
            context.view_layer.update()
            odcutils.parent_in_place(drill, implant)
            space.drill = drill.name
            if previous is not None and previous != implant:
                mesh = previous.data if previous.type == 'MESH' else None
                bpy.data.objects.remove(previous, do_unlink=True)
                if mesh is not None and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        odcutils.layer_management(context.scene.odc_implants, debug=settings.debug)
        return {'FINISHED'}

class OPENDENTAL_OT_implant_guide_cylinder(bpy.types.Operator):
    '''Implant Guide Cylinder'''
    bl_idname = "opendental.implant_guide_cylinder"
    bl_label = "Guide Cylinder"
    bl_options = {'REGISTER','UNDO'}
    

    #inner = bpy.props.FloatProperty(name="Slice Thickness", description="view slice thickenss", default=1, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    width: bpy.props.FloatProperty(name="Width", description="Width of Support", default=6, min=1, max=10, step=5, precision=2, options={'ANIMATABLE'})
    depth: bpy.props.FloatProperty(name="Top Edge to Apex of Implant", description="", default=20, min=10, max=30, step=5, precision=2, options={'ANIMATABLE'})
    trim_width: bpy.props.FloatProperty(name="Trim Width", description="Amount to shave off sides", default=0, min=0, max=4, step=5, precision=2, options={'ANIMATABLE'})
    use_wedge: bpy.props.BoolProperty(name = 'Use Wedge', description = "Make a fraction of a full circle", default = False)
    pctg: bpy.props.FloatProperty(name="Wedge pctg", description="Fraction of full circle to make", default=.65, min=0, max=1, step=5, precision=2, options={'ANIMATABLE'})
    
    
    def invoke(self, context, event): 
               
        context.window_manager.invoke_props_dialog(self, width=300) 
        return {'RUNNING_MODAL'}
    
    def execute(self,context):
        settings = get_settings()
        dbg  = settings.debug
        odcutils.scene_verification(context.scene, debug = dbg)
        spaces = odcutils.implant_selection(context)
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        for space in spaces:
            if not space.implant:
                self.report({'WARNING'}, "It seems you have not yet placed an implant for %s" % space.name)
            else:
                implant_utils.implant_outer_cylinder(context, space, 
                           self.width, self.depth, 
                           trim = self.trim_width, 
                           wedge = self.use_wedge, 
                           wedge_pct = self.pctg,
                           debug = dbg)    
        
            
        
        odcutils.material_management(context, context.scene.odc_implants)
        odcutils.layer_management(context.scene.odc_implants, debug = dbg)
        
        return {'FINISHED'}
 
class OPENDENTAL_OT_implant_inner_cylinder(bpy.types.Operator):
    '''
    Makes a cylinder the same diameter as the implant unless
    override thickness is used in which case it uses the
    user specified diameter
    '''
    bl_idname = "opendental.implant_inner_cylinder"
    bl_label = "Inner Cylinder"
    bl_options = {'REGISTER','UNDO'}
    
    use_thickness: bpy.props.BoolProperty(name="Manual Diameter", default=True)
    thickness: bpy.props.FloatProperty(name="Cylinder Diameter", description="diameter of the hole", default=5, min=1, max=7, step=5, precision=1, options={'ANIMATABLE'})

    def execute(self,context):
        settings = get_settings()
        dbg  = settings.debug
        odcutils.scene_verification(context.scene, debug = dbg)
        spaces = odcutils.implant_selection(context)
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        for space in spaces: 
            if not space.implant:
                self.report({'WARNING'}, "It seems you have not yet placed an implant for %s" % space.name)
        
            else:
                if self.use_thickness:
                    thickness = self.thickness
                else:
                    thickness = None
                
                implant_utils.implant_inner_cylinder(context, space, thickness = thickness, debug = dbg)
        
        
        odcutils.material_management(context, context.scene.odc_implants) 
        odcutils.layer_management(context.scene.odc_implants, debug = dbg)
        return {'FINISHED'}   
            
def post_register2():
    print('not needed')

def update_link_operators():
    #unregister get crown
    bpy.utils.unregister_class(OPENDENTAL_OT_place_implant)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_from_contour)
    #redefinte list from user prefs prop
    global lib_teeth_enum
    global lib_teeth
    lib_teeth_enum = []
    lib_teeth = []
    settings = get_settings()
    dbg = settings.debug
    lib_teeth = odcutils.obj_list_from_lib(settings.tooth_lib, exclude = '_', debug = dbg)
    for ind, obj in enumerate(lib_teeth):
        lib_teeth_enum.append((str(ind), obj, str(ind)))
    
    #reregister.
    bpy.utils.register_class(OPENDENTAL_OT_place_implant)
    bpy.utils.register_class(OPENDENTAL_OT_implant_from_contour)

           
def register():
    
    bpy.utils.register_class(OPENDENTAL_OT_implant_guide_cylinder)
    bpy.utils.register_class(OPENDENTAL_OT_implant_inner_cylinder)
    bpy.utils.register_class(OPENDENTAL_OT_implant_slice_view)
    bpy.utils.register_class(OPENDENTAL_OT_implant_normal_view)
    bpy.utils.register_class(OPENDENTAL_OT_implant_from_contour)
    bpy.utils.register_class(OPENDENTAL_OT_place_implant)
    bpy.utils.register_class(OPENDENTAL_OT_place_sleeve)
    bpy.utils.register_class(OPENDENTAL_OT_place_drill)
    #bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_place_drill)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_sleeve)
    bpy.utils.unregister_class(OPENDENTAL_OT_place_implant)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_from_contour)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_normal_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_slice_view)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_inner_cylinder)
    bpy.utils.unregister_class(OPENDENTAL_OT_implant_guide_cylinder)
    
#    bpy.utils.unregister_class(SetMaster)

if __name__ == "__main__":
    register()