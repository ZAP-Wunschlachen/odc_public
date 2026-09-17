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

## Margin slice geometry

`tests/test_margin_slice.py` verifies slice preparation on a translated, nonuniformly
scaled cube with a separately translated curve. Cached world points are no longer
transformed twice. The shared seeded-section function transforms plane normals
with the model matrix transpose. Slice points lie on the expected world plane,
and the 2D plot fits its intended bounds. Empty selection does not enter slice
mode. Interactive slice movement/drawing and irregular meshes remain pending.

## Interactive slice cancellation

The real-window margin-modal test now enters slice mode with S after closing its
three-point contour, moves the first point using a queued mouse-move event and
checks its coordinate changed. Escape restores the point while the marking tool
remains active; Enter then completes it. The run log was inspected and has no
Python/drawing exceptions. This confirms event integration on the cube fixture,
not visual quality or robustness across irregular preparation scans.

## Bounding-box control lattice

`tests/test_control_lattice.py` verifies local/world bounding-box centers and the
3x3x3 control lattice on an offset mesh with translation, rotation and nonuniform
scale. The padded lattice encloses every source vertex, its undeformed evaluated
result preserves geometry, and moving its control plane changes the evaluated
mesh. Legacy layers, scene linking and scene update calls are removed. Sheared
transforms and the complete crown seating workflow remain unverified.

## Crown seating first integration fixture

`tests/test_crown_seating.py` imports bundled tooth 25, accepts a circular margin
and executes Seat to Margin. Removed scene layers and selection APIs are ported,
as is the translation matrix multiplication. Modifier-copy detection now compares
names to names, avoiding accidentally applying the original modifier. The test
checks that base margin-group vertices lie within 1e-4 Blender units of the target
vertices, all coordinates are finite and Final Seal targets the margin. Repeated
seating, influence behavior, evaluated Multires quality, other library teeth and
anatomical margins remain unverified; this is not a production crown validation.

## Repeated seating

The crown-seating fixture now repeats the operator and checks stable modifier
count and retained base margin alignment. Final Seal is reused. The evaluated
Multires mesh has more vertices than the base and finite coordinates; this does
not establish surface quality or absence of self-intersections.

The control-lattice test also verifies bounding-box face/edge/corner locations and
mean edge spacing in local and transformed coordinates. These helpers now use
full matrix multiplication; empty spacing selections raise a clear error.

## Additional crown-library seating fixtures

The seating test accepts a library tooth identifier after `--`, for example
`blender --background --factory-startup --python-exit-code 1 --python tests/test_crown_seating.py -- 16`.
Tooth forms 11, 16 and 36 pass the same repeated seating, margin alignment and
evaluated finite-coordinate checks as 25. These remain circular synthetic margins.
All three runs report small unfreed memory blocks during Blender shutdown (about
4–5 KB); the source of that shutdown report still needs investigation. The test
assertions pass, but this is not evidence of leak-free operation or anatomical fit.

## Seating diagnostic follow-up

Loading tooth 16 directly from its blend library without enabling the add-on
produced no shutdown memory report. The complete seating fixture still reports
16 small unfreed blocks. Its copied projection modifier is now moved to the start
of the stack before application, removing Blender's non-first-modifier warning.
The tooth 16 repeated alignment/evaluated geometry assertions still pass; the
shutdown allocation source remains unresolved.

`tests/probe_seating_shutdown.py` provides separate `-- prepare` and `-- seat`
stages to investigate the allocation report. The preparation-only run (library
import plus accepted circular margin) exits without the report. One seating call
reports eight blocks (~2.3 KB), versus sixteen after two calls. This narrows the
source to per-call seating work, rather than the asset import or margin acceptance;
it does not yet identify the particular Blender operation or fix the allocation.

The shutdown report is now reproducible without importing or enabling ODC:
`tests/probe_asset_editmode_shutdown.py` loads tooth 16 and performs one native
Edit/Object mode round trip, yielding one 300-byte block at Blender exit. A plain
cube region-selection probe did not report it. This establishes an interaction
between Blender 5.1.2 and the loaded asset/edit-mode path, not a requirement to run
ODC's seating algorithm. Root cause within that path remains unresolved.

## Intaglio helper initial port

`tests/test_intaglio_helper.py` runs the seated-tooth fixture against a synthetic
preparation sphere and calls the interior helper. Evaluated BVH/BMesh access,
delete enums, matrix products, linking, selection, shrinkwrap surface mode and
new edge indexing have been updated. Initial execution creates the interior.
The test additionally checks zone groups, cement-gap modifier assignment and
finite evaluated geometry; exact gap geometry, full operator integration, failure
cleanup and anatomical fit remain pending.

The intaglio fixture now invokes the registered Calculate Intaglio operator with
`no_undercuts=True`. Scene layers and viewport pivot access are migrated; required
object references are checked before generation. The test also verifies missing
axis cancellation preserves the existing interior. The alternate
`no_undercuts=False` implementation remains unported and is not validated here.

## Cement-gap geometry measurement

The intaglio test now measures every fully weighted Filled Zone vertex on the
evaluated interior against the triangulated, unscaled preparation sphere. At
0.07 model units it measures 0.0696106–0.0699998; at 0.12 it measures
0.119333–0.120000. The test requires maximum error below 0.001 model units and
checks both settings. This tests distance magnitude on the synthetic sphere, not
signed clearance, scaled-object compensation, transition width or clinical fit.

