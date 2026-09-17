'''
Created on Nov 22, 2016

@author: Patrick
'''
import bpy
from . import clearance

class OPENDENTAL_OT_check_clearance(bpy.types.Operator):
    '''
    Select two meshes and calculate live clearance vertex weights for both.
    Updates when either mesh moves, without cyclic modifier dependencies.
    '''
    bl_idname = 'opendental.check_clearance'
    bl_label = "Check Clearance"
    bl_options = {'REGISTER','UNDO'}
    
    min_d: bpy.props.FloatProperty(name="Touching", description="", default=0, min=0, max=1, step=5, precision=2, options={'ANIMATABLE'})
    max_d: bpy.props.FloatProperty(name="Max D", description="", default=.5, min=.1, max=2, step=5, precision=2, options={'ANIMATABLE'})
    
    @classmethod
    def poll(cls, context):
        
        cond1 = context.object != None
        cond2 = len(context.selected_objects) == 2
        cond3 = all([ob.type == 'MESH' for ob in context.selected_objects])
        cond4 = context.mode == 'OBJECT'
        
        return cond1 & cond2 & cond3 & cond4
        
    def execute(self, context):
        if self.min_d >= self.max_d:
            self.report({'WARNING'}, 'Touching distance must be smaller than maximum distance')
            return {'CANCELLED'}
        first = context.object
        second = next(obj for obj in context.selected_objects if obj != first)
        clearance.configure_pair(first, second, self.min_d, self.max_d)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OPENDENTAL_OT_check_clearance)
    clearance.register()
    
def unregister():
    clearance.unregister()
    bpy.utils.unregister_class(OPENDENTAL_OT_check_clearance)
    
if __name__ == "__main__":
    register()