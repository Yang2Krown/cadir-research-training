#!/usr/bin/env python3
"""Summarize all predeclared seeds, retaining failures and denominator=5."""
import csv,json,pathlib,statistics,sys
out=pathlib.Path(sys.argv[1]);receipts=json.loads((out/'attempt-receipts.json').read_text());rows=[]
for method in ['cadir','pca_snn_louvain']:
 for seed in [2358,101,202,303,404]:
  found=[r for r in receipts if r['method']==method and r['seed']==seed]
  row={'method':method,'seed':seed,'status':'NOT_ATTEMPTED','success_denominator':5}
  if found:
   r=found[0];p=pathlib.Path(r['attempt_directory']);row.update(exit_code=r['exit_code'],status='FAILED' if r['exit_code'] else 'COMPLETE',diagnostic_exit_code=r.get('diagnostic_exit_code','NA'))
   for name in ['metrics.json','core-resources.json']:
    if (p/name).exists():row.update(json.loads((p/name).read_text()))
  rows.append(row)
fields=list(dict.fromkeys(k for row in rows for k in row))
with open(out/'all-seed-results.tsv','w') as f:
 w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
summary=[]
for method in ['cadir','pca_snn_louvain']:
 valid=[r for r in rows if r['method']==method and r.get('exit_code')==0]
 s={'method':method,'successes':len(valid),'denominator':5,'seed_repeats_are_biological_replicates':False}
 for k in ['ARI','NMI_max_entropy','inferred_clusters','core_elapsed_seconds','sampled_peak_rss_KiB']:
  x=[r[k] for r in valid if isinstance(r.get(k),(int,float))]
  if x:
   # R type-7 quantile convention, also for n<4 successes.
   def q(p):
    y=sorted(x);v=(len(y)-1)*p;i=int(v);return y[i]+(y[min(i+1,len(y)-1)]-y[i])*(v-i)
   s[k]={'n':len(x),'median':statistics.median(x),'IQR':q(.75)-q(.25),'min':min(x),'max':max(x)}
 summary.append(s)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