The cement-gap fixture also checks positive signed separation along the nearest
preparation face normals at both tested offsets. All fully weighted Filled Zone
vertices lie outside the synthetic surface. Holy Zone and Filled Zone memberships
are nonempty and disjoint. This does not measure the physical Holy Zone width or
prove absence of face intersections between sampled vertices.

Repeated protected-path intaglio generation now replaces the prior interior only
after the new object and modifiers have been constructed, and removes its mesh
when unused. The integration fixture verifies stable object count and the updated
gap setting on the replacement. Required preparation/margin/axis/crown objects
are excluded from deletion if an old reference is misassigned.

## Local-coordinate reorientation

`tests/test_reorient_object.py` verifies the shared reorientation helper used by
alternative intaglio construction. Direct data transforms replace legacy context
overrides and scene updates. A mesh under a rotated/scaled parent retains world
vertex positions and parent identity while adopting the requested world rotation;
shared mesh data is copied before modification. Curve control points also retain
world positions. Constraints and evaluated modifier preservation remain untested,
and the complete alternative intaglio path is still pending.

## Alternative intaglio first integration

`tests/test_alternate_intaglio.py` invokes Calculate Intaglio with
`no_undercuts=False` on the same seated-tooth/sphere fixture. Current selection,
hiding, normal recalculation and shrinkwrap settings replace removed APIs. Mesh
references are refreshed after modifier application before filling. The run
produces faces and zone groups with finite evaluated coordinates and the requested
gap setting. Exact clearance, repeated generation, cleanup and anatomical quality
remain unverified for this alternative path.

## Alternative intaglio regeneration

The alternative path now keeps the duplicate object directly instead of looking
it up by a requested name that may belong to the previous interior. On successful
completion it stores the actual new name and removes the previous interior and
its unused mesh. Modifier application iterates over a snapshot of the stack.
The Blender 5.1.2 integration test builds twice with different gap settings,
checks stable object count, removal of the previous object/mesh, zone groups,
faces and finite evaluated coordinates. It passes. This does not yet establish
measured clearance or failure rollback. Blender still reports a small allocation
at shutdown, consistent with the separately documented asset/edit-mode diagnostic;
this run is not evidence of leak-free operation.

## Cervical convergence

The operator now uses current visibility, selection, active-object and quaternion
APIs and no longer accesses removed scene layers. The ring-orientation condition
now recognizes either ordering of an existing vertical edge. The integration test
runs two requested angles on bundled tooth 25 and independently checks adjacent
boundary edges: angle to the insertion axis, preserved length and unchanged
boundary coordinates. Blender 5.1.2 passes. Nonuniform scaling, malformed boundary
loops and alternate crown topology remain unverified. The known small shutdown
allocation warning also appears in this edit-mode workflow.

## Solid restoration, bridge method

The default solid-restoration method now evaluates source meshes through the
current dependency graph, uses named BMesh deletion contexts and current collection
linking. The BMesh join helper uses matrix multiplication with `@`. Newly subdivided
vertices receive updated indices before the CEJ group is assigned. The operator
no longer uses scene layers. `test_solid_restoration.py` runs the protected intaglio
fixture followed by the actual default solid operator in Blender 5.1.2; the result
has faces, finite coordinates and exclusively manifold edges. This establishes
closure only on the synthetic tooth-25 fixture, not freedom from self-intersections,
clinical fit, repeated-build cleanup or the alternative merge method. The known
small edit-mode shutdown allocation warning remains.

## Solid restoration, merge method

The alternative merge method uses current active-object, visibility and selection
APIs. Objects must be unhidden before selection; otherwise a hidden crown was
omitted from duplication and joining. The parametrized integration test accepts
`-- 25 0` for the merge method (default remains the bridge method). Blender 5.1.2
passes the same finite-coordinate, nonempty-face and manifold-edge checks on the
synthetic fixture. Self-intersections and repeated-build cleanup remain pending.
The existing small shutdown allocation warning remains.

## Reproducible headless regression suite

Run `python3 tests/run_headless.py --blender /path/to/blender` to execute all
headless test scripts in separate factory-startup Blender processes, including
both solid-restoration methods. The runner records per-case logs and JSON under
`tests/artifacts/headless`, rejects nonzero exits, tracebacks and timeouts, and
records shutdown allocation warnings separately. Four foreground GPU/modal tests
are explicitly excluded and still require their separate commands.

On Blender 5.1.2, all 26 cases passed after the merge-method port; seven cases
reported the known shutdown allocation warning. This verifies existing test
coverage only. It does not establish compatibility of the entire operator
inventory; unported functions and untested UI paths remain outstanding.

## Crown lattice operator

The Crown Lattice operator no longer accesses removed scene layers. The existing
control-lattice geometry test now invokes the public operator rather than only
the helper. Blender 5.1.2 passes enclosure, unchanged initial geometry, actual
control-point deformation, repeat invocation without duplicate modifiers/objects,
and multi-object selection with a non-mesh reference. Degenerate bounding boxes
and exclusion from the active view layer remain untested.

## Scene state prerequisite for remaining crown tools

