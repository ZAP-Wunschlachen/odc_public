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
