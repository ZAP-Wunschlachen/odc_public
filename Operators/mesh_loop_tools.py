"""Context-independent entry points to the bundled LoopTools algorithms."""
import bmesh
from . import loops_tools


def flatten_selected(mesh):
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    for loop in loops_tools.flatten_get_input(bm):
        center, normal = loops_tools.calculate_plane(bm, loop, method='best_fit')
        for index, location in loops_tools.flatten_project(bm, loop, center, normal):
            bm.verts[index].co = location
    bmesh.update_edit_mesh(mesh)


def relax_selected(mesh, iterations=3):
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    loops = loops_tools.get_connected_selections([
        loops_tools.edgekey(edge) for edge in bm.edges if edge.select and not edge.hide])
    loops = loops_tools.check_loops(loops, False, bm)
    knots, points = loops_tools.relax_calculate_knots(loops)
    for _ in range(iterations):
        tknots, tpoints = loops_tools.relax_calculate_t(bm, knots, points, True)
        splines = [loops_tools.calculate_splines('cubic', bm, tknots[i], knot)
                   for i, knot in enumerate(knots)]
        for index, location in loops_tools.relax_calculate_verts(
                bm, 'cubic', tknots, knots, tpoints, points, splines):
            bm.verts[index].co = location
    bmesh.update_edit_mesh(mesh)


def space_selected(mesh):
    """Space selected boundary vertices with the bundled cubic spline algorithm."""
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    loops = loops_tools.get_connected_selections([
        loops_tools.edgekey(edge) for edge in bm.edges if edge.select and not edge.hide])
    for indices, circular in loops_tools.check_loops(loops, False, bm):
        knots = indices + [indices[0]] if circular else indices[:]
        tknots, tpoints = loops_tools.space_calculate_t(bm, knots)
        if not tknots[-1]:
            continue
        splines = loops_tools.calculate_splines('cubic', bm, tknots, knots)
        for index, location in loops_tools.space_calculate_verts(
                bm, 'cubic', tknots, tpoints, indices, splines):
            bm.verts[index].co = location
    bmesh.update_edit_mesh(mesh)
