"""Synthetic painted-area extraction and non-destructive paint controls."""
import sys
from pathlib import Path
import bpy, addon_utils
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add(location=(3,4,5))
source = bpy.context.object
original = [v.co.copy() for v in source.data.vertices]
other = source.vertex_groups.new(name='Unrelated')
other.add(list(range(8)), .7, 'REPLACE')
source.modifiers.new('Smooth', 'SMOOTH')
meta = bpy.data.objects.new('Unrelated Metaball', bpy.data.metaballs.new('Unrelated'))
bpy.context.collection.objects.link(meta)
collision = bpy.data.objects.new(source.name+'_splint_outline', None)
bpy.context.collection.objects.link(collision)
assert bpy.ops.opendental.splint_outline() == {'FINISHED'}
assert source.mode == 'WEIGHT_PAINT'
assert bpy.context.tool_settings.weight_paint.brush is not None
assert bpy.ops.opendental.splint_outline_erase() == {'FINISHED'}
assert bpy.context.tool_settings.weight_paint.unified_paint_settings.weight == 0
assert meta.name in bpy.data.objects and 'Smooth' in source.modifiers
assert bpy.ops.opendental.splint_outline_paint() == {'FINISHED'}
assert bpy.context.tool_settings.weight_paint.unified_paint_settings.weight == 1
assert bpy.ops.opendental.splint_outline() == {'CANCELLED'}
assert source.mode == 'WEIGHT_PAINT'
bpy.ops.object.mode_set(mode='OBJECT')
paint = source.vertex_groups['ODC Splint Area']
face = source.data.polygons[0]
paint.add(list(face.vertices), 1, 'REPLACE')
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
assert bpy.ops.opendental.splint_outline() == {'FINISHED'}
outline = bpy.context.object
assert outline != source and outline != collision
assert len(outline.data.polygons) == 1 and len(outline.data.vertices) == 4
assert outline.matrix_world == source.matrix_world
assert [v.co for v in source.data.vertices] == original
assert all(abs(other.weight(i)-.7) < 1e-6 for i in range(8))
assert 'Smooth' in source.modifiers
outline_name = outline.name
outline.select_set(False)
source.select_set(True)
bpy.context.view_layer.objects.active = source
assert bpy.ops.opendental.splint_outline() == {'FINISHED'}
assert bpy.ops.opendental.splint_outline() == {'FINISHED'}
assert len([o for o in bpy.context.scene.objects if o.get('odc_splint_outline')]) == 1
assert collision.name in bpy.data.objects and meta.name in bpy.data.objects
print('ODC_SPLINT_OUTLINE_PASSED')
