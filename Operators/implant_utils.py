'''
Created on Mar 6, 2013

@author: Patrick
'''
#python imports :
import time
import math

#Blender imports :
import bpy
from mathutils import Vector, Matrix

#Addon imports :
from .. import Addon_utils
from ..Addon_utils import odcutils
from ..Addon_utils.odcutils import get_settings

def place_implant(context, implant_space, location, orientation, imp, hardware=True):
    """Load an implant and its library hardware before replacing the old assembly."""
    settings = get_settings()
    previous = bpy.data.objects.get(implant_space.implant)
    loaded = []
    existing_objects = set(bpy.data.objects)
    try:
        implant = odcutils.obj_from_lib(settings.imp_lib, imp)
        loaded.append(implant)
        if hardware:
            for name in odcutils.obj_list_from_lib(settings.imp_lib, include=imp + '_'):
                loaded.append(odcutils.obj_from_lib(settings.imp_lib, name))
        for obj in loaded:
            context.collection.objects.link(obj)
        rotation = orientation.to_quaternion() if isinstance(orientation, Matrix) else orientation
        implant.rotation_mode = 'QUATERNION'
        implant.rotation_quaternion = rotation
        implant.location = location
        context.view_layer.update()
        master = bpy.data.objects.get(context.scene.odc_props.master)
        if master is not None:
            odcutils.parent_in_place(implant, master)
        for obj in loaded[1:]:
            obj.parent = implant
        # Appending each hardware object can also append its library parent.
        # After reparenting, remove only new, unused dependency objects.
        for dependency in set(bpy.data.objects) - existing_objects - set(loaded):
            if dependency.users == 0:
                data = dependency.data if dependency.type == 'MESH' else None
                bpy.data.objects.remove(dependency)
                if data is not None and data.users == 0:
                    bpy.data.meshes.remove(data)
        implant.name = implant_space.name + '_' + implant.name
    except Exception:
        for obj in reversed(loaded):
            data = obj.data if obj.type == 'MESH' else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
        raise
    implant_space.implant = implant.name
    if previous is not None:
        for obj in [*previous.children_recursive, previous]:
            data = obj.data if obj.type == 'MESH' else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                bpy.data.meshes.remove(data)
    return implant

def implant_outer_cylinder(context, space, 
                           width, depth, trim = 0, 
                           wedge = False, wedge_pct = .7,
                           debug = False):
    
    if debug:
        start_time = time.time()
    
    scene = bpy.context.scene
    Implant = scene.objects[space.implant]
    mx_w = Implant.matrix_world.copy()
    
    if Implant.rotation_mode != 'QUATERNION':
        Implant.rotation_mode = 'QUATERNION'
        Implant.update_tag()
        context.view_layer.update()
    
    R = width/2
    H = .1
    if wedge:
        bm = odcutils.primitive_wedge_cylinder(R, wedge_pct, 64, H)
        
    else:
        bm = odcutils.primitive_flattened_cylinder(R, R-trim, 64, H)

    if space.outer and space.outer in bpy.data.objects:
        Cylinder = bpy.data.objects[space.outer]
        me = Cylinder.data
        if len(Cylinder.modifiers):
            for mod in list(Cylinder.modifiers):
                Cylinder.modifiers.remove(mod)
    
    else:
        me = bpy.data.meshes.new(Implant.name + '_GC')
        Cylinder = bpy.data.objects.new(Implant.name + '_GC', me)
        context.collection.objects.link(Cylinder)
        name = Implant.name + '_GC'
        Cylinder.name = name
    
    # Recompute world placement on every invocation, including existing children.
    orientation = mx_w.to_quaternion()
    location = mx_w.translation + orientation @ Vector((0, 0, -depth))
    Cylinder.matrix_world = Matrix.LocRotScale(location, orientation, Vector((1, 1, 1)))

    bm.to_mesh(me)
    bm.free()

    #vert group    
    Cylinder.vertex_groups.clear() 
    Cylinder.vertex_groups.new(name="Project")
    vert_inds = [v.index for v in Cylinder.data.vertices if v.index%2]
    Cylinder.vertex_groups["Project"].add(vert_inds, 1,'REPLACE')

    Cylinder.update_tag()
    context.view_layer.update()

    if len(scene.odc_splints):
        splint = scene.odc_splints[scene.odc_splint_index]
        if splint.splint in bpy.data.objects:
            Splint = bpy.data.objects[splint.splint]
        
            mod = Cylinder.modifiers.new('Project','SHRINKWRAP')
            mod.wrap_method = 'PROJECT'
            mod.use_project_z = True
            mod.use_project_y = False
            mod.use_project_x = False
            mod.offset = .5
            mod.target = Splint
            mod.vertex_group = 'Project'
    

    space.outer = Cylinder.name
    
    odcutils.parent_in_place(Cylinder, Implant)
    if debug:
        print('finished outer cylinder for %s in %f seconds' % (space.name, time.time() - start_time))

def implant_inner_cylinder(context, space, thickness = None, debug = False):
    
    if debug:
        start_time = time.time()
    sce = context.scene
    Implant = sce.objects[space.implant]
    mx_w = Implant.matrix_world.copy()
    
    if thickness:
        D = thickness
    else:
        D = Implant.dimensions[0]
        
    #create a bmesh cylinder
    R = D/2
    bm = odcutils.primitive_flattened_cylinder(R, R, 64, 30)
    
    if Implant.rotation_mode != 'QUATERNION':
        Implant.rotation_mode = 'QUATERNION'
        Implant.update_tag()
        context.view_layer.update()

    if space.inner and space.inner in bpy.data.objects:
        Cylinder = bpy.data.objects[space.inner]
        me = Cylinder.data
        
    else:
        me = bpy.data.meshes.new(Implant.name + '_GC')
        Cylinder = bpy.data.objects.new(Implant.name + '_IC', me)
        # Add the mesh to the scene
        scene = bpy.context.scene
        context.collection.objects.link(Cylinder)
        
        #point the right direction
        Cylinder.rotation_mode = 'QUATERNION'
        Cylinder.rotation_quaternion = mx_w.to_quaternion()
    
        #now we must update to propagate changes to the
        #world matrix.  Otherwise, when we access matrix_world
        #it will not have the new information about scale and
        #rotation...and they changes will be lost when we access
        #the matrix to assign different values to other elements
        Cylinder.update_tag()
        context.view_layer.update()
    
        Trans = Implant.rotation_quaternion @ Vector((0,0,- (30 + Implant.dimensions[2])))
        Cylinder.matrix_world[0][3] = mx_w[0][3] + Trans[0]
        Cylinder.matrix_world[1][3] = mx_w[1][3] + Trans[1]
        Cylinder.matrix_world[2][3] = mx_w[2][3] + Trans[2]

    #Write the bmesh into a new mesh or replace the old mesh?
    bm.to_mesh(me)
    bm.free()

    Cylinder.vertex_groups.clear()        
    Cylinder.vertex_groups.new(name="Project")
    
    #rodd verts added to the "Project Group"
    vert_inds = [v.index for v in Cylinder.data.vertices if v.index%2]
    Cylinder.vertex_groups["Project"].add(vert_inds, 1,'REPLACE')
        
    Cylinder.update_tag()
    context.view_layer.update()
    
    space.inner = Cylinder.name
    
    odcutils.parent_in_place(Cylinder, Implant)
    if debug:
        print('finished inner cylinder for %s in %f seconds' % (space.name, time.time() - start_time))