The shared scene preservation helpers now use view-layer visibility/selection,
current tool settings and object mode identifiers. Snap element sets and mesh
selection arrays are captured independently; deleted objects are tolerated when
restoring. New objects retain their visibility and are deselected. The headless
Blender 5.1.2 test verifies edit-mode restoration, selection, hidden objects,
snapping, pivot and deleted active-object handling. Foreground gizmo restoration,
custom transform orientations and multi-object edit sessions remain unverified.
The separate pontic conversion operator still requires its geometry-path port;
this change only repairs its shared state-management prerequisite.

## Public pontic conversion

The separate pontic conversion path now uses current selection, visibility,
active-object, cursor, display, pivot and matrix APIs. The public operator test
runs OVATE, TISSUE and PRESCULPT on fresh bundled tooth-25 crowns. Blender 5.1.2
passes finite evaluated geometry, manifold edges, nonzero volume, tissue group,
variant target/offset configuration and active-object restoration checks.
Measured tissue clearance, repeated conversion of the same crown and rotated-axis
behavior remain unverified. The known small allocation warning appears at shutdown.

## Preparation from crown

The public prep-from-crown path now uses current object selection/visibility,
view-layer updates, matrix multiplication, closest-point dependency graph,
BMesh normal recalculation and in-front display. Removed scene-layer accesses
are gone and modifier application iterates over a snapshot. Blender 5.1.2 passes
the new operator test on bundled tooth 25: source geometry is preserved, a separate
mesh with margin/fill groups is created, reduction target/offset are configured,
and evaluated coordinates are finite. Measured reduction, explicit curve margins,
rotated/scaled cases and failure cleanup remain unverified. A small shutdown
allocation warning is still emitted.

## Implant/drill/orthodontic library prerequisite

The default drill library pointed to nonexistent `odc_drill_lib.blend`; it now
points to the shipped `odc_drill_library.blend`. The library integration test
loads every object from all three additional default libraries and checks for
nonempty mesh content: 45 implant objects, 27 drill/sleeve objects and 23 bracket
objects load in Blender 5.1.2. This verifies asset access only; placement operators
still contain obsolete scene updates and collection-as-layer mutations and need
separate porting and execution tests. Existing user-customized paths are unchanged.

## Guide sleeve placement

Guide sleeve placement now uses current library returns, view-layer updates and
object removal. It no longer mutates collection entries as though they were old
scene layers, or clears the implant's users when replacing a sleeve. The enum
reads the actual library and retains item strings. Existing sleeves are removed
only after their replacements have been loaded and positioned. Blender 5.1.2
passes a public-operator test for two depths on a rotated/translated implant,
orientation, parenting, stable object count and missing-implant cancellation.
The search popup, multi-implant load failure rollback and scaled implant cases
remain untested; drill placement is still pending.

## Drill placement

The drill operator now follows current object/library APIs, with an actual poll
and retained library enum items. Removed object layers and collection-as-layer
writes are gone. Replacements are loaded and positioned before the previous drill
is removed, and implant users are preserved. Blender 5.1.2 passes the public test
for negative and positive depths on a rotated/translated implant, orientation,
parenting, stable object count and missing-implant cancellation. Popup interaction,
scaled implants and multi-implant failure rollback remain unverified.

## Implant inner cylinder, initial port

The public inner-cylinder operator no longer treats collection entries as scene
layers. Its helper uses current collection linking, view-layer updates and
quaternion multiplication. The shared cylinder primitive uses the current BMesh
`radius1`/`radius2` arguments. Blender 5.1.2 passes repeated creation with diameters
5 and 3: measured local diameter and length, manifold edges, parenting and stable
object count. Projection-group membership (currently based on vertex parity),
world positioning, automatic diameter and outer-cylinder generation still require
additional tests and review.

## Inner-cylinder geometric follow-up

The expanded Blender 5.1.2 test confirms that the current cone primitive's odd
indices select exactly the complete upper cap, so no corrective group change was
necessary. It also verifies world translation and orientation against the existing
implant-relative offset formula, plus automatic diameter and stable object count.
These checks pass for the rotated/translated unit-scale fixture. They do not
establish anatomical apex conventions or behavior under scaled/parented implants.

## Outer guide cylinder, initial port

The public guide-cylinder operator no longer writes collection entries as layers.
The helper uses current linking, view-layer updates and quaternion multiplication,
and clears modifiers through a stable list. Blender 5.1.2 passes round and flattened
fixtures: measured width, trimmed width and height, manifold edges, complete upper
projection cap, parenting and stable object count. Wedge geometry, splint projection,
changed depth on regeneration and transformed-parent cases remain pending.

## Guide-cylinder depth regeneration

A regression test changing depth from 20 to 15 failed because placement only ran
when creating a new object. World placement now updates on every invocation using
the implant world orientation and requested axial offset. The same test passes in
Blender 5.1.2, including orientation, geometry dimensions and stable object count.
Scaled/parented implants and projection to splint geometry remain outstanding.

## Guide-cylinder wedge verification

The public outer-cylinder test now exercises quarter, 65-percent and 90-percent
wedges and the full-circle fallback. Blender 5.1.2 passes manifold edges, finite
coordinates, complete upper-cap group, stable object count and volume compared
with the analytic volume of the existing 64-segment polygonal sector. No additional
API change was needed. Fractions below 0.1 still use the upstream full-circle
fallback; whether that UI behavior should change requires separate review.
Splint projection remains untested.

