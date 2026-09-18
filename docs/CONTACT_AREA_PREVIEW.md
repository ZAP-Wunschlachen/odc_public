# Local contact-area preview

The **Kontaktfläche verbreitern** box appears directly below the selected tooth
in ODC → Tooth Restorations. Select mesial and/or distal, enter the total width
and height in model millimetres, then use **Vorschau**. **Zurücksetzen** removes
the derived preview and restores the source's previous visibility.

Width and height describe an elliptical deformation region with a smooth
transition. They are **not a measured contact-patch size**. There is no clinical
default width, height, force or interference. The unchanged source's measured
positive minimum clearance is retained. A new preview always starts from that
source, so repeated updates do not accumulate deformation. The tooth plan's
restoration/contour references continue to point to the original object.

## Prepared inputs

- `tooth.restoration`, falling back to `tooth.contour`: one connected triangulated mesh with
  consistent winding and no live modifiers or shape keys.
- `tooth.mesial` / `tooth.distal`: separately identified, sufficiently large
  neighbouring surface patches in their original world positions. The selected
  target must be locally representable by one smooth surface.
- `tooth.axis`: insertion-axis object; its world-space local +Z supplies height.
- `ODC Exterior`: source vertices that belong to the exterior.
- `ODC Contact Protected`: margin, cervical, occlusal and other protected points.
  Protection takes precedence over exterior membership. Open mesh boundaries
  are additionally protected automatically.
- `Mesial Contact` / `Distal Contact`: compact seed groups on the respective
  contact region. Existing Dundee `AnatomyProtected` serves a different purpose
  and is not substituted for the contact protection mask.

There is no fixed local-X assumption. Contact direction comes from the seed and
neighbour geometry; insertion direction comes from the axis. World transforms,
including positive nonuniform scales, are supported. Mirrored/singular object
transforms are refused until explicitly corrected. Library masks prepare an
asset for use but do not identify the patient's neighbours or confirm an axis.

## Geometry and refusal conditions

A robust quadratic fit smooths the local neighbouring surface. Its elliptical
support first includes a 20% margin; if that surrounding flank fails the fit
quality check, the full requested ellipse must independently pass the same
check. The source is
advanced toward a conservative offset of that fit, with an elliptical quintic
falloff and a metric surface-distance fade into protected regions. Individual
scan normals are not copied into the source. Missing target coverage, highly
irregular target surfaces, overlapping mesial/distal edit zones and unsuitable
source geometry are refused.

Clearance uses triangle/triangle distances including edge/edge minima, preceded
by a triangle-intersection test. Active and assigned inactive neighbours, plus
an assigned opposing target, are checked. The algorithm can reduce the whole
smooth displacement field to retain clearance; it does not clip individual
vertices against the scan. Final checks use the float32 coordinates Blender
will store. Numerical clearance tolerance is 0.000001 model millimetres, not a
clinical fit specification.

Collapsed/strongly rotated faces, new sharp creases and nonadjacent triangle
self-intersections are rejected before any preview object replaces the last
one. Protected and out-of-region local coordinates are retained exactly.
These are geometric checks, not certification of anatomy, material thickness,
occlusion or clinical suitability. Review the resulting shape and actual
near-contact area before using a derived design further.

## Python API

Set per-tooth properties `contact_area_mesial` / `contact_area_distal` and
`contact_area_{side}_width` / `contact_area_{side}_height`. Then call:

```python
from odc_public.Operators import contact_area
preview_object, metrics = contact_area.preview(bpy.context, tooth)
contact_area.reset(bpy.context, tooth)
```

`build_preview(tooth)` performs geometry calculations without scene writes and
returns `(source_object, proposed_local_coordinates, metrics)`.

Metrics record each selected side's original/preview minimum clearance,
requested ellipse, frame, fit residual range and accepted field fraction,
alongside changed-vertex count and maximum displacement. The preview stores
these as JSON in `odc_contact_area_metrics`; source custom properties, including
license and attribution, are copied. Actual contact-area measurement requires
an explicit distance threshold and should be reported separately from width
and height controls.

## Focused regression

`tests/test_contact_area.py` uses only synthetic geometry. It checks broader
near-contact regions, true edge/edge clearance, both sides, rotated/nonuniform
transforms, unchanged protected/excluded points, repeated-update idempotence,
atomic failed updates, fold/intersection refusals, missing masks and reset,
including recovery after the preview is renamed or manually deleted. The
headless runner discovers this test automatically through its `test_*.py` glob.
