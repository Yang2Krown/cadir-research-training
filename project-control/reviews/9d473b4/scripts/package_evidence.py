from pathlib import Path
import json,hashlib,shutil,subprocess
root=Path('/workspace/cadir-r3-independent-20261026');pub=root/'publish';pub.mkdir(exist_ok=True)
record={'actual_diagnostic_command':['bash','/workspace/cadir-r3-review-source/cases/tabula_muris_limb/scripts/run-r.sh',str(root/'scripts/independent_r3.R')],'diagnostic_exit_code':0,'original_log':'evidence/independent_r3.log','original_RNG_not_received':True,'new_RNG_snapshots_labelled_diagnostic':True,'full_pipeline_rerun':False,'implementation_diagnostic_scripts_executed':False,'upstream_heads':{p:subprocess.check_output(['git','-C','/workspace/cadir-env/sources/'+p,'rev-parse','HEAD']).decode().strip() for p in ['APL','CAdir']}}
(root/'evidence/execution_record.json').write_text(json.dumps(record,indent=2))
for d in ['scripts','evidence']:shutil.copytree(root/d,pub/d,dirs_exist_ok=True)
shutil.copyfile(root/'独立复验报告.md',pub/'独立复验报告.md')
index={'review_date':'2026-10-26 Asia/Shanghai','machine_log_timezone':'UTC','reviewed_sha':'9d473b441058c45b2563c2ebe94ae99dda1f5209','parent_sha':'0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b','R3':'CLOSED_BY_INDEPENDENT_ACTUAL_OBJECT_REPLAYS_AND_BIDIRECTIONAL_SIGN_INTERVENTIONS','N2':'CLOSED_METADATA_ONLY','stage_decision':'PASS_WITH_EXPLICIT_SCOPE','scope':'6000-HVG single case; fixed or actually verified aligned CA basis; does not assert arbitrary-basis ranking invariance','next_stage':'May proceed to new-data preparation, preset experiment protocol and formal experiments under that protocol, followed by independent review.','report':'独立复验报告.md','files':[]}
for p in sorted(pub.rglob('*')):
    if p.is_file() and p.name!='evidence_index.json':index['files'].append({'path':str(p.relative_to(pub)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(pub/'evidence_index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False))
print(json.dumps({'publish':str(pub),'files':len(index['files'])+1,'total_bytes':sum(i['bytes'] for i in index['files']),'report_sha256':hashlib.sha256((pub/'独立复验报告.md').read_bytes()).hexdigest(),'index_sha256':hashlib.sha256((pub/'evidence_index.json').read_bytes()).hexdigest()},indent=2))
