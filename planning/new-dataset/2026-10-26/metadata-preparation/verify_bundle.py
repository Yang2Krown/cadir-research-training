"""Verify committed preparation artifacts only; never reads external raw data.

This is a byte-integrity check, not an experiment, algorithm test, or approval.
Run: python verify_bundle.py
"""
from pathlib import Path
import csv
import hashlib

root = Path(__file__).resolve().parent
index = root / 'bundle_sha256.tsv'
seen = set()
with index.open() as stream:
    for row in csv.DictReader(stream, delimiter='\t'):
        relative = Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise SystemExit('Invalid relative path in bundle index')
        if relative.suffix == '.rds' or relative.name == 'GSE81682_HTSeq_counts.txt.gz':
            raise SystemExit('Raw data must not be part of this bundle')
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise SystemExit(f'Missing or indirect artifact: {relative}')
        if relative.as_posix() in seen:
            raise SystemExit(f'Duplicate index path: {relative}')
        seen.add(relative.as_posix())
        if path.stat().st_size != int(row['bytes']):
            raise SystemExit(f'Size mismatch: {relative}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise SystemExit(f'Hash mismatch: {relative}')
print(f'PASS: {len(seen)} preparation artifacts match the bundle index; external raw data not accessed.')
