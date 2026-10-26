#!/usr/bin/env python3
"""Byte-lock existing external R package code/native libraries; no R or installs."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[4];BASE=ROOT/'cases/nestorowa_hsc/fair-experiment';lib=pathlib.Path('/workspace/.cadir-r-lib/4.4')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
paths=[p for p in lib.rglob('*') if p.is_file() and (p.suffix in ['.so','.rdb','.rdx'] or p.name in ['DESCRIPTION','NAMESPACE'])]
path=BASE/'locks/runtime-library-lock.json'
dump(path,dict(library_root=str(lib),scope='All installed external package DESCRIPTION/NAMESPACE plus R/data lazyload databases and native .so bytes. System R/base/BLAS fixed by exact Docker image ID.',files=[dict(path=str(p.relative_to(lib)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]))
datalock=BASE/'locks/data-input-lock.json';data=json.loads(datalock.read_text());data['runtime_library_lock_path']=str(path)
data['files']=[e for e in data['files'] if e['path']!=str(path)]+[dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))];dump(datalock,data)
sourcepaths=[]
for folder in [BASE/'scripts',BASE/'design',BASE/'evidence/environment-probe-03',BASE/'evidence/C04']:
 sourcepaths.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
sourcepaths.append(ROOT/'cases/nestorowa_hsc/scripts/metadata_identity.R')
dump(BASE/'locks/source-manifest.json',dict(schema_version=1,repository_root=str(ROOT),files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(sourcepaths)]))
print(json.dumps(dict(runtime_files=len(paths),runtime_bytes=sum(p.stat().st_size for p in paths),library_lock_sha256=sha(path),data_lock_sha256=sha(datalock),source_manifest_sha256=sha(BASE/'locks/source-manifest.json')),indent=2))
