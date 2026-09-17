# Blender 5.1 port — in progress

Target: Blender 5.1.2 / Python 3.13.9 on macOS. Source: upstream commit
`99496cb` in `patmo141/odc_public`; development takes place on `blender-5.1`
in the `ZAP-Wunschlachen/odc_public` fork.

The scope remains the entire add-on. This is not yet a finished or validated
release. Loading successfully is only the first verification gate.

## Verified so far

- All 117 exposed operator polls tolerate empty, selected-mesh and planned-tooth
  states without exceptions (351 direct class-hook and native poll checks).
- Package-relative imports and annotation-based operator properties.
- Enable, disable, and re-enable; 117 operator declarations resolve at runtime.
- Synthetic model workflows: join/separate, parenting with preserved world
  transforms, material add/remove, decimation, offset magnitude and preservation
  of its source, closed remeshed surface, restoration add/remove, cursor reset.
- Symmetric clearance honors its input distances and refreshes after movement.
  Vertex weights now update from evaluated surfaces instead of two mutually
  dependent proximity modifiers. Original-mesh weights on topology-changing
  sources still need further verification.

## Shared helpers verified with bundled assets

- Object append and link use Blender 5.1 keyword arguments and return the actual
  loaded datablock, including when Blender renames duplicate imports.
- Material enumeration returns material names; material append returns the actual
  loaded material and supports duplicate imports.
- Missing asset names raise an explicit error. Appended objects remain unlinked
  until their caller links them to a collection.
- Shared preferences and selection-button lookup use current APIs; mesh and
  BMesh centroids apply translated, nonuniformly scaled matrices correctly.
- These helper checks do not yet verify their crown/implant callers. Those still
  need migration from name-based lookup and legacy scene APIs.

## Crown import and organization verified

The normal crown import operator loads bundled tooth 25 at the cursor, applies
its insertion-axis world rotation and replaces the previous restoration without
mistaking an existing object named like the library asset for the imported tooth.
Planning references and collection membership survive a saved-file round trip.
Legacy layer organization now creates scene-local ODC role collections, supports
individual planning items and is idempotent without unlinking user collections.
Scene verification clears known missing object references while preserving notes,
restoration types and custom metadata. Active-object selection now calls
`select_get()` instead of comparing the method itself to a boolean.

Pontic import now uses direct entry points to the bundled best-fit flattening and
cubic relaxation algorithms, without requiring separately registered LoopTools
operators. Bundled tooth 25 passes repeated pontic import, closed manifold edge
checks, finite coordinates and nonzero volume for both base and evaluated meshes.
Saved-file round-trip checks pass too. This does not establish anatomical quality,
self-intersection freedom, crown adaptation or manufacturing suitability; visual
review and broader tooth-library fixtures remain outstanding.
Remaining direct legacy layer accesses elsewhere still need migration; role
collections alone do not replace those visibility workflows.

## Dental materials and master assignment verified

Role materials are assigned directly through current material slots, including
when relative paths are enabled. Tests cover preservation of custom materials,
forced first-slot replacement, additional slots and face material indices,
selection, active object, hidden objects, and repeated assignment without duplicate
material imports. The actual Set Master operator resolves a name collision and
stores the final object name, assigns the master material and Models collection.
Set as Prep now supports object assignment, independent master duplication and
selected-geometry extraction using BMesh. Synthetic tests verify transformed world
coordinates, preservation of the master, extracted face count and materials,
actual-name references on collisions, abutment parenting, returning to source edit
mode in the parallel workflow and safe cancellation for an empty selection.
The 3D viewport alignment, multi-object edit behavior and complex scan/modifier
fixtures still require further coverage. Other model assignment operators remain
pending.

## Implemented, not yet verified visually

A package-local GPU adapter replaces legacy immediate-mode drawing. Image
quads use Blender GPU textures. The full interactive display and modal workflows
still require tests in a real Blender window; a successful background import
does not establish that the display works.

## Remaining work

- Migrate and verify legacy scene layers, object visibility/selection, matrix
  multiplication, mesh evaluation and operator context usage across all modules.
- Exercise crown/margin/intaglio/contact workflows, bridges, implants, splints,
  orthodontics, dentures and interactive model operations with suitable fixtures.
- Verify empty-context polls, panels, modal accept/cancel, GPU overlays, asset
  loading, saved-file round trips and add-on lifecycle cleanup.
- Audit all feature declarations in `operator_inventory.json`, retain the full
  upstream functional scope, then package and test installation of the result.

## Running the current checks

Run from this repository with Blender 5.1:

```
blender --background --factory-startup --python-exit-code 1 --python tests/test_registration.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_model_workflows.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_library_helpers.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_crown_import.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_pontic_import.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_dental_materials.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_preparation_assignment.py
```

Tests use synthetic geometry. The port tests do not validate a patient-specific
restoration or define material/manufacturing parameters.
