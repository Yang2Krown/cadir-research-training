#!/usr/bin/env python3
"""Render frozen, accepted history coordinates at a readable publication size.

No correspondence analysis, membership inference or clustering is performed.
"""
from pathlib import Path
import gzip
import hashlib
import json
import os
import textwrap

os.environ.setdefault('MPLCONFIGDIR', '/tmp/cjc-history-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import MaxNLocator, FixedLocator
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'layout/figures'
STAGES = ['iter_0', 'merge_iter_1', 'split_iter_2']
NAMES = ['Initial', 'After merging', 'After splitting']


def main():
    sources = json.loads((ROOT / 'evidence/history-data-sources.json').read_text())
    for item in sources:
        raw = (ROOT / item['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item['gzip_sha256']
        assert hashlib.sha256(gzip.decompress(raw)).hexdigest() == item['source_sha256']

    def read(name):
        return pd.read_csv(ROOT / 'evidence/history-data' / (name + '.tsv.gz'), sep='\t')

    annotations = read('Fig3D_node_annotations')
    edges = read('Fig3D_history_edges')
    coords = read('Fig3D_all_node_APL_coordinates')
    membership = read('Fig3D_all_node_cell_membership')
    keys = ['node', 'cell_id']
    assert not coords.duplicated(keys).any() and not membership.duplicated(keys).any()
    data = coords.merge(membership, on=keys, how='outer', validate='one_to_one', indicator=True)
    assert data['_merge'].eq('both').all()
    assert len(data) == 39522 and len(annotations) == 21 and len(edges) == 23
    assert np.isfinite(data[['x', 'y']].to_numpy()).all()
    ids = set(data.cell_id)
    assert len(ids) == 1882
    for node, d in data.groupby('node'):
        assert len(d) == 1882 and set(d.cell_id) == ids
        assert int(d.in_cluster.sum()) == int(annotations.set_index('node').loc[node, 'ncells'])
    for stage in STAGES:
        assert annotations.loc[annotations.iteration.eq(stage), 'ncells'].sum() == 1882
        stage_nodes = annotations.loc[annotations.iteration.eq(stage), 'node']
        assert data.loc[data.node.isin(stage_nodes)].groupby('cell_id').in_cluster.sum().eq(1).all()
    node_set = set(annotations.node) | {'root-0'}
    assert set(edges['from']) | set(edges['to']) == node_set and len(node_set) == 22

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.titlesize': 9, 'axes.labelsize': 8,
                         'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
                         'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    info = annotations.set_index('node')
    groups = {node: d for node, d in data.groupby('node')}
    outputs = []
    OUT.mkdir(parents=True, exist_ok=True)

    def panel(ax, node, title):
        d = groups[node]
        inside = d.in_cluster.to_numpy()
        ax.scatter(d.x[~inside], d.y[~inside], c='#1b514d', s=3, alpha=.62,
                   linewidths=0, rasterized=True)
        ax.scatter(d.x[inside], d.y[inside], c='#9ae43c', s=6, alpha=.95,
                   linewidths=.12, edgecolors='#507d17', rasterized=True)
        ax.set_title(title, pad=6, linespacing=1.25)
        ax.set_xlabel('Association strength')
        ax.set_ylabel('Distance')
        ax.set_aspect('equal', adjustable='box')
        ax.margins(.04)
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(length=2.5, pad=2)
        # Two well-spaced labels remain readable for narrow, equal-aspect axes.
        xmin, xmax = ax.get_xlim()
        ticks = MaxNLocator(nbins=2).tick_values(xmin, xmax)
        ticks = ticks[(ticks >= xmin) & (ticks <= xmax)]
        if len(ticks) > 2:
            ticks = ticks[[0, -1]]
        ax.xaxis.set_major_locator(FixedLocator(ticks))

    def save(fig, name, nodes):
        path = OUT / name
        fig.savefig(path, dpi=240, metadata={'Creator': 'Frozen history display renderer',
                                            'CreationDate': None, 'ModDate': None})
        plt.close(fig)
        raw = path.read_bytes()
        outputs.append(dict(file=str(path.relative_to(ROOT)), bytes=len(raw),
                            sha256=hashlib.sha256(raw).hexdigest(), nodes=nodes))

    # Place all actual nodes and edges; only the visual arrangement is changed.
    row_maps = [{1: 0, 4: 1, 2: 2, 7: 3, 3: 4, 5: 5, 6: 6, 8: 7},
                {1: .5, 2: 2.5, 3: 4, 4: 5, 5: 6, 6: 7},
                {1: .5, 2: 2, 7: 3, 3: 4, 4: 5, 5: 6, 6: 7}]
    positions = {'root-0': (0, 3.5)}
    for k, stage in enumerate(STAGES):
        for c, row in row_maps[k].items():
            positions[f'{stage}-cluster_{c}'] = (1 + k * 1.32, row)
    fig = plt.figure(figsize=(6.8, 6.3), layout='constrained')
    grid = fig.add_gridspec(2, 3, height_ratios=[1.35, 1])
    ax = fig.add_subplot(grid[0, :])
    for a, b in edges.itertuples(index=False, name=None):
        x, y = positions[a]; xx, yy = positions[b]
        ax.add_patch(FancyArrowPatch((x + (.25 if a == 'root-0' else .36), y),
                                    (xx - .36, yy), arrowstyle='-|>',
                                    mutation_scale=8, linewidth=.85, color='#77899a', zorder=1))
    for node, (x, y) in positions.items():
        if node == 'root-0':
            label, color, width = 'Input\nn=1882', '#edf2f7', .56
        else:
            c = node.rsplit('_', 1)[1]
            label = f'C{c}   n={int(info.loc[node, "ncells"])}'
            color = '#e5f2ff' if node.startswith('iter_0') else '#e6f4ec'
            width = .78
        height = .76 if node == 'root-0' else .46
        ax.add_patch(FancyBboxPatch((x-width/2, y-height/2), width, height,
                                   boxstyle='round,pad=0.02,rounding_size=0.06',
                                   facecolor=color, edgecolor='#526a7f', linewidth=.7, zorder=2))
        ax.text(x, y, label, ha='center', va='center', fontsize=8.5, zorder=3)
    ax.text(0, -1.0, '(a) Full history: 22 nodes, 23 edges', weight='bold', fontsize=9)
    for k, title in enumerate(NAMES):
        ax.text(1+k*1.32, -.6, title, ha='center', fontsize=9, weight='bold')
    ax.set_xlim(-.40, 4.18); ax.set_ylim(7.5, -1.25); ax.axis('off')
    chosen = ['merge_iter_1-cluster_2', 'split_iter_2-cluster_2', 'split_iter_2-cluster_7']
    for k, node in enumerate(chosen):
        phase = 'Merged' if k == 0 else 'Split'
        c = node.rsplit('_', 1)[1]
        panel(fig.add_subplot(grid[1, k]), node,
              f'({chr(98+k)}) {phase} C{c}  (n={int(info.loc[node, "ncells"])})')
    save(fig, 'Fig3D_history_readable.pdf', list(positions))

    # Preserve every historical name in enlarged stage panels in the appendix.
    for stage, name in zip(STAGES, ['initial', 'merge', 'split']):
        records = annotations[annotations.iteration.eq(stage)]
        rows = (len(records) + 1) // 2
        fig, axes = plt.subplots(rows, 2, figsize=(6.8, rows * 2.05 + .25),
                                 layout='constrained')
        for ax, row in zip(axes.flat, records.itertuples()):
            label = row.automatic_annotation.replace('_', ' ')
            wrapped = '\n'.join(textwrap.wrap(label, width=37))
            c = row.cluster_id.rsplit('_', 1)[1]
            panel(ax, row.node, f'C{c}  (n={row.ncells})\n{wrapped}')
        for ax in list(axes.flat)[len(records):]:
            ax.axis('off')
        save(fig, f'history_{name}_panels.pdf', records.node.tolist())

    result = dict(source_commit='ab68da7ef154f133ec436275fcf11396f37f884a',
                  action='Display-only rendering of frozen APL coordinates and membership',
                  coordinate_rows=len(data), cells_per_node=1882, history_nodes=22,
                  history_edges=23, stage_clusters=[8, 6, 7], stage_cells=[1882]*3,
                  member_counts=annotations.set_index('node').ncells.to_dict(),
                  equal_aspect=True, outputs=outputs)
    (ROOT / 'evidence/history-readable.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['member_counts', 'outputs']}))


if __name__ == '__main__':
    main()
