#!/usr/bin/env python3
"""Verify the Conda runtime authorized by continuation-task.md; no installation."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
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


def run_smoke():
    # smoke.R honors its output argument. The historical runtime launcher does
    # not, so invoke R directly and never consult the shared latest-smoke file.
    source = out / 'synthetic-smoke'
    source.mkdir()
    command = ['bash', str(base / 'scripts/run-r.sh'),
               str(runtime / 'smoke.R'), str(source)]
    start = time.monotonic()
    evidence = {'run_directory': str(source), 'command': command,
                'scope': 'Whole Rscript including package loading; engineering diagnostic only, not a paper reproduction or algorithm benchmark.'}
    with (source / 'console.log').open('w') as log:
        with subprocess.Popen(command, cwd=out, stdout=log, stderr=subprocess.STDOUT) as proc:
            # Per-child usage, excluding the preceding version check.
            _, wait_status, usage = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(wait_status)
        evidence.update(exit_code=proc.returncode,
                        elapsed_seconds=time.monotonic() - start,
                        max_rss_KiB_linux=usage.ru_maxrss)
    artifacts = ['status.txt', 'sessionInfo.txt', 'installed-packages.csv',
                 'synthetic-sce.rds', 'smoke-results.rds', 'ca-cadir-smoke.png']
    if evidence['exit_code'] == 0:
        missing_artifacts = [name for name in artifacts
                             if not (source / name).is_file() or (source / name).stat().st_size == 0]
        if missing_artifacts or not (source / 'status.txt').read_text().startswith('PASS:'):
            evidence['artifact_failure'] = missing_artifacts or ['PASS status missing']
            evidence['exit_code'] = 1
        else:
            evidence['png_sha256'] = hashlib.sha256((source / 'ca-cadir-smoke.png').read_bytes()).hexdigest()
    (source / 'resources.json').write_text(json.dumps(evidence, indent=2) + '\n')
    state['synthetic_smoke'] = evidence
    state['synthetic_smoke_evidence'] = evidence
    for name in ['status.txt', 'sessionInfo.txt', 'installed-packages.csv',
                 'console.log', 'resources.json', 'ca-cadir-smoke.png']:
        if (source / name).is_file():
            shutil.copy2(source / name, out / ('synthetic-' + name))
    return evidence['exit_code'] == 0

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
    smoke_ok = run_smoke() if version_ok else False
    state['status'] = 'PASS' if version_ok and smoke_ok else 'FAILED_CONDA_ENVIRONMENT_CHECK'
    if version_ok and smoke_ok:
        state['environment_check'] = 'verified_this_run'
(out / 'status.json').write_text(json.dumps(state, indent=2) + '\n')
(root / 'latest-environment.json').write_text(json.dumps(state, indent=2) + '\n')
print(json.dumps(state, indent=2))
raise SystemExit(0 if state['status'] == 'PASS' else 1)
