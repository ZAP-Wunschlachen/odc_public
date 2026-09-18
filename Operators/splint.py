#python imports :

#Blender imports :
import bpy
import bmesh
from bpy.types import Panel

#Addon imports :


#from time import process_time
def create_material(name):
    if name in bpy.data.materials:  # if material already exists, just configure it
        ob = bpy.context.object
        me = ob.data
        print("Material already exists: " + name + "; changing...")

        index = bpy.data.materials.find(name)
        mat = bpy.data.materials[index]
        mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
        mat.metallic = 1
        mat.roughness = 0.02


        if (
            len(ob.material_slots) < 1
        ):  # check if the material slot already exists and use it

            me.materials.append(mat)
        else:
            bpy.ops.object.material_slot_remove()
            me.materials.append(mat)

    else: #Repeat in case material doesnt exist, bue creating it first
        ob = bpy.context.object
        me = ob.data        
        if len(ob.material_slots) < 1:
            mat = bpy.data.materials.new(name=name)
            mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
            mat.metallic = 1
            mat.roughness = 0.02
            me.materials.append(mat)

        else:
            bpy.ops.object.material_slot_remove()
            mat = bpy.data.materials.new(name=name)
            mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
            mat.metallic = 1
            mat.roughness = 0.02
            print("color " + name+" was created")
            me.materials.append(mat)

            

def create_particles(name, vertexgroup): #Same process as with material but with a particle system, a bit more complicated
    if name in bpy.context.object.particle_systems:
        ob = bpy.context.object
        me = ob.data
        print("Particles system already exists: "+ name+ "; changing...")
        index = bpy.context.object.particle_systems.find(name)
        part = bpy.data.particles[index]
        part.type = 'HAIR'
        part.use_advanced_hair = True
        part.render_type = 'OBJECT'
        bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
        part.particle_size = 0.2
        part.count = 10000
        part.hair_length = 6

    else:
        ob = bpy.context.object
        me = ob.data   
        bpy.ops.object.particle_system_add()
        bpy.context.object.particle_systems[0].name = name

        findparticles = name in bpy.data.particles
        finddefaultp = 'ParticleSettings' in bpy.data.particles

        if findparticles == True:
            part = bpy.data.particles[index]
            part.name = name
            part.type = 'HAIR'
            part.use_advanced_hair = True
            part.render_type = 'OBJECT'
            bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
            part.particle_size = 0.2
            part.count = 10000
            part.hair_length = 6
            me.particles.append(part)
        else:
            if finddefaultp == True:
                part = bpy.data.particles[0]
                part.name = name
                part.type = 'HAIR'
                part.use_advanced_hair = True
                part.render_type = 'OBJECT'
                bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
                part.particle_size = 0.2
                part.count = 10000
                part.hair_length = 6

            else:

                part = bpy.data.particles.new(name=name)
                part.name = name
                part.type = 'HAIR'
                part.use_advanced_hair = True
                part.render_type = 'OBJECT'
                bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
                part.particle_size = 0.2
                part.count = 10000
                part.hair_length = 6
                me.particles.append(part) 
    


class btn_Splint_draw(bpy.types.Operator):
    bl_idname = "object.splint_draw"
    bl_label = "Draw splint"


    def execute(self, context):

        # First rename de model to 'model'
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob
        ob.name = "model"
        
        # Check if there's already a metaball in the scene
        foundmeta = 'Mball' in bpy.data.objects
        
        #If there's not a metaball create the meta and setup resolution and material
        if foundmeta == False:
            bpy.ops.object.metaball_add(type='BALL', enter_editmode=False, align='WORLD', location=(0, 0, 100))
            ob = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = ob
            bpy.context.object.data.resolution = 1
            bpy.context.object.data.threshold = 0.01  
            create_material('splintmat')


            
        #If its already created setup resolution and material
        else:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Mball'].select_set(True)
            ob = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = ob
            bpy.context.object.data.resolution = 1
            bpy.context.object.data.threshold = 0.01
            create_material('splintmat')


        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['model'].select_set(True)
        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob #Set the model as active object

        #We check if the model already has a vertex group and rename it as VG_Influence, we create if it doesnt exist
        
        if len(ob.vertex_groups) == 0:
            bpy.ops.object.vertex_group_add()
            ob.vertex_groups[0].name = 'VG_Influence'

        else:
            bpy.ops.object.material_slot_remove()
            mat = bpy.data.materials.new(name=name)
            mat.diffuse_color = (0.295508, 0.439708, 0.8, 0.5)
            mat.metallic = 1
            mat.roughness = 0.02
            print("color " + name + " was created")
            me.materials.append(mat)

            return {"FINISHED"}


