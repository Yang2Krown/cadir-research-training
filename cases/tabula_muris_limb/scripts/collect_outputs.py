#!/usr/bin/env python3
"""Collect small verified deliverables; preserve every full raw run locally."""
import csv
import hashlib
import json
from pathlib import Path
import shutil

base = Path(__file__).resolve().parents[1]
status = json.loads((base / 'latest-case.json').read_text())
source = Path(status['run_directory'])
assert status['exit_code'] == 0 and status['single_case'] == 'PASS'
assert json.loads((source / 'verification.json').read_text())['status'] == 'PASS'
results = base / 'results'
figures = base / 'figures'
results.mkdir(exist_ok=True)
figures.mkdir(exist_ok=True)
names = [
    'status.json', 'metrics.json', 'data_audit.json', 'selection.json',
    'cluster_sizes.tsv', 'cell_clusters.tsv', 'gene_clusters.tsv',
    'coclustered_gene_ranks.tsv', 'predicted_annotations.tsv',
    'reference_label_counts.tsv', 'cluster_reference_contingency.tsv',
    'effective_cadir_parameters.txt', 'annotation_resources.json',
    'paper_differences.txt', 'stage_times_seconds.json', 'verification.json',
    'sessionInfo.txt', 'config.json', 'console.log', 'input_integrity.json',
    'required_version_check.tsv', 'verification.log',
]
for name in names:
    shutil.copy2(source / name, results / name)
for name in ['association_plots.png', 'association_plots.pdf', 'ca_clusters.png']:
    shutil.copy2(source / name, figures / name)
with (source / 'predicted_annotations.tsv').open() as handle:
    annotations = list(csv.DictReader(handle, delimiter='\t'))
mapping = {}
for row in annotations:
    if row['cluster'] in mapping:
        assert mapping[row['cluster']] == row['predicted_annotation']
    mapping[row['cluster']] = row['predicted_annotation']
with (results / 'cluster_annotations.tsv').open('w', newline='') as handle:
    writer = csv.writer(handle, delimiter='\t', lineterminator='\n')
    writer.writerow(['cluster', 'predicted_annotation', 'source'])
    for cluster in sorted(mapping):
        writer.writerow([cluster, mapping[cluster], 'CAdir::cellmarker_v2; GOA; predicted only'])
raw_manifest = []
for path in sorted(source.iterdir()):
    if path.is_file():
        raw_manifest.append({'file': path.name, 'bytes': path.stat().st_size,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
index = {'source_run': str(source), 'single_case': 'PASS', 'paper_reproduction': 'not_established',
         'raw_runs_git_ignored': True, 'raw_artifacts': raw_manifest}
(results / 'result_index.json').write_text(json.dumps(index, indent=2) + '\n')
print(json.dumps({'collected_results': str(results), 'figures': str(figures), 'source_run': str(source)}, indent=2))
