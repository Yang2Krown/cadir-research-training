import csv, json, math, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment

out=pathlib.Path('reviews/lm-fig3-20261027')
render=pathlib.Path('/workspace/cadir-lm-fig3-artifacts-20261027/render-final/tables')
def read(p):
    with open(p,newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
goa=read(out/'independent_GOA.tsv')
history=read(render/'Fig3D_node_annotations.tsv')
final=read(render/'cluster_annotation_reference_map.tsv')
results=[]
for stage in dict.fromkeys(x['stage'] for x in goa):
    rows=[x for x in goa if x['stage']==stage]
    clusters=list(dict.fromkeys(x['cluster_id'] for x in rows))
    # Upstream annotation truncates each sorted GOA list to ncluster candidates.
    candidates={c:[x for x in rows if x['cluster_id']==c][:len(clusters)] for c in clusters}
    types=list(dict.fromkeys(x['gene_set'] for c in clusters for x in candidates[c]))
    for cost in ('pval','logpval'):
        matrix=np.full((len(clusters),len(types)),1. if cost=='pval' else 0.)
        for i,c in enumerate(clusters):
            for x in candidates[c]:
                val=float(x['padj'])
                matrix[i,types.index(x['gene_set'])]=val if cost=='pval' else math.log10(val)
        ri,ci=linear_sum_assignment(matrix)
        predicted=dict(zip(clusters,clusters))
        for i,j in zip(ri,ci):
            accepted=matrix[i,j]<=.05 if cost=='pval' else matrix[i,j]<=math.log10(.05)
            if accepted: predicted[clusters[i]]=types[j]
        actual={x['cluster_id']:x['predicted_annotation'] for x in final} if stage=='final' else {x['cluster_id']:x['automatic_annotation'] for x in history if x['iteration']==stage}
        selected=(cost=='logpval' if stage=='final' else cost=='pval')
        exact=all(predicted[c]==actual[c] for c in actual)
        constrained=matrix.copy()
        if selected:
            for c,name in actual.items():
                i=clusters.index(c)
                if name!=c:
                    assert name in types, (stage,c,name)
                    j=types.index(name)
                    constrained[i,:]=np.inf
                    constrained[i,j]=matrix[i,j]
                    assert (matrix[i,j]<=.05 if cost=='pval' else matrix[i,j]<=math.log10(.05))
                else:
                    # An unchanged numeric name means its chosen cost failed alpha.
                    significant=matrix[i,:]<=.05 if cost=='pval' else matrix[i,:]<=math.log10(.05)
                    constrained[i,significant]=np.inf
            ari,aci=linear_sum_assignment(constrained)
            actual_objective=float(constrained[ari,aci].sum())
            optimum=float(matrix[ri,ci].sum())
            assert abs(actual_objective-optimum)<1e-12, (stage,cost,actual_objective,optimum)
        else:
            actual_objective=None
        results.append({'stage':stage,'cost':cost,'selected_by_render':selected,'predictions':predicted,'matches_actual':exact,'objective':float(matrix[ri,ci].sum()),'actual_annotation_constrained_objective':actual_objective,'actual_annotations':actual if selected else None})
json.dump({'status':'PASS_INDEPENDENT_SCIPY_HUNGARIAN','final_cost':'logpval','history_cost':'pval','results':results},open(out/'annotation_result.json','w'),indent=2)
print(json.dumps({'status':'PASS_INDEPENDENT_SCIPY_HUNGARIAN','verified_actual_annotations':sum(len(x['predictions']) for x in results if x['selected_by_render']),'costs_produce_different_names':any(x['predictions']!=next(y['predictions'] for y in results if y['stage']==x['stage'] and y['cost']!=x['cost']) for x in results)},indent=2))
