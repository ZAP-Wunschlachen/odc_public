# Open Dental CAD — Blender 5.1 port

This ZAP-Wunschlachen fork adapts Open Dental CAD to **Blender 5.1.2**.
The port is still being verified; a working installation and passing tests do not
establish that every dental workflow is finished or that a restoration is ready
for manufacture. See [the verification notes](docs/PORTING.md) for tested behavior
and remaining gaps.

The add-on includes tools for crowns, bridges, implants, splints, dentures,
orthodontic setup and model preparation, together with the original asset libraries.

## Build and install

From a Git checkout, create the installable legacy add-on archive:

```sh
python3 tools/build_addon.py --output /tmp/odc_public-blender-5.1.zip
```

In Blender Preferences, use **Install from Disk…** (or the legacy **Install…**
button) to select the ZIP, then enable **Open Dental CAD for Blender** in Add-ons.
The tools appear in the 3D View sidebar under **ODC**. Library paths default to the
bundled files in the installed add-on's `Resources/data` directory.

The builder packages tracked runtime files, the README and bundled resources. It
excludes the Git repository, test fixtures, generated test results and local files.
It reads the current contents of tracked files, so commit or review local changes
before distributing a build. The archive is a legacy add-on, not an Extensions
Platform package.

## Verification

Run these from the checkout, supplying your Blender executable:

```sh
python3 tests/run_headless.py --blender /path/to/blender
python3 tests/run_foreground.py --blender /path/to/blender
python3 tests/run_installation.py --blender /path/to/blender
```

The foreground runner opens real Blender windows and sends test input events.
The installation runner builds a ZIP, installs it into a temporary user profile,
restarts Blender in a separate process, loads a bundled tooth and removes the
add-on. Logs are written to `tests/artifacts/`. Each suite covers its explicit test
cases; full clinical validation is outside those synthetic checks.

## Origins

ODC was originally developed by Dr. Patrick Moore. ODC v2.0 continued that work
with Dr. Issam Dakir, Dr. Raúl Ruiz Vera and Dr. Georgi Talmazov.

[Original tutorial videos](https://www.youtube.com/playlist?list=PLXpbHlzIjUBQGTrnWkcbROYL656YTEfO8)
may show older Blender interfaces.
