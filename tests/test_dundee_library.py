"""Load every prepared FDI asset and exercise real anatomy-preserving fitting."""
import importlib
import json
import math
import sys
from pathlib import Path

import bpy
import addon_utils
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
assert addon_utils.enable(ROOT.name, default_set=True)
utils = importlib.import_module(f'{ROOT.name}.Addon_utils.odcutils')
m = importlib.import_module(f'{ROOT.name}.Operators.dundee_cervical')
settings = utils.get_settings()
if '--' in sys.argv:
    settings.tooth_lib = sys.argv[sys.argv.index('--')+1]
expected = {str(10*q+i) for q in range(1, 5) for i in range(1, 9)}
assert set(utils.obj_list_from_lib(settings.tooth_lib)) == expected
scene = bpy.context.scene
results = []
for name in sorted(expected):
    scene.odc_teeth.clear()
    tooth = scene.odc_teeth.add()
    tooth.name = name
    tooth.rest_type = '0'
    axis = bpy.data.objects.new('Dundee fixture axis '+name, None)
    scene.collection.objects.link(axis)
    tooth.axis = axis.name
    assert bpy.ops.opendental.get_crown_form(ob_list=name) == {'FINISHED'}
    obj = bpy.data.objects[tooth.contour]
    assert m.is_dundee(obj), name
    before, faces, edges, boundary, blend, protected = m._validate_contract(obj)
    assert not m._self_intersections(before, faces), name
    # Real nonempty anatomical alignment groups, not placeholder vertex groups.
    cusp = ('Incisal Edge',) if int(name[1]) <= 3 else (
        ('Buccal Cusp',) if int(name[1]) <= 5 else ('Mesiobuccal Cusp', 'Distobuccal Cusp'))
    for group in cusp + ('Mesial Contact', 'Distal Contact', 'Mesial Connector', 'Distal Connector'):
        assert np.count_nonzero(m._weights(obj, group)) > 0, (name, group)
    fossa = 'Palatinal Face' if int(name[1]) <= 3 else 'Middle Fissure'
    assert np.count_nonzero(m._weights(obj, fossa)) > 0, (name, fossa)
    assert obj.scale[:] == (1., 1., 1.)
    target = before[boundary].copy()
    target[:, :2] *= .985
    target[:, 2] -= .05
    mesh = bpy.data.meshes.new('Accepted Dundee fixture margin '+name)
    mesh.from_pydata(target.tolist(), [(i, (i+1)%len(target)) for i in range(len(target))], [])
    margin = bpy.data.objects.new(mesh.name, mesh)
    scene.collection.objects.link(margin)
    margin.matrix_world = obj.matrix_world.copy()
    tooth.margin = tooth.pmargin = margin.name
    assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}, name
    after = m._positions(obj.data)
    assert np.array_equal(before[protected], after[protected]), name
    nearest, _, _ = m._closest_loop(after[boundary], target)
    max_error = float(np.max(np.linalg.norm(nearest-after[boundary], axis=1)))
    assert max_error < 1.e-5, (name, max_error)
    assert bpy.ops.opendental.seat_to_margin() == {'FINISHED'}, name
    assert np.max(np.abs(m._positions(obj.data)-after)) < 1.e-5, name
    assert not m._self_intersections(after, faces), name
    # Convergence can be unsafe for a particular morphology. A conservative
    # rejection must preserve the whole mesh; accepted results preserve CEJ and
    # upper anatomy and must be repeatable. Both outcomes are reported per FDI.
    convergence = bpy.ops.opendental.cervical_convergence(ang=math.radians(6))
    converged = m._positions(obj.data)
    if convergence == {'CANCELLED'}:
        assert np.array_equal(after, converged), name
    else:
        assert convergence == {'FINISHED'}, name
        assert np.array_equal(after[boundary], converged[boundary]), name
        assert np.array_equal(before[protected], converged[protected]), name
        assert not m._self_intersections(converged, faces), name
        assert bpy.ops.opendental.cervical_convergence(ang=math.radians(6)) == {'FINISHED'}
        assert np.max(np.abs(m._positions(obj.data)-converged)) < 1.e-5, name
    results.append({'fdi': name, 'vertices': len(before), 'faces': len(faces),
                    'boundary_vertices': len(boundary), 'margin_max_error_mm': max_error,
                    'protected_vertices': int(np.count_nonzero(protected)),
                    'convergence': sorted(convergence)})
    print('DUNDEE_ASSET_CHECKED', json.dumps(results[-1]), flush=True)
    for item in (obj, axis, margin):
        data = item.data if item.type == 'MESH' else None
        bpy.data.objects.remove(item, do_unlink=True)
        if data is not None and data.users == 0:
            bpy.data.meshes.remove(data)
output = ROOT / 'tests/artifacts/dundee_library.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(results, indent=2)+'\n')
print('ODC_DUNDEE_LIBRARY_PASSED', bpy.app.version_string, len(results))
