"""Import bundled GLBs, bake hierarchy transforms and weld exact UV seams.

The source points themselves are never smoothed. FDI26 uses a texture scalar to
identify the crown/root transition; its two internal helper bodies are excluded.
"""
import bpy
import numpy as np
import json

(W / "imported").mkdir(exist_ok=True)
(W / "tooth26").mkdir(exist_ok=True)


def sample_texture_crown26():
    source = bpy.data.objects["Object_4"]
    mesh = source.data
    local = np.array([v.co[:] for v in mesh.vertices])
    faces = np.array([p.vertices[:] for p in mesh.polygons])
    matrix = np.array(source.matrix_world)
    image = bpy.data.images["Image_0"]
    width, height = image.size[:]
    pixels = np.array(image.pixels[:], float).reshape(height, width, 4)
    uv = np.zeros((len(local), 2))
    counts = np.zeros(len(local))
    for loop in mesh.loops:
        uv[loop.vertex_index] += mesh.uv_layers.active.data[loop.index].uv[:]
        counts[loop.vertex_index] += 1
    uv /= counts[:, None]
    x = np.clip(uv[:, 0] * width - .5, 0, width - 1)
    y = np.clip(uv[:, 1] * height - .5, 0, height - 1)
    x0, y0 = x.astype(int), y.astype(int)
    x1, y1 = np.minimum(x0 + 1, width - 1), np.minimum(y0 + 1, height - 1)
    tx, ty = (x - x0)[:, None], (y - y0)[:, None]
    colors = ((pixels[y0, x0] * (1 - tx) + pixels[y0, x1] * tx) * (1 - ty)
              + (pixels[y1, x0] * (1 - tx) + pixels[y1, x1] * tx) * ty)
    vertices, indices, inverse = np.unique(local, axis=0, return_index=True, return_inverse=True)
    averaged = np.zeros((len(vertices), 4))
    counts = np.zeros(len(vertices))
    np.add.at(averaged, inverse, colors)
    np.add.at(counts, inverse, 1)
    averaged /= counts[:, None]
    triangles = inverse[faces]
    scalar = averaged[:, 0] - averaged[:, 2]
    edges = np.unique(np.sort(np.concatenate([
        triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]],
    ]), axis=1), axis=0)
    counts = np.zeros(len(vertices))
    np.add.at(counts, edges[:, 0], 1)
    np.add.at(counts, edges[:, 1], 1)
    band = (scalar > .10) & (scalar < .30)
    for _ in range(20):
        sums = np.zeros(len(vertices))
        np.add.at(sums, edges[:, 0], scalar[edges[:, 1]])
        np.add.at(sums, edges[:, 1], scalar[edges[:, 0]])
        scalar[band] = .5 * scalar[band] + .5 * (sums / counts)[band]
    threshold = .20
    points, new_colors, source_ids = list(vertices), list(averaged), list(indices)
    cuts, clipped = {}, []

    def intersection(a, b):
        key = tuple(sorted((a, b)))
        if key not in cuts:
            t = (threshold - scalar[a]) / (scalar[b] - scalar[a])
            cuts[key] = len(points)
            points.append(vertices[a] + t * (vertices[b] - vertices[a]))
            new_colors.append(averaged[a] + t * (averaged[b] - averaged[a]))
            source_ids.append(-1)
        return cuts[key]

    for triangle in triangles:
        polygon = []
        for j in range(3):
            a, b = int(triangle[j]), int(triangle[(j + 1) % 3])
            inside_a, inside_b = scalar[a] <= threshold, scalar[b] <= threshold
            if inside_a:
                polygon.append(a)
            if inside_a != inside_b:
                polygon.append(intersection(a, b))
        for j in range(1, len(polygon) - 1):
            clipped.append((polygon[0], polygon[j], polygon[j + 1]))
    used = np.unique(clipped)
    remap = np.full(len(points), -1, int)
    remap[used] = np.arange(len(used))
    world = (np.c_[np.array(points)[used], np.ones(len(used))] @ matrix.T)[:, :3]
    np.savez(W / "tooth26/crown_no_root.npz",
             world_vertices=world, faces=remap[clipped],
             colors=np.array(new_colors)[used],
             source_vertex_indices=np.array(source_ids)[used], threshold=threshold)


reports = []
for asset in MANIFEST["assets"]:
    fdi = asset["source_left_fdi"]
    path = SOURCE_DIR / asset["local_path"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    if fdi == 26:
        sample_texture_crown26()
    vertices, faces, colors, parts = [], [], [], []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        mesh = obj.data
        mesh.calc_loop_triangles()
        world = np.array([tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices])
        color = np.ones((len(world), 4))
        attr = next(iter(mesh.color_attributes), None)
        if attr:
            if attr.domain == "POINT":
                color = np.array([tuple(item.color) for item in attr.data])
            else:
                color = np.zeros((len(world), 4))
                counts = np.zeros(len(world))
                for loop, value in zip(mesh.loops, attr.data):
                    color[loop.vertex_index] += value.color
                    counts[loop.vertex_index] += 1
                color /= np.maximum(1, counts[:, None])
        offset = len(vertices)
        vertices.extend(world)
        colors.extend(color)
        faces.extend([tuple(int(i) + offset for i in tri.vertices)
                      for tri in mesh.loop_triangles])
        parts.append({"object": obj.name, "vertices": len(world)})
    raw_vertices, raw_faces, raw_colors = np.array(vertices), np.array(faces), np.array(colors)
    vertices, indices, inverse = np.unique(raw_vertices, axis=0, return_index=True, return_inverse=True)
    colors = np.zeros((len(vertices), 4))
    counts = np.zeros(len(vertices))
    np.add.at(colors, inverse, raw_colors)
    np.add.at(counts, inverse, 1)
    colors /= counts[:, None]
    faces = inverse[raw_faces]
    np.savez(W / "imported" / f"{fdi}_source.npz",
             world_vertices=vertices, faces=faces, colors=colors,
             source_object_vertex_indices=indices)
    reports.append({"fdi": fdi, "file": path.name, "parts": parts,
                    "raw_vertices": len(raw_vertices),
                    "duplicates_welded": len(raw_vertices) - len(vertices),
                    "full_bounds": [vertices.min(0).tolist(), vertices.max(0).tolist()]})
    print("IMPORTED", fdi, path.name, flush=True)
(W / "import_report.json").write_text(json.dumps(reports, indent=2))
