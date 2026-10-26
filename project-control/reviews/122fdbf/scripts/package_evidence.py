from pathlib import Path
import json,shutil,hashlib
root=Path('/workspace/cadir-newdata-prep-independent-20261026');pub=root/'publish';pub.mkdir(exist_ok=True)
for d in ['evidence','scripts']:shutil.copytree(root/d,pub/d,dirs_exist_ok=True)
shutil.copyfile(root/'独立准备复核报告.md',pub/'独立准备复核报告.md')
for folder in ['offline-plan','missing-real','toy-positive','toy-duplicate']:
    for p in sorted((root/folder).rglob('*')):
        if p.is_file() and p.suffix in ['.json','.tsv']:
            target=pub/'test-outputs'/folder/p.relative_to(root/folder);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
raw=pub/'raw-receipts';raw.mkdir(exist_ok=True)
for n in ['hub-correct-redirect.json','correct-mghp-head.json','geo-network-attempt.txt.gz.json','hub-redirect-probe.json']:
    shutil.copyfile(Path('/workspace/cadir-newdata-20261026/acquisition')/n,raw/n)
index={'reviewed_sha':'122fdbf2986f3791917197385f8d07ba0a75fce6','review_date':'2026-10-26 Asia/Shanghai','raw_log_timestamps':'UTC','decision':'PREPARATION_MATERIALS_ACCEPTED_FORMAL_DATA_AND_DESIGN_BLOCKED','real_HSC_input_audit_pass':False,'formal_experiment_released':False,'network_configuration_request_supported':True,'minimum_extra_hosts':['mghp.osn.xsede.org','ftp.ncbi.nlm.nih.gov'],'reviewer_network_requests':0,'reviewer_clustering_or_metrics_executions':0,'report':'独立准备复核报告.md','files':[]}
for p in sorted(pub.rglob('*')):
    if p.is_file() and p.name!='evidence_index.json':index['files'].append({'path':str(p.relative_to(pub)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(pub/'evidence_index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False))
print(json.dumps({'publish':str(pub),'files':len(index['files'])+1,'total_bytes':sum(x['bytes'] for x in index['files']),'report_sha256':hashlib.sha256((pub/'独立准备复核报告.md').read_bytes()).hexdigest(),'index_sha256':hashlib.sha256((pub/'evidence_index.json').read_bytes()).hexdigest()},indent=2))
