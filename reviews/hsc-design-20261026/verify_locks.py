#!/usr/bin/env python3
"""Independent host content audit, syntax checks and non-executing gate negatives."""
import ast,csv,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path('/workspace/hsc-design-independent-review')
ORIGINAL=pathlib.Path('/workspace/hsc-fair-experiment')
BASE=ROOT/'cases/nestorowa_hsc/fair-experiment'
OUT=ROOT/'reviews/hsc-design-20261026'
COMMIT='fc5ce7b4911a3ee42bca9099dec8700fd974d23b'
rows=[]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(kind,path,passed,detail=''):
 rows.append(dict(kind=kind,path=str(path),pass_=passed,detail=detail))
 if not passed:raise AssertionError((kind,path,detail))
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def j(p):return json.loads(p.read_text())
expected={
 'locks/data-input-lock.json':'ac46362a024950ebeda08795b5f64857d3487435328c273e1dc2b8107feee6c1',
 'locks/source-manifest.json':'f573a94a569782fbe5557e2ca319980f22e4434bc81dfb9378bdc90505375cf9',
 'design/scientific-config.json':'b1e30c8d292b289095bcc1b5159f82b4568f16ca4b07207e039795e15219a969',
 'evidence/environment-probe-03/environment-signature.rds':'e2e6b0b03a1952068eaa8c4ccec469671d947bb4553926b326d4f1086b0b2fc5',
 'locks/runtime-library-lock.json':'37bd6195b8605db9572addc842431a723b1980deb4a6cc96c8e23fee5aac5d52'}
try:
 for rel,expected_sha in expected.items():
  check('fixed_binding',rel,sha(BASE/rel)==expected_sha)
 check('external_authority_lock','data-input-lock.json',sha(pathlib.Path('/workspace/hsc-fair-experiment-data-20261026/data-input-lock.json'))==expected['locks/data-input-lock.json'])
 manifest=j(BASE/'locks/source-manifest.json')
 for e in manifest['files']:
  p=ROOT/e['path'];actual=sha(p)
  check('review_source',p,actual==e['sha256'] and p.stat().st_size==e['bytes'])
  check('original_source',e['path'],sha(ORIGINAL/e['path'])==actual)
  check('fixed_git_blob',e['path'],hashlib.sha256(git('show',COMMIT+':'+e['path'])).hexdigest()==actual)
 lock=j(BASE/'locks/data-input-lock.json')
 for e in lock['files']:
  p=pathlib.Path(e['path']);check('protected_data',p,p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
 runtime=j(BASE/'locks/runtime-library-lock.json');lib=pathlib.Path(runtime['library_root'])
 paths={str(p.relative_to(lib)) for p in lib.rglob('*') if p.is_file() and (p.suffix in ['.so','.rdb','.rdx'] or p.name in ['DESCRIPTION','NAMESPACE'])}
 check('runtime_file_set',lib,paths=={e['path'] for e in runtime['files']})
 for e in runtime['files']:
  p=lib/e['path'];check('runtime_file',e['path'],p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
 authority=j(pathlib.Path('/workspace/hsc-fair-experiment-handoff-20261026/authority.json'))
 check('management_authority','authority.json',authority['control_commit']=='574c71e357f4b3bb714a3d4ddceb28593b0afd27')
 for e in authority['documents']:
  p=pathlib.Path('/workspace/hsc-fair-experiment-handoff-20261026')/pathlib.Path(e['path']).name
  check('management_document',p,sha(p)==e['sha256'])
 for p in sorted((BASE/'scripts').glob('*.py')):
  ast.parse(p.read_text());check('python_parse',p,True)
 for name in ['container.sh','sample_rss.sh']:
  p=BASE/'scripts'/name;r=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True);check('shell_parse',p,r.returncode==0,r.stderr)
 for name,gate in [('missing',[]),('false-template',['--admission',str(BASE/'design/admission-template.json')])]:
  r=subprocess.run(['python3',str(BASE/'scripts/run_experiment.py'),'--check-only',*gate],capture_output=True,text=True)
  (OUT/f'host-gate-{name}.log').write_text(r.stdout+r.stderr)
  check('gate_rejection',name,r.returncode==2 and 'BLOCKED:' in r.stderr,r.stderr.strip())
 cfg=j(BASE/'design/scientific-config.json')
 check('prespecified_seeds','config',cfg['seeds']==[2358,101,202,303,404])
 # Record the committed config history; timestamp alone does not prove blindness.
 hist=git('log','--format=%H %aI %s','--',str((BASE/'design/scientific-config.json').relative_to(ROOT))).decode()
 (OUT/'scientific-config-history.txt').write_text(hist)
 result={'status':'PASS_LOCK_CONTENT_SYNTAX_AND_HOST_GATE_NEGATIVES','source_commit':COMMIT,'source_files':len(manifest['files']),'protected_data_files':len(lock['files']),'runtime_files':len(runtime['files']),'runtime_bytes':sum(e['bytes'] for e in runtime['files']),'forbidden_algorithms_called':False}
except Exception as e:
 result={'status':'FAILED','error':repr(e),'forbidden_algorithms_called':False}
with open(OUT/'lock-differences.tsv','w') as f:
 w=csv.DictWriter(f,fieldnames=['kind','path','pass_','detail'],delimiter='\t');w.writeheader();w.writerows(rows)
(OUT/'host-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
if result['status']=='FAILED':raise SystemExit(1)
