"""Read-only Blender QA for a prepared Dundee runtime library.

blender --background --factory-startup --python verify_dundee_library.py -- \
    --library /path/library.blend --output /path/audit.json \
    [--reference /path/staging.blend] [--anchors /path/reviewed_landmark_overrides.json]

No .blend file is written or changed. Optional reference verification checks exact
geometry and all existing cervical/protected groups. Anchors are checked for both
source and mirrored FDI positions, including exact member indices and coordinates.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils.bvhtree import BVHTree

FDI = {str(q * 10 + p) for q in (1, 2, 3, 4) for p in range(1, 9)}
PROTECTED_GROUPS = {
    "CEJ", "CervicalBlend", "Cervical Band", "AnatomyProtected", "Protected Anatomy"
}


def load_library(path):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        names = list(source.objects)
        if set(names) != FDI:
            raise ValueError({"library": str(path), "missing": sorted(FDI - set(names)),
                              "unexpected": sorted(set(names) - FDI)})
        target.objects = names[:]
    return dict(zip(names, target.objects))


def arrays_and_groups(obj):
    vertices = np.array([vertex.co[:] for vertex in obj.data.vertices], dtype=float)
    faces = np.array([polygon.vertices[:] for polygon in obj.data.polygons], dtype=int)
    groups = {group.name: {} for group in obj.vertex_groups}
    names = {group.index: group.name for group in obj.vertex_groups}
    for vertex in obj.data.vertices:
        for membership in vertex.groups:
            groups[names[membership.group]][vertex.index] = membership.weight
    return vertices, faces, groups


def canonical_faces(faces):
    # Preserve winding, while ignoring cyclic corner starts and face ordering.
    ordered = []
    for face in faces:
        start = int(np.argmin(face))
        ordered.append(tuple(np.roll(face, -start)))
    return sorted(ordered)


def topology(obj, vertices, faces, groups):
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    mesh.verts.ensure_lookup_table()
    mesh.faces.ensure_lookup_table()
    boundary_edges = [edge for edge in mesh.edges if edge.is_boundary]
    boundary_vertices = {vertex.index for edge in boundary_edges for vertex in edge.verts}
    boundary_adjacency = {}
    for edge in boundary_edges:
        a, b = [vertex.index for vertex in edge.verts]
        boundary_adjacency.setdefault(a, []).append(b)
        boundary_adjacency.setdefault(b, []).append(a)
    unseen = set(range(len(vertices)))
    components = 0
    while unseen:
        components += 1
        pending = [unseen.pop()]
        while pending:
            index = pending.pop()
            for edge in mesh.verts[index].link_edges:
                neighbor = edge.other_vert(mesh.verts[index]).index
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
    bvh = BVHTree.FromBMesh(mesh, epsilon=1e-9)
    face_sets = [set(face) for face in faces]
    overlaps = sum(a < b and not face_sets[a] & face_sets[b] for a, b in bvh.overlap(bvh))
    result = {
        "vertices": len(vertices), "triangles": len(faces),
        "components": components,
        "euler": len(mesh.verts) - len(mesh.edges) + len(mesh.faces),
        "boundary_edges": len(boundary_edges),
        "boundary_degree_errors": sum(len(neighbors) != 2 for neighbors in boundary_adjacency.values()),
        "boundary_equals_CEJ": boundary_vertices == {i for i, weight in groups.get("CEJ", {}).items() if weight > 0},
        "nonmanifold_nonboundary_edges": sum(not edge.is_manifold and not edge.is_boundary for edge in mesh.edges),
        "degenerate_faces": sum(face.calc_area() < 1e-12 for face in mesh.faces),
        "inconsistent_winding_edges": sum(edge.is_manifold and edge.link_loops[0].vert == edge.link_loops[1].vert for edge in mesh.edges),
        "nonadjacent_self_intersections": overlaps,
        "finite_coordinates": bool(np.isfinite(vertices).all()),
        "identity_transform": bool(np.allclose(np.array(obj.matrix_world), np.eye(4), atol=1e-9)),
        "CEJ_origin_error_mm": float(np.linalg.norm(vertices[list(boundary_vertices)].mean(0))) if boundary_vertices else None,
        "asset_marked": obj.asset_data is not None,
    }
    mesh.free()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--anchors", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    final = load_library(args.library)
    reference = load_library(args.reference) if args.reference else None
    report = {"schema_version": 1, "library": str(args.library),
              "reference": str(args.reference) if args.reference else None,
              "geometry_objects_checked": len(final), "objects": {}, "anchors": [], "failures": []}
    cache = {}
    for fdi, obj in sorted(final.items()):
        if obj.type != "MESH":
            raise ValueError(f"FDI {fdi} is not a mesh")
        vertices, faces, groups = arrays_and_groups(obj)
        cache[fdi] = (vertices, faces, groups)
        result = topology(obj, vertices, faces, groups)
        failed = []
        for key in ("boundary_degree_errors", "nonmanifold_nonboundary_edges", "degenerate_faces",
                    "inconsistent_winding_edges", "nonadjacent_self_intersections"):
            if result[key]:
                failed.append(key)
        for key in ("boundary_equals_CEJ", "finite_coordinates", "identity_transform", "asset_marked"):
            if not result[key]:
                failed.append(key)
        if result["components"] != 1 or result["euler"] != 1:
            failed.append("surface_topology")
        if result["CEJ_origin_error_mm"] is None or result["CEJ_origin_error_mm"] > 1e-5:
            failed.append("origin")
        if reference:
            old_vertices, old_faces, old_groups = arrays_and_groups(reference[fdi])
            geometry_identical = vertices.shape == old_vertices.shape and np.array_equal(vertices, old_vertices)
            faces_identical = faces.shape == old_faces.shape and canonical_faces(faces) == canonical_faces(old_faces)
            checked_groups = {name: groups.get(name) == members for name, members in old_groups.items() if name in PROTECTED_GROUPS}
            result["reference_comparison"] = {
                "vertex_coordinates_exactly_identical": geometry_identical,
                "oriented_triangle_geometry_identical": faces_identical,
                "vertex_array_sha256": hashlib.sha256(vertices.astype("<f8").tobytes()).hexdigest(),
                "cervical_and_protected_groups_identical": checked_groups,
                "Middle_Fissure_unchanged": groups.get("Middle Fissure") == old_groups.get("Middle Fissure"),
            }
            if not geometry_identical or not faces_identical:
                failed.append("reference_geometry_changed")
            if not all(checked_groups.values()):
                failed.append("cervical_or_protected_group_changed")
        report["objects"][fdi] = result
        if failed:
            report["failures"].append({"fdi": fdi, "checks": failed})
    for left in list(range(21, 29)) + list(range(31, 39)):
        right = left - 10 if left < 30 else left + 10
        source = cache[str(left)][0]
        target = cache[str(right)][0]
        exact = source.shape == target.shape and np.array_equal(source * [1, -1, 1], target)
        report["objects"][str(right)]["exact_reflection_of"] = str(left) if exact else None
        if not exact:
            report["failures"].append({"fdi": str(right), "checks": ["mirror_geometry"]})
    if args.anchors:
        anchors = json.loads(args.anchors.read_text())["anchors"]
        for left_fdi, source_groups in anchors.items():
            left = int(left_fdi)
            right = left - 10 if left < 30 else left + 10
            for fdi in (left, right):
                vertices, faces, groups = cache[str(fdi)]
                for name, anchor in source_groups.items():
                    index = anchor["prepared_vertex_index"]
                    coordinate = np.array(anchor["prepared_coordinate_mm"])
                    if fdi == right:
                        coordinate *= [1, -1, 1]
                    position_error = float(np.linalg.norm(vertices[index] - coordinate))
                    included = groups.get(name, {}).get(index, 0) > 0
                    entry = {"fdi": fdi, "group": name, "index": index,
                             "anchor_in_group": included, "position_error_mm": position_error,
                             "anchor_role": anchor["anchor_role"]}
                    if "cusp" in anchor["anchor_role"]:
                        members = [i for i, weight in groups[name].items() if weight > 0]
                        entry["group_max_above_anchor_mm"] = float(vertices[members, 2].max() - vertices[index, 2])
                    report["anchors"].append(entry)
                    if not included or position_error > 1e-5 or entry.get("group_max_above_anchor_mm", 0) > 1e-6:
                        report["failures"].append({"fdi": str(fdi), "checks": ["reviewed_anchor"], "group": name})
    report["anchors_checked"] = len(report["anchors"])
    report["passed"] = not report["failures"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps({"passed": report["passed"], "objects": len(final),
                      "anchors": report["anchors_checked"], "failures": report["failures"]}), flush=True)
    if report["failures"]:
        raise RuntimeError("Dundee library verification failed; see output JSON")


if __name__ == "__main__":
    main()
