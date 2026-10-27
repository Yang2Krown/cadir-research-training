#!/usr/bin/env python3
"""Display the accepted 7x7 angle table with type sized for a journal page."""
from pathlib import Path
import os
import hashlib
import json
os.environ.setdefault('MPLCONFIGDIR', '/tmp/cjc-history-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[1]
record = json.loads((root/'evidence/angle-data-source.json').read_text())
source = root/record['file']
assert hashlib.sha256(source.read_bytes()).hexdigest() == record['sha256']
table = pd.read_csv(source, sep='\t', index_col=0)
assert table.shape == (7,7) and table.index.tolist() == table.columns.tolist()
values = table.to_numpy()
assert np.isfinite(values).all() and np.allclose(values, values.T, atol=1e-10)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
fig,ax=plt.subplots(figsize=(3.5,2.6),layout='constrained')
im=ax.imshow(values,vmin=0,vmax=130,cmap='YlOrBr')
labels=['C'+str(i) for i in range(1,8)]
ax.set_xticks(range(7),labels);ax.set_yticks(range(7),labels)
ax.tick_params(length=0,pad=3)
for i in range(7):
    for j in range(7):
        ax.text(j,i,f'{values[i,j]:.1f}',ha='center',va='center',fontsize=7.2,
                color='white' if values[i,j]>85 else '#282828')
bar=fig.colorbar(im,ax=ax,fraction=.045,pad=.035)
bar.set_label('Angle (degrees)',fontsize=8);bar.ax.tick_params(labelsize=7)
path=root/'layout/figures/S1A_angles_readable.pdf'
fig.savefig(path,metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
record.update(display=str(path.relative_to(root)),display_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              operation='Display only; no angles recalculated',display_precision='One decimal place')
(root/'evidence/angle-readable.json').write_text(json.dumps(record,indent=2)+'\n')