## Guide-cylinder splint projection

The outer-cylinder integration test now creates a plane parallel to the cap in a
rotated/translated frame and invokes the public operator with a splint reference.
Blender 5.1.2 evaluates the upper cap from local z=0.1 to z=1.5 against a plane at
z=2: the existing 0.5 offset keeps it on the source side. Lower-cap coordinates
and upper-cap x/y coordinates remain unchanged. This establishes the actual
projection behavior on a plane, not clinical clearance or intersection quality
against curved splints. No code correction was required for this tested path.

## Implant placement helper

The shared placement helper now loads the implant and hardware before replacing
an existing assembly, uses current linking/removal and accepts matrix or quaternion
orientation. Unused new library-parent dependencies are removed after hardware is
reparented. Blender 5.1.2 passes location/orientation, linked hardware, stable object
count on replacement and missing-asset preservation. Public placement operators,
master parenting, mid-load failure cleanup and user-attached child ownership still
need review. This is helper coverage, not completion of the placement UI.

## Public implant placement

The public placement operator now uses a retained library enum and the current
assembly helper instead of duplicated legacy linking/deletion code. Removed layer
writes are gone. Local bounding-box length and world transforms preserve the
upstream platform convention when replacing a rotated implant. Blender 5.1.2
passes first placement at the cursor platform and replacement with a second
library asset while preserving platform and orientation. Standalone placement,
search popup, scaled/master-parented cases and hardware world transforms require
further tests. The platform convention itself is not a clinical validation.

## Implant from crown

The crown-driven placement operator now provides a retained library enum and
removes obsolete collection-as-layer accesses. Its depth expression no longer
attempts matrix multiplication on an integer. Local implant length and an explicit
world-matrix assignment position the platform below the crown bounding-box CEJ
reference. Blender 5.1.2 passes two depths with a rotated/translated crown fixture,
checking platform position and axis direction. Explicit insertion-axis overrides,
missing-input reporting, multi-tooth selection and UI interaction remain pending.

## Implant view operators and regression

All 36 existing headless cases passed after the implant placement changes.
A new foreground test invokes slice view and normal view in a real VIEW_3D region,
verifying four quad views, requested clip interval and return to a single view.
Both operators now poll for the correct area/region. Blender 5.1.2 passes this
foreground test without tracebacks. The headless runner excludes it explicitly.
This checks view switching, not clinical cross-section interpretation or every
other interactive workflow. Full plugin compatibility remains incomplete.

## Bridge selection

Bridge resolution now checks named RNA object roles rather than indexing
ID-property views or uninitialized variables. It handles absent active objects,
role exclusions and duplicate matches while preserving member-tooth fallback.
Blender 5.1.2 passes public bridge definition from two selected units, member
resolution, direct object role matching, unrelated metadata rejection and list
selection. The geometry-producing bridge operators remain to be ported.

## Pre-bridge initial integration

Make Pre-Bridge now uses current selection, visibility and active-object APIs;
removed scene layers are gone and modifier loops use snapshots. Blender 5.1.2
passes a two-library-tooth public-operator fixture without margins, verifying a
separate combined mesh, summed vertex count, connector/margin groups, smoothing
modifier and retained source objects. Source modifier application still follows
upstream behavior; source geometry preservation, real margins, repeated creation
and connector construction are not yet verified. The small edit-mode shutdown
allocation warning remains.

## Pre-bridge with accepted margins

The integration fixture now accepts and seats two separate circular margins before
invoking Make Pre-Bridge. Blender 5.1.2 passes combined margin vertex count, world
coordinate preservation (nearest-vertex comparison), retained original margins and
the bridge shrinkwrap target. The run reports that applied modifiers were not first
in the stack; source/evaluated geometry preservation must be reviewed before this
path can be considered fully validated. The known shutdown allocation warning also
appears. These tests establish margin assembly, not final bridge quality.

## Pre-bridge source preservation

Pre-bridge modifier baking now happens after duplication and only on the copies.
Each non-Multires modifier is moved to the first stack position before application,
removing the non-first-modifier warning in the seated-margin fixture. Blender 5.1.2
passes the expanded test asserting unchanged source vertex coordinates and modifier
names/types, in addition to the previous combined mesh/margin checks. Detailed
evaluated-surface equivalence and all possible modifier stacks remain unverified;
the known small shutdown allocation warning persists.

## Keep Shape, lattice integration

Keep Shape now uses current active-object/visibility APIs and captures lattice
targets before applying and invalidating modifiers. It preserves controls still
used by another lattice modifier and removes unused lattice data after the last
application. Blender 5.1.2 passes evaluated-to-baked coordinate equivalence, shared
control preservation and final cleanup. Mixed modifier stacks, Multires/shrinkwrap
interaction and controls used through constraints or other mechanisms still need
review; this test establishes the lattice-only workflow.

## Keep Shape reference cleanup

Control cleanup now consults Blender's ID user map rather than only lattice
modifiers. Object-level constraint references and fake users retain the control;
collection/scene membership alone does not. If the deleted control was active,
the processed mesh becomes active. Blender 5.1.2 passes the expanded shared-lattice,
constraint-target and active-control tests. Scene-level custom references and
other specialized data-block ownership cases remain unverified.

## Break Contact slice path

