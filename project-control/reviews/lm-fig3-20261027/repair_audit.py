import json,pathlib,hashlib,subprocess

out=pathlib.Path('reviews/lm-fig3-20261027')
review=out/'repair';review.mkdir(exist_ok=True)
prefix='cases/tabula_muris_limb/fig3_completion/'
fixed='8c1ff1c08cbc177402bc0148ca7bb4f3133fa0e3'
tip='ab68da7ef154f133ec436275fcf11396f37f884a'
def gitblob(sha,path): return subprocess.check_output(['git','show',f'{sha}:{path}'])
def digest(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name in ['direction_legend.R','repair_s1_legend.R','render_fig3.R']:
    (review/name).write_bytes(gitblob(fixed,prefix+'scripts/'+name))
changed=subprocess.check_output(['git','diff','--name-only','-z',fixed,tip]).decode().strip('\0').split('\0')
assert set(changed)=={prefix+'evidence/'+x+'.json' for x in ['external_artifacts','preservation','review_packet']}
idx=json.loads(gitblob(tip,prefix+'evidence/external_artifacts.json'))
for e in idx:
    p=pathlib.Path(e['path']);assert p.stat().st_size==e['bytes'] and digest(p)==e['sha256'],str(p)
rdsi=json.loads(gitblob(tip,prefix+'evidence/external_RDS_index.json'))
assert rdsi==json.loads(gitblob('a33e815',prefix+'evidence/external_RDS_index.json'))
tables=[]
for p in pathlib.Path(prefix+'tables').iterdir():
    assert p.read_bytes()==gitblob(tip,str(p)),str(p)
    tables.append({'path':str(p),'sha256':digest(p)})
for e in json.load(open(out/'external_index_checks.json')):
    assert digest(pathlib.Path(e['path']))==e['sha256'],e['path']
figures=[]
repairroot=pathlib.Path('/workspace/cadir-lm-fig3-artifacts-20261027/s1-legend-fix-20261027')
for panel in ['S1D_Bcell_standard','S1E_endothelial_standard']:
    for ext in ['png','pdf']:
        p=repairroot/(panel+'.'+ext)
        assert p.read_bytes()==gitblob(fixed,prefix+'figures/'+p.name)==gitblob(tip,prefix+'figures/'+p.name)
        original=repairroot/'original'/p.name
        assert original.read_bytes()==gitblob('a33e815',prefix+'figures/'+p.name)
        figures.append({'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)})
    subprocess.run(['pdftoppm','-scale-to','1200','-singlefile','-png',str(repairroot/(panel+'.pdf')),str(review/(panel+'_PDF'))],check=True,capture_output=True)
    text=subprocess.check_output(['pdftotext','-layout',str(repairroot/(panel+'.pdf')),'-']).decode()
    (review/(panel+'_PDF.txt')).write_text(text)
    expected=['T cell','Macrophage'] if panel.startswith('S1D') else ['Vascular endothelial cell']
    assert all(label in text for label in expected)
packet=json.loads(gitblob(tip,prefix+'evidence/review_packet.json'))
assert digest(pathlib.Path(packet['path']))==packet['sha256'] and pathlib.Path(packet['path']).stat().st_size==packet['bytes']
json.dump({'status':'PASS_INDEPENDENT_REPAIR_FILES','scientific_fix_sha':fixed,'delivery_tip':tip,'packaging_only_changed_paths':changed,'new_figures':figures,'tracked_scientific_tables_unchanged':tables,'all_old_external_records_unchanged':True,'current_external_records_checked':len(idx),'RDS_index_unchanged':True,'review_packet':packet},open(review/'file_result.json','w'),indent=2)
print('PASS: repaired images and original preservation; scientific tables and RDS index unchanged; delivery-only metadata verified.')
