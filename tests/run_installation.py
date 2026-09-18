"""Build/install/restart/remove the add-on without touching the user's profile."""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--blender', required=True)
args = parser.parse_args()
output = ROOT / 'tests' / 'artifacts' / 'installation'
output.mkdir(parents=True, exist_ok=True)
archive = output / 'odc_public-blender-5.1.zip'
subprocess.run([sys.executable, str(ROOT/'tools/build_addon.py'), '--output', str(archive)], check=True)
results = []
with tempfile.TemporaryDirectory(prefix='odc-install-') as temporary:
    profile = Path(temporary)
    env = os.environ.copy()
    for key, folder in [('BLENDER_USER_SCRIPTS', 'scripts'), ('BLENDER_USER_CONFIG', 'config'),
                        ('BLENDER_USER_DATAFILES', 'datafiles'), ('BLENDER_USER_EXTENSIONS', 'extensions')]:
        directory = profile / folder
        directory.mkdir()
        env[key] = str(directory)
    for stage in ('install', 'restart', 'remove'):
        command = [args.blender, '--background', '--disable-autoexec', '--python-exit-code', '1']
        if stage == 'install':
            command.append('--factory-startup')
        command += ['--python', str(ROOT/'tests/installation_probe.py'), '--', stage, str(archive)]
        log = output / (stage + '.log')
        with log.open('w') as handle:
            result = subprocess.run(command, cwd=profile, env=env, stdout=handle,
                                    stderr=subprocess.STDOUT, timeout=180)
        text = log.read_text()
        passed = (result.returncode == 0 and 'ODC_INSTALLATION_' + stage.upper() + '_PASSED' in text
                  and 'Traceback' not in text and 'Dependency cycle detected' not in text)
        results.append({'stage':stage, 'passed':passed, 'returncode':result.returncode,
                        'shutdown_allocation_warning':'Not freed memory blocks' in text})
        print(stage, 'PASS' if passed else 'FAIL', flush=True)
        if not passed:
            print(text[-4000:])
            break
(output/'results.json').write_text(json.dumps(results, indent=2)+'\n')
sys.exit(len(results) != 3 or not all(item['passed'] for item in results))