The slice path uses current quaternion multiplication, display, collection linking
and modifier positioning. An overlapping-cube test exposed that positive shrinkwrap
offsets retained overlap; offsets now cross the separator plane, giving the requested
per-side clearance. Blender 5.1.2 passes a measured 0.4 gap for sep=0.2 and unchanged
outer faces. DEFORM, the Apply option, rotated/nonconvex geometry and repeated use
remain pending. This test establishes the slice path only.

## Break Contact deform path

The deform helper uses current quaternion/linking APIs and receives the previously
ignored separation property. Negative projection offsets cross the separator.
Cardinal interpolation replaces B-spline attenuation for this operation: the cube
fixture otherwise retained overlap. Blender 5.1.2 now measures separated extents
at approximately -0.07167/+0.07167 for separation=0.2. This is a soft deformation,
not an exact-clearance operation. The test verifies separated bodies and lattice
modifiers; anatomical meshes, overshoot, Apply and repeated invocation remain
unverified. The slice path remains the measured per-side-clearance test.

## Break Contact Apply option

The previously ignored Apply option now bakes only modifiers created by the current
contact operation and removes its unused controls/separator. The operator polls for
two meshes in Object mode. Blender 5.1.2 passes both DEFORM and SLICE with Apply,
checking separated baked vertices, no remaining operation modifiers, unchanged
object count and restored active object. Mixed pre-existing modifier stacks and
partial application failure cleanup remain unverified.

## Boolean bridge integration

Boolean bridge mesh evaluation now uses dependency-graph objects and persistent
`new_from_object` meshes. Current collection linking/removal replaces old APIs,
and superseded temporary meshes are removed when unused. Blender 5.1.2 passes
left-only, right-only and midline-spanning fixtures with overlapping cubes,
verifying manifold edges and the analytic union volume of 12. Anatomical open
crowns, repeated-build replacement, missing input handling and final restoration
assembly remain unverified.

## Boolean bridge regeneration

After successful assembly, the previous bridge object and its unused mesh are
removed unless the object is also an input contour. The operator poll now handles
an empty bridge selection without indexing it. Blender 5.1.2 passes repeated builds
for left, right and midline fixtures, verifying stable object counts, old mesh/object
removal and unchanged analytic union volume. Partial evaluation failure rollback
and anatomical mesh behavior still require verification.

## Solidify Bridge initial integration

Solidify Bridge uses dependency-graph mesh evaluation, named BMesh delete contexts,
current collection/selection APIs and the current from_mesh signature. Missing
shell/intaglio inputs return before geometry mutation; renamed final objects update
bridge references. Blender 5.1.2 passes a one-abutment integration fixture using a
seated crown and calculated intaglio, yielding manifold geometry. Multi-unit shells,
pontics, repeated solidification and temporary mesh cleanup remain unverified.
This is initial operator coverage, not validation of a complete multi-unit bridge.

## Solidify Bridge input and mesh cleanup

Superseded shell meshes and temporary joined interior meshes are removed when
unused. Redundant late input checking was removed in favor of the existing
preflight. Blender 5.1.2 verifies that a missing interior preserves shell vertices,
modifiers and object count, and that successful assembly introduces no new unused
mesh data-blocks. The manifold-result check still passes. Multi-unit assembly and
mid-operation failure rollback remain outstanding; the known native shutdown
allocation warning is separate from unused mesh data-block accounting.

## Keep Arch Plan

The helper uses current view-layer updates and identifies FOLLOW_PATH constraints
by type and target instead of their display name. Blender 5.1.2 passes a public
operator test with a renamed path constraint, translated/rotated parent, world
matrix preservation and repeat invocation. Other remaining constraint stacks,
animated transforms and multi-object arch generation still require testing.

## Connector helper initial port

`bridge_loop_2` uses current active-object/visibility APIs, bundled LoopTools relax
and BMesh normal recalculation. Blender 5.1.2 passes a two-box connector fixture:
the resulting mesh has manifold edges and a single connected component. Modal
Bridge Individual interaction, anatomical connector groups, parameter mapping
(segments/twist/cubic currently follow upstream behavior) and repeat edits remain
unverified. This establishes the helper path, not the complete connector workflow.

## Connector path actually used by Bridge Individual

Call-site review confirmed that Bridge Individual invokes `bridge_loop`, not
`bridge_loop_2`. That SURFACE-interpolation path now also uses current selection
APIs, bundled relax and BMesh normal recalculation. Its separate Blender 5.1.2
test passes manifold edges and a single connected component on the two-box fixture.
The earlier test covered only the alternate PATH helper. Modal interaction and
parameter mapping remain outstanding for the actual user workflow.

## Surface connector parameter mapping

The active `bridge_loop` path now maps segment count to bridge subdivisions,
twist to twist_offset and cubic/bulbous strength to SURFACE smoothness instead of
hardcoding them. Blender 5.1.2 tests show increased vertices with more segments
and changed geometry with twist and strength, with manifold edges in all fixtures.
The existing connected-component surface test also passes. The alternate PATH
helper, separate UI smooth property, modal parameter interaction and anatomical
shape quality still require work.

## Connector smoothing control

