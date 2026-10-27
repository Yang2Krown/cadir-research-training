#!/usr/bin/env python3
"""Copy only the fixed Limb Muscle dependencies from the read-only source cache."""
import hashlib
import json
import shutil
from pathlib import Path

base = Path(__file__).resolve().parents[1]
cache = Path('/workspace/cadir-full-paper-scope-review-20261027')
ref = 'c15b49578bde38b42fd5db2c9830c10dd441ee4c'
paths = ['results/figure2.qmd', 'results/utils.R', 'results/cluster_tabula_muris.R',
         'download_raw_data/tabula_muris/tabula_muris_limb_save_RAW_data.R',
         'download_raw_data/tabula_muris/download_full_tabula_muris.R',
         'preprocessing/data_preprocessing.R', 'preprocessing/submit_to_cluster_preprocessing.sh',
         'renv.lock']
records = {x['path']: x for x in json.loads((cache/'evidence/source-downloads.json').read_text())}
manifest = []
for name in paths:
    src = cache/'author-fixed'/name
    if name == 'renv.lock' and not src.exists():
        src = base/'evidence/author-fixed/renv.lock'
        record = json.loads((base/'evidence/renv_download.json').read_text())
    else:
        record = records.get(name)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if record:
        assert record['sha256'] == digest
        assert ref in record['url'] and record['status'] == 200
    dest = base/'evidence/author-fixed'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    manifest.append({'path': name, 'sha256': digest, 'bytes': src.stat().st_size,
                     'cache_path': str(src), 'upstream_ref': ref,
                     'url': f'https://raw.githubusercontent.com/VingronLab/CAdir_results/{ref}/{name}',
                     'cache_download_record_verified': bool(record)})
(base/'evidence/author_sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
pipeline = base.parents[0]/'scripts'
files = ['pipeline.R','run_case.py','run-r.sh','sample_rss.sh','check_environment.py','verify_results.R']
implementation = []
for name in files:
    src = pipeline/name
    implementation.append({'path': str(src), 'sha256': hashlib.sha256(src.read_bytes()).hexdigest()})
(base/'evidence/base_implementation_sha256.json').write_text(json.dumps(implementation, indent=2)+'\n')
cfg = json.loads((base.parent/'config/case.json').read_text())
cfg['data_path']='/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds'
(base/'evidence/run_config.json').write_text(json.dumps(cfg, indent=2)+'\n')
resources={p: Path('/sys/fs/cgroup',p).read_text().strip() for p in ['memory.max','cpu.max']}
(base/'evidence/cgroup_limits.json').write_text(json.dumps(resources, indent=2)+'\n')
print(json.dumps({'source_files':len(manifest),'all_verified':all(x['cache_download_record_verified'] for x in manifest),'resources':resources}))
