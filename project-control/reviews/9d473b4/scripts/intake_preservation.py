from pathlib import Path
import json,hashlib,subprocess,sys
root=Path('/workspace/cadir-r3-independent-20261026');root.mkdir(exist_ok=True);ev=root/'evidence';ev.mkdir(exist_ok=True)
source=Path('/workspace/cadir-r3-review-source');old=Path('/workspace/cadir-r3-evidence-20261026');base=Path('/workspace/cadir-stage1-retest/complete-entry/case-e_ilcvjv')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in source.rglob('*') if p.is_file() and p.name!='.git')+sorted(p for p in old.rglob('*') if p.is_file())+[base/n for n in ['ca.rds','cadir_unranked.rds','runtime_config.json','sessionInfo.txt']]+[Path('/workspace/cadir-stage1-retest/publish/独立复验报告.md')]
snapshot={str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}
if len(sys.argv)>1 and sys.argv[1]=='after':
    before=json.loads((ev/'preservation_before.json').read_text());assert snapshot==before
    (ev/'preservation_after.json').write_text(json.dumps(snapshot,indent=2));(ev/'preservation_summary.json').write_text(json.dumps({'all_files_unchanged':True,'compared_files':len(snapshot),'source_head':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip(),'source_status':subprocess.check_output(['git','-C',str(source),'status','--porcelain']).decode()},indent=2));sys.exit()
(ev/'preservation_before.json').write_text(json.dumps(snapshot,indent=2))
assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD']).decode().strip()=='9d473b441058c45b2563c2ebe94ae99dda1f5209'
manifest=json.loads((old/'导出清单.json').read_text());checks=[]
for row in manifest['files']:
    rel=row['export_relative_path'];p=old/rel if not rel.startswith('text/') else old/'text-export'/rel
    checks.append({'relative_path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'match':p.stat().st_size==row['bytes'] and sha(p)==row['sha256']})
assert len(checks)==34 and all(r['match'] for r in checks)
pub=json.loads((source/'cases/tabula_muris_limb/publication/external_resources.json').read_text());baseline=[]
for row in pub['data_and_intermediate_artifacts']:
    if '/case-ppkaow9s/' in row['path'] and Path(row['path']).name in ['ca.rds','cadir_unranked.rds']:
        p=base/Path(row['path']).name;baseline.append({'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'match':sha(p)==row['sha256'] and p.stat().st_size==row['bytes']})
assert len(baseline)==2 and all(r['match'] for r in baseline)
cfg1=json.loads((base/'runtime_config.json').read_text());cfg2=json.loads((old/'text-export/text/rerun/runtime_config.json').read_text());diff={k:{'baseline':cfg1.get(k),'review':cfg2.get(k)} for k in cfg1.keys()|cfg2.keys() if cfg1.get(k)!=cfg2.get(k)}
assert set(diff)=={'data_path'}
session_equal=(base/'sessionInfo.txt').read_bytes()==(old/'text-export/text/rerun/full/sessionInfo.txt').read_bytes();assert session_equal
hist=json.loads((old/'text-export/text/evidence/upstream_sources.json').read_text());sources=[]
for pkg in ['APL','CAdir']:
    for rel,h in hist[pkg]['R_files_sha256'].items():
        p=Path('/workspace/cadir-env/sources')/pkg/rel;sources.append({'package':pkg,'file':rel,'sha256':sha(p),'old_sha256':h,'match':sha(p)==h})
assert len(sources)==22 and all(r['match'] for r in sources)
(ev/'intake_checks.json').write_text(json.dumps({'manifest_files':checks,'baseline_vs_frozen_index':baseline,'configuration_differences':diff,'sessionInfo_byte_identical':session_equal,'source_files':sources},indent=2))
changed=subprocess.check_output(['git','-C',str(source),'diff','--name-only','0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b']).decode().splitlines()
assert all(p.startswith('cases/tabula_muris_limb/review_fixes/2026-10-26-r3/') or p in ['cases/tabula_muris_limb/scripts/pipeline.R','README.md','cases/tabula_muris_limb/README.md'] for p in changed)
prior=subprocess.check_output(['git','-C',str(source),'show','0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b:cases/tabula_muris_limb/scripts/pipeline.R']).decode();current=(source/'cases/tabula_muris_limb/scripts/pipeline.R').read_text()
before='historical_ranking_equivalence = "not_established; original CA/unranked objects unavailable"';after='ranking_scope = "Scores and ranks use this run\'s stored CA basis, RNG state, alpha and installed functions."'
assert current==prior.replace(before,after) and prior.count(before)==1
(ev/'increment_scope.json').write_text(json.dumps({'changed_paths':changed,'production_change_metadata_only':True,'two_README_updates_only_describe_diagnosis_and_limits':True,'all_prior_results_figures_acceptance_and_reports_unchanged':True,'old_independent_report_hash':sha(Path('/workspace/cadir-stage1-retest/publish/独立复验报告.md'))},indent=2))
print(json.dumps({'manifest_matches':len(checks),'baseline_matches':len(baseline),'source_matches':len(sources),'session_equal':session_equal,'config_diff':list(diff),'snapshot_files':len(snapshot)}))
