#!/usr/bin/env python3
"""Run one complete entry and verify its smoke output leaves shared state intact."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('case', type=Path)
parser.add_argument('data', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True)
runtime = Path('/workspace/cadir-env')


def hash_file(path):
    return {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def shared_snapshot():
    paths = [runtime / 'latest-smoke.json'] + list((runtime / 'runs').rglob('*'))
    states = {str(path.relative_to(runtime)): dict(hash_file(path), mtime_ns=path.stat().st_mtime_ns)
              for path in sorted(paths) if path.is_file()}
    return {'files': states,
            'directories': sorted(str(path.relative_to(runtime))
                                  for path in (runtime / 'runs').rglob('*') if path.is_dir()),
            'runtime_source_sha256': {name: hash_file(runtime / name)['sha256'] for name in
                                     ['activate.sh', 'provenance.md', 'upstream-renv.lock',
                                      'sources.json', 'smoke.R', 'run-smoke.py']}}


before = shared_snapshot()
(args.output / 'shared_before.json').write_text(json.dumps(before, indent=2) + '\n')
root = args.output / 'full-entry'
command = ['bash', str(args.case / 'scripts/rerun.sh'), '--data', str(args.data), '--output-root', str(root)]
with (args.output / 'full-entry.log').open('w') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
after = shared_snapshot()
(args.output / 'shared_after.json').write_text(json.dumps(after, indent=2) + '\n')
summary = {'command': command, 'exit_code': result.returncode,
           'shared_latest_and_runs_unchanged': before == after,
           'runtime_source_files_unchanged': before['runtime_source_sha256'] == after['runtime_source_sha256'],
           'shared_file_count': len(before['files'])}
if result.returncode == 0:
    env_state = json.loads((root / 'latest-environment.json').read_text())
    case_state = json.loads((root / 'latest-case.json').read_text())
    environment = Path(env_state['run_directory'])
    smoke = env_state['synthetic_smoke_evidence']
    smoke_dir = Path(smoke['run_directory'])
    required = ['status.txt', 'sessionInfo.txt', 'installed-packages.csv', 'synthetic-sce.rds',
                'smoke-results.rds', 'ca-cadir-smoke.png', 'console.log', 'resources.json']
    artifacts = {name: hash_file(smoke_dir / name) for name in required}
    summary.update(environment_status=env_state['status'],
                   environment_directory=str(environment), smoke_directory=str(smoke_dir),
                   smoke_within_environment_directory=smoke_dir.is_relative_to(environment),
                   smoke_artifacts=artifacts,
                   smoke_pass_status=(smoke_dir / 'status.txt').read_text().startswith('PASS:'),
                   smoke_nonempty_artifacts=all(item['bytes'] > 0 for item in artifacts.values()),
                   smoke_png_sha256_matches=smoke['png_sha256'] == artifacts['ca-cadir-smoke.png']['sha256'],
                   smoke_elapsed_seconds=smoke['elapsed_seconds'],
                   smoke_child_max_rss_KiB_linux=smoke['max_rss_KiB_linux'],
                   case_status=case_state['status'], case_directory=case_state['run_directory'],
                   verification=json.loads((Path(case_state['run_directory']) / 'verification.json').read_text()),
                   deliverables_exist=(root / 'deliverables/results/verification.json').is_file())
    summary['passed'] = all([summary['shared_latest_and_runs_unchanged'], summary['runtime_source_files_unchanged'],
                             summary['smoke_within_environment_directory'], summary['smoke_pass_status'],
                             summary['smoke_nonempty_artifacts'], summary['smoke_png_sha256_matches'],
                             summary['environment_status'] == 'PASS', summary['verification']['status'] == 'PASS',
                             summary['deliverables_exist']])
else:
    summary['passed'] = False
(args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary['passed'] else 1)
