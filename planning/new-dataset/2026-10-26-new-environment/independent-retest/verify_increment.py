#!/usr/bin/env python3
"""Read-only archival and conclusion increment verification; no network or algorithms."""
from pathlib import Path
import datetime,hashlib,json,subprocess
repo=Path('/workspace/cadir-validation-20261026/repo')
source=Path('/workspace/cadir-validation-review-e987d4c-20261026')
out=Path(__file__).resolve().parent
base='e987d4c10c65e54977d44790a13c3be5da2518f8'
target='731b6c6f8f8866b50aff21184ff246ace63cc93c'
prefix='planning/new-dataset/2026-10-26-new-environment/'
root=repo/prefix
archive=root/'independent-review'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def sha(b):return hashlib.sha256(b).hexdigest()
def tree(ref):
    records=git('ls-tree','-r','-z',ref).split(b'\0')
    return {x.split(b'\t',1)[1].decode():x.split(b'\t',1)[0].decode() for x in records if x}
def files(path):return {str(p.relative_to(path)):p for p in path.rglob('*') if p.is_file()}
checks=[]
def check(name,value,details=None):checks.append({'check':name,'pass':bool(value),'details':details})
check('exact_target',git('rev-parse','HEAD').decode().strip()==target)
check('clean_worktree_before',not git('status','--porcelain=v1','--untracked-files=all').strip())
old,new=tree(base),tree(target)
old_changed=[p for p in old if new.get(p)!=old[p]]
check('every_original_file_same_git_blob',not old_changed,{'original_file_count':len(old),'changed':old_changed})
added=set(new)-set(old)
expected={prefix+'independent-review/'+p for p in files(source)}|{prefix+p for p in ['evidence/environment-diagnostics-index.json','阶段结论.md','final_evidence_index.json']}
check('only_expected_archive_and_three_new_files',added==expected,{'added_count':len(added),'unexpected':sorted(added-expected),'missing':sorted(expected-added)})
sourcefiles,archivefiles=files(source),files(archive)
check('archive_path_set_exact',sourcefiles.keys()==archivefiles.keys(),len(sourcefiles))
rows=[]
for name,p in sorted(sourcefiles.items()):
    src=p.read_bytes(); dst=archivefiles[name].read_bytes()
    committed=git('show',target+':'+prefix+'independent-review/'+name)
    rows.append({'path':name,'bytes':len(src),'sha256':sha(src),'archive_sha256':sha(dst),'pass':src==dst==committed})
check('all_51_archived_files_byte_exact',len(rows)==51 and all(x['pass'] for x in rows))
index=json.loads((root/'final_evidence_index.json').read_text())
indexpaths={x['path'] for x in index}
actual=set(files(root))-{'final_evidence_index.json'}
check('final_index_complete_except_self',indexpaths==actual and len(indexpaths)==len(index),{'entries':len(index),'expected':len(actual)})
index_rows=[]
for row in index:
    b=(root/row['path']).read_bytes()
    index_rows.append({'path':row['path'],'bytes':len(b),'sha256':sha(b),'pass':len(b)==row['bytes'] and sha(b)==row['sha256']})
check('every_final_index_size_and_sha',all(x['pass'] for x in index_rows))
diag=json.loads((root/'evidence/environment-diagnostics-index.json').read_text())
check('diagnostics_metadata_only',diag['history_status']=='not_found' and diag['legacy_snapshot_available'] is False and diag['records']==[])
conclusion=(root/'阶段结论.md').read_text()
required=['真实数据审计、正式设计与正式实验继续 BLOCKED','restricted/**unknown**','缺诊断日志不代表健康',
          '本轮没有需要返修的实质实施问题','S1覆盖、真实QC/标签/输入锁、正式实现与独立设计',
          '不要求重复添加相同域名','独立设计门槛关闭前继续禁止正式实验']
check('conclusion_retains_scope_and_blockers',all(x in conclusion for x in required),required)
check('conclusion_report_sha_exact','b7fd50ec3c84d54be74207c72299a1adc24d1a899cf3d6cdcc5100195154de65' in conclusion
      and sha((archive/'独立评审报告.md').read_bytes())=='b7fd50ec3c84d54be74207c72299a1adc24d1a899cf3d6cdcc5100195154de65')
diffcheck=subprocess.run(['git','-C',str(repo),'diff','--check',base,target],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
check('git_diff_check_clean',diffcheck.returncode==0 and not diffcheck.stdout and not diffcheck.stderr)
check('clean_worktree_after',not git('status','--porcelain=v1','--untracked-files=all').strip())
result={'reviewed_sha':target,'previous_reviewed_sha':base,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope':'archive/conclusion/index increment only','check_count':len(checks),'checks':checks,
        'failed_checks':[x['check'] for x in checks if not x['pass']], 'archive_comparison':rows,'final_index_comparison':index_rows,
        'manual_conclusion_review':'No expanded scientific approval. unknown retained. Real data/formal design/formal experiments BLOCKED. Diagnostics metadata interpreted as no retained logs, not proof of health.',
        'network_requests':0,'algorithms_run':False,'original_40_checks_repeated':False,'modified_repo':False}
(out/'increment_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed_checks':result['failed_checks'],'original_files':len(old),'archived_files':len(rows),'final_index_entries':len(index)},ensure_ascii=False,indent=2))
raise SystemExit(1 if result['failed_checks'] else 0)
