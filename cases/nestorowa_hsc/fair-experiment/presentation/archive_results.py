#!/usr/bin/env python3
"""Archive real small outputs and hash every external artifact; never rerun science."""
import csv,hashlib,json,pathlib,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=ROOT/'cases/nestorowa_hsc/fair-experiment'
run=pathlib.Path(sys.argv[1]).resolve();presentation=pathlib.Path(sys.argv[2]).resolve()
dest=BASE/'results'/run.name
assert not dest.exists(), 'Refusing to overwrite an existing result archive'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entry(p,role):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),role=role)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
receipts=json.loads((run/'attempt-receipts.json').read_text());assert len(receipts)==10 and all(r['exit_code']==0 for r in receipts)
assert all(r.get('diagnostic_exit_code')==0 for r in receipts if r['method']=='cadir')
assert json.loads((presentation/'presentation-status.json').read_text())['status']=='PRESENTATION_COMPLETE_PENDING_INDEPENDENT_RESULT_REVIEW'
manifest=json.loads((BASE/'locks/source-manifest.json').read_text())
for e in manifest['files']:
 p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],str(p)
for r in receipts:
 p=pathlib.Path(r['attempt_directory']);m=json.loads((p/'core-artifacts-sha256.json').read_text())
 for e in m['files']:
  x=p/e['path'];assert x.stat().st_size==e['bytes'] and sha(x)==e['sha256'],str(x)
dest.mkdir(parents=True)
external=[];copied=[];large=[]
roots=[('formal',run),('presentation',presentation),('terminal-capture',run.parents[1]/'formal-capture'/run.name)]
for prefix,src in roots:
 for p in sorted(src.rglob('*')):
  if not p.is_file():continue
  role='serialized_external_object' if p.suffix.lower()=='.rds' else 'small_result_or_evidence'
  external.append(entry(p,role))
  # Exact small RNG states are retained; expression/CA/cluster/graph objects stay external.
  keep=p.suffix.lower()!='.rds' or (p.name=='rng.rds' and p.stat().st_size<=65536)
  if keep:
   q=dest/prefix/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
   copied.append(dict(archive_path=str(q.relative_to(ROOT)),source_path=str(p),bytes=q.stat().st_size,sha256=sha(q)))
  else:large.append(entry(p,role))
review=pathlib.Path('/workspace/hsc-design-independent-review/reviews/hsc-design-20261026')
for name in ['admission.json','独立阶段一科学审查报告.md','C04独立裁定.md','execution-role-disclosure.json']:
 p=review/name
 if p.is_file():
  q=dest/'design-admission'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
  copied.append(dict(archive_path=str(q.relative_to(ROOT)),source_path=str(p),bytes=q.stat().st_size,sha256=sha(q)))
lock=json.loads((BASE/'locks/data-input-lock.json').read_text())
for e in lock['files']:
 p=pathlib.Path(e['path']);assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],str(p)
dump(dest/'post-run-input-source-integrity.json',dict(source_manifest_sha256=sha(BASE/'locks/source-manifest.json'),source_entries=len(manifest['files']),data_lock_sha256=sha(BASE/'locks/data-input-lock.json'),data_entries=len(lock['files']),all_current_bytes_match_frozen_locks=True,original_admission_equals_run_copy=json.loads((review/'admission.json').read_text())==json.loads((run/'admission-used.json').read_text())))
backup=[dict(**e,role='raw_or_common_preparation') for e in lock['files'] if pathlib.Path(e['path']).suffix.lower()=='.rds' or pathlib.Path(e['path']).name=='GSE81682_HTSeq_counts.txt.gz']+large
dump(dest/'external-artifacts-sha256.json',dict(files=external,all_formal_and_presentation_files_hashed=True))
dump(dest/'archive-copy-sha256.json',dict(files=copied))
dump(dest/'large-objects-export-manifest.json',dict(files=backup,backup_status='External execution workspace only. User-local download and independent hash verification not established.',not_in_git=[e['path'] for e in large]))
with open(dest/'large-objects-export-manifest.tsv','w') as f:
 w=csv.DictWriter(f,fieldnames=['path','bytes','sha256','role'],delimiter='\t');w.writeheader();w.writerows(backup)
rank_rows=[]
for r in receipts:
 if r['method']!='cadir':continue
 p=pathlib.Path(r['attempt_directory']);s=json.loads((p/'gene-assignment-summary.json').read_text());k=json.loads((p/'diagnostics/ranking-provenance.json').read_text())
 rank_rows.append(dict(seed=r['seed'],input_genes=s['input_genes'],assigned_genes=s['assigned_genes'],unassigned_genes=s['unassigned_genes'],qcutoff=s['qcutoff'],ranked_genes=k['complete_ranked_genes'],alpha_genes=k['alpha_genes'],score_max_error=k['independent_score_max_error'],ranking_elapsed_seconds=k['ranking_elapsed_seconds'],CA_sha256=k['CA_sha256'],unranked_sha256=k['unranked_sha256']))
with open(dest/'gene-ranking-summary.tsv','w') as f:
 w=csv.DictWriter(f,fieldnames=list(rank_rows[0]),delimiter='\t');w.writeheader();w.writerows(rank_rows)
dump(dest/'archive-status.json',dict(status='REAL_RESULTS_ARCHIVED_PENDING_NEW_INDEPENDENT_RESULT_REVIEW',source_commit='6cc7b3da67c193da11a67c45a75167d6521438b0',design_review_commit='2d2565c24b3958260d7232ff03f211c06bd2e845',core_successes=10,core_denominator=10,diagnostic_successes=5,diagnostic_denominator=5,source_files_verified=len(manifest['files']),external_files_hashed=len(external),copied_small_files=len(copied),external_large_objects=len(large),no_new_scientific_computation=True))
print(json.dumps(dict(archive=str(dest),small_files=len(copied),large_objects=len(large),external_files=len(external)),indent=2))
