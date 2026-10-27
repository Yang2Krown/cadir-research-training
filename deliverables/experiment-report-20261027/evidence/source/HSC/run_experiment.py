#!/usr/bin/env python3
"""Admission-gated sequential fresh-process runner. Stage 1 never invokes it."""
import argparse, hashlib, json, os, pathlib, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=ROOT/'cases/nestorowa_hsc/fair-experiment'
IMAGE='sha256:baf71525f92cb9813846199dce68c6190c23d4774b025a7baec85e9688b642c7'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text())
def git(*a):return subprocess.check_output(['git','-C',str(ROOT),*a],text=True).strip()
def validate(admission_path):
 if not admission_path or not pathlib.Path(admission_path).is_file():raise ValueError('BLOCKED: independent admission is absent')
 gate=read(admission_path)
 required={'formal_execution_permitted':True,'decision':'PASS_LIMITED_FORMAL_EXECUTION','reviewer_participated_in_implementation':False,'reviewer_model':'gpt-6.1-sol','reviewer_reasoning_effort':'high'}
 for k,v in required.items():
  if gate.get(k)!=v:raise ValueError(f'BLOCKED: invalid independent admission field {k}')
 if not gate.get('reviewer_agent_id') or not gate.get('review_report') or gate.get('C04_decision') not in ['ACCEPTED_LIMITED_NOVELTY_SCOPE','VERIFIED_NEW_WITH_FIRST_SOURCE']:raise ValueError('BLOCKED: reviewer identity/report/C04 decision missing')
 manifest=BASE/'locks/source-manifest.json';lock=BASE/'locks/data-input-lock.json';config=BASE/'design/scientific-config.json'
 for p,k in [(manifest,'source_manifest_sha256'),(lock,'data_lock_sha256'),(config,'scientific_config_sha256')]:
  if sha(p)!=gate.get(k):raise ValueError(f'BLOCKED: {k} differs')
 source=read(manifest)
 commit=gate['source_commit'];git('cat-file','-e',commit+'^{commit}')
 for e in source['files']:
  p=ROOT/e['path']
  if sha(p)!=e['sha256'] or p.stat().st_size!=e['bytes']:raise ValueError('BLOCKED: source changed '+str(p))
  committed=subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+e['path']])
  if hashlib.sha256(committed).hexdigest()!=e['sha256']:raise ValueError('BLOCKED: reviewed commit/source mismatch '+e['path'])
 data=read(lock)
 for e in data['files']:
  p=pathlib.Path(e['path'])
  if not p.is_file() or p.stat().st_size!=e['bytes'] or sha(p)!=e['sha256']:raise ValueError('BLOCKED: input/lock changed '+str(p))
 env=pathlib.Path(data['environment_signature_path'])
 if sha(env)!=gate.get('environment_signature_sha256'):raise ValueError('BLOCKED: environment signature binding differs')
 library=read(data['runtime_library_lock_path'])
 libroot=pathlib.Path(library['library_root'])
 actual_paths={str(p.relative_to(libroot)) for p in libroot.rglob('*') if p.is_file() and (p.suffix in ['.so','.rdb','.rdx'] or p.name in ['DESCRIPTION','NAMESPACE'])}
 if actual_paths!={e['path'] for e in library['files']}:raise ValueError('BLOCKED: external R runtime file set differs')
 for e in library['files']:
  p=libroot/e['path']
  if not p.is_file() or p.stat().st_size!=e['bytes'] or sha(p)!=e['sha256']:raise ValueError('BLOCKED: external R library changed '+str(p))
 cfg=read(config)
 if cfg['seeds']!=[2358,101,202,303,404]:raise ValueError('BLOCKED: frozen seed list differs')
 return gate,data,cfg

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--admission');ap.add_argument('--output-root');ap.add_argument('--check-only',action='store_true');a=ap.parse_args()
 try:g,d,c=validate(a.admission)
 except (ValueError,KeyError,FileNotFoundError,subprocess.CalledProcessError) as e:ap.exit(2,str(e)+'\n')
 if a.check_only:print('INDEPENDENT_ADMISSION_AND_EXACT_BINDINGS_VALID');return
 if not a.output_root:ap.error('--output-root required')
 out=pathlib.Path(a.output_root).resolve()
 allowed=pathlib.Path('/workspace/hsc-fair-experiment-data-20261026/formal')
 if not out.is_relative_to(allowed) or out==allowed:ap.error('output must be a new child of '+str(allowed))
 out.mkdir(parents=True,exist_ok=False)
 observed=subprocess.check_output(['docker','--host=unix:///var/run/docker.sock','image','inspect','--format={{.Id}}',IMAGE],text=True).strip()
 if observed!=IMAGE:raise ValueError('Actual Docker image differs')
 (out/'admission-used.json').write_text(json.dumps(g,indent=2)+'\n')
 receipts=[]
 for seed in c['seeds']:
  for method in ['cadir','pca_snn_louvain']:
   p=out/f'{method}-seed-{seed}-attempt-01';p.mkdir()
   # Fresh R process per method/seed; common input loaded before core timer.
   cmd=[str(BASE/'scripts/container.sh'),str(p),'Rscript',str(BASE/'scripts/formal_run.R'),str(BASE/'scripts/common.R'),str(pathlib.Path(a.admission).resolve()),str(BASE/'locks/source-manifest.json'),str(BASE/'locks/data-input-lock.json'),str(BASE/'design/scientific-config.json'),method,str(seed),str(p)]
   print(json.dumps({'event':'METHOD_SEED_START','method':method,'seed':seed,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'output':str(p)}),flush=True)
   t=time.monotonic()
   with open(p/'console.log','wb') as log:
    container_name=f'hsc-{method}-{seed}-{os.getpid()}'
    env=os.environ.copy();env['HSC_CONTAINER_NAME']=container_name
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env)
    # Host monitor enforces the declared core timeout; sampler measures RSS only.
    core_observed=None;timed_out=False
    while proc.poll() is None:
     now=time.monotonic()
     if (p/'core-start.json').exists() and core_observed is None:core_observed=now
     core_active=(p/'core.running').exists()
     if (core_active and core_observed is not None and now-core_observed>c['resources']['core_timeout_seconds']) or now-t>c['resources']['core_timeout_seconds']+600:
      subprocess.run(['docker','--host=unix:///var/run/docker.sock','stop','--time','5',container_name],capture_output=True)
      proc.kill();timed_out=True;break
     time.sleep(.05)
    rc=124 if timed_out else proc.wait()
   if rc==0:
    files=[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(p.iterdir()) if f.is_file()]
    (p/'core-artifacts-sha256.json').write_text(json.dumps({'files':files},indent=2)+'\n')
   print(json.dumps({'event':'METHOD_SEED_EXIT','method':method,'seed':seed,'exit_code':rc,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
   rec={'method':method,'seed':seed,'exit_code':rc,'wall_seconds_process_including_load_exports':time.monotonic()-t,'attempt_directory':str(p),'success':rc==0}
   receipts.append(rec);(out/'attempt-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
   if rc==0 and method=='cadir':
    diag=p/'diagnostics';diag.mkdir()
    diagcmd=[str(BASE/'scripts/container.sh'),str(diag),'Rscript',str(BASE/'scripts/rank_diagnostics.R'),str(BASE/'scripts/common.R'),str(pathlib.Path(a.admission).resolve()),str(BASE/'locks/source-manifest.json'),str(BASE/'locks/data-input-lock.json'),str(BASE/'design/scientific-config.json'),str(seed),str(p),str(diag)]
    with open(diag/'console.log','wb') as log:
     diag_name=f'hsc-diag-{seed}-{os.getpid()}';diag_env=os.environ.copy();diag_env['HSC_CONTAINER_NAME']=diag_name
     dp=subprocess.Popen(diagcmd,stdout=log,stderr=subprocess.STDOUT,env=diag_env)
     try:drc=dp.wait(timeout=c['resources']['core_timeout_seconds']+600)
     except subprocess.TimeoutExpired:
      subprocess.run(['docker','--host=unix:///var/run/docker.sock','stop','--time','5',diag_name],capture_output=True);dp.kill();drc=124
    print(json.dumps({'event':'DIAGNOSTIC_EXIT','seed':seed,'exit_code':drc,'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}),flush=True)
    rec['diagnostic_exit_code']=drc;(out/'attempt-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
 # Summary consumes every declared seed; absent/failed runs retain denominator 5.
 subprocess.run(['python3',str(BASE/'scripts/summarize_results.py'),str(out)],check=True)
if __name__=='__main__':main()
