#!/usr/bin/env python3
"""Read back implementation evidence and byte hashes; no RDS parsing or QC."""
import argparse,csv,hashlib,json,pathlib
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--raw-root',type=pathlib.Path,required=True)
p.add_argument('--output',type=pathlib.Path,required=True)
a=p.parse_args()
repo=pathlib.Path(__file__).resolve().parents[3]
stage=repo/'planning/new-dataset/2026-10-26/input-legality-a03';ev=stage/'evidence'
prior=repo/'planning/new-dataset/2026-10-26/metadata-preparation'
def load(path):return json.loads(path.read_text())
def rows(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def keyed(path):
    r=rows(path);d={x['cell_id']:x for x in r};assert len(d)==len(r);return d
checks={}
meta=load(ev/'metadata-only-03/metadata_identity.json');full=load(ev/'full-03/metadata_identity.json')
checks['metadata_modes_identical']=meta==full
checks['NULL_sentinel_and_semantic_NULL_preserved']=(meta['raw_top_level_rownames_is_null'] and meta['raw_top_level_rownames'] is None and meta['raw_top_level_rownames_encoding']=={'type':'symbol','symbol':'\x01NULL\x01'})
checks['input_metadata_unchanged']=meta['input_object_unchanged']
checks['NA_and_unassigned_preserved']=(meta['fields']['diffusion']['all_missing_rows']==421 and meta['fields']['FACS']['all_missing_rows']==430 and meta['broad_unassigned']==136)
old=keyed(prior/'metadata-audit/cell_type_memberships.tsv');new=keyed(ev/'full-03/metadata_memberships.tsv')
assert old.keys()==new.keys()
cols=[c for c in next(iter(old.values())) if c!='cell_id']
def bit(v):return v in ('TRUE','1','1.0')
checks['all_44160_memberships_equal_prior']=all(bit(old[i][c])==bit(new[i][c]) for i in old for c in cols)
old_labels=keyed(prior/'metadata-audit/candidate_broad_reference.tsv');new_labels=keyed(ev/'full-03/metadata_candidate.tsv')
checks['all_1920_candidate_labels_equal_prior']=old_labels.keys()==new_labels.keys() and all((new_labels[i]['candidate_label'] if new_labels[i]['candidate_label']!='NA' else '')==old_labels[i]['candidate_label'] for i in old_labels)
old_flags=keyed(prior/'metadata-audit/cell_metadata_flags.tsv');new_flags=keyed(ev/'full-03/metadata_flags.tsv')
checks['all_missing_and_projected_flags_equal_prior']=old_flags.keys()==new_flags.keys() and all(bit(old_flags[i][c])==bit(new_flags[i][c]) for i in old_flags for c in ['diffusion_missing','FACS_missing','Projected'])
alignment=rows(ev/'full-03/count_metadata_alignment.tsv');genes=rows(ev/'full-03/gene_ids.tsv')
checks['explicit_cell_gene_IDs_unique']=len(alignment)==len({r['cell_id'] for r in alignment})==1920 and len(genes)==len({r['gene_id'] for r in genes})==46175
checks['count_metadata_by_ID']=all(list(new)[int(r['metadata_canonical_row'])-1]==r['cell_id'] for r in alignment)
legality=load(ev/'full-03/counts_legality.json');geo=load(ev/'full-03/geo_correspondence.json')
checks['full_count_legality_report']=legality['dimensions']==[46175,1920] and all(legality['statistics'][k]==0 for k in ['nonfinite','negative','noninteger'])
checks['GEO_all_values_equal']=geo['values_compared']==88656000 and geo['numeric_mismatches']==0 and geo['gene_sets_equal'] and geo['cell_sets_equal']
for mode in ['metadata-only','full']:
    status=load(ev/(mode+'-03')/'audit_status.json')
    checks[mode+'_boundary']=not any(status[k] for k in ['formal_execution_permitted','QC_filtering_performed','normalization_performed','clustering_or_metrics_run','scientific_input_lock_complete'])
    checks[mode+'_count_access']=status['counts_rds_read']==(mode=='full')
    receipt=load(ev/(mode+'-03.execution.json'))
    checks[mode+'_executed_source_hashes']=receipt['exit_code']==0 and all(hashlib.sha256((pathlib.Path(__file__).parent/n).read_bytes()).hexdigest()==h for n,h in receipt['source_sha256'].items())
    namespaces=load(ev/(mode+'-03')/'runtime.json')['loaded_namespaces']
    checks[mode+'_no_algorithm_namespace']=not ({'APL','CAdir','CAbiNet'} & set(namespaces))
cmd=load(ev/'metadata-only-03.execution.json')['command']
checks['metadata_only_has_no_counts_GEO_mount']=not any('/inputs/counts.rds' in x or '/inputs/GSE81682_HTSeq_counts.txt.gz' in x for x in cmd)
reg=load(ev/'metadata_identity_regression_03.json')
checks['nine_real_metadata_regressions_pass']=reg['status']=='PASS' and len(reg['checks'])==9 and all(reg['checks'].values())
reg_source=load(ev/'metadata_identity_regression_03.execution.json')['source_sha256']
checks['regression_source_hashes_match']=all(hashlib.sha256((pathlib.Path(__file__).parent/n).read_bytes()).hexdigest()==h for n,h in reg_source.items())
post_hashes=[]
for name,x in load(ev/'full-03/file_integrity.json').items():
    path=a.raw_root/name;h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    same=h.hexdigest()==x['sha256']==x['expected_sha256'] and path.stat().st_size==x['bytes']==x['expected_bytes']
    checks['source_unchanged_'+name]=same
    post_hashes.append({'name':name,'bytes':path.stat().st_size,'sha256':h.hexdigest(),'matches_pre_audit_and_receipt':same})
if a.output.exists():raise SystemExit('Output exists; preserve it and choose a new output')
a.output.write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'post_audit_source_integrity':post_hashes,'independent_review':False,'formal_execution_permitted':False},indent=2)+'\n')
print(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':len(checks)}))
raise SystemExit(0 if all(checks.values()) else 1)
