#!/usr/bin/env python3
"""Check result accounting and prove every frozen baseline byte is unchanged."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np

review=Path(__file__).resolve().parents[1]
case=review.parents[1]
manifest=json.loads((review/'freeze/baseline_manifest.json').read_text())
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
changes=[]
for record in manifest['files']:
    path=Path(record['path'])
    if not path.is_file() or path.stat().st_size!=record['bytes'] or digest(path)!=record['sha256']:
        changes.append(record['path'])
assert not changes,changes
counts=pd.read_csv(review/'tables/counts_7x8.tsv',sep='\t',index_col=0)
row=pd.read_csv(review/'tables/fraction_within_cluster.tsv',sep='\t',index_col=0)
column=pd.read_csv(review/'tables/fraction_within_reference.tsv',sep='\t',index_col=0)
assert counts.shape==(7,8) and counts.values.sum()==1882
assert np.allclose(row.sum(axis=1),1) and np.allclose(column.sum(axis=0),1)
cells=pd.read_csv(case/'results/cell_clusters.tsv',sep='\t')
expected=pd.crosstab(cells.cluster,cells.reference).reindex(index=counts.index,columns=counts.columns,fill_value=0)
assert np.array_equal(counts.values,expected.values)
existing=pd.read_csv(case/'results/cluster_reference_contingency.tsv',sep='\t')
for entry in existing.itertuples(index=False):assert counts.loc[entry.cluster,entry.reference]==entry.Freq
goa=pd.read_csv(review/'annotation/goa_all.tsv',sep='\t')
assert goa.pval.between(0,1).all() and goa.padj.between(0,1).all()
assert np.array_equal(goa.support_genes.fillna('').map(lambda x:len(x.split(';')) if x else 0),goa.ngois_in_set)
decisions=pd.read_csv(review/'annotation/annotation_decisions.tsv',sep='\t')
original=pd.read_csv(case/'results/cluster_annotations.tsv',sep='\t').set_index('cluster').predicted_annotation
assert all(row.original_prediction==original[row.cluster] for row in decisions.itertuples(index=False))
assert decisions.set_index('cluster').loc['cluster_1','significant_sets_BH_005']==0
assert decisions.hungarian_candidate_tested.all()
assert json.loads((review/'annotation/review_status.json').read_text())['saved_annotations_reproduced']
result={'status':'PASS','verified_utc':datetime.now(timezone.utc).isoformat(),
 'baseline_files_checked':len(manifest['files']),'baseline_files_changed':changes,
 'count_table_matches_both_cell_assignments_and_original_contingency':True,
 'both_normalization_axes_sum_to_one':True,'all_goa_overlap_counts_match_saved_support_lists':True,
 'predictions_preserved':True,'full_clustering_repeated':False,
 'same_seed_repeatability_is_not_multiseed_robustness':True}
(review/'freeze/baseline_preservation_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
