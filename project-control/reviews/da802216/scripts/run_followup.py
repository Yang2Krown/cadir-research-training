#!/usr/bin/env python3
"""Reviewer-authored runner. Coordinator only executes this unchanged file."""
import datetime, hashlib, json, os, pathlib, subprocess, time
ROOT=pathlib.Path('/workspace/hsc-input-independent-review')
BASE=ROOT/'project-control/reviews/b7ee233-real-input-20261026'
DATA=pathlib.Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026')
IMAGE='sha256:baf71525f92cb9813846199dce68c6190c23d4774b025a7baec85e9688b642c7'
TAG='cadir-r-ver:4.4.1-bioc3.19'
OUT=BASE/'execution-attempt-02'
OUT.mkdir(exist_ok=False)
env=os.environ.copy()
for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']: env.pop(key,None)
D=['docker','--host=unix:///var/run/docker.sock']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def snapshot():
 return {'inputs':{n:{'bytes':(DATA/n).stat().st_size,'sha256':sha(DATA/n)} for n in ['counts.rds','coldata.rds','GSE81682_HTSeq_counts.txt.gz']},'sources':{str(p.relative_to(ROOT)):sha(p) for p in list((ROOT/'cases/nestorowa_hsc/scripts').glob('*'))+list((BASE/'scripts').glob('*')) if p.is_file()}}
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
write('before.json',snapshot())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head=='b7ee2335dc25ffab3a60d1feab44272d6d5a45cb',head
for p in (ROOT/'cases/nestorowa_hsc/scripts').glob('*'):
 if p.is_file(): assert subprocess.check_output(['git','show',head+':'+str(p.relative_to(ROOT))],cwd=ROOT)==p.read_bytes(),str(p)
image_id=subprocess.check_output(D+['image','inspect','--format','{{.Id}}',TAG],env=env,text=True).strip()
assert image_id==IMAGE,image_id
write('provenance.json',{'reviewer':'GPT-6.1 Sol / High','privileged_command_executor':'coordinator; reviewer-authored runner executed unchanged','reviewed_commit':head,'image_id':image_id,'image_tag':TAG,'formal_execution_permitted':False,'environment_status':'reviewer tool wait interrupted without output; coordinator preflight records supplied separately; actual offline image execution below is primary runtime evidence'})
records=[]
def run(name,cmd):
 start=time.time();record={'stage':name,'command':cmd,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with (OUT/(name+'.console.log')).open('x') as log:
  try: record['exit_code']=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900).returncode
  except subprocess.TimeoutExpired: record.update(exit_code=124,error='900 second timeout')
 record['elapsed_seconds']=time.time()-start;records.append(record);write('commands.json',records);print(json.dumps(record),flush=True)
 return record['exit_code']
def container(name,script,inputs):
 dest=OUT/name;dest.mkdir()
 cname='hsc-independent-'+name+'-20261026'
 cmd=D+['run','--rm','--name',cname,'--network','none','--read-only','--tmpfs','/tmp','--cpus','2','--memory','4g','--user',f'{os.getuid()}:{os.getgid()}','-e','R_LIBS_USER=/library','--workdir','/repo']
 for source,target in [(ROOT,'/repo'),(pathlib.Path('/workspace/.cadir-r-lib/4.4'),'/library')]+[(DATA/n,'/inputs/'+n) for n in inputs]:cmd+=['--mount',f'type=bind,src={source},dst={target},readonly']
 cmd+=['--mount',f'type=bind,src={dest},dst=/out',IMAGE,'Rscript','--vanilla','/repo/'+str((BASE/'scripts'/script).relative_to(ROOT)),'/out/results']
 try:return run(name,cmd)
 finally:subprocess.run(D+['rm','-f',cname],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
container('real-metadata-negatives','real_metadata_negatives_v2.R',['coldata.rds'])
wrapper=ROOT/'cases/nestorowa_hsc/scripts/run_input_audit.py'
manifest=ROOT/'planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json'
for mode in ['metadata-only','full']:
 assert subprocess.check_output(D+['image','inspect','--format','{{.Id}}',TAG],env=env,text=True).strip()==IMAGE
 cmd=['python3',str(wrapper),mode,'--metadata',str(DATA/'coldata.rds'),'--manifest',str(manifest),'--output',str(OUT/('original-'+mode))]
 if mode=='full':cmd+=['--counts',str(DATA/'counts.rds'),'--geo',str(DATA/'GSE81682_HTSeq_counts.txt.gz')]
 run('launcher-original-'+mode,cmd)
assert subprocess.check_output(D+['image','inspect','--format','{{.Id}}',TAG],env=env,text=True).strip()==IMAGE
write('after.json',snapshot())
write('runner_status.json',{'all_commands_exit_zero':all(x['exit_code']==0 for x in records),'formal_execution_permitted':False})
raise SystemExit(0 if all(x['exit_code']==0 for x in records) else 1)
