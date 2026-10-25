from pathlib import Path
import csv,json,shutil,subprocess,os
root=Path('/workspace/cadir-stage1-retest');base=Path('/workspace/cadir-stage1-review-source/cases/tabula_muris_limb');out=Path(json.loads((root/'complete-entry/latest-case.json').read_text())['run_directory'])
def read(p):
    with p.open() as f:
        r=csv.DictReader(f,delimiter='\t');return r.fieldnames,list(r)
results=[]
for kind in ['wrong_cluster_same_counts','wrong_NA_same_assigned_count','wrong_Score','wrong_Rank','wrong_cluster_count']:
    dst=root/'mutations'/kind;dst.mkdir(parents=True)
    target='gene_clusters.tsv' if kind.startswith('wrong_cluster_same') or kind.startswith('wrong_NA') else 'cluster_sizes.tsv' if kind=='wrong_cluster_count' else 'coclustered_gene_ranks.tsv'
    for p in out.iterdir():
        if p.is_file() and p.name not in [target,'verification.json']: (dst/p.name).symlink_to(p)
    shutil.copyfile(out/'verification.json',dst/'verification.json');assert json.loads((dst/'verification.json').read_text())['status']=='PASS'
    fields,rs=read(out/target);change={}
    if kind=='wrong_cluster_same_counts':
        i=next(i for i,r in enumerate(rs) if r['cluster']!='NA'); j=next(j for j,r in enumerate(rs) if r['cluster'] not in ['NA',rs[i]['cluster']]);before=sorted(r['cluster'] for r in rs);change={'genes':[rs[i]['gene_id'],rs[j]['gene_id']]};rs[i]['cluster'],rs[j]['cluster']=rs[j]['cluster'],rs[i]['cluster'];assert before==sorted(r['cluster'] for r in rs)
    elif kind=='wrong_NA_same_assigned_count':
        i=next(i for i,r in enumerate(rs) if r['cluster']!='NA');j=next(j for j,r in enumerate(rs) if r['cluster']=='NA');change={'genes':[rs[i]['gene_id'],rs[j]['gene_id']]};rs[i]['cluster'],rs[j]['cluster']=rs[j]['cluster'],rs[i]['cluster']
    elif kind=='wrong_Score':change={'gene':rs[0]['Rowname'],'before':rs[0]['Score']};rs[0]['Score']=str(float(rs[0]['Score'])+0.25)
    elif kind=='wrong_Rank':rs[0]['Rank'],rs[1]['Rank']=rs[1]['Rank'],rs[0]['Rank']
    else:rs[0]['ngenes']=str(int(rs[0]['ngenes'])+1);rs[1]['ngenes']=str(int(rs[1]['ngenes'])-1)
    with (dst/target).open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rs)
    with (root/f'evidence/mutation-{kind}.log').open('w') as log:
        p=subprocess.run(['bash',str(base/'scripts/run-r.sh'),str(base/'scripts/verify_results.R'),str(dst)],stdout=log,stderr=subprocess.STDOUT)
    state=json.loads((dst/'verification.json').read_text());results.append({'case':kind,'exit_code':p.returncode,'initial_status':'PASS','final':state,'mutation':change})
    (root/'evidence/mutation_results.json').write_text(json.dumps(results,indent=2))
    assert p.returncode!=0 and state['status']=='FAIL'
    print(kind,p.returncode,state,flush=True)