def clean_object():
    me = bpy.context.object.data
    bm = bmesh.new()  # create an empty BMesh
    bm.from_mesh(me)  # fill it in from a Mesh
    # Erase single vertices (not forming faces)
    def cleaning():
        for v in bm.verts:
            if not v.link_edges:
                v.select = True
                bm.verts.remove(v)
        # Erase edges not forming faces
        for ed in bm.edges:
            if len(ed.link_faces) == 0:
                for v in ed.verts:
                    if len(v.link_faces) == 0:
                        v.select = True
                        bm.verts.remove(v)
        # Erase trienagles with less than 2 neighbours
        for v in bm.verts:
            if len(v.link_edges) == 2:
                v.select = True
                bm.verts.remove(v)
        bm.to_mesh(me)
        me.update()
        bm.free()

    cleaning()
    return {"FINISHED"}


class OPENDENTAL_OT_splint_outline(bpy.types.Operator):
    bl_idname = "opendental.splint_outline"
    bl_label = "Outline Area"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.object.mode in {'OBJECT', 'WEIGHT_PAINT'})

    def execute(self, context):
        source = context.object
        if source.mode == 'OBJECT':
            group = source.vertex_groups.get('ODC Splint Area')
            if group is None:
                group = source.vertex_groups.new(name='ODC Splint Area')
            source.vertex_groups.active_index = group.index
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.brush.asset_activate(
                asset_library_type='ESSENTIALS',
                relative_asset_identifier='brushes/essentials_brushes-mesh_weight.blend/Brush/Paint')
            brush = context.tool_settings.weight_paint.brush
            brush.use_frontface = False
            brush.curve_distance_falloff_preset = 'CONSTANT'
            context.tool_settings.weight_paint.unified_paint_settings.use_unified_weight = True
            context.tool_settings.weight_paint.unified_paint_settings.weight = 1.0
            context.scene.splint_mode = 'PAINT'
            return {'FINISHED'}

        group = source.vertex_groups.get('ODC Splint Area') or source.vertex_groups.active
        if group is None:
            self.report({'WARNING'}, 'Paint a splint area first')
            return {'CANCELLED'}
        indices = {vertex.index for vertex in source.data.vertices
                   if any(item.group == group.index and item.weight > 0
                          for item in vertex.groups)}
        if not any(all(index in indices for index in face.vertices)
                   for face in source.data.polygons):
            self.report({'WARNING'}, 'The painted area must contain at least one complete face')
            return {'CANCELLED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        bm = bmesh.new()
        try:
            bm.from_mesh(source.data)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in indices], context='VERTS')
            mesh = bpy.data.meshes.new(source.name + '_splint_outline')
            bm.to_mesh(mesh)
        finally:
            bm.free()
        # Only replace outlines generated for this source; preserve name collisions.
        for old in list(context.scene.objects):
            if old.get('odc_splint_source') == source and old.get('odc_splint_outline'):
                old_mesh = old.data
                bpy.data.objects.remove(old, do_unlink=True)
                if old_mesh.users == 0:
                    bpy.data.meshes.remove(old_mesh)
        outline = bpy.data.objects.new(source.name + '_splint_outline', mesh)
        outline['odc_splint_source'] = source
        outline['odc_splint_outline'] = True
        context.collection.objects.link(outline)
        outline.matrix_world = source.matrix_world.copy()
        for ob in context.selected_objects:
            ob.select_set(False)
        outline.select_set(True)
        context.view_layer.objects.active = outline
        context.scene.splint_mode = 'OBJECT'
        return {'FINISHED'}

