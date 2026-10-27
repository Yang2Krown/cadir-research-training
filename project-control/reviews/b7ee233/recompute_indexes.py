#!/usr/bin/env python3
import csv, hashlib, json, pathlib, subprocess
repo=pathlib.Path('/workspace/cadir-hsc-a03-review-source-20261026')
out=pathlib.Path('/workspace/cadir-hsc-a03-independent-review-20261026')
stage=repo/'planning/new-dataset/2026-10-26/input-legality-a03'
prep=repo/'planning/new-dataset/2026-10-26/metadata-preparation'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def rows(p):
    with p.open(newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
def write_tsv(path,header,items):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=header,delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(items)
a03=json.loads((stage/'evidence_index.json').read_text())['artifacts']
a03_rows=[]
for x in a03:
    p=repo/x['path']; actual=sha(p) if p.is_file() else ''
    size=p.stat().st_size if p.is_file() else -1
    a03_rows.append({'path':x['path'],'indexed_bytes':x['bytes'],'actual_bytes':size,
                     'indexed_sha256':x['sha256'],'actual_sha256':actual,
                     'matches':str(size==x['bytes'] and actual==x['sha256']).lower()})
write_tsv(out/'recomputed_a03_evidence_sha256.tsv',list(a03_rows[0]),a03_rows)
bundle=rows(prep/'bundle_sha256.tsv'); bundle_rows=[]
for x in bundle:
    p=prep/x['path']; actual=sha(p) if p.is_file() else ''; size=p.stat().st_size if p.is_file() else -1
    bundle_rows.append({'path':x['path'],'indexed_bytes':x['bytes'],'actual_bytes':size,
                        'indexed_sha256':x['sha256'],'actual_sha256':actual,
                        'matches':str(size==int(x['bytes']) and actual==x['sha256']).lower()})
write_tsv(out/'historical_bundle_readback.tsv',list(bundle_rows[0]),bundle_rows)
status=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
parent=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD^'],text=True).strip()
ref=subprocess.check_output(['git','-C',str(repo),'rev-parse','refs/remotes/origin/fix/nestorowa-input-audit-a03-20261026'],text=True).strip()
source_names=['audit_inputs.R','metadata_identity.R','run_input_audit.py','test_metadata_identity.R','verify_a03_evidence.py','inspect_legacy_rownames.R']
source_hashes={n:sha(repo/'cases/nestorowa_hsc/scripts'/n) for n in source_names}
proof={'target_HEAD':head,'target_parent':parent,'local_origin_ref':ref,
       'worktree_clean':not status,'status_porcelain':status,
       'source_sha256':source_hashes,
       'real_raw_directory_present':pathlib.Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026').exists(),
       'source_worktree_modified_by_reviewer':bool(status),
       'output_directory':'/workspace/cadir-hsc-a03-independent-review-20261026'}
(out/'source_protection.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'A03_hashes':len(a03_rows),'A03_all_match':all(x['matches']=='true' for x in a03_rows),
                  'historical_bundle':len(bundle_rows),'historical_all_match':all(x['matches']=='true' for x in bundle_rows),
                  'source_clean':not status,'HEAD':head,'origin_ref':ref}))
