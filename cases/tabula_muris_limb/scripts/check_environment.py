#!/usr/bin/env python3
"""Verify the Conda runtime authorized by continuation-task.md; no installation."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from output_paths import output_root, prepare_root

base = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
output_root(parser, base)
parser.add_argument('--config', type=Path, default=base / 'config/case.json')
args = parser.parse_args()
root = prepare_root(args.output_root)
out = Path(tempfile.mkdtemp(prefix='environment-', dir=root))
runtime = Path('/workspace/cadir-env')
state = {'started_utc': datetime.now(timezone.utc).isoformat(), 'run_directory': str(out),
         'runtime': 'verified_conda', 'environment_check': 'not_verified'}

def run(name, command):
    start = time.monotonic()
    with (out / f'{name}.log').open('w') as log:
        proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    state[name] = {'exit_code': proc.returncode, 'elapsed_seconds': time.monotonic() - start, 'command': command}
    return proc.returncode == 0

run('resources', ['bash', '-c', 'lscpu; free -b; df -B1 /workspace /tmp; cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max'])
required = ['activate.sh', 'provenance.md', 'upstream-renv.lock', 'sources.json', 'smoke.R', 'run-smoke.py']
missing = [str(runtime / name) for name in required if not (runtime / name).is_file()]
state['missing_required_files'] = missing
if missing:
    state['status'] = 'BLOCKED_CONDA_RUNTIME_MISSING'
else:
    state['source_document_sha256'] = {}
    for name in required:
        shutil.copy2(runtime / name, out / name)
        state['source_document_sha256'][name] = hashlib.sha256((runtime / name).read_bytes()).hexdigest()
    cfg = args.config.resolve()
    version_ok = run('versions', ['bash', str(base / 'scripts/run-r.sh'), str(base / 'scripts/versions.R'), str(cfg)])
    smoke_ok = run('synthetic_smoke', ['bash', '-c', 'source /workspace/cadir-env/activate.sh; exec python /workspace/cadir-env/run-smoke.py']) if version_ok else False
    if smoke_ok:
        smoke = json.loads((runtime / 'latest-smoke.json').read_text())
        state['synthetic_smoke_evidence'] = smoke
        source = Path(smoke['run_directory'])
        for name in ['status.txt','sessionInfo.txt','installed-packages.csv','console.log','resources.json','ca-cadir-smoke.png']:
            shutil.copy2(source / name, out / ('synthetic-' + name))
    state['status'] = 'PASS' if version_ok and smoke_ok else 'FAILED_CONDA_ENVIRONMENT_CHECK'
    if version_ok and smoke_ok:
        state['environment_check'] = 'verified_this_run'
(out / 'status.json').write_text(json.dumps(state, indent=2) + '\n')
(root / 'latest-environment.json').write_text(json.dumps(state, indent=2) + '\n')
print(json.dumps(state, indent=2))
raise SystemExit(0 if state['status'] == 'PASS' else 1)
