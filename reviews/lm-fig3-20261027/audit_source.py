import json,pathlib,hashlib,subprocess

root=pathlib.Path('cases/tabula_muris_limb/fig3_completion')
out=pathlib.Path('reviews/lm-fig3-20261027')
def sha(p):
    with open(p,'rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
checks=[]
for name in ['base_implementation_sha256.json','implementation_source_sha256.json']:
    for entry in json.load(open(root/'evidence'/name)):
        rel=pathlib.Path(entry['path']).relative_to('/workspace/cadir-lm-fig3-completion-20261027')
        actual=pathlib.Path(rel)
        checks.append({'index':name,'path':str(actual),'sha256':sha(actual),'match':sha(actual)==entry['sha256']})
assert all(entry['match'] for entry in checks)
changes=subprocess.check_output(['git','diff','--name-only','-z','9d473b441058c45b2563c2ebe94ae99dda1f5209','a33e815971f8bb89e8136ed65ee41b99a2f3a2e9']).decode().strip('\0').split('\0')
assert all(x.startswith(str(root)+'/') for x in changes)
json.dump({'status':'PASS','source_index_checks':checks,'all_changes_under_fig3_completion':True,'changed_paths':len(changes),'cgroup_cpu_max':pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'cgroup_memory_max':pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip()},open(out/'source_resource_result.json','w'),indent=2)
print('PASS:',len(checks),'source hashes;',len(changes),'paths confined to fig3_completion')
