# Blender 5.1.2 verification

The port preserves the upstream add-on's active functional scope. All 117 original
operator IDs remain registered, along with all eight panels. The Bridges panel's
RNA identifier was corrected to Blender's naming convention; its class and label
are retained. The repaired Draw Arch Curve action adds one operator, for 118 total.
Strict enable/disable/re-enable checks cover 142 registered classes.

The installed ZIP's runtime code was tested at revision `703a660`. Both complete
suites passed in isolated Blender processes using the installed copy and bundled
resources, not imports from the development checkout:

| Gate | Result | Evidence |
| --- | --- | --- |
| Upstream operators and panels retained | Passed; none removed | [Scope comparison](upstream_scope.json), `tools/audit_upstream_scope.py` |
| Operator context checks | 118 operators in three scene states | `tests/test_poll_contexts.py` |
| Background cases | 97/97 passed | [Recorded results](verification_results.json) |
| Foreground cases | 26/26 passed | [Recorded results](verification_results.json) |
| Install, fresh-process enable, library loading, removal | All passed | `tests/run_installation.py` |
| Test references for active declarations | All 118 operators and eight panels mapped | [Declaration inventory](operator_inventory.json) |

The cases cover model preparation, crowns/margins/intaglios/contact adjustment,
bridges, implant assets/sleeves/cylinders, splints, denture surfaces/trays/rims,
orthodontic brackets/roots/staging/physics, arch and occlusal setup, GPU drawing,
panel layout calls, modal completion/cancellation and saved-file round trips.
Fixture-specific assertions check geometry, distances, transforms, ownership and
cleanup; this is more than a registration or import test. The chronological
[engineering log](PORTING.md) describes the individual fixtures and fixes.

## Reproduce

```sh
python3 tests/run_installation.py --blender /path/to/blender --suites headless foreground
```

This uses temporary Blender user directories. It builds the archive, installs it,
starts a separate process, copies the test harness beside the installed code, runs
both suites, and removes the installed add-on. It does not change the normal user
profile. Detailed generated logs are under `tests/artifacts/installation/`.

## Limits

- Fifteen background cases report Blender shutdown allocation warnings. Tests
  still complete without Python tracebacks or dependency cycles. The port is not
  represented as allocation-warning-free; native asset/edit-mode reproduction is
  recorded in the engineering log.
- Synthetic geometry and scripted UI checks do not validate arbitrary scans,
  clinical intercuspation, fit, wall thickness or a manufacturing profile. KATANA
  cement-space and milling parameters have not been established by this port.
- Upstream-disabled margin-tracing/splint experiments remain inactive. Image
  registration has separate explicit-module tests but is not newly exposed in the
  normal add-on UI. Existing placeholder help content is not a newly implemented
  clinical workflow.
- Individual tests establish their stated cases, not every combination of
  modifiers, input topology, constraints, selection state and user action.

These limits do not remove or replace any originally registered tool. They define
what the verification evidence supports and prevent a software compatibility
result from being mistaken for a clinical approval.
