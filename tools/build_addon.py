"""Build a legacy add-on ZIP from tracked runtime files and bundled assets."""
import argparse
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = {'Addon_utils', 'Operators', 'Panels', 'Resources', 'odcmenus'}
RUNTIME_FILES = {'__init__.py', 'gpu_compat.py', 'README.md'}

def build(output):
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    included = [name for name in tracked if name and
                (Path(name).parts[0] in RUNTIME_DIRS or name in RUNTIME_FILES)]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(included):
            info = zipfile.ZipInfo('odc_public/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes())
    print(f'{output}: {len(included)} files, {output.stat().st_size} bytes')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    build(parser.parse_args().output.resolve())
