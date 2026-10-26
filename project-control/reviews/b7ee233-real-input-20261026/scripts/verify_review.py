#!/usr/bin/env python3
"""Mechanical readback of this review's own evidence, not implementation PASS files."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda p: json.loads((root/p).read_text())
checks = []
def check(name, condition):
    checks.append({'check':name,'passed':bool(condition)})

before, after = read('source_before.json'), read('source_after.json')
check('fixed_HEAD_clean_unchanged', before['HEAD']==after['HEAD']=='b7ee2335dc25ffab3a60d1feab44272d6d5a45cb'
      and before['status_porcelain']==after['status_porcelain']=='')
check('four_source_hashes_unchanged', before['files']==after['files'] and len(before['files'])==4)
for name, ent in before['files'].items():
    data=(root/'preserved-target-source'/name).read_bytes()
    check('preserved_source_'+name,len(data)==ent['bytes'] and hashlib.sha256(data).hexdigest()==ent['sha256'])
search=read('real_file_search_no_follow.json')
check('normal_search_no_match_no_error', search['execution']['exit_code']==1 and search['candidates']==[] and search['stderr']=='')
attempts=read('acquisition_attempts.json')
check('three_unique_URL_attempts', len(attempts)==3 and len({x['url'] for x in attempts})==3 and all(x['attempt_count']==1 for x in attempts))
for attempt in attempts:
    curl=attempt['curl_metadata']
    check('exact_blocked_receipt_'+attempt['name'], attempt['exit_code']==curl['exitcode']==22
          and curl['http_connect']==403 and curl['http_code']==0 and curl['num_redirects']==0
          and curl['num_retries']==0 and curl['size_download']==0 and curl['proxy_used']==1
          and attempt['partial_file'] is None and not attempt['matches_expected']
          and attempt['status']=='BLOCKED_ACQUISITION')
probes=read('entry_startup_probes.json')
check('two_fixed_entry_startup_failures', {x['mode'] for x in probes}=={'metadata-only','full'}
      and all(x['execution']['exit_code']==1 and not x['audit_completed']
      and not x['target_execution_receipt_exists'] and not x['target_console_log_exists']
      and not x['output_directory_exists'] and x['source_before']['files']==x['source_after']['files']==before['files']
      and not any(x['intended_raw_input_paths_exist'].values()) for x in probes))
for mode in ['metadata-only','full']:
    log=(root/'logs'/('wrapper_'+mode+'_startup.stderr.log')).read_text()
    check('real_original_wrapper_image_exception_'+mode,'line 22' in log and 'No such image: cadir-r-ver:4.4.1-bioc3.19' in log and 'CalledProcessError' in log)
result=read('review_result.json')
check('no_false_A01_PASS_or_release',result['overall']=='BLOCKED' and not result['A01_can_close']
      and result['real_input_audits_completed']==result['real_metadata_negative_tests_completed']==0
      and not result['formal_execution_permitted'] and not result['counts_simulation_used']
      and not result['synthetic_metadata_used'] and not result['implementation_verifier_invoked'])
check('no_large_raw_payloads_in_review',all(p.stat().st_size<1024*1024 for p in root.rglob('*') if p.is_file())
      and not any(p.name in ('counts.rds','coldata.rds','GSE81682_HTSeq_counts.txt.gz') for p in root.rglob('*') if p.is_file()))
print(json.dumps({'subject':'independent availability/startup receipts only','checks':checks,
      'passed':all(x['passed'] for x in checks),'not_a_real_input_PASS':True},indent=2))
raise SystemExit(0 if all(x['passed'] for x in checks) else 1)
