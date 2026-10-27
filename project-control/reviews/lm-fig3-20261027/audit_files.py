import hashlib, json, pathlib, subprocess

root = pathlib.Path('cases/tabula_muris_limb/fig3_completion')
out = pathlib.Path('reviews/lm-fig3-20261027')
def digest(p):
    with open(p, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

checks=[]
for name in ('external_RDS_index.json','external_artifacts.json'):
    for entry in json.loads((root/'evidence'/name).read_text()):
        p=pathlib.Path(entry['path'])
        checks.append({'index':name,'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p),
                       'match':p.stat().st_size==entry['bytes'] and digest(p)==entry['sha256']})
assert all(x['match'] for x in checks)
for sub in ('tables','figures'):
    for p in (root/sub).iterdir():
        actual=pathlib.Path('/workspace/cadir-lm-fig3-artifacts-20261027/render-final')/sub/p.name
        assert actual.is_file() and digest(p)==digest(actual), str(p)

old=json.loads((out/'hashes_before.json').read_text())
preserved=[]
for entry in old:
    p=pathlib.Path(entry['path'])
    preserved.append({'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p),'unchanged':p.stat().st_size==entry['bytes'] and digest(p)==entry['sha256']})
assert all(x['unchanged'] for x in preserved)
json.dump(checks,open(out/'external_index_checks.json','w'),indent=2)
json.dump(preserved,open(out/'hashes_after.json','w'),indent=2)
report={'status':'PASS','indexed_checks':len(checks),'preserved_files':len(preserved),
        'tracked_tables_and_figures_identical_to_external':True,
        'review_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
json.dump(report,open(out/'file_audit_result.json','w'),indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
