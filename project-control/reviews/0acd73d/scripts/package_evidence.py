from pathlib import Path
import json,hashlib,shutil
root=Path('/workspace/cadir-stage1-retest');publish=root/'publish';publish.mkdir(exist_ok=True)
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
artifacts=[info(p) for part in ['complete-entry','final-smoke-entry'] for p in sorted((root/part).rglob('*')) if p.is_file()]
(root/'evidence/external_artifacts.json').write_text(json.dumps({'root':str(root),'input_not_copied':'/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds','raw_run_artifacts':artifacts},indent=2))
for sub in ['evidence','scripts']:
    shutil.copytree(root/sub,publish/sub,dirs_exist_ok=True)
shutil.copyfile(root/'独立复验报告.md',publish/'独立复验报告.md')
rawlogs=publish/'raw-logs';rawlogs.mkdir(exist_ok=True)
for part in ['complete-entry','final-smoke-entry']:
    for p in sorted((root/part).rglob('*')):
        if p.is_file() and (p.suffix=='.log' or p.name in ['status.json','verification.json','ranking_provenance.json','input_integrity.json','resources.json']):
            target=rawlogs/part/p.relative_to(root/part);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
index={'body_review_sha':'8561914bc67c511ec76374996fb12d713f23f171','final_review_sha':'0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b','baseline_sha':'756c8d16ae22fe671f7b715a696c8272523e08ed','decision':'PENDING_EVIDENCE_NO_STAGE_RELEASE','blocking_item':'R3 old independent actual ranking discrepancy remains untraced','R1_final':'CLOSED_BY_INDEPENDENT_INCREMENTAL_RETEST','R2':'CLOSED','R4':'CLOSED','R5':'CLOSED','R6':'CLOSED','scope':'independent full body retest + independent environment isolation incremental retest','report':'独立复验报告.md','files':[]}
for p in sorted(publish.rglob('*')):
    if p.is_file() and p.name!='evidence_index.json':
        item=info(p);item['path']=str(p.relative_to(publish));index['files'].append(item)
(publish/'evidence_index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False))
print(json.dumps({'published_files':len(index['files'])+1,'total_bytes':sum(x['bytes'] for x in index['files']),'publish':str(publish)},indent=2))