class OPENDENTAL_OT_splint_make(bpy.types.Operator):
    bl_idname = "opendental.splint_make"
    bl_label = "Finalize Splint"

    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == 'MESH'
                and context.object.mode in {'OBJECT', 'WEIGHT_PAINT'})

    def execute(self, context):
        import math
        try:
            thickness = float(context.scene.splint_shell_thickness)
            offset = float(context.scene.splint_shell_offset)
        except ValueError:
            self.report({'WARNING'}, 'Thickness and offset must be numbers')
            return {'CANCELLED'}
        if not math.isfinite(thickness) or not math.isfinite(offset) or thickness <= 0 or offset < 0:
            self.report({'WARNING'}, 'Thickness must be positive and offset non-negative')
            return {'CANCELLED'}
        base_name = context.scene.splint_base_model
        base = context.scene.objects.get(base_name) if base_name else None
        if base_name and (base is None or base.type != 'MESH'):
            self.report({'WARNING'}, 'Select an existing mesh as the base model')
            return {'CANCELLED'}
        source = context.object
        if source.mode == 'WEIGHT_PAINT' or not source.get('odc_splint_outline'):
            if source.mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            if bpy.ops.opendental.splint_outline() != {'FINISHED'}:
                if source.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                context.scene.splint_mode = 'OBJECT'
                return {'CANCELLED'}
        ob = context.object
        if ob == base:
            self.report({'WARNING'}, 'The outline and base model must be different objects')
            return {'CANCELLED'}
        for selected in context.selected_objects:
            selected.select_set(False)
        ob.select_set(True)
        if "_splint_outline" in bpy.context.selected_objects[0].name:
            bpy.context.selected_objects[0].name = bpy.context.selected_objects[0].name.replace("_splint_outline", "_splint")
            bpy.context.selected_objects[0]['odc_splint_outline'] = False

        ob = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = ob
        create_material("splintmat")  # Apply material

        # Metaballs in fact where only for visualize, we use other method to create final splint, becasue with metaballs everything gets so bulgy
        # Clean free borders
        clean_object()

        # Edit model again, select non-manifold and generate a face, voxel remesh, solidify 1 mm, voxel remesh and smooth the result

        #        bpy.ops.object.mode_set(mode='EDIT')
        #        bpy.ops.mesh.select_non_manifold()
        #        bpy.ops.transform.translate(value=(0, 0, 5), orient_type='GLOBAL', constraint_axis=(False, False, True))
        #        bpy.ops.transform.resize(value=(1, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        #        bpy.ops.mesh.fill()
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.modifier_add(type="REMESH")
        bpy.context.object.modifiers["Remesh"].mode = "SMOOTH"
        bpy.context.object.modifiers["Remesh"].octree_depth = 6
        bpy.context.object.modifiers["Remesh"].scale = 0.99
        bpy.ops.object.transform_apply()
        bpy.ops.object.modifier_apply(modifier="Remesh")

        bpy.ops.object.modifier_add(type="SOLIDIFY")
        bpy.context.object.modifiers["Solidify"].thickness = float(context.scene.splint_shell_thickness) + float(context.scene.splint_shell_offset)
        bpy.context.object.modifiers["Solidify"].offset = 0.5
        bpy.ops.object.modifier_apply(modifier="Solidify")

        bpy.context.object.data.remesh_voxel_size = 0.5
        bpy.context.object.data.use_remesh_fix_poles = True
        bpy.context.object.data.use_remesh_preserve_volume = True
        bpy.ops.object.voxel_remesh()
        for polygon in bpy.context.object.data.polygons:
            polygon.use_smooth = True

        bpy.ops.object.modifier_add(type="SMOOTH")
        bpy.context.object.modifiers["Smooth"].factor = 1
        bpy.context.object.modifiers["Smooth"].iterations = 7

        bpy.ops.object.modifier_apply(modifier="Smooth")
        #        objs = [ob for ob in bpy.context.scene.objects if ob.type in ('METABALL')]
        #        bpy.ops.object.delete({"selected_objects": objs})

        #t1_stop = process_time()
        #print("Elapsed time during the whole program in seconds:", t1_stop - t1_start)
        if context.scene.splint_base_model != "":
            ob.select_set(False)
            bpy.data.objects[context.scene.splint_base_model].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[context.scene.splint_base_model]
            bpy.ops.object.duplicate()
            offset_model = bpy.context.view_layer.objects.active
            bpy.ops.object.modifier_add(type="SOLIDIFY")
            bpy.context.object.modifiers["Solidify"].solidify_mode = "NON_MANIFOLD"
            bpy.context.object.modifiers["Solidify"].nonmanifold_thickness_mode = "FIXED"
            bpy.context.object.modifiers["Solidify"].nonmanifold_boundary_mode = "NONE"
            bpy.context.object.modifiers["Solidify"].use_rim = True
            bpy.context.object.modifiers["Solidify"].use_flip_normals = True
            bpy.context.object.modifiers["Solidify"].thickness = float(context.scene.splint_shell_offset)
            bpy.context.object.modifiers["Solidify"].offset = 1.0
            bpy.ops.object.modifier_apply(modifier="Solidify")
            bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
            offset_model.select_set(False)
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.modifier_add(type="BOOLEAN")
            bpy.context.object.modifiers["Boolean"].operation = "DIFFERENCE"
            bpy.context.object.modifiers["Boolean"].object = offset_model
            bpy.ops.object.modifier_apply(modifier="Boolean")
            offset_model.select_set(True)
            ob.select_set(False)
            bpy.context.view_layer.objects.active = offset_model
            bpy.ops.object.delete()
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.opendental.remesh_model("INVOKE_DEFAULT")
            
        return {"FINISHED"}

