from pathlib import Path
import json,hashlib,sqlite3,subprocess,sys
root=Path('/workspace/cadir-newdata-prep-independent-20261026');ev=root/'evidence';ev.mkdir(parents=True,exist_ok=True)
src=Path('/workspace/cadir-newdata-prep-review-source');plan=src/'planning/new-dataset/2026-10-26';art=Path('/workspace/cadir-newdata-20261026/acquisition')
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sourcefiles=sorted(p for p in src.rglob('*') if p.is_file() and p.name!='.git')
runtime=Path('/workspace/cadir-env');protected=[runtime/n for n in ['activate.sh','sources.json','provenance.md','smoke.R','run-smoke.py','latest-smoke.json']]+sorted(p for pkg in ['APL','CAdir'] for p in (runtime/'sources'/pkg/'R').glob('*.R'))
received=[Path(x['path']) for x in json.loads((plan/'evidence/external_artifacts_sha256.json').read_text())]
files=sourcefiles+protected+received
snapshot={str(p):{'bytes':p.stat().st_size,'sha256':hashfile(p)} for p in files}
if len(sys.argv)>1:
    prior=json.loads((ev/'preservation_before.json').read_text());assert prior==snapshot
    status=subprocess.check_output(['git','-C',str(src),'status','--porcelain']).decode()
    (ev/'preservation_after.json').write_text(json.dumps(snapshot,indent=2));(ev/'preservation_summary.json').write_text(json.dumps({'files_compared':len(snapshot),'source_files':len(sourcefiles),'runtime_source_and_config_files':len(protected),'received_evidence_files':len(received),'all_unchanged':True,'source_status':status,'scope_note':'Runtime audit covers named configs and APL/CAdir R source; no package install or runtime writes executed.'},indent=2));sys.exit()
assert subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD']).decode().strip()=='122fdbf2986f3791917197385f8d07ba0a75fce6'
(ev/'preservation_before.json').write_text(json.dumps(snapshot,indent=2))
manifest=json.loads((plan/'evidence/external_artifacts_sha256.json').read_text());checks=[]
for item in manifest:
    p=Path(item['path']);checks.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashfile(p),'match':p.stat().st_size==item['bytes'] and hashfile(p)==item['sha256']})
assert all(x['match'] for x in checks)
catalog=art/'experimenthub.sqlite3';assert catalog.stat().st_size==10378240 and hashfile(catalog)=='1c0786502f29cf67b892d7452dc03d29af6c1dda82ddd89118a4d79d10a83c4e'
db=sqlite3.connect(catalog.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
resources=[]
for ah_id in ['EH2694','EH2695']:
    r=db.execute('SELECT * FROM resources WHERE ah_id=?',(ah_id,)).fetchone();assert r is not None
    paths=db.execute('SELECT * FROM rdatapaths WHERE resource_id=?',(r['id'],)).fetchall();prefix=db.execute('SELECT location_prefix FROM location_prefixes WHERE id=?',(r['location_prefix_id'],)).fetchone()[0]
    resources.append({'ah_id':ah_id,'resource_id':r['id'],'dataprovider':r['dataprovider'],'location_prefix':prefix,'paths':[dict(p) for p in paths]})
for i,(fetch,name,klass) in enumerate([(2710,'counts','dgCMatrix'),(2711,'coldata','DataFrame')]):
    p=resources[i]['paths'];assert len(p)==1 and p[0]['id']==fetch and p[0]['rdatapath']==f'scRNAseq/nestorowa-hsc/2.0.0/{name}.rds' and p[0]['rdataclass']==klass
    resources[i]['storage_url']=resources[i]['location_prefix']+p[0]['rdatapath']
redirect=json.loads((art/'hub-correct-redirect.json').read_text());head=json.loads((art/'correct-mghp-head.json').read_text());geo=json.loads((art/'geo-network-attempt.txt.gz.json').read_text());wrong=json.loads((art/'hub-redirect-probe.json').read_text())
assert redirect['status']==302 and redirect['headers']['location']==resources[0]['storage_url'] and redirect['url'].endswith('/2710')
assert head['url']==resources[0]['storage_url'] and 'Tunnel connection failed: 403' in head['error'] and 'Tunnel connection failed: 403' in geo['error']
assert wrong['url'].endswith('/2694') and '/lun-spikein/' in wrong['headers']['location']
policy=json.loads(Path('/etc/codex/network-policy.json').read_text());allowed=[x['host'] for x in policy['http_network_policy']['egress_rules']]
assert 'mghp.osn.xsede.org' not in allowed and 'ftp.ncbi.nlm.nih.gov' not in allowed
result={'catalog_bytes':catalog.stat().st_size,'catalog_sha256':hashfile(catalog),'open_mode':'SQLite URI mode=ro','mapping':resources,'validated_external_receipts':checks,'correct_redirect':redirect,'correct_storage_head':head,'geo_original_request':geo,'initial_wrong_fetch_redirect':wrong,'required_extra_hosts':['mghp.osn.xsede.org','ftp.ncbi.nlm.nih.gov'],'hosts_absent_from_current_policy':True,'no_network_request_performed_by_reviewer':True,'actual_counts_or_coldata_downloaded':False}
(ev/'independent_catalog_network.json').write_text(json.dumps(result,indent=2))
changed=[p for p in subprocess.check_output(['git','-C',str(src),'diff','--name-only','-z','9d473b441058c45b2563c2ebe94ae99dda1f5209']).decode().split('\0') if p];assert all(p.startswith('cases/nestorowa_hsc/') or p.startswith('planning/new-dataset/2026-10-26/') for p in changed)
(ev/'increment_scope.json').write_text(json.dumps({'changed_paths':changed,'all_stage1_files_unchanged_vs_9d473b4':True,'largest_tracked_file_bytes':max(p.stat().st_size for p in sourcefiles),'tracked_RDS_files':subprocess.check_output(['git','-C',str(src),'ls-files','*.rds','*.RDS']).decode().splitlines()},indent=2))
print(json.dumps({'catalog_mapping':resources,'external_manifest_matches':len(checks),'protected_files':len(snapshot)},indent=2))
