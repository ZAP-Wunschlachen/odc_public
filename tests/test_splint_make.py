"""Exercise splint finalization on a synthetic painted curved surface."""
import sys
from pathlib import Path
import bpy, bmesh, addon_utils
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent))
assert addon_utils.enable(ROOT.name,default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=10)
source=bpy.context.object
original=[v.co.copy() for v in source.data.vertices]
group=source.vertex_groups.new(name='ODC Splint Area')
group.add([v.index for v in source.data.vertices if v.co.z >= 0],1,'REPLACE')
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
assert bpy.ops.opendental.splint_outline()=={'FINISHED'}
outline=bpy.context.object
if '--with-base' in sys.argv:
    bpy.context.scene.splint_base_model=source.name
# Invalid settings must not rename or alter the prepared outline.
outline_mesh=outline.data
outline_name=outline.name
outline_coords=[v.co.copy() for v in outline.data.vertices]
for thickness,offset in [('bad','.5'),('0','.5'),('3','-1'),('nan','.5')]:
    bpy.context.scene.splint_shell_thickness=thickness
    bpy.context.scene.splint_shell_offset=offset
    assert bpy.ops.opendental.splint_make()=={'CANCELLED'}
    assert outline.data==outline_mesh and outline.name==outline_name
    assert [v.co for v in outline.data.vertices]==outline_coords
bpy.context.scene.splint_shell_thickness='3'
bpy.context.scene.splint_shell_offset='.5'
base_name=bpy.context.scene.splint_base_model
bpy.context.scene.splint_base_model='Missing base model'
assert bpy.ops.opendental.splint_make()=={'CANCELLED'}
assert outline.data==outline_mesh and outline.name==outline_name
bpy.context.scene.splint_base_model=base_name
assert bpy.ops.opendental.splint_make()=={'FINISHED'}
assert bpy.context.object==outline
assert len(outline.data.polygons)>0,'Empty splint'
bm=bmesh.new();bm.from_mesh(outline.data)
assert all(e.is_manifold for e in bm.edges),'Open or nonmanifold splint'
assert bm.calc_volume(signed=False)>0
bm.free()
assert [v.co for v in source.data.vertices]==original
print('ODC_SPLINT_MAKE_PASSED',len(outline.data.polygons))
bpy.ops.mesh.primitive_cube_add(location=(30,0,0))
empty_source=bpy.context.object
empty_coords=[v.co.copy() for v in empty_source.data.vertices]
objects_before=set(bpy.data.objects)
assert bpy.ops.opendental.splint_make()=={'CANCELLED'}
assert set(bpy.data.objects)==objects_before
assert empty_source.mode=='OBJECT'
assert [v.co for v in empty_source.data.vertices]==empty_coords
print('ODC_SPLINT_EMPTY_AREA_PASSED')
