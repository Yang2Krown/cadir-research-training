#!/usr/bin/env python3
"""Package only small reviewable artifacts, with a hard 24 MiB limit."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import zipfile

review=Path(__file__).resolve().parents[1]
case=review.parents[1]
repo=case.parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=Path('/workspace/cadir-deliverables/tabula_muris_limb_acceptance_20261025.zip'))
args=parser.parse_args()
archive=args.output
if archive.exists():raise SystemExit('Archive exists; choose another --output to preserve it.')
archive.parent.mkdir(parents=True,exist_ok=True)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

baseline=json.loads((review/'freeze/baseline_manifest.json').read_text())
for record in baseline['files']:
    path=Path(record['path'])
    assert path.is_file() and path.stat().st_size==record['bytes'] and digest(path)==record['sha256'],record['path']
preservation=json.loads((review/'freeze/baseline_preservation_check.json').read_text())
assert preservation['status']=='PASS' and preservation['baseline_files_changed']==[]
external=[dict(x,reason='Raw expression input or raw run artifact retained at its original path; selected small logs are separately copied into the bundle.')
          for x in baseline['files'] if x['relative_to_repo'].startswith('data/') or '/runs/' in x['relative_to_repo']]
(review/'report/external_artifacts.json').write_text(json.dumps({
 'input_and_large_intermediates_are_not_packaged':True,'artifacts':external},ensure_ascii=False,indent=2)+'\n')
# Historical failure and success logs are copied, not moved. No run RDS, expression
# matrices or the first run's 15 MiB expanded parameter dump are included.
history=review/'freeze/history_logs'
history.mkdir(exist_ok=True)
history_summary=[]
for run in sorted((case/'runs').iterdir()):
    if not run.is_dir():continue
    copied=[]
    for path in sorted(run.iterdir()):
        if not path.is_file() or path.stat().st_size>256*1024:continue
        if path.suffix in ['.log','.json'] or path.name in ['sessionInfo.txt','status.txt','installed_packages.tsv','installed-packages.csv','required_version_check.tsv'] or path.name.endswith('_rss_samples_KiB.txt'):
            destination=history/run.name/path.name
            destination.parent.mkdir(exist_ok=True)
            shutil.copy2(path,destination)
            copied.append(path.name)
    history_summary.append({'run':run.name,'original_path':str(run),'copied_key_logs':copied})
(history/'index.json').write_text(json.dumps(history_summary,indent=2)+'\n')
git_list=review/'report/GIT_FILES.txt'
git_list.touch(exist_ok=True)
files=[repo/'.gitignore',repo/'README.md']
for path in case.rglob('*'):
    if not path.is_file():continue
    relative=path.relative_to(case)
    if relative.parts[0]=='runs' or any('cache' in part.lower() for part in relative.parts):continue
    if path.suffix.lower() in ['.rds','.rda','.rdata','.zip','.gz','.h5','.h5ad','.loom','.bin']:continue
    assert path.stat().st_size<=5*1024*1024, f'Unexpected large Git candidate: {path}'
    files.append(path)
files=sorted(set(files))
git_list.write_text('\n'.join(str(p.relative_to(repo)) for p in files)+'\n')
root='cadir_limb_acceptance_20261025'
readme='''# Tabula Muris Limb Muscle 验收成果包

请先打开 repository/cases/tabula_muris_limb/acceptance/2026-10-25/report/结果解读报告.html。
HTML已内嵌两张中文热图，可离线阅读；同时附Markdown、原始TSV、PDF图。

本轮未重复运行完整实验、未调参。冻结240个既有文件未改变；7簇与8类参考的对应、GOA显著性和支持基因、Figure2对照和marker来源核查均已记录。
两次同种子一致只证明可复跑，不是多种子稳健性或独立生物学验证。

目录 repository/ 按原研究仓库相对路径保存小型成果。
acceptance/2026-10-25/README.md 提供文件索引和仅验收复核命令。
report/GIT_FILES.txt 是适合提交Git的路径清单，本轮没有执行暂存、提交或推送。
freeze/history_logs/ 保存所有原运行的关键成功/失败日志副本。

原始数据、全部中间RDS、R运行库和缓存不在包中，仍保留在云端原处；外部制品路径/大小/SHA256见 report/external_artifacts.json 与 freeze/baseline_manifest.json。
重新计算GOA需要外部RDS及当前CAdir环境。原始实验脚本仍依赖 /workspace/cadir-env 和输入RDS，不是空机器安装器。

MANIFEST_SHA256.tsv 保存包内文件大小和SHA256（不包含自身）；ZIP完成CRC与逐文件哈希检查并强制不超过24MiB。
'''
payload={f'{root}/README_交付.md':readme.encode()}
for path in files:payload[f'{root}/repository/{path.relative_to(repo).as_posix()}']=path.read_bytes()
rows=[{'path':name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()} for name,body in sorted(payload.items())]
stream=io.StringIO()
writer=csv.DictWriter(stream,fieldnames=['path','bytes','sha256'],delimiter='\t',lineterminator='\n')
writer.writeheader();writer.writerows(rows)
payload[f'{root}/MANIFEST_SHA256.tsv']=stream.getvalue().encode()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
    for name,body in sorted(payload.items()):
        info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=0o100644<<16
        bundle.writestr(info,body,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
assert archive.stat().st_size<=24*1024*1024
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert set(bundle.namelist())==set(payload)
    for row in rows:assert hashlib.sha256(bundle.read(row['path'])).hexdigest()==row['sha256']
    assert not any(Path(name).suffix.lower() in ['.rds','.rda','.rdata','.bin','.h5','.h5ad'] for name in bundle.namelist())
summary={'archive':str(archive),'bytes':archive.stat().st_size,'MiB':archive.stat().st_size/(1024*1024),
 'maximum_bytes':24*1024*1024,'sha256':digest(archive),'files':len(payload),
 'CRC_check':'PASS','all_manifest_file_hashes':'PASS','all_240_baseline_files_unchanged':True,
 'raw_expression_and_RDS_excluded':True,'git_files':str(git_list)}
archive.with_suffix('.sha256').write_text(summary['sha256']+'  '+archive.name+'\n')
archive.with_suffix('.bundle_info.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
