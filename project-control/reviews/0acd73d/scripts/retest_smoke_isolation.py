from pathlib import Path
import json,hashlib,subprocess,os
root=Path('/workspace/cadir-stage1-retest'); source=Path('/workspace/cadir-stage1-final-review-source');base=source/'cases/tabula_muris_limb';runtime=Path('/workspace/cadir-env');dst=root/'final-smoke-entry'
def snapshot():
    paths=[runtime/'runs',runtime/'latest-smoke.json']+sorted((runtime/'runs').rglob('*'))
    result={}
    for p in paths:
        s=p.stat(); result[str(p.relative_to(runtime))]={'type':'dir' if p.is_dir() else 'file','mtime_ns':s.st_mtime_ns,'bytes':s.st_size}
        if p.is_file():result[str(p.relative_to(runtime))]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return result
assert not dst.exists()
sha=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip();assert sha=='0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b'
tracked=subprocess.check_output(['git','-C',str(source),'ls-files','-z']).decode().split('\0');source_before={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in tracked if p}
before=snapshot();(root/'evidence/final_smoke_shared_before.json').write_text(json.dumps(before,indent=2))
cmd=['python',str(base/'scripts/check_environment.py'),'--output-root',str(dst)]
with (root/'evidence/final_smoke_check.log').open('w') as log:p=subprocess.run(cmd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=log,stderr=subprocess.STDOUT)
after=snapshot();(root/'evidence/final_smoke_shared_after.json').write_text(json.dumps(after,indent=2));state=json.loads((dst/'latest-environment.json').read_text());smoke=Path(state['synthetic_smoke_evidence']['run_directory']);assert smoke.is_relative_to(dst)
required=['status.txt','sessionInfo.txt','installed-packages.csv','synthetic-sce.rds','smoke-results.rds','ca-cadir-smoke.png','console.log','resources.json']
artifacts={n:{'bytes':(smoke/n).stat().st_size,'sha256':hashlib.sha256((smoke/n).read_bytes()).hexdigest()} for n in required}
source_changed=[p for p,h in source_before.items() if hashlib.sha256((source/p).read_bytes()).hexdigest()!=h]
result={'source_sha':sha,'command':cmd,'output_root_absent_before':True,'exit_code':p.returncode,'environment_status':state['status'],'smoke_run_directory':str(smoke),'smoke_status':(smoke/'status.txt').read_text(),'shared_entry_count':len(before),'shared_file_count':sum(v['type']=='file' for v in before.values()),'shared_entries_bytes_hash_and_mtime_identical':before==after,'source_tracked_files':len(source_before),'source_changed':source_changed,'git_status_after':subprocess.check_output(['git','-C',str(source),'status','--porcelain']).decode(),'required_artifacts':artifacts}
(root/'evidence/final_smoke_isolation.json').write_text(json.dumps(result,indent=2))
assert p.returncode==0 and state['status']=='PASS' and before==after and not source_changed and all(v['bytes']>0 for v in artifacts.values())
print(json.dumps(result,indent=2))
