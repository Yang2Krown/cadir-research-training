from pathlib import Path
import csv,json,math,hashlib,subprocess
from collections import Counter
root=Path('/workspace/cadir-stage1-retest'); source=Path('/workspace/cadir-stage1-review-source'); base=source/'cases/tabula_muris_limb'
out=Path(json.loads((root/'complete-entry/latest-case.json').read_text())['run_directory'])
def rows(p):
    with p.open() as h: return list(csv.DictReader(h,delimiter='\t'))
labels={r['cell_id']:r['reference'] for r in rows(root/'evidence/original_labels.tsv')}
cells=rows(out/'cell_clusters.tsv'); assert len(labels)==len(cells)==1882
assert len({r['cell_id'] for r in cells})==len(cells) and set(labels)=={r['cell_id'] for r in cells}
assert all(r['reference']==labels[r['cell_id']] for r in cells)
genes=rows(out/'gene_clusters.tsv');sizes=rows(out/'cluster_sizes.tsv')
gc=Counter(r['cluster'] for r in genes if r['cluster']!='NA');cc=Counter(r['cluster'] for r in cells)
assert all(int(r['ngenes'])==gc[r['cluster']] and int(r['ncells'])==cc[r['cluster']] for r in sizes)
assert {r['cluster'] for r in sizes}==set(cc)==set(gc)
frozen_cells={r['cell_id']:r['cluster'] for r in rows(base/'results/cell_clusters.tsv')};frozen_genes={r['gene_id']:r['cluster'] for r in rows(base/'results/gene_clusters.tsv')}
assert all(frozen_cells[r['cell_id']]==r['cluster'] for r in cells) and all(frozen_genes[r['gene_id']]==r['cluster'] for r in genes)
(root/'evidence/independent_assignment_counts.json').write_text(json.dumps({'cells':len(cells),'genes':len(genes),'cluster_counts_verified':True,'cell_counts':cc,'assigned_gene_counts':gc,'cell_and_gene_assignments_match_frozen':True},indent=2))
cont=Counter((r['cluster'],labels[r['cell_id']]) for r in cells); a=Counter(r['cluster'] for r in cells); b=Counter(labels.values()); n=len(cells)
choose=lambda x:x*(x-1)/2
sa=sum(map(choose,a.values()));sb=sum(map(choose,b.values()));sij=sum(map(choose,cont.values()));expect=sa*sb/choose(n)
ari=(sij-expect)/((sa+sb)/2-expect)
ha=-sum(v/n*math.log(v/n) for v in a.values());hb=-sum(v/n*math.log(v/n) for v in b.values())
mi=sum(v/n*math.log(v*n/(a[c]*b[t])) for (c,t),v in cont.items());nmi=mi/max(ha,hb)
claimed=json.loads((out/'metrics.json').read_text()); tol=1e-12
m={'n':n,'cluster_count':len(a),'reference_count':len(b),'ARI':ari,'NMI_max':nmi,'MI':mi,'H_cluster':ha,'H_reference':hb,'ARI_abs_error':abs(ari-claimed['ARI']),'NMI_abs_error':abs(nmi-claimed['NMI']),'tolerance':tol,'reference_source':'original RDS via independent extract_independent.R, ID joined','formula_ARI':'(sum C(nij,2)-sum C(ai,2)*sum C(bj,2)/C(n,2))/(0.5*(sum C(ai,2)+sum C(bj,2))-sum C(ai,2)*sum C(bj,2)/C(n,2))','formula_NMI':'sum(pij*ln(pij/(pi*pj)))/max(-sum(pi*ln(pi)),-sum(pj*ln(pj)))','counts':[{ 'cluster':c,'reference':t,'count':v} for (c,t),v in sorted(cont.items())]}
assert m['ARI_abs_error']<tol and m['NMI_abs_error']<tol
(root/'evidence/independent_metrics.json').write_text(json.dumps(m,indent=2))
fresh={r['Rowname']:r for r in rows(out/'coclustered_gene_ranks.tsv')}; frozen={r['Rowname']:r for r in rows(base/'results/coclustered_gene_ranks.tsv')}
assert fresh.keys()==frozen.keys()
scores=max(abs(float(v['Score'])-float(frozen[k]['Score'])) for k,v in fresh.items()); ranks=sum(v['Rank']!=frozen[k]['Rank'] for k,v in fresh.items()); clusters=all(v['Cluster']==frozen[k]['Cluster'] for k,v in fresh.items())
manifest=json.loads((base/'publication/external_resources.json').read_text())['data_and_intermediate_artifacts']; matches=[]
for item in manifest:
    if '/case-ppkaow9s/' in item['path']:
        p=out/Path(item['path']).name
        actual=hashlib.sha256(p.read_bytes()).hexdigest(); matches.append({'file':p.name,'bytes':p.stat().st_size,'historical_bytes':item['bytes'],'sha256':actual,'historical_sha256':item['sha256'],'match':actual==item['sha256'] and p.stat().st_size==item['bytes']})
assert scores<=1e-10 and ranks==0 and clusters and all(x['match'] for x in matches)
comparison={'alpha_genes':json.loads((out/'ranking_provenance.json').read_text())['alpha_genes'],'ranked_genes':len(fresh),'frozen_score_max_abs_difference':scores,'rank_changes':ranks,'gene_cluster_pairs_identical':clusters,'historical_objects_read':False,'fresh_objects_vs_historical_index':matches}
(root/'evidence/independent_ranking_hashes.json').write_text(json.dumps(comparison,indent=2))
print(json.dumps({'ARI':ari,'NMI':nmi,'ranking':comparison},indent=2))
