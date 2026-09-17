"""Live, symmetric clearance weights without cyclic proximity modifiers."""
import hashlib
from array import array
import bpy
from bpy.app.handlers import persistent
from mathutils.bvhtree import BVHTree

_cache = {}
_updating = False
_TARGET = 'odc_clearance_target'
_MIN = 'odc_clearance_touching'
_MAX = 'odc_clearance_maximum'
_GROUP = 'odc_clearance_group'


def _surface(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        faces = [tuple(p.vertices) for p in mesh.polygons]
        digest = hashlib.blake2b(digest_size=16)
        digest.update(array('d', (c for v in vertices for c in v)).tobytes())
        digest.update(array('i', (i for face in faces for i in (*face, -1))).tobytes())
        tree = BVHTree.FromPolygons(vertices, faces) if faces else None
        return vertices, tree, digest.digest()
    finally:
        evaluated.to_mesh_clear()


def _update(obj, target, source_surface, target_surface):
    low, high = float(obj[_MIN]), float(obj[_MAX])
    if high <= low:
        return
    group_name = obj[_GROUP]
    group = obj.vertex_groups.get(group_name)
    # Weight storage is on the original mesh. Use original vertex positions;
    # deformations preserving topology can use evaluated vertex positions.
    vertices, _, source_signature = source_surface
    if len(vertices) != len(obj.data.vertices):
        vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
    _, tree, target_signature = target_surface
    key = obj.as_pointer()
    signature = (source_signature, target_signature, low, high, group_name)
    if group is not None and _cache.get(key) == signature:
        return
    if group is None:
        group = obj.vertex_groups.new(name=group_name)
    for index, point in enumerate(vertices):
        nearest = tree.find_nearest(point) if tree is not None else None
        distance = nearest[3] if nearest and nearest[0] is not None else high
        weight = max(0.0, min(1.0, (high - distance) / (high - low)))
        group.add([index], weight, 'REPLACE')
    _cache[key] = signature


@persistent
def update_clearance(scene, depsgraph=None):
    global _updating
    if _updating:
        return
    _updating = True
    try:
        depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
        objects = [o for o in scene.objects if o.type == 'MESH' and _TARGET in o
                   and o.get(_TARGET) is not None and o.mode != 'EDIT']
        surfaces = {}
        for obj in objects:
            target = obj.get(_TARGET)
            if not isinstance(target, bpy.types.Object) or target.type != 'MESH':
                continue
            for item in (obj, target):
                pointer = item.as_pointer()
                if pointer not in surfaces:
                    surfaces[pointer] = _surface(item, depsgraph)
            _update(obj, target, surfaces[obj.as_pointer()], surfaces[target.as_pointer()])
    finally:
        _updating = False


def configure_pair(first, second, touching, maximum):
    if not 0 <= touching < maximum:
        raise ValueError('Touching distance must be smaller than maximum distance')
    for obj, target in ((first, second), (second, first)):
        name = 'clearance ' + target.name
        for modifier in list(obj.modifiers):
            if (modifier.type == 'VERTEX_WEIGHT_PROXIMITY'
                    and modifier.vertex_group == name and modifier.target == target):
                obj.modifiers.remove(modifier)
        obj[_TARGET] = target
        obj[_MIN] = float(touching)
        obj[_MAX] = float(maximum)
        obj[_GROUP] = name
        _cache.pop(obj.as_pointer(), None)
    update_clearance(bpy.context.scene)


def register():
    if update_clearance not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(update_clearance)


def unregister():
    if update_clearance in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(update_clearance)
    _cache.clear()
