"""Tray fill creates a connected projected surface from mesh and curve loops."""
import sys, os, traceback, math
from pathlib import Path
import bpy, bmesh, addon_utils
from mathutils import Matrix, Euler, Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))

def run():
    try:
        assert addon_utils.enable(ROOT.name,default_set=True)
        area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW')
        for kind in ('mesh','curve'):
            if kind=='mesh':
                bpy.ops.mesh.primitive_circle_add(vertices=32,radius=10,fill_type='NOTHING')
            else:
                bpy.ops.curve.primitive_bezier_circle_add(radius=10)
            source=bpy.context.object
            rotation=Euler((.2,.3,.4)).to_quaternion()
            center=Vector((3,4,5))
            source.matrix_world=Matrix.Translation(center)@rotation.to_matrix().to_4x4()
            if kind=='curve':
                parent=bpy.data.objects.new('Tray parent',None)
                bpy.context.collection.objects.link(parent)
                parent.location=(20,0,3)
                bpy.context.view_layer.update()
                world=source.matrix_world.copy()
                source.parent=parent
                source.matrix_world=world
            bpy.context.view_layer.update()
            original_world=source.matrix_world.copy()
            original_data=source.data
            coords=[v.co.copy() for v in (source.data.vertices if kind=='mesh' else source.data.splines[0].bezier_points)]
            before=set(bpy.data.objects)
            before_meshes=set(bpy.data.meshes)
            before_curves=set(bpy.data.curves)
            bpy.context.scene.cursor.location=(8,9,10)
            bpy.context.tool_settings.transform_pivot_point='CURSOR'
            bpy.context.scene.transform_orientation_slots[0].type='NORMAL'
            bpy.context.tool_settings.mesh_select_mode=(False,False,True)
            with bpy.context.temp_override(area=area,region=region):
                area.spaces.active.region_3d.view_rotation=rotation
                assert bpy.ops.opendental.cloth_fill_tray(oct=5,smooth=3)=={'FINISHED'}
            result=bpy.context.object
            assert set(bpy.data.objects)-before=={result}
            assert result!=source and result.type=='MESH'
            assert set(bpy.data.meshes)-before_meshes=={result.data}
            assert set(bpy.data.curves)==before_curves
            assert tuple(bpy.context.scene.cursor.location)==(8,9,10)
            assert bpy.context.tool_settings.transform_pivot_point=='CURSOR'
            assert bpy.context.scene.transform_orientation_slots[0].type=='NORMAL'
            assert tuple(bpy.context.tool_settings.mesh_select_mode)==(False,False,True)
            assert source.data==original_data and source.matrix_world==original_world
            assert all((v.co-co).length<1e-7 for v,co in zip(source.data.vertices if kind=='mesh' else source.data.splines[0].bezier_points,coords))
            if kind=='curve':assert result.parent==parent
            normal=rotation@Vector((0,0,1))
            world_coords=[result.matrix_world@v.co for v in result.data.vertices]
            assert max(abs((co-center).dot(normal)) for co in world_coords)<1e-4
            assert 9<max((co-center).length for co in world_coords)<11
            bm=bmesh.new();bm.from_mesh(result.data);bm.verts.ensure_lookup_table()
            assert len(bm.faces)>100
            assert len(bm.verts)-len(bm.edges)+len(bm.faces)==1
            assert all(edge.is_manifold or edge.is_boundary for edge in bm.edges)
            assert all(vertex.link_faces for vertex in bm.verts)
            boundary=[edge for edge in bm.edges if edge.is_boundary]
            assert boundary
            reached=set();pending=[bm.verts[0]]
            while pending:
                vertex=pending.pop()
                if vertex not in reached:
                    reached.add(vertex);pending.extend(edge.other_vert(vertex) for edge in vertex.link_edges)
            assert len(reached)==len(bm.verts)
            bm.free()
        print('ODC_CLOTH_FILL_GEOMETRY_PASSED',flush=True)
        bpy.ops.wm.quit_blender()
    except Exception:
        traceback.print_exc();os._exit(1)
bpy.app.timers.register(run,first_interval=2)
