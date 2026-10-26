#!/usr/bin/env python3
"""Run input preparation in the existing offline R container; never installs packages."""
import argparse, datetime, json, os, pathlib, subprocess, time
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('mode',choices=['metadata-only','full'])
p.add_argument('--metadata',type=pathlib.Path,required=True)
p.add_argument('--counts',type=pathlib.Path)
p.add_argument('--geo',type=pathlib.Path)
p.add_argument('--manifest',type=pathlib.Path,required=True)
p.add_argument('--output',type=pathlib.Path,required=True)
a=p.parse_args()
if a.mode=='metadata-only' and (a.counts or a.geo): p.error('metadata-only must not accept counts/GEO paths')
if a.mode=='full' and not (a.counts and a.geo): p.error('full requires counts and GEO paths')
repo=pathlib.Path(__file__).resolve().parents[3]
out=a.output.resolve();out.parent.mkdir(parents=True,exist_ok=True)
log=out.with_suffix('.console.log');receipt=out.with_suffix('.execution.json')
if any(x.exists() for x in [out,log,receipt]): p.error('Attempt path exists; use a fresh path')
image='cadir-r-ver:4.4.1-bioc3.19'
env=os.environ.copy()
for name in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']: env.pop(name,None)
base=['docker','--host=unix:///var/run/docker.sock']
image_info=json.loads(subprocess.check_output(base+['image','inspect','--format','{{json .Id}}',image],env=env,text=True))
cmd=base+['run','--rm','--network','none','--read-only','--tmpfs','/tmp','--cpus','2','--memory','4g',
    '--user',f'{os.getuid()}:{os.getgid()}','--workdir','/repo','-e','R_LIBS_USER=/library']
mounts=[(repo,'/repo'),(pathlib.Path('/workspace/.cadir-r-lib/4.4'),'/library'),
    (a.metadata.resolve(),'/inputs/coldata.rds'),(a.manifest.resolve(),'/inputs/acquisition_manifest.json')]
if a.mode=='full':mounts += [(a.counts.resolve(),'/inputs/counts.rds'),(a.geo.resolve(),'/inputs/GSE81682_HTSeq_counts.txt.gz')]
for src,dst in mounts:cmd+=['--mount',f'type=bind,src={src},dst={dst},readonly']
cmd+=['--mount',f'type=bind,src={out.parent},dst=/out',image,'Rscript','--vanilla',
    '/repo/cases/nestorowa_hsc/scripts/audit_inputs.R',a.mode]
if a.mode=='full':cmd+=['/inputs/counts.rds']
cmd+=['/inputs/coldata.rds']
if a.mode=='full':cmd+=['/inputs/GSE81682_HTSeq_counts.txt.gz']
cmd+=['/inputs/acquisition_manifest.json','/out/'+out.name]
record={'started_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'mode':a.mode,'image':image,'image_id':image_info,'command':cmd,
    'network':'none','input_mounts_readonly':True,'formal_execution_permitted':False}
start=time.monotonic()
with log.open('x') as stream:
    try:r=subprocess.run(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=900);record['exit_code']=r.returncode
    except subprocess.TimeoutExpired:record.update(exit_code=124,error='900-second audit timeout; see retained log')
record['elapsed_seconds']=time.monotonic()-start
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'output':str(out),'receipt':str(receipt),'exit_code':record['exit_code']}))
raise SystemExit(record['exit_code'])
