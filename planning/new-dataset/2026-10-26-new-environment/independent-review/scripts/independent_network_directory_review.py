#!/usr/bin/env python3
"""Independent offline evidence review. No downloads, clustering, or evaluation."""
import argparse
import datetime as dt
import email.utils
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess

TARGET = 'e987d4c10c65e54977d44790a13c3be5da2518f8'
BASE = '122fdbf2986f3791917197385f8d07ba0a75fce6'
PREFIX = 'planning/new-dataset/2026-10-26-new-environment/'
STORAGE = 'https://mghp.osn.xsede.org/bir190004-bucket01/ExperimentHub/'
EXPECTED_CATALOG_SHA = '1c0786502f29cf67b892d7452dc03d29af6c1dda82ddd89118a4d79d10a83c4e'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, required=True)
parser.add_argument('--output-root', type=Path, required=True)
parser.add_argument('--catalog', type=Path, required=True)
args = parser.parse_args()
repo, out, catalog = args.repo.resolve(), args.output_root.resolve(), args.catalog.resolve()
assert not out.is_relative_to(repo)
out.mkdir(parents=True, exist_ok=False)
evidence = out / 'evidence'
evidence.mkdir()
root = repo / PREFIX
checks = []

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def check(name, condition, details=None):
    checks.append({'check': name, 'pass': bool(condition), 'details': details})

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*words):
    return subprocess.check_output(['git', '-C', str(repo), *words])

def tree(ref):
    return set(git('ls-tree', '-r', '--name-only', '-z', ref).decode().strip('\x00').split('\x00'))

def verify_manifest(manifest, basepath):
    result = []
    for entry in manifest:
        path = basepath / entry['path']
        data = path.read_bytes()
        result.append({'path': entry['path'], 'bytes': len(data), 'sha256': sha(data),
                       'pass': len(data) == entry['bytes'] and sha(data) == entry['sha256']})
    return result

check('exact_detached_target', git('rev-parse', 'HEAD').decode().strip() == TARGET)
initial_status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
check('initial_worktree_clean', not initial_status, initial_status)
basefiles = tree(BASE)
targetfiles = tree(TARGET)
delta = git('diff', '--name-status', BASE, TARGET).decode().splitlines()
check('only_additions_under_new_directory', all(x.startswith('A\t' + PREFIX) for x in delta), delta)
check('expected_46_additions', len(delta) == 46, len(delta))
check('baseline_365_files', len(basefiles) == 365, len(basefiles))
protection = json.loads((root / 'evidence/protected-files.json').read_text())
check('protection_manifest_covers_entire_baseline', {x['path'] for x in protection} == basefiles
      and len(protection) == 365, len(protection))
protected = verify_manifest(protection, repo)
for row in protected:
    base_data = git('show', BASE + ':' + row['path'])
    target_data = git('show', TARGET + ':' + row['path'])
    row.update(baseline_sha256=sha(base_data), target_blob_sha256=sha(target_data))
    row['pass'] = row['pass'] and base_data == target_data and sha(base_data) == row['sha256']
dump(evidence / 'protected-files-independent.json', protected)
check('all_365_baseline_files_byte_preserved', all(x['pass'] for x in protected))

index = json.loads((root / 'evidence_index.json').read_text())
indexed = verify_manifest(index, root)
actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
check('implementation_index_complete_except_self', {x['path'] for x in index} == actual - {'evidence_index.json'}
      and len(index) == len({x['path'] for x in index}), {'indexed': len(index), 'actual': len(actual)})
check('all_lightweight_index_hashes', all(x['pass'] for x in indexed))
dump(evidence / 'implementation-index-independent.json', indexed)
for p in root.rglob('*.json'):
    json.loads(p.read_text())

external_manifest = json.loads((root / 'evidence/external-artifacts.json').read_text())
external = verify_manifest(external_manifest, Path('/'))
dump(evidence / 'external-artifacts-independent.json', external)
check('all_8_external_artifacts', len(external) == 8 and all(x['pass'] for x in external))
catalog_before = catalog.read_bytes()
check('catalog_bytes_and_hash', len(catalog_before) == 10378240 and sha(catalog_before) == EXPECTED_CATALOG_SHA,
      {'path': str(catalog), 'bytes': len(catalog_before), 'sha256': sha(catalog_before)})