class OPENDENTAL_OT_splint_outline_paint(bpy.types.Operator):
    bl_idname = "opendental.splint_outline_paint"
    bl_label = "Add Area"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.mode == 'WEIGHT_PAINT'

    def execute(self, context):
        context.tool_settings.weight_paint.unified_paint_settings.use_unified_weight = True
        context.tool_settings.weight_paint.unified_paint_settings.weight = 1.0
        return {'FINISHED'}


class OPENDENTAL_OT_splint_outline_erase(bpy.types.Operator):
    bl_idname = "opendental.splint_outline_erase"
    bl_label = "Erase Area"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.mode == 'WEIGHT_PAINT'

    def execute(self, context):
        context.tool_settings.weight_paint.unified_paint_settings.use_unified_weight = True
        context.tool_settings.weight_paint.unified_paint_settings.weight = 0.0
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OPENDENTAL_OT_splint_outline)
    bpy.utils.register_class(OPENDENTAL_OT_splint_make)
    bpy.utils.register_class(OPENDENTAL_OT_splint_outline_paint)
    bpy.utils.register_class(OPENDENTAL_OT_splint_outline_erase)

    
def unregister():
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_outline_erase)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_outline_paint)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_make)
    bpy.utils.unregister_class(OPENDENTAL_OT_splint_outline)


# def create_particles(name, vertexgroup): #Same process as with material but with a particle system, a bit more complicated
#         if name in bpy.context.object.particle_systems:
#             ob = bpy.context.object
#             me = ob.data
#             print("Particles system already exists: "+ name+ "; changing...")
#             index = bpy.context.object.particle_systems.find(name)
#             part = bpy.data.particles[index]
#             part.type = 'HAIR'
#             part.use_advanced_hair = True
#             part.render_type = 'OBJECT'
#             bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
#             part.particle_size = 0.2
#             part.count = 10000
#             part.hair_length = 6

#         else:
#             ob = bpy.context.object
#             me = ob.data
#             bpy.ops.object.particle_system_add()
#             bpy.context.object.particle_systems[0].name = name

#             findparticles = name in bpy.data.particles
#             finddefaultp = 'ParticleSettings' in bpy.data.particles

#             if findparticles == True:
#                 part = bpy.data.particles[index]
#                 part.name = name
#                 part.type = 'HAIR'
#                 part.use_advanced_hair = True
#                 part.render_type = 'OBJECT'
#                 bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
#                 part.particle_size = 0.2
#                 part.count = 10000
#                 part.hair_length = 6
#                 me.particles.append(part)
#             else:
#                 if finddefaultp == True:
#                     part = bpy.data.particles[0]
#                     part.name = name
#                     part.type = 'HAIR'
#                     part.use_advanced_hair = True
#                     part.render_type = 'OBJECT'
#                     bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
#                     part.particle_size = 0.2
#                     part.count = 10000
#                     part.hair_length = 6

#                 else:

#                     part = bpy.data.particles.new(name=name)
#                     part.name = name
#                     part.type = 'HAIR'
#                     part.use_advanced_hair = True
#                     part.render_type = 'OBJECT'
#                     bpy.context.object.particle_systems[name].vertex_group_density = vertexgroup
#                     part.particle_size = 0.2
#                     part.count = 10000
#                     part.hair_length = 6
#                     me.particles.append(part)


#                 return {'FINISHED'}