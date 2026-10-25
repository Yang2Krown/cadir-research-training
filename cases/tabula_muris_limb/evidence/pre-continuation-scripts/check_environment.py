#!/usr/bin/env python3
"""Check the specified Docker restoration. Never fall back to legacy Conda."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time

base = Path(__file__).resolve().parents[1]
out = Path(tempfile.mkdtemp(prefix='environment-', dir=base / 'runs'))
setup = Path('/workspace/.cadir-setup')
state = {'started_utc': datetime.now(timezone.utc).isoformat(), 'run_directory': str(out),
         'target_environment': 'not_verified', 'legacy_runtime_substituted': False}

def run(name, command):
    start = time.monotonic()
    with (out / f'{name}.log').open('w') as log:
        proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    state[name] = {'exit_code': proc.returncode, 'elapsed_seconds': time.monotonic() - start, 'command': command}
    return proc.returncode == 0

run('resources', ['bash', '-c', 'lscpu; free -b; df -B1 /workspace /tmp; cat /sys/fs/cgroup/cpu.max /sys/fs/cgroup/memory.max'])
missing = []
for name in ['START_SKILL.md', 'SOFTWARE.md', 'run-r.sh']:
    file = setup / name
    if file.is_file():
        (out / name).write_bytes(file.read_bytes())
    else:
        missing.append(str(file))
state['missing_required_files'] = missing
if missing:
    state['status'] = 'BLOCKED_SETUP_MISSING'
else:
    version_ok = run('versions', ['bash', str(base / 'scripts/run-r.sh'), str(base / 'scripts/versions.R')])
    smoke_ok = run('target_smoke', ['bash', str(setup / 'run-r.sh'), 'Rscript', '/setup/smoke-test.R']) if version_ok else False
    state['status'] = 'PASS' if version_ok and smoke_ok else 'FAILED_TARGET_ENVIRONMENT_CHECK'
    if version_ok and smoke_ok:
        state['target_environment'] = 'verified_this_run'
(out / 'status.json').write_text(json.dumps(state, indent=2) + '\n')
(base / 'latest-environment.json').write_text(json.dumps(state, indent=2) + '\n')
print(json.dumps(state, indent=2))
raise SystemExit(0 if state['status'] == 'PASS' else 1)
