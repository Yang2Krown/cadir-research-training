#!/usr/bin/env python3
"""Publish a small review packet; retain complete data/RDS outside Git."""
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

base=Path(__file__).resolve().parents[1]
root=Path('/workspace/cadir-lm-fig3-artifacts-20261027')
run=root/'hvg-only/case-htbeu88g'
render=root/'render-final'
assert json.loads((render/'provenance/verification.json').read_text())['status']=='PASS_IMPLEMENTER_SELFCHECK_ONLY'
for folder in ['figures','tables','evidence/render','evidence/real-run','evidence/parent-sources']:
    (base/folder).mkdir(parents=True,exist_ok=True)
for p in (render/'figures').glob('*'):
    shutil.copyfile(p,base/'figures'/p.name)
# Full point clouds, all CA coordinates and all history membership/coordinates
# remain in the indexed external artifacts; concise review tables are in Git.
tables=['cluster_annotation_reference_map.tsv','panel_cluster_selection.tsv','all_cell_assignments.tsv',
        'all_gene_assignments.tsv','all_gene_ranks.tsv','top5_genes.tsv','Fig3A_actual_gene_labels.tsv',
        'directions_principal.tsv','directions_standard.tsv','CA_singular_values.tsv',
        'principal_standard_projection_angle_checks.tsv','S1A_pairwise_direction_angles_degrees.tsv',
        'S1B_all_direction_projections.tsv','S1C_reference_flows.tsv','Fig3D_node_annotations.tsv','Fig3D_history_edges.tsv']
for name in tables:
    shutil.copyfile(render/'tables'/name,base/'tables'/name)
for p in (render/'provenance').glob('*'):
    shutil.copyfile(p,base/'evidence/render'/p.name)
for name in ['console.log','verify-console.log']:
    shutil.copyfile(render/name,base/'evidence/render'/name)
for attempt in ['render-attempt-1','render-attempt-2','render-attempt-3']:
    shutil.copyfile(root/attempt/'console.log',base/'evidence/render'/f'{attempt}.console.log')
for name in ['config.json','runtime_config.json','status.json','r_status.json','console.log','verification.json',
             'ranking_provenance.json','rng_stages.json','effective_cadir_parameters.txt','stage_times_seconds.json',
             'selection.json','metrics.json','input_integrity.json','data_audit.json','annotation_resources.json',
             'sessionInfo.txt','required_version_check.tsv','installed_packages.tsv']:
    shutil.copyfile(run/name,base/'evidence/real-run'/name)
for p in Path('/workspace/cadir-lm-parent-source-audit-20261027').glob('*'):
    if p.is_file(): shutil.copyfile(p,base/'evidence/parent-sources'/p.name)

def record(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
external=[record(p) for folder in [run,render] for p in sorted(folder.rglob('*')) if p.is_file()]
(base/'evidence/external_artifacts.json').write_text(json.dumps(external,indent=2)+'\n')
rds=[r for r in external if r['path'].lower().endswith('.rds')]
(base/'evidence/external_RDS_index.json').write_text(json.dumps(rds,indent=2)+'\n')
protected=Path('/workspace/cadir-stage1-fix')
preservation={'original_worktree_status':subprocess.check_output(['git','-C',str(protected),'status','--short'],text=True),
              'original_worktree_HEAD':subprocess.check_output(['git','-C',str(protected),'rev-parse','HEAD'],text=True).strip(),
              'input_after':record(Path('/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds')),
              'changed_tracked_paths':subprocess.check_output(['git','-C',str(base.parents[2]),'diff','--name-only','9d473b441058c45b2563c2ebe94ae99dda1f5209'],text=True).splitlines()}
assert preservation['original_worktree_status']==''
assert preservation['input_after']['sha256']=='af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b'
assert all('/fig3_completion/' in p for p in preservation['changed_tracked_paths'])
(base/'evidence/preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
scripts=[record(p) for p in sorted((base/'scripts').glob('*')) if p.is_file()]
(base/'evidence/implementation_source_sha256.json').write_text(json.dumps(scripts,indent=2)+'\n')
packet=root/'Limb_Muscle_Fig3_S1_review_packet.tar.gz'
with tarfile.open(packet,'w:gz') as tf:
    for p in sorted(base.rglob('*')):
        if p.is_file(): tf.add(p,arcname=Path('fig3_completion')/p.relative_to(base))
(base/'evidence/review_packet.json').write_text(json.dumps(record(packet),indent=2)+'\n')
print(json.dumps({'review_packet':record(packet),'external_files':len(external),'RDS_objects':len(rds)}))
