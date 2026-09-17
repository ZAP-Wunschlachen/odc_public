"""ODC's immediate-mode overlays implemented using Blender's supported GPU API.

This is package-local: it does not install a fake global ``bgl`` module or patch
Blender. Geometry is batched on glEnd; callers keep their existing draw order.
"""
import math

import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

GL_POINTS = 0
GL_LINES = 1
GL_LINE_LOOP = 2
GL_LINE_STRIP = 3
GL_QUADS = 7
GL_POLYGON = 9
GL_BLEND = 3042
GL_DEPTH_TEST = 2929
GL_LINE_STIPPLE = 2852
GL_POINT_SMOOTH = 2832
GL_ENABLE_BIT = 8192
GL_LINE_WIDTH = 2849
GL_SRC_ALPHA = 770
GL_ONE_MINUS_SRC_ALPHA = 771

_color = (1.0, 1.0, 1.0, 1.0)
_vertices = []
_colors = []
_mode = None
_stipple = False
_stipple_factor = 1
_stipple_pattern = 0xFFFF
_state_stack = []


def glColor4f(r, g, b, a):
    global _color
    _color = (r, g, b, a)


def glBegin(mode):
    global _mode, _vertices, _colors
    if _mode is not None:
        raise RuntimeError("Nested ODC overlay batches are not supported")
    _mode, _vertices, _colors = mode, [], []


def glVertex3f(x, y, z):
    if _mode is None:
        raise RuntimeError("ODC overlay vertex outside a batch")
    _vertices.append((float(x), float(y), float(z)))
    _colors.append(_color)


def glVertex2f(x, y):
    glVertex3f(x, y, 0.0)


glVertex2i = glVertex2f


def _line_indices(mode, count):
    if mode == GL_LINES:
        return [(i, i + 1) for i in range(0, count - 1, 2)]
    indices = [(i, i + 1) for i in range(count - 1)]
    if mode == GL_LINE_LOOP and count > 1:
        indices.append((count - 1, 0))
    return indices


def _stippled_lines(vertices, colors, indices):
    """Segment legacy two-dimensional, pixel-coordinate dashed overlays."""
    result, shades = [], []
    distance = 0.0
    for i, j in indices:
        a, b = Vector(vertices[i]), Vector(vertices[j])
        length = (b - a).length
        if length == 0:
            continue
        cursor = 0.0
        while cursor < length:
            bit = int(distance / _stipple_factor) % 16
            step = min(length - cursor,
                       _stipple_factor - distance % _stipple_factor)
            step = max(step, min(1e-6, length - cursor))
            if _stipple_pattern & (1 << bit):
                for t in (cursor / length, (cursor + step) / length):
                    result.append(tuple(a.lerp(b, t)))
                    shades.append(tuple(x + (y - x) * t
                                        for x, y in zip(colors[i], colors[j])))
            cursor += step
            distance += step
    return result, shades


def glEnd():
    global _mode, _vertices, _colors
    mode, vertices, colors = _mode, _vertices, _colors
    _mode, _vertices, _colors = None, [], []
    if mode is None:
        raise RuntimeError("ODC overlay batch was not started")
    if not vertices:
        return
    indices = None
    if mode in (GL_LINES, GL_LINE_LOOP, GL_LINE_STRIP):
        primitive = 'LINES'
        indices = _line_indices(mode, len(vertices))
        if _stipple:
            vertices, colors = _stippled_lines(vertices, colors, indices)
            indices = None
    elif mode == GL_POINTS:
        primitive = 'POINTS'
    elif mode == GL_QUADS:
        primitive = 'TRIS'
        indices = [tri for i in range(0, len(vertices) - 3, 4)
                   for tri in ((i, i + 1, i + 2), (i, i + 2, i + 3))]
    elif mode == GL_POLYGON:
        primitive = 'TRIS'
        polygon = [Vector(v) for v in vertices]
        lookup = {tuple(v): i for i, v in enumerate(polygon)}
        indices = [tuple(lookup[tuple(v)] for v in triangle)
                   for triangle in tessellate_polygon([polygon])]
    else:
        raise ValueError(f"Unsupported ODC overlay primitive: {mode}")
    if not vertices or indices == []:
        return
    shader = gpu.shader.from_builtin('SMOOTH_COLOR')
    batch = batch_for_shader(shader, primitive,
                             {'pos': vertices, 'color': colors}, indices=indices)
    shader.bind()
    batch.draw(shader)


def glLineWidth(width):
    gpu.state.line_width_set(max(1.0, float(width)))


def glPointSize(size):
    gpu.state.point_size_set(max(1.0, float(size)))


def glEnable(capability):
    global _stipple
    if capability == GL_BLEND:
        gpu.state.blend_set('ALPHA')
    elif capability == GL_DEPTH_TEST:
        gpu.state.depth_test_set('LESS_EQUAL')
    elif capability == GL_LINE_STIPPLE:
        _stipple = True
    elif capability != GL_POINT_SMOOTH:
        raise ValueError(f"Unsupported overlay capability: {capability}")


def glDisable(capability):
    global _stipple
    if capability == GL_BLEND:
        gpu.state.blend_set('NONE')
    elif capability == GL_DEPTH_TEST:
        gpu.state.depth_test_set('NONE')
    elif capability == GL_LINE_STIPPLE:
        _stipple = False
    elif capability != GL_POINT_SMOOTH:
        raise ValueError(f"Unsupported overlay capability: {capability}")


def glBlendFunc(source, destination):
    if (source, destination) != (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA):
        raise ValueError("Only standard alpha blending is used by ODC")
    gpu.state.blend_set('ALPHA')


def glLineStipple(factor, pattern):
    global _stipple_factor, _stipple_pattern
    _stipple_factor = max(1, int(factor))
    _stipple_pattern = int(pattern) & 0xFFFF


def glPushAttrib(mask):
    _state_stack.append((gpu.state.blend_get(), gpu.state.depth_test_get(),
                         gpu.state.line_width_get(), _stipple, _color))


def glPopAttrib():
    global _stipple, _color
    blend, depth, width, _stipple, _color = _state_stack.pop()
    gpu.state.blend_set(blend)
    gpu.state.depth_test_set(depth)
    gpu.state.line_width_set(width)
