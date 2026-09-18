# Dundee catalog consumer integration

Implemented in `odc_public/Operators/dundee_cervical.py`, dispatched from `crown_methods.py`, with clear operator warnings and CANCELLED results in `crown.py`. No patient files or geometry were used in the implementation or regression fixtures. No Git commit/push was performed by this subtask.

## Data contract

Prepared crown assets use `odc_library='dundee'`, `odc_topology='triangulated_crown'`. `CEJ` identifies exactly the one open boundary with full `CervicalBlend`. `AnatomyProtected` points are disjoint from the editable blend and remain numerically identical. Blender units are nominal mm; local +X mesial, +Z occlusal; buccal +Y for Q1/Q3, −Y for Q2/Q4. The full original integration contract and measured old-catalog inventory remain in `integration_contract.md` and `existing_catalog_contract.json`.

## Changes

- Marker-dispatched seating accepts an irregular triangulated crown shell. It maps the ordered CEJ onto the accepted closed margin polyline, reproduces affine components exactly, and smooths only the displacement field in the authored cervical blend band. It does not change the upper crown mesh or rely on an `Equator` ring. Repeated seating does not creep. Unlike legacy NEAREST_VERTEX shrinkwrap, it does not collapse hundreds of dense CEJ points onto a smaller margin vertex set. The actual edited geometry is validated and committed; moving the margin later requires re-seating.
- Cervical convergence uses the insertion-axis direction in world space, holds CEJ and protected anatomy fixed, retains tangential components on the scalloped cervical edge, and blends radial rise. A reference attribute plus result hash makes repeated angle changes stable. This is a blended cervical edit, not a claim of an exact conical wall everywhere.
- Proposals are rejected before mesh mutation on bad groups/topology, nonfinite coordinates, excessive displacement, triangle collapse, large face rotation, new sharp creases, or detected nonadjacent triangle intersections. Active modifiers/shape keys must be applied or disabled before cervical editing. These checks protect the template; they do not validate a clinical margin, thickness, cement gap or insertion path.
- Both solid methods dispatch to the same geometry-checked Dundee connector. It removes a **metric 0.15 mm geodesic cervical strip** instead of deleting an assumed four quad rings, joins unequal boundary counts with an ordered zipper, then verifies finite nondegenerate geometry, absence of detected intersections, closed manifold topology and positive volume. The strip width is joining geometry, not cement gap or a material minimum. Failed assembly leaves the previous solid in place. Inconsistent legacy-generated inside winding is fixed in the final joined copy; input coordinates are not edited.
- Solid derivatives retain all actual source/license metadata, including `Source identification review` and mirror provenance.
- Dense Dundee pontic import/conversion now uses a validated rounded cervical closure, retaining every original anatomical vertex. The prior `fill_loop_scale` could leave holes on the dense cropped CEJ. The generic closed pontic remains a tissue-unfitted template; case-specific tissue adaptation is separate. Existing ovate/tissue/presculpt conversion variants remain available and their evaluated meshes were checked.
- The original library/ring implementations remain available unchanged through the legacy assets. Six tests that intentionally use their old circle/sphere/Multires fixtures now explicitly select the archived legacy library. Dedicated new tests cover actual Dundee assets and the new geometry contracts.

## Verification results

`tests/test_dundee_library.py` on the 32-object staging library:

- 32/32 append/import through the actual crown operator passed.
- 32/32 seating on a modest CEJ-shaped test margin passed, including repeated seating, unchanged protected vertices, and zero detected surface self-intersections.
- Maximum numeric vertex-to-test-polyline error was **2.498924704270577e-7 mm**. This is floating-point agreement to a synthetic test curve, **not clinical precision**.
- At a requested 6° cervical angle, 26/32 proposals passed. Six were refused with the complete prior mesh preserved.

| FDI | Geometric reason for the refused 6° proposal |
| --- | --- |
| 12, 22 | New 81.7° cervical crease; source dihedral at that edge was 1.9° |
| 32, 42 | Local triangle rotated 100.1° relative to the source, exceeding the fold guard |
| 35, 45 | New 79.4° cervical crease; source dihedral at that edge was 0.9° |

These are morphology/operation limitations of that requested angle, not hidden successful fits and not evidence that the source crown is defective. The original meshes and source landmarks are preserved. See `convergence_rejections.json` and `convergence_rejections.log`.

New synthetic `test_dundee_cervical.py` passed: irregular triangles, independent object transforms, 37/83-point boundary correspondence, exact anatomy protection, repeatable convergence, refusal of remote margins and degenerate proposals, unequal 43/61-point solid assembly through both operator methods, source metadata retention, and refusal of intersecting inputs without losing the prior solid.

Actual staging consumer tests passed:

- `test_teeth_to_curve.py`
- `test_occlusal_scheme.py`
- `test_prep_from_crown.py`
- `test_pontic_import.py` including replacement, collision, save/reopen
- `test_pontic_conversion.py`, all three variants. An additional independent check of the evaluated resulting meshes found **zero nonadjacent self-intersections in all three**, with minimum twice-triangle-area 0.003464926923216801 in local numeric units.

All six explicitly archived legacy regression tests passed, as did the final synthetic test including attribution retention. Results are logged as `final_test_*.log`. The original pre-change legacy crown seating, convergence and solid tests also passed. Legacy Blender Multires shutdown allocation notices were already present in those old tests and are not a Dundee geometry failure.

The existing `tests/run_headless.py` automatically discovers both new `test_*.py` files. The actual library test accepts an optional path following `--`, or uses the configured default. All generated repository test output stays in the ignored `tests/artifacts` directory.

## Explicit limits from representative inside probes

The real Dundee shells for 11, 25 and 36 can feed the existing Calculate Intaglio operation with synthetic ellipsoidal preparation fixtures. Those artificial inside surfaces are not automatically good fits: the new solid checker correctly rejects bad generated triangles/fit instead of turning them into a nominally closed result. A valid independently built synthetic inside/outer pair passes the same connector. Therefore there is no longer a hard dependency on old quad rings, but neither these probes nor this library work establish clinical intaglio quality or manufacture-ready crowns. Clinical inner surfaces, margins, spacer transitions, undercut blockout, contacts, wall thickness, material and CAM settings remain case-specific.

## Final asset release check

After final cusp/fossa group corrections and thumbnails, the final `final_library.blend` passed `test_teeth_to_curve.py`, `test_occlusal_scheme.py`, and `test_crown_import.py` again (3/3, exit 0). Geometry/CEJ/blend remained unchanged relative to the 32-object fitting audit, independently compared by the main catalog task. Final logs are `final_asset_test_*.log`.
