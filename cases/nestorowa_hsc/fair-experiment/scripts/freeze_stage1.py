#!/usr/bin/env python3
"""Archive real small preparation evidence and build exact external-data locks."""
import hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[4];BASE=ROOT/'cases/nestorowa_hsc/fair-experiment'
raw=pathlib.Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026')
prior=pathlib.Path('/workspace/hsc-fair-experiment-data-20261026/stage1/attempt-01')
final=prior.with_name('attempt-01-finalization-01')
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entry(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
status=json.loads((final/'stage1-finalization-status.json').read_text())
assert status['status']=='COMMON_PREPARATION_FINALIZED_NO_ALGORITHMS',status
for name,src in [('common-preparation-attempt-01',prior),('common-preparation-finalization-01',final)]:
 dst=BASE/'evidence'/name;dst.mkdir(parents=True,exist_ok=False)
 for p in sorted(src.iterdir()):
  if p.is_file() and p.suffix!='.rds':shutil.copy2(p,dst/p.name)
 # RNG snapshot is small and supports preparation provenance.
 if (src/'rng.rds').exists():shutil.copy2(src/'rng.rds',dst/'rng.rds')
c04=BASE/'evidence/C04';shutil.copytree('/workspace/hsc-c04-evidence-20261026',c04)
probe=BASE/'evidence/environment-probe-03/environment-signature.rds'
files=[entry(p) for d in [raw,prior,final] for p in sorted(d.iterdir()) if p.is_file()]
# Raw sidecar JSONs are provenance artifacts; any present files are intentionally protected.
files.append(entry(probe))
for p in sorted(c04.iterdir()):
 if p.is_file():files.append(entry(p))
lock={'schema_version':1,'stage':'COMMON_PREPARATION_FINALIZED_NO_ALGORITHMS','accepted_input_review':'da802216238bc66a60eff514b1ccebf213e77351','formal_execution_permitted':False,'C04_status':'FIRST_SOURCE_PARTIAL_REQUIRES_INDEPENDENT_ADJUDICATION','environment_signature_path':str(probe),'shared_input_path':str(prior/'shared-hvg-sce.rds'),'final_cell_ids_path':str(prior/'final-cell-ids.txt'),'HVG_ids_path':str(prior/'hvg-gene-ids.txt'),'reference_path':str(prior/'frozen-reference.tsv'),'evaluation_ids_path':str(prior/'evaluation-cell-ids.txt'),'scientific_config_sha256':sha(BASE/'design/scientific-config.json'),'files':files,'large_external_artifacts':[entry(p) for p in sorted(prior.glob('*.rds'))],'backup_status':'External workspace only; local export/hash verification still required. Git small evidence is not a complete raw/object backup.'}
dump(BASE/'locks/data-input-lock.json',lock)
# Source manifest is generated last, after all code/design changes are fixed.
sourcefiles=[]
for folder in [BASE/'scripts',BASE/'design']:
 sourcefiles.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
sourcefiles.append(ROOT/'cases/nestorowa_hsc/scripts/metadata_identity.R')
sourcefiles.extend(p for p in (BASE/'evidence/environment-probe-03').iterdir() if p.is_file())
sourcefiles.extend(p for p in c04.iterdir() if p.is_file())
manifest={'schema_version':1,'repository_root':str(ROOT),'files':[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(sourcefiles)]}
dump(BASE/'locks/source-manifest.json',manifest)
print(json.dumps({'data_lock_sha256':sha(BASE/'locks/data-input-lock.json'),'source_manifest_sha256':sha(BASE/'locks/source-manifest.json'),'config_sha256':sha(BASE/'design/scientific-config.json'),'environment_signature_sha256':sha(probe)},indent=2))
