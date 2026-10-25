#!/usr/bin/env python3
"""Describe the frozen 7x8 assignments; no clustering or parameter changes."""
import os
from pathlib import Path
import json
import textwrap
import numpy as np
import pandas as pd

review = Path(__file__).resolve().parents[1]
case = review.parents[1]
os.environ.setdefault('MPLCONFIGDIR', '/tmp/cadir-limb-acceptance-mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns

fontfile = next(iter(Path('/usr/share/fonts').rglob('NotoSansCJK-Regular.ttc')), None)
if fontfile:
    font_manager.fontManager.addfont(str(fontfile))
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(fontfile)).get_name()
plt.rcParams['axes.unicode_minus'] = False
cells = pd.read_csv(case/'results/cell_clusters.tsv', sep='\t')
assert cells.shape[0] == 1882 and cells.cell_id.is_unique and cells.reference.notna().all()
clusters = sorted(cells.cluster.unique())
references = sorted(cells.reference.unique())
counts = pd.crosstab(cells.cluster, cells.reference).reindex(index=clusters, columns=references, fill_value=0)
assert counts.shape == (7, 8) and counts.to_numpy().sum() == 1882
row = counts.div(counts.sum(axis=1), axis=0)
column = counts.div(counts.sum(axis=0), axis=1)
assert np.allclose(row.sum(axis=1), 1) and np.allclose(column.sum(axis=0), 1)
for name,frame in [('counts_7x8',counts),('fraction_within_cluster',row),('fraction_within_reference',column)]:
    frame.to_csv(review/'tables'/f'{name}.tsv', sep='\t', index_label='cluster')
long = counts.stack().rename('count').reset_index()
long['fraction_within_cluster'] = [row.loc[c,r] for c,r in zip(long.cluster,long.reference)]
long['fraction_within_reference'] = [column.loc[c,r] for c,r in zip(long.cluster,long.reference)]
long.to_csv(review/'tables/counts_and_fractions_long.tsv',sep='\t',index=False)
cluster_summary = []
for cluster,values in counts.iterrows():
    ranked = values[values>0].sort_values(ascending=False)
    cluster_summary.append({'cluster':cluster,'cells':int(values.sum()),'dominant_reference':ranked.index[0],
      'dominant_count':int(ranked.iloc[0]),'dominant_fraction':float(ranked.iloc[0]/values.sum()),
      'observed_reference_classes':int((values>0).sum()),
      'composition':'; '.join(f'{label}: {n} ({n/values.sum():.2%})' for label,n in ranked.items())})
pd.DataFrame(cluster_summary).to_csv(review/'tables/cluster_composition.tsv',sep='\t',index=False)
reference_summary = []
for reference,values in counts.items():
    ranked = values[values>0].sort_values(ascending=False)
    reference_summary.append({'reference':reference,'cells':int(values.sum()),'observed_clusters':int((values>0).sum()),
      'dominant_cluster':ranked.index[0],'dominant_count':int(ranked.iloc[0]),
      'dominant_fraction':float(ranked.iloc[0]/values.sum()),
      'allocation':'; '.join(f'{cluster}: {n} ({n/values.sum():.2%})' for cluster,n in ranked.items())})
pd.DataFrame(reference_summary).to_csv(review/'tables/reference_distribution.tsv',sep='\t',index=False)
for name,frame,title,meaning in [
 ('within_cluster',row,'按簇归一化：每一行之和为 100%','P(参考类别 | 簇)；格内为比例及计数'),
 ('within_reference',column,'按参考类别归一化：每一列之和为 100%','P(簇 | 参考类别)；格内为比例及计数')]:
    fig,ax=plt.subplots(figsize=(14,7.8))
    annot=np.array([[f'{frame.loc[c,r]*100:.1f}%\n(n={counts.loc[c,r]})' for r in references] for c in clusters])
    sns.heatmap(frame,annot=annot,fmt='',vmin=0,vmax=1,cmap='Blues',linewidths=.6,linecolor='#e5e7eb',
                cbar_kws={'label':'比例'},annot_kws={'fontsize':9},ax=ax)
    ax.set_xticklabels(['\n'.join(textwrap.wrap(r,23)) for r in references],rotation=0,fontsize=9)
    ax.set_yticklabels([f'{c} (n={counts.loc[c].sum()})' for c in clusters],rotation=0,fontsize=10)
    ax.set_xlabel('原始 cell_ontology_class（仅用于事后对照）',labelpad=14)
    ax.set_ylabel('冻结的 CAdir 分配')
    ax.set_title(title+'\n'+meaning,pad=16,fontsize=14)
    fig.tight_layout()
    fig.savefig(review/'figures'/f'confusion_{name}.png',dpi=180,facecolor='white')
    fig.savefig(review/'figures'/f'confusion_{name}.pdf',facecolor='white')
    plt.close(fig)
(review/'tables/cluster_review_checks.json').write_text(json.dumps({
 'status':'PASS','counts_shape':[7,8],'total_cells':1882,'rows_sum_to_one':True,'columns_sum_to_one':True,
 'reference_use':'Post hoc description only; no reclustering or prediction renaming.',
 'baseline_cells_sha256_source':'freeze/baseline_manifest.json'},indent=2)+'\n')
print(pd.DataFrame(cluster_summary).to_string(index=False))
print(pd.DataFrame(reference_summary).to_string(index=False))
