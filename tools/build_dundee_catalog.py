"""Rebuild the Dundee crown library from the attributed, hash-verified GLB sources.

Run with Blender 5.1:
  blender -b --factory-startup --python tools/build_dundee_catalog.py -- \
    --output /tmp/dundee.blend --work-dir /tmp/dundee-build

Only anatomical outer surfaces are generated. Millimetre sizes are nominal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--work-dir", required=True, type=Path)
parser.add_argument("--manifest", type=Path, default=ROOT / "Resources/dundee/manifest.json")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
args.output = args.output.resolve()
args.work_dir = args.work_dir.resolve()
args.manifest = args.manifest.resolve()
args.work_dir.mkdir(parents=True, exist_ok=True)
args.output.parent.mkdir(parents=True, exist_ok=True)
manifest = json.loads(args.manifest.read_text())
for asset in manifest["assets"]:
    source = args.manifest.parent / asset["local_path"]
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != asset["sha256"]:
        raise ValueError(f"Source checksum mismatch: {source.name}")
context = {
    "W": args.work_dir,
    "SOURCE_DIR": args.manifest.parent,
    "MANIFEST": manifest,
    "OUTPUT": args.output,
}
runpy.run_path(str(ROOT / "tools/dundee/import_sources.py"), init_globals=context)
runpy.run_path(str(ROOT / "tools/dundee/prepare.py"), init_globals=context)
