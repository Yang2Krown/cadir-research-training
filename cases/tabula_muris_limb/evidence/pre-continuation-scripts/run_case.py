#!/usr/bin/env python3
"""Verify the authorized input, then run one case. Every attempt gets a new log."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone

base = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, default=base / 'config/case.json')
parser.add_argument('--data', type=Path)
parser.add_argument('--marker-csv', type=Path)
parser.add_argument('--audit-only', action='store_true')
args = parser.parse_args()
cfg = json.loads(args.config.read_text())
if args.data:
    cfg['data_path'] = str(args.data.resolve())
if args.marker_csv:
    cfg['marker_csv'] = str(args.marker_csv.resolve())
cfg['audit_only'] = args.audit_only
cfg['mode'] = 'real_case'
out = Path(tempfile.mkdtemp(prefix='case-', dir=base / 'runs'))
(out / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
start = time.monotonic()
status = {'started_utc': datetime.now(timezone.utc).isoformat(),
          'run_directory': str(out), 'mode': 'real_case',
          'data_audit': 'not_started', 'single_case': 'not_started',
          'paper_reproduction': 'not_established'}
status['required_runtime'] = {
    name: (Path('/workspace/.cadir-setup') / name).is_file()
    for name in ['START_SKILL.md', 'SOFTWARE.md', 'run-r.sh']}
code = 1
r_started = False
try:
    path = Path(cfg['data_path'])
    if not path.is_file():
        status['status'] = 'BLOCKED_INPUT_MISSING'
        raise FileNotFoundError(f'Required input unavailable: {path}')
    sha = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            sha.update(chunk)
    actual = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha.hexdigest()}
    (out / 'input_integrity.json').write_text(json.dumps(actual, indent=2) + '\n')
    if actual['bytes'] != cfg['expected_bytes'] or actual['sha256'] != cfg['expected_sha256']:
        status['status'] = 'BLOCKED_INPUT_INTEGRITY'
        raise ValueError('Input size/SHA256 mismatch; see input_integrity.json. No data were altered.')
    if cfg['marker_csv'] and not Path(cfg['marker_csv']).is_file():
        raise FileNotFoundError(f"Explicit marker CSV unavailable: {cfg['marker_csv']}")
    if cfg['marker_csv']:
        marker = Path(cfg['marker_csv'])
        status['marker_csv_sha256'] = hashlib.sha256(marker.read_bytes()).hexdigest()
    status['integrity'] = 'PASS'
    if not all(status['required_runtime'].values()):
        status['status'] = 'BLOCKED_REQUIRED_DOCKER_SETUP_MISSING'
        raise RuntimeError('Required Docker setup/launcher documents are missing. Legacy Conda is not substituted.')
    repo = base.parents[1]
    runtime_cfg = dict(cfg)
    for key in ['data_path', 'marker_csv']:
        if not cfg.get(key):
            continue
        source = Path(cfg[key]).resolve()
        try:
            relative = source.relative_to(repo)
        except ValueError:
            data_dir = repo / 'data'
            data_dir.mkdir(exist_ok=True)
            destination = data_dir / source.name
            if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != hashlib.sha256(source.read_bytes()).hexdigest():
                raise FileExistsError(f'Refusing to overwrite different input: {destination}')
            if not destination.exists():
                shutil.copy2(source, destination)
            if destination.stat().st_size != source.stat().st_size or hashlib.sha256(destination.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                raise RuntimeError(f'Copied input failed integrity check: {destination}')
            relative = destination.relative_to(repo)
        runtime_cfg[key] = '/repo/' + relative.as_posix()
    (out / 'runtime_config.json').write_text(json.dumps(runtime_cfg, ensure_ascii=False, indent=2) + '\n')
    command = ['bash', str(base / 'scripts/run-r.sh'), str(base / 'scripts/pipeline.R'),
               str(out / 'runtime_config.json'), str(out)]
    status['command'] = command
    with (out / 'console.log').open('w') as log:
        r_started = True
        code = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=base).returncode
    rstatus = out / 'r_status.json'
    if rstatus.is_file():
        status.update(json.loads(rstatus.read_text()))
    else:
        status['status'] = 'FAILED_BEFORE_R_STATUS'
except Exception as exc:
    status.setdefault('status', 'FAILED_PREFLIGHT')
    status['error'] = str(exc)
    (out / 'console.log').write_text(str(exc) + '\n')
finally:
    status.update(exit_code=code, elapsed_seconds=time.monotonic() - start,
                  launcher_children_max_rss_KiB_linux=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss if r_started else None,
                  launcher_started=r_started,
                  resource_scope='Launcher child usage excludes the inner Docker R process. True R peak is r_peak_rss_KiB_linux from /proc/self/status inside R; stage peaks are sampled RSS, not algorithm benchmarks.')
    (out / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    (base / 'latest-case.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(status, ensure_ascii=False, indent=2))
raise SystemExit(code)