# Query by logical AH IDs independently; explicitly expose both integer key spaces.
query = '''SELECT r.id AS resource_id, r.ah_id, r.title, r.rdatadateadded,
                  p.id AS fetch_id, p.resource_id AS rdatapath_resource_id,
                  p.rdatapath,p.rdataclass,l.location_prefix
           FROM resources r
           JOIN rdatapaths p ON p.resource_id=r.id
           JOIN location_prefixes l ON l.id=r.location_prefix_id
           WHERE r.ah_id IN ('EH2694','EH2695') ORDER BY r.ah_id'''
conn = sqlite3.connect(catalog.as_uri() + '?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
rows = [dict(row) for row in conn.execute(query)]
sources = [dict(row) for row in conn.execute('SELECT * FROM input_sources WHERE resource_id IN (2694,2695) ORDER BY resource_id')]
for row in rows:
    row['official_storage_url'] = row['location_prefix'] + row['rdatapath']
    row['fetch_url'] = 'https://experimenthub.bioconductor.org/fetch/' + str(row['fetch_id'])
conn.close()
expected = [('EH2694',2694,2710,'counts','dgCMatrix'), ('EH2695',2695,2711,'coldata','DataFrame')]
check('sqlite_exact_mapping', len(rows) == 2 and all(
    row['ah_id'] == ah and row['resource_id'] == rid and row['rdatapath_resource_id'] == rid
    and row['fetch_id'] == fetch and row['rdatapath'] == 'scRNAseq/nestorowa-hsc/2.0.0/' + kind + '.rds'
    and row['rdataclass'] == klass and row['location_prefix'] == STORAGE
    for row, (ah,rid,fetch,kind,klass) in zip(rows,expected)), rows)
dump(evidence / 'sqlite-independent.json', {'uri_mode': 'ro', 'query': query, 'rows': rows, 'input_sources': sources,
     'content_verified': False, 'matrix_or_label_audit_performed': False})
plan = json.loads((root / 'evidence/acquisition/acquisition_plan.json').read_text())
check('implementation_plan_matches_independent_sqlite', all(
    original['ah_id'] == row['ah_id'] and original['fetch_id'] == row['fetch_id'] and original['rdatapath'] == row['rdatapath']
    and original['official_storage_url'] == row['official_storage_url'] for original,row in zip(plan['resources'],rows)))

network = root / 'evidence/network'
network_findings = []
for key in ['counts','coldata','geo']:
    receipt = json.loads((network / (key + '-network-enabled.request.json')).read_text())
    old = json.loads((network / (key + '.request.json')).read_text())
    headers = (network / (key + '-network-enabled.headers.txt')).read_bytes()
    stderr = (network / (key + '-network-enabled.stderr.txt')).read_text()
    curl = receipt['curl']
    expected_url = (STORAGE + 'scRNAseq/nestorowa-hsc/2.0.0/' + key + '.rds') if key != 'geo' else \
        'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81682/suppl/GSE81682_HTSeq_counts.txt.gz'
    check(key + '_formal_connect403', receipt['url'] == expected_url and receipt['exit_code'] == curl['exitcode'] == 56
          and curl['http_connect'] == 403 and curl['http_code'] == 0 and curl['size_download'] == 0
          and receipt['downloaded_bytes'] == 0 and receipt['sha256'] is None
          and curl['method'] == 'GET' and curl['num_redirects'] == 0 and curl['proxy_used'] == 1
          and curl['time_appconnect'] == 0 and b'HTTP/1.1 403 Forbidden\r\n' in headers
          and b'server: envoy\r\n' in headers and 'CONNECT tunnel failed, response 403' in stderr
          and receipt['network_permission_enabled'] and receipt['inherited_proxy_preserved']
          and receipt['tls_verification_enabled'])
    check(key + '_initial_proxy_failure_separate', old['exit_code'] == old['curl']['exitcode'] == 7
          and old['curl']['http_connect'] == 0 and old['curl']['http_code'] == 0
          and old['curl']['num_connects'] == 0 and 'Failed to connect to proxy port 8080' in old['curl']['errormsg']
          and not (network / (key + '.headers.txt')).read_bytes()
          and dt.datetime.fromisoformat(old['end_utc']) < dt.datetime.fromisoformat(receipt['start_utc']))
    check(key + '_safe_recorded_curl_options', '--insecure' not in receipt['command'] and '-k' not in receipt['command']
          and '--noproxy' not in receipt['command'] and '--proxy' not in receipt['command'])
    network_findings.append({'kind':key, 'formal_start_utc':receipt['start_utc'], 'formal_end_utc':receipt['end_utc'],
         'formal_exit':receipt['exit_code'], 'http_connect':curl['http_connect'], 'origin_http':curl['http_code'],
         'downloaded_bytes':receipt['downloaded_bytes'], 'sha256':receipt['sha256'], 'initial_exit':old['exit_code'],
         'url':receipt['url'], 'origin_tls_established':False})

head_findings = []
for row in rows:
    stem = 'fetch-' + str(row['fetch_id'])
    receipt = json.loads((network / (stem + '.request.json')).read_text())
    headers = (network / (stem + '.headers.txt')).read_text()
    curl = receipt['curl']
    dates = [line.split(': ',1)[1] for line in headers.splitlines() if line.lower().startswith('date: ')]
    parsed_dates = [email.utils.parsedate_to_datetime(x) for x in dates]
    when = dt.datetime.fromisoformat(receipt['time_utc'])
    check(stem + '_correct_head302_and_date', receipt['command'][-1] == row['fetch_url']
          and '--head' in receipt['command'] and '--location' not in receipt['command']
          and receipt['exit_code'] == 0 and curl['method'] == 'HEAD' and curl['http_code'] == 302
          and curl['http_connect'] == 200 and curl['num_redirects'] == 0 and curl['size_download'] == 0
          and curl['redirect_url'] == row['official_storage_url']
          and 'location: ' + row['official_storage_url'] in headers and len(parsed_dates) == 2
          and all(x.date() == when.date() and abs((x - when).total_seconds()) < 5 for x in parsed_dates))
    head_findings.append({'fetch_id':row['fetch_id'], 'time_utc':receipt['time_utc'], 'header_dates':dates,
                          'http_code':curl['http_code'], 'location':curl['redirect_url'], 'followed':False})
dump(evidence / 'network-receipts-independent.json', {'get_requests':network_findings, 'head_requests':head_findings,
     'new_requests_by_reviewer':0, 'reason_no_new_request':'Existing explicit CONNECT403 evidence sufficient; no retry or bypass.'})

status = json.loads((out.parent / 'evidence/current-environment-status.json').read_text())
shutil.copyfile('/etc/codex/network-policy.json', evidence / 'current-network-policy.json')
policy = json.loads((evidence / 'current-network-policy.json').read_text())
recorded = json.loads((network / 'environment-status.json').read_text())
recorded_again = json.loads((network / 'environment-status-recheck.json').read_text())
targets = ['mghp.osn.xsede.org','ftp.ncbi.nlm.nih.gov']
check('fresh_environment_unknown_not_enforced', status['observations_current'] is True
      and status['network_policy']['mode'] == 'restricted' and status['network_policy']['state'] == 'unknown')
check('same_bound_config_version', all(status[k] == recorded[k] == recorded_again[k]
      for k in ['environment_id','source_config_id','source_config_version_id','spec_revision','observed_spec_revision']))
check('current_targets_absent_from_returned_lists', all(host not in status['network_policy']['effective_allowed_hosts'] for host in targets))
check('policy_snapshot_matches_recorded_bytes', (network / 'network-policy.json').read_bytes() == (evidence / 'current-network-policy.json').read_bytes())
check('policy_v1_no_vpn_and_no_target_entries', policy['version'] == 1 and policy['vpn_configured'] is False
      and all(host not in [x['host'] for x in policy['http_network_policy']['egress_rules']] for host in targets))
dump(evidence / 'environment-interpretation.json', {'observations_current':status['observations_current'],
    'network_policy_state':status['network_policy']['state'], 'enforced_established':False,
    'matching_bound_config':status['source_config_version_id'], 'actual_request_evidence':'CONNECT403',
    'user_new_published_version_id_available':False, 'cause_of_binding_mismatch_established':False})

# Read a focused set of control documents from the control ref, never treating them as files in the plan branch.
docs = ['README.md','下一阶段启动与验收规则.md','首阶段结论-2026-10-26.md','新数据准备阶段结论-2026-10-26.md','AI使用与调度记录.md']
control_dir = evidence / 'control-reference'
control_dir.mkdir()
for name in docs:
    (control_dir / name).write_bytes(git('show','origin/control/stage1-quality-20261025:project-control/' + name))
refs = {'origin/control/stage1-quality-20261025':'9db89e675fa13fdc1d08b97b7f4782f9a2dad337',
        'origin/fix/stage1-review-20261025':'9d473b441058c45b2563c2ebe94ae99dda1f5209',
        'origin/plan/new-dataset-audit-20261026':BASE}
ref_rows = {ref:git('rev-parse',ref).decode().strip() for ref in refs}
check('three_fixed_ref_values', ref_rows == refs, ref_rows)
dump(evidence / 'refs-independent.json',ref_rows)

# Execute existing offline/refusal interfaces into new directories only. No --download option.
executions = []
commands = [
 ('offline-mapping', ['python3','cases/nestorowa_hsc/scripts/acquire_hub.py','--catalog',str(catalog),'--output-root',str(out / 'offline-plan')],0),
 ('protocol-gate', ['python3','cases/nestorowa_hsc/scripts/check_protocol.py','planning/new-dataset/2026-10-26/pre-registration.json','--require-ready'],2),
 ('missing-inputs', ['bash','cases/nestorowa_hsc/scripts/run-r.sh','cases/nestorowa_hsc/scripts/audit_inputs.R',
      '/workspace/cadir-validation-20261026/data/hub-attempt/counts.rds',
      '/workspace/cadir-validation-20261026/data/hub-attempt/coldata.rds',str(out / 'missing-inputs')],2)]
check('real_rds_inputs_absent_before_audit', all(not Path(p).exists() for p in commands[2][1][-3:-1]))
if any(Path(p).exists() for p in commands[2][1][-3:-1]):
    raise SystemExit('Real inputs now exist; refuse this missing-input-only review execution.')
for name,command,expected_exit in commands:
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = subprocess.run(command,cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
    (evidence / (name + '.stdout.txt')).write_bytes(result.stdout)
    (evidence / (name + '.stderr.txt')).write_bytes(result.stderr)
    executions.append({'name':name,'command':command,'start_utc':started,'end_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                       'exit_code':result.returncode,'expected_exit':expected_exit})
    check(name + '_independent_exit', result.returncode == expected_exit)
offline = json.loads((out / 'offline-plan/acquisition_plan.json').read_text())
check('offline_plan_matches_sqlite_and_no_download', not offline['download_requested'] and offline['catalog_sha256'] == EXPECTED_CATALOG_SHA
      and [x['fetch_id'] for x in offline['resources']] == [2710,2711]
      and [x['official_storage_url'] for x in offline['resources']] == [x['official_storage_url'] for x in rows])
gate = json.loads((evidence / 'protocol-gate.stdout.txt').read_text())
check('formal_gate_refuses', gate['formal_execution_permitted'] is False and bool(gate['blocking_conditions']))
missing = json.loads((out / 'missing-inputs/audit_status.json').read_text())
check('missing_audit_blocks_without_algorithm', missing['status'] == 'BLOCKED_INPUTS_NOT_ACQUIRED'
      and missing['clustering_or_evaluation_run'] is False and missing['matrix_version_shape_QC_labels'] == 'NOT_VERIFIED')
dump(evidence / 'independent-executions.json',executions)

check('catalog_unchanged_after_review', catalog.read_bytes() == catalog_before)
check('worktree_still_clean', not git('status','--porcelain=v1','--untracked-files=all').decode())
check('implementation_repo_still_target', subprocess.check_output(['git','-C','/workspace/cadir-validation-20261026/repo','rev-parse','HEAD']).decode().strip() == TARGET)
summary = {'reviewed_sha':TARGET, 'baseline_sha':BASE, 'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
           'checks':checks, 'check_count':len(checks), 'failed_checks':[x['check'] for x in checks if not x['pass']],
           'scope':'network/catalog/directory/blocking evidence only', 'real_data':'BLOCKED', 'formal_design':'BLOCKED',
           'formal_experiment':'BLOCKED', 'reviewer_network_requests':0, 'new_clustering_or_ARI_NMI_run':False}
dump(evidence / 'independent-checks.json',summary)
print(json.dumps({'check_count':len(checks),'failed_checks':summary['failed_checks'],'evidence_directory':str(evidence)},ensure_ascii=False,indent=2))
raise SystemExit(1 if summary['failed_checks'] else 0)
