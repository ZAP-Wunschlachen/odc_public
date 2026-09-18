"""Run the headless integration suite in isolated Blender processes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
UI_TESTS = {'test_axis_modal', 'test_margin_modal', 'test_curve_manager', 'test_overlay_gpu', 'test_implant_views', 'test_bridge_modal', 'test_root_modal', 'test_label_modal', 'test_bracket_manager', 'test_bracket_modal', 'test_image_registration_modal'}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--blender', required=True)
args = parser.parse_args()
output = ROOT / 'tests' / 'artifacts' / 'headless'
output.mkdir(parents=True, exist_ok=True)
results = []
cases = [(path, []) for path in sorted((ROOT / 'tests').glob('test_*.py'))
         if path.stem not in UI_TESTS]
cases.append((ROOT / 'tests/test_solid_restoration.py', ['25', '0']))
cases.append((ROOT / 'tests/test_splint_make.py', ['--with-base']))
for path, extra in cases:
    name = path.stem + ('_with_base' if '--with-base' in extra else '_merge' if extra else '')
    command = [args.blender, '--background', '--factory-startup', '--disable-autoexec',
               '--python-exit-code', '1', '--python', str(path)]
    if extra:
        command += ['--', *extra]
    log_path = output / (name + '.log')
    timed_out = False
    with log_path.open('w') as log:
        try:
            process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                     timeout=180)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = None
    text = log_path.read_text(errors='replace')
    failed = timed_out or returncode != 0 or 'Traceback (most recent call last)' in text
    result = {'test': name, 'passed': not failed, 'returncode': returncode,
              'timeout': timed_out, 'shutdown_allocation_warning': 'Not freed memory blocks' in text,
              'log': str(log_path.relative_to(ROOT))}
    results.append(result)
    print(name, 'FAIL' if failed else 'PASS', flush=True)
(output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
sys.exit(any(not result['passed'] for result in results))