Bridge Individual now passes its smooth property to the connector helper instead
of always relaxing three times. The helper preserves three iterations as its
default for existing callers and accepts zero iterations. Blender 5.1.2 passes
the parameter test showing different vertex coordinates for zero versus five
iterations alongside the existing segment/twist/strength checks. Modal UI testing
and anatomical connector-quality checks remain outstanding.

## Bridge Individual foreground execution

A separate foreground Blender 5.1.2 test invokes Bridge Individual on named
24/25 connector groups, sends Space through window event simulation, checks new
connector vertices and sends Enter. The modal handler is removed and the log has
no tracebacks. The headless runner excludes this foreground test. Scroll navigation,
Escape semantics, repeated connector edits and anatomical fixtures remain untested.

## Bridge Individual input guards

Invoke rejects fewer than two or nonnumeric bridge units before adding a draw/modal
handler, and execute checks required connector groups before geometry mutation.
The Blender 5.1.2 foreground test now verifies single-unit cancellation without a
modal handler followed by successful normal invocation, Space execution and Enter.
Missing-group messaging is guarded in code but not yet exercised by this test;
neighbor navigation and Escape rollback remain outstanding.

### Bridge connector modal cancellation

The interactive connector now edits a private mesh copy. Escape restores the original mesh datablock and removes the working copy; Enter commits and removes the unused original. Shared original meshes remain intact. Invocation is restricted to Object mode, and the help text now documents the actual Space/Enter/Escape controls.

Validation: `tests/test_bridge_modal.py` passed in a Blender 5.1.2 window with simulated events: invalid single-unit input cancels, Space creates geometry, Escape restores original mesh identity and coordinates with stable mesh count, and a fresh session commits with Enter and stable mesh count. This does not yet verify all bridge navigation or repeated connector selections.

### Teeth along an arch curve

Ported `teeth_to_curve` object activation, visibility, collection linking, dependency updates, matrix/quaternion products, and library object identity handling. Replacement removes mesh data only when unused, and newly created Follow Path constraints are addressed directly. Updated the shared vertex-group selection helper to current object APIs.

Validation: `test_teeth_to_curve.py` passes on Blender 5.1.2 using the bundled 14 upper-arch teeth across COM, BUCCAL and FOSSA alignment, including repeated replacement. Checks cover finite transforms, nonzero dimensions, one path constraint per tooth, and spatial distribution. Anatomical orientation, exact curve placement, lower arches, mirroring, linked restorations and the public modal workflow remain unverified. Blender reports a small shutdown allocation warning (32 blocks).

### Public Teeth to Arch operator

Removed obsolete scene-layer access and ported active-object/selection restoration in `opendental.teeth_to_arch`; polling now requires Object mode. The arch placement test now invokes the public operator for both MAX and MAND, each with BODY, BUCCAL and FOSSA alignment. All six executions pass under Blender 5.1.2, including repeated replacement and restoring the curve as active object. This covers operator execution, not the properties dialog or anatomical correctness. Shutdown allocation warning persists (64 blocks in this expanded run).

### Linked arch placement repetition

Reuses an existing Follow Path constraint targeting the selected arch and removes duplicate constraints for that same arch, preserving unrelated constraints. Extended the public operator test with two working teeth (11/21), `link=True, limit=True`, and repeated execution. Blender 5.1.2 passes object identity, contour references, exactly one path per retained tooth and absence of unrequested planned teeth. This does not establish repeated geometric invariance, which remains to be checked.

### Occlusal scheme initial execution

Ported the public occlusal scheme operator away from scene layers and legacy selection. The helper uses evaluated mesh extraction, current BMesh dependency-graph arguments, matrix products, collection linking and actual returned library objects. Its temporary curve mesh is released, replacement mesh deletion respects users, and contact-group checks require both groups.

Validation: `test_occlusal_scheme.py` executes the public operator with the bundled tooth library and a semicircular arch under Blender 5.1.2. It produces 28 teeth with finite transforms and positive scales, including execution of anterior cross-section measurement. This is initial execution coverage only: anatomical intercuspation, linked/repeated placement, mirror/reverse options and exact geometry remain unverified. Small shutdown allocation warning persists.

### Occlusal scheme Link option

The public operator now forwards its Link setting and requires Object mode. The helper reuses a valid contour and imports/assigns a replacement for empty or stale contour references. Extended `test_occlusal_scheme.py` passes in Blender 5.1.2 with an existing posterior contour, an empty anterior reference and a missing lower-arch reference in one invocation. It verifies retained object identity, valid resulting references, finite transforms and 28 planned objects. Repeat geometric stability and transformed anterior cross-sections remain unverified.

### Regression after arch placement ports

Expanded the occlusal Link fixture to reuse a translated and rotated anterior tooth (11), exercising its cross-section path. The operator passes identity, reference and finite-transform checks; this is not a geometric invariance assertion.

Ran `python3 tests/run_headless.py --blender /Applications/Blender.app/Contents/MacOS/Blender` after these changes: all 50 headless integration cases passed, process exit 0. Detailed local results are in ignored `tests/artifacts/headless/results.json`. UI tests are excluded by the runner. Remaining legacy APIs in other modules and untested workflows prevent claiming a complete plugin port.

### Denture meta scaffold and surface

Ported scaffold and meta-surface dependency graphs, mesh extraction, collection linking and deletion. Polls require meshes; scaffold rejects empty-edge meshes or nonpositive radius. Meta surface now builds its BMesh in execute, freeing dialog preview data immediately. Distinct metaball family names prevent subsequent surfaces from evaluating as empty family members.

