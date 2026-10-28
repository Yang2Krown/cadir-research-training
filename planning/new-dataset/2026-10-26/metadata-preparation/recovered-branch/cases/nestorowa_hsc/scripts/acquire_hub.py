#!/usr/bin/env python3
"""Resolve the pinned legacy dataset from the official Hub catalog; optional download."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--catalog', type=Path, required=True)
parser.add_argument('--output-root', type=Path, required=True)
parser.add_argument('--download', action='store_true')
args = parser.parse_args()
args.output_root.mkdir(parents=True, exist_ok=False)
connection = sqlite3.connect('file:' + str(args.catalog.resolve()) + '?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
resources = []
for kind in ['counts', 'coldata']:
    path = f'scRNAseq/nestorowa-hsc/2.0.0/{kind}.rds'
    rows = connection.execute('''SELECT r.ah_id, p.id AS fetch_id, p.rdatapath, p.rdataclass,
                                r.dataprovider, r.rdatadateadded, l.location_prefix
                                FROM resources r JOIN rdatapaths p ON r.id=p.resource_id
                                JOIN location_prefixes l ON r.location_prefix_id=l.id
                                WHERE p.rdatapath=?''', (path,)).fetchall()
    if len(rows) != 1:
        raise SystemExit(f'Expected one exact resource for {path}, found {len(rows)}.')
    row = dict(rows[0])
    row.update(kind=kind, url=f"https://experimenthub.bioconductor.org/fetch/{row['fetch_id']}",
               official_storage_url=row['location_prefix'] + path)
    resources.append(row)
plan = {'dataset': 'Nestorowa HSC, legacy scRNAseq resource version 2.0.0',
        'catalog_sha256': hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
        'resources': resources, 'download_requested': args.download,
        'data_content_status': 'NOT_VERIFIED'}
(args.output_root / 'acquisition_plan.json').write_text(json.dumps(plan, indent=2) + '\n')
if args.download:
    for resource in resources:
        command = ['python', str(Path(__file__).with_name('fetch_public.py')), resource['url'],
                   str(args.output_root / (resource['kind'] + '.rds'))]
        result = subprocess.run(command)
        if result.returncode:
            raise SystemExit(result.returncode)
print(json.dumps(plan, indent=2))
