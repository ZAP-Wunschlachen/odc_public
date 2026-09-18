"""Run the foreground integration suite in isolated Blender processes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
from case_catalog import UI_TESTS
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--blender', required=True)
args = parser.parse_args()
output = ROOT / 'tests' / 'artifacts' / 'foreground'
output.mkdir(parents=True, exist_ok=True)
results = []
for name in sorted(UI_TESTS):
    path = ROOT / 'tests' / (name + '.py')
    command = [args.blender, '--factory-startup', '--enable-event-simulate', '--disable-autoexec',
               '--python-exit-code', '1', '--python', str(path)]
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
    dependency_cycle = 'Dependency cycle detected' in text
    marker = 'ODC_' + path.stem.removeprefix('test_').upper() + '_PASSED'
    failed = (marker not in text or timed_out or returncode != 0 or dependency_cycle
              or 'Traceback (most recent call last)' in text)
    result = {'test': name, 'passed': not failed, 'returncode': returncode,
              'timeout': timed_out, 'success_marker': marker in text, 'dependency_cycle': dependency_cycle, 'shutdown_allocation_warning': 'Not freed memory blocks' in text,
              'log': str(log_path.relative_to(ROOT))}
    results.append(result)
    print(name, 'FAIL' if failed else 'PASS', flush=True)
(output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
sys.exit(any(not result['passed'] for result in results))
