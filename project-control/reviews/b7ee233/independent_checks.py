#!/usr/bin/env python3
"""Independent byte/source/readback checks; intentionally never opens raw RDS/GEO inputs."""
import csv, hashlib, json, pathlib, subprocess

repo = pathlib.Path('/workspace/cadir-hsc-a03-review-source-20261026')
stage_rel = pathlib.Path('planning/new-dataset/2026-10-26/input-legality-a03')
stage = repo / stage_rel
ev = stage / 'evidence'
checks = {}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text())

def rows(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()

head = git('rev-parse', 'HEAD')
checks['target_HEAD_exact'] = head == 'b7ee2335dc25ffab3a60d1feab44272d6d5a45cb'
checks['target_parent_exact'] = git('rev-parse', 'HEAD^') == 'd853986e2e3a1cabc9f3f728f616e402432257ec'
checks['detached_clean_worktree'] = not git('status', '--porcelain')
checks['preparation_history_unchanged_from_base'] = subprocess.run(
    ['git', '-C', str(repo), 'diff', '--quiet', 'd853986e2e3a1cabc9f3f728f616e402432257ec', head, '--',
     'planning/new-dataset/2026-10-26/metadata-preparation']).returncode == 0

# Independently rehash the committed A03 inventory, excluding its two self-indexes.
index = load(stage / 'evidence_index.json')
indexed = index['artifacts']
tsv = rows(stage / 'evidence_sha256.tsv')
checks['a03_evidence_index_has_90_entries'] = len(indexed) == len(tsv) == 90
checks['a03_indexes_agree'] = [(x['path'], x['bytes'], x['sha256']) for x in indexed] == [
    (x['path'], int(x['bytes']), x['sha256']) for x in tsv]
entry_results = []
for item in indexed:
    rel = pathlib.PurePosixPath(item['path'])
    safe = not rel.is_absolute() and '..' not in rel.parts
    path = repo / rel
    same = safe and path.is_file() and path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
    entry_results.append({'path': item['path'], 'ok': bool(same)})
checks['a03_all_indexed_bytes_match'] = all(x['ok'] for x in entry_results)

# Independently compare source files in this exact clean Git worktree to final run receipts.
source_names = ['audit_inputs.R', 'metadata_identity.R', 'run_input_audit.py']
source_paths = {n: repo / 'cases/nestorowa_hsc/scripts' / n for n in source_names}
source_hashes = {n: sha(p) for n, p in source_paths.items()}
source_receipts = {}
for name in ['metadata-only-03.execution.json', 'full-03.execution.json']:
    receipt = load(ev / name)
    source_receipts[name] = receipt['source_sha256']
    checks[name + '_exit_zero'] = receipt.get('exit_code') == 0
    checks[name + '_source_hashes_match_clean_HEAD'] = all(
        source_hashes[k] == v for k, v in receipt['source_sha256'].items())
reg_receipt = load(ev / 'metadata_identity_regression_03.execution.json')
reg_test_hash = sha(repo / 'cases/nestorowa_hsc/scripts/test_metadata_identity.R')
checks['regression_exit_zero'] = reg_receipt.get('exit_code') == 0
checks['regression_source_hashes_match_clean_HEAD'] = (
    reg_receipt['source_sha256'].get('test_metadata_identity.R') == reg_test_hash and
    reg_receipt['source_sha256'].get('metadata_identity.R') == source_hashes['metadata_identity.R'])

# Read-only mode, exact count/GEO metrics, and closeout boundaries from committed run outputs.
meta_cmd = load(ev / 'metadata-only-03.execution.json')['command']
full_cmd = load(ev / 'full-03.execution.json')['command']
checks['metadata_only_has_no_count_or_geo_file_mount'] = not any(
    token.endswith('/inputs/counts.rds') or token.endswith('/inputs/GSE81682_HTSeq_counts.txt.gz')
    for token in meta_cmd)
checks['metadata_only_manifest_contains_expected_metadata_only_mode'] = (
    'metadata-only' in meta_cmd and '/inputs/acquisition_manifest.json' in meta_cmd)
checks['full_mode_has_both_readonly_count_geo_mounts'] = all(
    any(f'src=/workspace/nestorowa-metadata-preparation/reacquired-20261026/{name}' in token and 'readonly' in token
        for token in full_cmd)
    for name in ['counts.rds', 'GSE81682_HTSeq_counts.txt.gz'])
for mode in ['metadata-only', 'full']:
    status = load(ev / f'{mode}-03/audit_status.json')
    checks[mode + '_formal_work_boundary_false'] = all(
        status[k] is False for k in ['formal_execution_permitted', 'QC_filtering_performed',
            'normalization_performed', 'clustering_or_metrics_run', 'scientific_input_lock_complete'])
    checks[mode + '_read_counts_state_matches_mode'] = status['counts_rds_read'] is (mode == 'full')
    checks[mode + '_audit_status_is_review_required'] = status['status'].endswith('REVIEW_REQUIRED')
counts = load(ev / 'full-03/counts_legality.json')
geo = load(ev / 'full-03/geo_correspondence.json')
checks['recorded_full_counts_statistics_strictly_legal'] = (
    counts['class'] == 'dgCMatrix' and counts['dimensions'] == [46175, 1920] and
    counts['statistics']['stored_values'] == 22595902 and
    all(counts['statistics'][k] == 0 for k in ['nonfinite', 'negative', 'noninteger']))
checks['recorded_geo_streaming_comparison_complete'] = (
    geo['values_compared'] == 88656000 and geo['numeric_mismatches'] == 0 and
    geo['GEO_rows'] == 46175 and geo['GEO_cells'] == 1920 and
    geo['gene_sets_equal'] and geo['cell_sets_equal'])
reg = load(ev / 'metadata_identity_regression_03.json')
checks['nine_identity_regressions_recorded_pass'] = (
    reg['status'] == 'PASS' and len(reg['checks']) == 9 and all(reg['checks'].values()) and
    len(reg['expected_rejections']) == 6)
readback = load(ev / 'implementation_readback.json')
checks['implementation_readback_is_explicitly_not_independent'] = (
    readback['status'] == 'PASS' and len(readback['checks']) == 25 and
    readback['independent_review'] is False)
for attempt in ['metadata-only-02', 'full-02']:
    old = load(ev / f'{attempt}/audit_status.json')
    receipt = load(ev / f'{attempt}.execution.json')
    checks[attempt + '_failure_is_retained_nonzero'] = (
        old['status'] == 'FAILED_INPUT_AUDIT' and receipt['exit_code'] != 0 and
        old['counts_rds_read'] is False)

# Recompute historical preparation bundle (61 entries), and verify no modification in this commit.
prep = repo / 'planning/new-dataset/2026-10-26/metadata-preparation'
bundle = rows(prep / 'bundle_sha256.tsv')
checks['historical_preparation_bundle_has_61_entries'] = len(bundle) == 61
bundle_results = []
for item in bundle:
    path = prep / item['path']
    bundle_results.append(path.is_file() and path.stat().st_size == int(item['bytes']) and sha(path) == item['sha256'])
checks['historical_preparation_bundle_hashes_match'] = all(bundle_results)
recovered = rows(prep / 'recovered_files_sha256.tsv')
recovered_results = [sha(prep / x['path']) == x['sha256'] for x in recovered]
checks['recovered_historical_files_hashes_match'] = all(recovered_results)

manifest = load(prep / 'acquisition_manifest.json')
raw_expected = {pathlib.PurePosixPath(x['path']).name: x for x in manifest['artifacts']
                if pathlib.PurePosixPath(x['path']).name in
                ['counts.rds', 'coldata.rds', 'GSE81682_HTSeq_counts.txt.gz']}
raw_dir = pathlib.Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026')
checks['specified_real_raw_directory_unavailable_here'] = not raw_dir.exists()
checks['manifest_records_three_expected_raw_inputs'] = len(raw_expected) == 3

result = {
    'status': 'PASS' if all(checks.values()) else 'FAIL',
    'checks': checks,
    'counts': {
        'A03_indexed_evidence_objects': len(indexed),
        'historical_preparation_bundle_objects': len(bundle),
        'recovered_historical_file_entries': len(recovered),
        'identity_regression_checks': len(reg['checks']),
        'implementation_readback_checks_not_independent': len(readback['checks']),
    },
    'source_HEAD': head,
    'source_sha256': source_hashes,
    'raw_expected_sha256_from_committed_manifest': {
        k: {'bytes': v['bytes'], 'sha256': v['sha256']} for k,v in raw_expected.items()},
    'raw_data_read_or_hashed_by_this_review': False,
    'limitations': [
        'No real reacquired RDS/GEO files are mounted or present in this workspace, so recorded raw hashes and numerical claims were not independently reproduced.',
        'This script only reads committed evidence and preparation bundle files; it does not deserialize RDS, read GEO numeric rows, or run a scientific pipeline.'
    ],
    'indexed_evidence_item_results': entry_results,
}
out = pathlib.Path('/workspace/cadir-hsc-a03-independent-review-20261026/independent_readback.json')
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'checks': len(checks), 'failed': [k for k,v in checks.items() if not v]}))
raise SystemExit(0 if all(checks.values()) else 1)
