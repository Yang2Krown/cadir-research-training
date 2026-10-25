#!/usr/bin/env python3
"""Freeze hashes and small code/config snapshots; never modify the baseline."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

review = Path(__file__).resolve().parents[1]
case = review.parents[1]
repo = case.parents[1]
dest = review / 'freeze'
manifest_file = dest / 'baseline_manifest.json'
if manifest_file.exists():
    raise SystemExit('Freeze already exists; refusing to overwrite it.')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

paths = [p for p in case.rglob('*') if p.is_file() and 'acceptance' not in p.relative_to(case).parts]
paths += [repo / '.gitignore', repo / 'README.md', repo / 'data/tabula_muris_limb_preproc.rds']
records = [{'path': str(p), 'relative_to_repo': str(p.relative_to(repo)),
            'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(paths)]
manifest = {'frozen_utc': datetime.now(timezone.utc).isoformat(),
            'git_branch': subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip(),
            'git_HEAD': subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
            'code_state': 'Uncommitted baseline code is identified by per-file SHA256, not by HEAD alone.',
            'final_run': str(case / 'runs/case-ppkaow9s'),
            'first_successful_run': str(case / 'runs/case-5los7t_s'),
            'repeated_seed': 2358,
            'interpretation': 'Identical same-seed runs demonstrate repeatability only; no multi-seed robustness experiment was performed.',
            'files': records}
manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(dest / 'baseline_manifest.sha256').write_text(digest(manifest_file)+'  baseline_manifest.json\n')
for name,command in [('git_status.txt',['git','-C',str(repo),'status','--short','--untracked-files=all']),
                     ('tracked_diff.patch',['git','-C',str(repo),'diff','--binary'])]:
    (dest / name).write_text(subprocess.check_output(command,text=True))
for folder in ['scripts','config']:
    shutil.copytree(case / folder, dest / folder)
for name in ['latest-case.json','latest-environment.json']:
    shutil.copy2(case/name,dest/name)
for name in ['provenance.md','sources.json','upstream-renv.lock','runtime-renv.lock','conda-explicit-linux-64.txt','activate.sh']:
    shutil.copy2(Path('/workspace/cadir-env')/name,dest/name)
print(json.dumps({'frozen_files':len(records),'manifest':str(manifest_file)},indent=2))
