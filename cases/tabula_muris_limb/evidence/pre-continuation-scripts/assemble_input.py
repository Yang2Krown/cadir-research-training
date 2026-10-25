#!/usr/bin/env python3
"""Reassemble uploaded <32 MiB pieces; never accept a changed RDS."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

base = Path(__file__).resolve().parents[1]
cfg = json.loads((base / 'config/case.json').read_text())
p = argparse.ArgumentParser()
p.add_argument('parts', type=Path, nargs='+', help='Parts in original byte order: aa, ab, ...')
args = p.parse_args()
destination = Path(cfg['data_path'])
destination.parent.mkdir(parents=True, exist_ok=True)
manifest = {'parts': [], 'expected_bytes': cfg['expected_bytes'], 'expected_sha256': cfg['expected_sha256']}
digest = hashlib.sha256()
total = 0
with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='limb-assembly-', delete=False) as output:
    temporary = Path(output.name)
    for path in args.parts:
        local_digest = hashlib.sha256()
        size = 0
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                output.write(chunk)
                digest.update(chunk)
                local_digest.update(chunk)
                total += len(chunk)
                size += len(chunk)
        manifest['parts'].append({'path': str(path.resolve()), 'bytes': size, 'sha256': local_digest.hexdigest()})
manifest.update(actual_bytes=total, actual_sha256=digest.hexdigest())
manifest['verified'] = total == cfg['expected_bytes'] and digest.hexdigest() == cfg['expected_sha256']
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
if manifest['verified']:
    if destination.exists():
        existing = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing != cfg['expected_sha256']:
            manifest['verified'] = False
            manifest['error'] = 'Destination exists with different contents; refused overwrite'
        else:
            temporary.unlink()
    else:
        temporary.rename(destination)
manifest['output_path'] = str(destination if manifest['verified'] else temporary)
(base / 'evidence' / f'assembly-{stamp}.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
raise SystemExit(0 if manifest['verified'] else 1)