`test_meta_surface.py` passes on Blender 5.1.2: reduced scaffold vertex count, world-transform preservation within tolerance, nonfinalized ball positions/radii, finalized nonempty mesh while an earlier meta surface exists, and unchanged source mesh coordinates. No shutdown warning in this test. Tray/rim and further denture workflows remain unported.

### Custom tray outer envelope

The custom tray operator now delegates its identical outer-envelope generation to the ported meta-surface operator using radius = thickness + offset. This preserves the original outer-only behavior; the original inner-spacer block was commented out. Dialog BMesh data is released immediately and polling requires a mesh. Extended `test_meta_surface.py` passes both META and finalized MESH outputs, configured ball radius, element count and nonempty polygon output with other meta surfaces already present. Exact physical spacer/wall thickness and the separate Boolean Intaglio workflow remain unverified.

### Simple offset surface

Ported evaluated mesh extraction, collection linking and Shrinkwrap ABOVE_SURFACE mode. Fixed the chained legacy property assignment so Smooth and Shrink register independently. Both offset paths copy normals before changing coordinates; the in-place mesh is updated explicitly.

`test_simple_offset_surface.py` passes on Blender 5.1.2: all four smooth/shrink combinations, unchanged source for duplicate mode, expected modifier counts, raw and evaluated planar offset +0.4, and in-place offset -0.2. Curved geometry, self-intersections and nonuniform object scale are not validated by this planar fixture.

### Denture Boolean Intaglio

Replaced invocation-only target enumeration with retained dynamic enum items from scene meshes, excluding the active object and offering an explicit empty choice. Polling requires a mesh in Object mode; execution validates the target before creating an Exact Difference modifier. Corrected the operator label.

`test_denture_boolean.py` passes on Blender 5.1.2: empty selection cancels without modifier creation; direct execution with a master cast creates a manifold hollow result with signed volume 56 for nested cubes of volumes 64 and 8. Source meshes remain unbaked. Anatomical tray geometry and dialog interaction remain unverified.

### Meta wax rim

Ported evaluated curve mesh extraction and collection linking, releases temporary mesh data, validates two usable edge paths before creating a result, and uses independent metaball family names. Invalid spline counts now produce a user-facing warning. Removed obsolete commented conversion code.

`test_meta_rim.py` passes in Blender 5.1.2 for CUBE and ELLIPSOID elements on two semicircular paths: correct element midpoint and half-height, more than 50 elements, nonempty evaluated surface for both simultaneous results, no temporary mesh accumulation, and no created objects on an invalid empty curve. Degenerate, cyclic, bevelled and intersecting path cases remain unverified.

### Meta input validation

Meta surface validates positive radius/resolution and an evaluated source with vertices before allocating result objects. Custom tray validates positive thickness and nonnegative offset separately. The expanded meta-surface test passes valid workflows plus zero/negative parameters and empty source meshes, checking stable object/mesh/metaball counts on rejected surface/scaffold operations.

### Orthodontic visibility and treatment stages

Ported the four jaw/side visibility operators to view-layer hide_set and view-layer object iteration. Treatment staging uses direct location/rotation keyframe insertion with rotation-mode-specific paths, avoids deprecated keying-set operators and handles no visible teeth by cancellation. It no longer changes object selection.

`test_ortho_staging.py` passes on Blender 5.1.2: upper/lower/right/left visibility, upper master toggle, empty-stage cancellation, two-frame position restoration with Euler/quaternion objects, exclusion of hidden lower teeth and unnumbered masters. Rotation interpolation, armature workflows and treatment UI remain unverified.

### Root parenting and adjustment

Ported armature activation/visibility, PoseBone selection and constraint context overrides for root parenting. Adjust Roots validates the armature and supported mode, reveals/selects it and enters armature Edit mode. `test_root_parenting.py` passes in Blender 5.1.2: initial pose preserved with nonidentity tooth/armature translations, root follows a two-unit tooth displacement, repeated setup retains one constraint, and a hidden armature can be opened for adjustment. Jaw proximity deformation, multiple roots and root creation remain unverified.

### Root-to-cast deformation coverage

Extended `test_root_parenting.py` through `link_to_cast=True` with an UpperJaw mesh. Blender 5.1.2 passes repeated setup without duplicate armature/proximity modifiers, correct modifier order, bone vertex-group creation, measurable X deformation after tooth movement with unchanged Y/Z, and unchanged base mesh coordinates. This synthetic single-root test establishes functioning dependency propagation, not anatomical gingival simulation accuracy or lower/multi-root coverage.

### Simple orthodontic base

The base operator now searches boundary edges and chooses the largest closed loop, cancels cleanly when no suitable loop exists, and explicitly updates mesh data. `test_ortho_base.py` passes on Blender 5.1.2: a closed cube cancels without coordinate changes; removing its bottom and adding a -2 base produces a manifold volume-16 solid with expected Z bounds [-3, 1]. Multiple boundaries, curved casts and nonuniform transforms remain unverified.

### Physics scene and rigid-body setup

Replaced legacy scene linking/screen scene assignment with tagged object copies, collection linking and window scene switching. Copies retain world placement with parent/constraints/animation cleared; mesh data remains shared as in the original single-user-object workflow. Rebuild removes only tagged copies from simulation collections and deletes them only if unused. Rigid-body setup uses current active/selection APIs and filters meshes.

