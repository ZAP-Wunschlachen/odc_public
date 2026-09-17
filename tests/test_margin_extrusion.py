"""World-distance offsets and ribbon topology remain correct under affine transforms."""
import sys
import math
import importlib
from pathlib import Path
import bpy
import bmesh
import addon_utils
from mathutils import Matrix, Vector, Euler
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
extrude = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils').extrude_bmesh_loop
rotation = Euler((.3,.4,.5)).to_matrix().to_4x4()
transform = Matrix.Translation((2,3,4)) @ rotation @ Matrix.Diagonal((2,3,4,1))
normal = rotation.to_3x3() @ Vector((0,0,1))
center = transform.translation
for reverse in (False, True):
    bm = bmesh.new()
    # Circular world-space fixture expressed in a scaled local frame.
    points = [center + rotation.to_3x3() @ Vector((2*math.cos(i*math.tau/40),2*math.sin(i*math.tau/40),0)) for i in range(40)]
    if reverse:
        points.reverse()
    vertices = [bm.verts.new(transform.inverted() @ p) for p in points]
    for i in range(40):
        bm.edges.new((vertices[i],vertices[(i+1)%40]))
    extrude(bm, list(bm.edges), transform, normal, .2, move_only=True)
    assert all(abs(((transform @ v.co)-center).length-1.8) < 1e-5 for v in bm.verts)
    extrude(bm, list(bm.edges), transform, normal, -.4)
    assert len(bm.verts) == 80 and len(bm.faces) == 40
    radii = sorted(((transform @ v.co)-center).length for v in bm.verts)
    assert all(abs(r-1.8) < 1e-5 for r in radii[:40])
    assert all(abs(r-2.2) < 1e-5 for r in radii[40:])
    assert sum(e.is_boundary for e in bm.edges) == 80
    assert all(e.is_boundary or e.is_manifold for e in bm.edges)
    bm.free()
# Invalid open paths must fail before mutating geometry.
bm = bmesh.new()
a = bm.verts.new((0,0,0)); b = bm.verts.new((1,0,0))
bm.edges.new((a,b))
try:
    extrude(bm, list(bm.edges), Matrix.Identity(4), Vector((0,0,1)), .2)
except ValueError:
    pass
else:
    raise AssertionError('Open loop was accepted')
assert len(bm.verts) == 2 and len(bm.edges) == 1
bm.free()
addon_utils.disable(ROOT.name, default_set=True)
print('ODC_MARGIN_EXTRUSION_PASSED', bpy.app.version_string)
