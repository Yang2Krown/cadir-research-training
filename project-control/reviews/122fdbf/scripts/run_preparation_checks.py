from pathlib import Path
import subprocess,json,os,csv
root=Path('/workspace/cadir-newdata-prep-independent-20261026');ev=root/'evidence';src=Path('/workspace/cadir-newdata-prep-review-source');base=src/'cases/nestorowa_hsc';protocol=src/'planning/new-dataset/2026-10-26/pre-registration.json';results=[]
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
def run(name,cmd,want):
    with (ev/(name+'.log')).open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    results.append({'name':name,'command':cmd,'exit_code':p.returncode,'expected_exit_code':want});(ev/'executions.json').write_text(json.dumps(results,indent=2));assert p.returncode==want
run('protocol_structure',['python',str(base/'scripts/check_protocol.py'),str(protocol)],0)
run('formal_gate',['python',str(base/'scripts/check_protocol.py'),str(protocol),'--require-ready'],2)
run('offline_acquisition_plan',['python',str(base/'scripts/acquire_hub.py'),'--catalog','/workspace/cadir-newdata-20261026/acquisition/experimenthub.sqlite3','--output-root',str(root/'offline-plan')],0)
audit=lambda a,b,c:['bash',str(base/'scripts/run-r.sh'),str(base/'scripts/audit_inputs.R'),str(a),str(b),str(c)]
run('missing_real_inputs',audit(root/'not-acquired-counts.rds',root/'not-acquired-coldata.rds',root/'missing-real'),2)
run('make_own_toy',['bash',str(base/'scripts/run-r.sh'),str(root/'scripts/make_independent_toy.R')],0)
run('own_positive',audit(root/'toy/counts.rds',root/'toy/coldata.rds',root/'toy-positive'),0)
run('own_duplicate_ID',audit(root/'toy/duplicate_cells.rds',root/'toy/coldata.rds',root/'toy-duplicate'),1)
def read(n):return json.loads((root/n).read_text())
status=read('toy-positive/audit_status.json');meta=read('toy-positive/metadata_audit.json');dup=read('toy-duplicate/audit_status.json');missing=read('missing-real/audit_status.json')
with (root/'toy-positive/flat_cell_metadata.tsv').open() as h:flat=list(csv.DictReader(h,delimiter='\t'))
assert [(r['cell_id'],r['donor']) for r in flat]==[('cell_B','donor_B'),('cell_A','donor_A')]
assert 'FACS' not in flat[0] and meta['unique_reference_field']=='NOT_FROZEN' and meta['aligned_by_explicit_ids'] and not meta['metadata_ids_order_identical']
facs=next(x for x in meta['fields'] if x['name']=='FACS');assert facs['dimensions']==[2,2] and facs['subfields']==['broad_HSPC','narrow_HSC']
assert status['scientific_input_lock_complete'] is False and status['clustering_or_evaluation_run'] is False and dup['status']=='FAILED_STRUCTURE' and missing['status']=='BLOCKED_INPUTS_NOT_ACQUIRED'
result={'independent_synthetic_dimensions':[3,2],'positive':status,'flat_ID_donor_alignment':flat,'nested_FACS':facs,'nested_overlapping_FACS_not_coerced_to_exclusive_truth':True,'unique_reference_field':meta['unique_reference_field'],'duplicate_ID_case':dup,'missing_real_input_case':missing,'formal_execution_permitted':json.loads((ev/'formal_gate.log').read_text())['formal_execution_permitted'],'no_clustering_or_metrics_executed':True}
(ev/'independent_preparation_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
