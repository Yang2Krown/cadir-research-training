#!/usr/bin/env python3
"""Bounded metadata/text-only check. No data downloads or invented markers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

review = Path(__file__).resolve().parents[1]
out = review / 'source_check'
record = {'checked_utc':datetime.now(timezone.utc).isoformat(),
 'target':'tabula_muris_marker_genes.csv',
 'scope':'Two pinned author trees; provided local materials; at most 3 GitHub metadata requests, each <=2 MiB, no retries; no archives or full datasets.',
 'trees':[], 'local_candidates':[], 'http_requests':[]}
for repo in ['CAdir','CAdir_results']:
    root=Path('/workspace/cadir-env/sources')/repo
    sha=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    tree=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','--name-only',sha],text=True)
    path=out/f'{repo}_tree_paths.txt'
    path.write_text(tree)
    record['trees'].append({'repository':repo,'commit':sha,'tree_list_sha256':hashlib.sha256(tree.encode()).hexdigest(),
      'exact_matches':[p for p in tree.splitlines() if Path(p).name.lower()==record['target']],
      'tabula_marker_filename_candidates':[p for p in tree.splitlines() if 'tabula' in p.lower() and 'marker' in p.lower()]})
for root in ['/workspace/attachments','/workspace/shared','/workspace/library-files','/workspace/scratch','/workspace/cadir-research-training/data']:
    for path in Path(root).rglob('*'):
        if path.is_file() and path.suffix.lower() in ['.csv','.tsv'] and ('marker' in path.name.lower() or 'tabula' in path.name.lower()):
            record['local_candidates'].append(str(path))
record['local_roots_checked']=['/workspace/attachments','/workspace/shared','/workspace/library-files','/workspace/scratch','/workspace/cadir-research-training/data']

def fetch(label,url):
    item={'label':label,'url':url}
    try:
        req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'CAdir-case-audit'})
        with urllib.request.urlopen(req,timeout=20) as response:
            body=response.read(2*1024*1024+1)
            item['status']=response.status
        if len(body)>2*1024*1024:
            raise ValueError('Metadata exceeded 2 MiB bounded limit')
        (out/f'{label}.json').write_bytes(body)
        item.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        payload=json.loads(body)
    except Exception as exc:
        item['error']=str(exc)
        payload=None
    record['http_requests'].append(item)
    return payload

head=fetch('results_main_commit','https://api.github.com/repos/VingronLab/CAdir_results/commits/main')
releases=fetch('results_releases_first20','https://api.github.com/repos/VingronLab/CAdir_results/releases?per_page=20')
record['remote_main_sha']=head.get('sha') if isinstance(head,dict) else None
record['release_asset_names']=[asset.get('name') for release in releases for asset in release.get('assets',[])] if isinstance(releases,list) else None
pinned=next(x['commit'] for x in record['trees'] if x['repository']=='CAdir_results')
if record['remote_main_sha'] and record['remote_main_sha']!=pinned:
    tree=fetch('results_current_tree','https://api.github.com/repos/VingronLab/CAdir_results/git/trees/'+record['remote_main_sha']+'?recursive=1')
    if isinstance(tree,dict):
        record['current_tree_truncated']=tree.get('truncated')
        record['current_tree_matches']=[x['path'] for x in tree.get('tree',[]) if Path(x.get('path','')).name.lower()==record['target']]
record['conclusion']='No exact CSV in the checked pinned trees or provided materials; release metadata and current-main coverage are reported separately. Absence is scoped, not proof that the file never existed.'
record['substitution']='No reference-derived markers and no substitute CSV were produced. CellMarker annotation resource is distinct from the missing Figure 2 feature-augmentation CSV.'
(out/'marker_search.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
