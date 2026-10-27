#!/usr/bin/env python3
"""Final source re-verification after the scoped gene-subset-contract repair."""
import ast,csv,hashlib,json,pathlib,subprocess,sys
review=pathlib.Path('/workspace/hsc-design-independent-review/reviews/hsc-design-20261026')
root=pathlib.Path('/workspace/hsc-fair-experiment');base=root/'cases/nestorowa_hsc/fair-experiment'
commit=sys.argv[1];out=review/'revised-lock-check';out.mkdir(exist_ok=False)
rows=[]
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(name,p,predicate):
 rows.append(dict(check=name,path=str(p),pass_=bool(predicate)))
 if not predicate:raise AssertionError((name,p))
def blob(path):return subprocess.check_output(['git','-C',str(root),'show',commit+':'+str(path)])
result={'status':'FAILED','source_commit':commit,'forbidden_algorithms_called':False}
try:
 stable={'locks/data-input-lock.json':'ac46362a024950ebeda08795b5f64857d3487435328c273e1dc2b8107feee6c1','design/scientific-config.json':'b1e30c8d292b289095bcc1b5159f82b4568f16ca4b07207e039795e15219a969','evidence/environment-probe-03/environment-signature.rds':'e2e6b0b03a1952068eaa8c4ccec469671d947bb4553926b326d4f1086b0b2fc5','locks/runtime-library-lock.json':'37bd6195b8605db9572addc842431a723b1980deb4a6cc96c8e23fee5aac5d52'}
 for rel,h in stable.items():check('scientific_input_unchanged',rel,sha(base/rel)==h)
 manifest=json.loads((base/'locks/source-manifest.json').read_text())
 for e in manifest['files']:
  p=root/e['path'];h=sha(p)
  check('source_content',e['path'],h==e['sha256'] and p.stat().st_size==e['bytes'])
  check('source_exact_commit',e['path'],hashlib.sha256(blob(e['path'])).hexdigest()==h)
 for rel in ['locks/source-manifest.json',*stable]:
  p=base/rel;check('lock_exact_commit',p,hashlib.sha256(blob(p.relative_to(root))).hexdigest()==sha(p))
 lock=json.loads((base/'locks/data-input-lock.json').read_text())
 for e in lock['files']:
  p=pathlib.Path(e['path']);check('data_content_unchanged',p,p.stat().st_size==e['bytes']and sha(p)==e['sha256'])
 rt=json.loads((base/'locks/runtime-library-lock.json').read_text());lib=pathlib.Path(rt['library_root'])
 actual={str(p.relative_to(lib))for p in lib.rglob('*')if p.is_file()and(p.suffix in ['.so','.rdb','.rdx']or p.name in ['DESCRIPTION','NAMESPACE'])}
 check('runtime_file_set',lib,actual=={e['path']for e in rt['files']})
 for e in rt['files']:
  p=lib/e['path'];check('runtime_byte_content',p,sha(p)==e['sha256']and p.stat().st_size==e['bytes'])
 for p in (base/'scripts').glob('*.py'):ast.parse(p.read_text());check('python_parse',p,True)
 for name,args in [('absent',[]),('false-template',['--admission',str(base/'design/admission-template.json')])]:
  r=subprocess.run(['python3',str(base/'scripts/run_experiment.py'),'--check-only',*args],capture_output=True,text=True)
  (out/f'gate-{name}.log').write_text(r.stdout+r.stderr)
  check('host_gate_before_algorithm',name,r.returncode==2 and 'BLOCKED:'in r.stderr)
 result.update(status='PASS_REVISED_EXACT_SOURCE_AND_UNCHANGED_SCIENTIFIC_LOCKS',source_manifest_sha256=sha(base/'locks/source-manifest.json'),source_files=len(manifest['files']),protected_data_files=len(lock['files']),runtime_files=len(rt['files']))
except Exception as e:result['error']=repr(e)
with open(out/'differences.tsv','w')as f:
 w=csv.DictWriter(f,fieldnames=['check','path','pass_'],delimiter='\t');w.writeheader();w.writerows(rows)
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if result['status']=='FAILED':raise SystemExit(1)
