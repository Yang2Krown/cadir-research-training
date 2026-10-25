#!/usr/bin/env python3
"""Exercise validator failure paths on isolated copies of one fresh run."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('case', type=Path)
parser.add_argument('run', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
required = ['config.json', 'metrics.json', 'cell_clusters.tsv', 'gene_clusters.tsv',
            'cluster_sizes.tsv', 'coclustered_gene_ranks.tsv', 'selected_genes.tsv',
            'ca.rds', 'cadir.rds', 'cadir_annotated.rds', 'verification.json']
summary = []
for name in ['normal', 'swap_clusters', 'wrong_NA', 'wrong_Score', 'wrong_Rank', 'wrong_cluster_count']:
    out = args.output / name
    out.mkdir()
    for filename in required:
        src = args.run / filename
        if src.suffix == '.rds':
            (out / filename).symlink_to(src.resolve())
        else:
            shutil.copy2(src, out / filename)
    # Start every negative case with a real PASS and demand it is replaced by FAIL.
    assert json.loads((out / 'verification.json').read_text())['status'] == 'PASS'
    if name != 'normal':
        filename = ('gene_clusters.tsv' if name in ['swap_clusters', 'wrong_NA'] else
                    'cluster_sizes.tsv' if name == 'wrong_cluster_count' else 'coclustered_gene_ranks.tsv')
        path = out / filename
        with path.open() as handle:
            reader = csv.DictReader(handle, delimiter='\t')
            rows = list(reader)
            columns = reader.fieldnames
        if name == 'swap_clusters':
            first = next(i for i, row in enumerate(rows) if row['cluster'] != 'NA')
            second = next(i for i, row in enumerate(rows) if row['cluster'] not in ['NA', rows[first]['cluster']])
            rows[first]['cluster'], rows[second]['cluster'] = rows[second]['cluster'], rows[first]['cluster']
        elif name == 'wrong_NA':
            assigned = next(i for i, row in enumerate(rows) if row['cluster'] != 'NA')
            empty = next(i for i, row in enumerate(rows) if row['cluster'] == 'NA')
            rows[assigned]['cluster'], rows[empty]['cluster'] = rows[empty]['cluster'], rows[assigned]['cluster']
        elif name == 'wrong_Score':
            rows[0]['Score'] = str(float(rows[0]['Score']) + 0.5)
        elif name == 'wrong_Rank':
            rows[0]['Rank'], rows[1]['Rank'] = rows[1]['Rank'], rows[0]['Rank']
        elif name == 'wrong_cluster_count':
            rows[0]['ngenes'] = str(int(rows[0]['ngenes']) + 1)
            rows[1]['ngenes'] = str(int(rows[1]['ngenes']) - 1)
        with path.open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    command = ['bash', str(args.case / 'scripts/run-r.sh'), str(args.case / 'scripts/verify_results.R'), str(out)]
    with (out / 'verification.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    status = json.loads((out / 'verification.json').read_text())
    expected = 'PASS' if name == 'normal' else 'FAIL'
    ok = status['status'] == expected and (result.returncode == 0) == (name == 'normal')
    summary.append(dict(case=name, exit_code=result.returncode, status=status, expected=expected, matched=ok))
(args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if all(row['matched'] for row in summary) else 1)
