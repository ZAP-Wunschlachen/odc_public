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

## Neighbor and opposing references verified

Tests execute mesial/distal assignment for one selected planning item and opposing
assignment for either one item or all items. The global opposing reference is
preserved during individual assignment, and can be assigned before tooth planning.
Missing planning or an invalid active index is handled without an exception.
These checks verify references, not contact adjustment or occlusal geometry.
Registration, model workflows, all operator poll contexts, crown/pontic imports and
preparation assignment were rerun successfully after these changes.

## Insertion-axis placement geometry verified

The placement helper now uses evaluated scene ray casting and current Empty
properties. Tests verify surface hits, view-plane fallback on misses, reuse of an
existing axis, correct world translation/rotation/unit scale under a rotated and
nonuniformly scaled master, and following subsequent master movement. The modal
operator calls this helper. Its selection API, obsolete layer access, previous-tooth
wraparound and Space event handling have been updated. A tested cancellation
session restores existing axis transforms/display and removes newly created axes
while preserving unrelated objects; repeated cleanup is safe. A separate foreground test now invokes the registered operator and sends events
through Blender's window event queue. Space placement, Escape cancellation,
left-click placement, Enter acceptance and removal of the modal handler pass.
Multi-tooth navigation, right-click selection, existing-axis cancellation through
the UI and all viewport configurations still require broader coverage.

## GPU overlay verification

A separate foreground Blender 5.1 instance renders the actual TextBox and insertion
axis arrow callbacks into a GPU offscreen framebuffer. The captured image was
visually inspected: the help text, rounded box and labeled Mesial/Distal arrows
render correctly. This exposed and fixed current tessellation index output,
removed preference access, independent BLF text color and matrix/vector arrow
transforms. Run `blender --factory-startup --python tests/test_overlay_gpu.py`
without `--background`; it closes its own test instance and writes
`tests/artifacts/axis_overlay.png`. It does not yet verify full modal interaction,
other overlays, all display scales or interaction with the scene's drawing state.

## Other display work remains

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
blender --background --factory-startup --python-exit-code 1 --python tests/test_reference_assignment.py
blender --background --factory-startup --python-exit-code 1 --python tests/test_insertion_axis.py
```

Tests use synthetic geometry. The port tests do not validate a patient-specific
restoration or define material/manufacturing parameters.

## Real window event test

Run a separate test instance with
`blender --factory-startup --enable-event-simulate --disable-autoexec --python tests/test_axis_modal.py`.
It uses synthetic scene geometry, exercises actual modal dispatch, asserts scene
results and handler cleanup, then closes that instance. Failure exits nonzero.
The successful run log was also checked for drawing callback exceptions.

## Crown contact assessment

`tests/test_crown_contact_assessment.py` exercises the registered assessment
operator with synthetic planes: the actual restoration receives the modifier,
the library contour stays unchanged, selection stays intact, evaluated weights
match known distances, repeated assessment updates the same modifier, and moving
the target updates the result. Invalid distance ranges cancel without mutation.
The helper now uses native vertex groups and modifier creation without legacy
selection/edit-mode operators. These checks do not yet validate geometric grinding,
self-intersections, cyclic dependencies from other workflows or weight-paint UI.

## Directional contact adjustment

`tests/test_contact_adjustment.py` evaluates actual shrinkwrap output on plane
fixtures for occlusal, mesial and distal projection. It checks requested offset
changes, preservation of source vertices, no duplicate modifiers on repeat calls
and no targetless modifier when a requested neighbor is missing. The original
local-axis directions and offset signs are retained: in the distal fixture the
negative offset projects beyond the target plane, not away from it. Connector
group restrictions, anatomical geometry and rotated/nonuniformly scaled crowns
still need coverage. The assessment and adjustment modifiers may share a display
name; lookup distinguishes their types.

## Margin curve conversion

`tests/test_margin_curve.py` verifies evaluated curve-to-wire conversion using
Blender 5.1 mesh lifetime APIs. A closed Bezier circle produces 200 connected
vertices/edges near the expected radius without changing the source. An open
curve produces 30 vertices/29 edges with preserved endpoints. Beveled surfaces
are rejected rather than misinterpreted as a margin path. The conversion orders
evaluated edges and resamples by arc length. The complete Accept Margin operator,
pseudo-margin extrusion and interactive margin marking remain pending.

## Margin ribbon geometry

`tests/test_margin_extrusion.py` verifies the shared loop extrusion helper on a
world-space circular fixture under translation, rotation and nonuniform scaling.
Both windings produce a 0.2 inward offset followed by a 0.4 outward extrusion,
with 80 vertices, 40 quads and two boundary loops. Distances are computed in world
space and transformed back to local space. Open input rejects before mutation.
This replaces quaternion/scale decomposition and stale BMesh edge-index traversal.
The complete Accept Margin operator and irregular anatomical loops remain pending.

## Accept Margin operator

`tests/test_accept_margin.py` executes the registered operator on a translated
Bezier circle, converts it to a 200-vertex loop and creates the hidden 400-vertex,
200-face ribbon. Repeated acceptance replaces the previous ribbon. An open curve
cancels before changing the original object or prior ribbon and releases temporary
mesh data. Conversion and extrusion finish before scene changes are committed.
Complex anatomical boundaries, linked collections, parented/edit-mode cases and
interactive marking/refinement still require additional coverage.

## Refine Margin operator

`tests/test_refine_margin.py` executes Refine Margin repeatedly with a translated
curve and synthetic preparation sphere. It verifies mesh conversion, preserved
world-space plane, edit mode, current face snapping/proportional editing settings
and a single reused shrinkwrap constraint. The refine-to-accept transition creates
the ribbon and returns to object mode. Interactive dragging, snapping behavior,
complex scans and parented/linked collection cases remain unverified.

## Shared curve manager

Foreground `tests/test_curve_manager.py` exercises real viewport projection for
scene and object surface snapping, three point insertions, point movement and
cancellation with a translated curve object. World-space cached points and local
Bezier coordinates agree after cancellation. Collection linking, current scene
ray casting, matrix multiplication, cursor access and shrinkwrap surface mode are
ported. Hover/edge insertion/deletion, complete margin-marking modal dispatch and
modifier-heavy target fixtures remain pending.

## Curve rebuilding and deletion

`tests/test_curve_topology_edit.py` checks rebuilding under translation and
nonuniform scale, including the previously incorrect first point. Curve settings
are copied, shared original datablocks remain intact, and deletion resets stale
selection/hover indices. Removing all points leaves a restartable empty manager;
curves with fewer than three points are not cyclic. Edge-hover insertion and
complete interactive marking remain pending.

## Curve hover and edge insertion

The foreground curve-manager test now checks point hover and insertion into the
closing edge of a cyclic U-shaped fixture. The same edge is not selectable while
the curve is open. Hover ignores unprojectable points, clears stale state and
chooses the closest qualifying edge. Inserted Blender points agree with cached
world coordinates. Full margin-marking modal dispatch remains pending.

## Margin-marking modal lifecycle

`tests/test_margin_modal.py` uses actual foreground window events to start marking,
place a point, cancel, restart and finish. Cancellation restores the previous
margin reference; exit restores object visibility and frees the slicer's BMesh.
The drawing log is clean after removing an invalid GL_POINTS capability disable.
The extended test now rejects an incomplete outline, adds three points, closes the
contour by clicking the first point and confirms it through the real event queue.
The operator requires at least three points and a cyclic curve before acceptance.
The help text now correctly identifies the first point as the closure target.
Slice interaction and more complex point editing still need verification.