`test_physics_scene.py` passes on Blender 5.1.2 for initial and repeated setup: one independent object copy, same mesh and world matrix, intact source scene object, rigid-body settings on the copy only, and disabled gravity. Actual simulation dynamics, forcefields and animated/deformed sources remain unverified.

### Forcefield API port — simulation cycle still open

Ported forcefield object linking/selection/activation. Tagged fields are reused per parent tooth and cleaned with simulation copies on rebuild. The expanded physics-scene test passes field count, parent-relative world position, FORCE type, strength and radius checks across repeated setup. However Blender reports a dependency cycle: a field parented to a simulated rigid body affects that same simulation. Thus the API/setup test passes but forcefield dynamics are not validated; the inherited simulation design still needs correction. Do not treat this as a completed physics workflow.

### Physics movement controls — basic API coverage

Ported quaternion-vector products in movement limits and removed obsolete dialog height arguments in limit/unlimit. `test_physics_limits.py` passes on Blender 5.1.2: repeated setup retains one constraint, an unrotated object is clamped to expected XYZ limits, removing the limit restores its unconstrained transform, and lock/unlock changes all location locks. This does not verify rotated tooth axes or constraint enforcement during rigid-body dynamics. The forcefield dependency cycle remains open.

### Rotated tooth movement axes

Movement limits now use a fixed, unit-scale custom reference at the initial tooth world pose. This replaces incorrectly mixed local coordinates and rotated world projections. Repeated configuration reuses the reference; unlimit removes it when no non-scene/collection references remain. References are tagged for simulation rebuild cleanup.

The extended physics limits test passes both unrotated and 90-degree-rotated objects, no initial position jump, expected clamped world position and reference cleanup. These remain transform-constraint tests, not proof of rigid-body dynamics enforcement; the forcefield cycle remains unresolved.

### Simulation lock dynamics and result transfer

`test_physics_lock.py` verifies real sequential rigid-body evaluation: a location-locked cube remains at height 10 through frame 24 and falls after unlocking/resetting. No lock implementation change was required.

Physics copies now record source object and source scene ID references. Keep Simulation Results collects evaluated world transforms and applies them only to mapped originals, returning to the recorded scene without destructively baking simulation objects. Expanded setup test verifies transfer while leaving another object sharing the source mesh unchanged. Existing field dependency-cycle warnings persist; this is not complete forcefield dynamics validation.

### Root axis conversion

Ported activation/selection and helper removal in `empties_to_bones`. Converts axis transforms into armature space before setting head/tail and roll, replacing mixed world/local placement. `test_root_axis_conversion.py` passes under Blender 5.1.2 with translated/rotated axis and armature: world tail matches the axis origin, head is 16 units along negative axis Z, and the temporary empty is removed. Nonuniform armature scale and the upstream modal axis workflow remain unverified.

### Root modal startup

Ported root-axis empty display settings, collection linking, object visibility/selection/activation and scene ray-casting to the dependency-graph API. Added space validation before accessing region_3d. `test_root_modal.py` passes in a real Blender 5.1.2 window: startup creates the numbered root bone, draw callbacks run without tracebacks and simulated Enter finishes in Object mode. This startup test intentionally has no placed axis; mouse placement and Escape rollback remain open. Added the window test to headless-runner exclusions.

### Root modal surface placement

Axis helper creation now occurs only after a successful ray hit on the selected tooth. The Blender window test simulates a miss (no helper created), a center click on a cube tooth in top orthographic view (axis at Z=1), and Enter. The resulting root tail is Z=1 and head Z=-15, with helper removal and modal completion verified. Escape rollback and multi-tooth navigation remain open.

### Root modal cancellation

Added session snapshots of existing bone names and axis transforms/display settings. Escape removes newly added bones or a newly created armature and restores existing axis state/removes new axes. The window test now places an axis, cancels, verifies removal of new armature/helper, then restarts, places and commits successfully. Existing-armature cancellation, selection/viewport restoration and shared armature data remain unverified.

### Existing-root cancellation coverage

Extended the real-window root modal test with an existing 11root bone, a preexisting axis with distinct transform/display settings, and a second tooth requiring a new 21root bone. After mouse replacement of the axis and Escape, Blender 5.1.2 preserves the original bone endpoints, removes the newly added bone, restores the axis matrix/display type/size and exits the modal handler. Viewport/selection restoration and shared armature data remain unverified.

### Fast tooth labeling

Ported scene ray-casting, view-layer selection/activation and preflight view-space validation. Corrected backward quadrant transitions to invert the existing 28-tooth forward sequence (11→47, 21→17, 31→27, 41→37). `test_label_modal.py` passes in Blender 5.1.2 with real Down-arrow, mouse and Enter events, verifies label 47 and name display, and clean modal completion. Added it to headless exclusions. Escape rollback, label collisions and origin preservation remain open.

### Tooth label collisions

Fast labeling now rejects a number already used by another object before changing the hit object or advancing the label sequence. The real-window test verifies unchanged names after a conflicting click, then frees the number and confirms a second click receives the exact same intended label. Passed on Blender 5.1.2. Escape rollback and preservation of off-center/shared mesh origins remain open.
