#!/usr/bin/env python3
# Host-only independent structural/numeric lexical check. No RDS equivalence claim.
import gzip,json,re,time
from pathlib import Path
p=Path('/workspace/nestorowa-metadata-preparation/reacquired-20261026/GSE81682_HTSeq_counts.txt.gz');b=Path(__file__).resolve().parents[1];start=time.time()
with gzip.open(p,'rb') as f:
 sample=[v.strip(b'"').decode() for v in f.readline().rstrip(b'\r\n').split(b'\t')]
 first=f.readline().rstrip(b'\r\n').split(b'\t');n=len(first)-1
 if len(sample)==n+1:sample=sample[1:]
 assert len(sample)==n and len(set(sample))==n and all(sample)
 seen=set();count=0;valid=re.compile(rb'(?:0|[1-9][0-9]*)(?:\t(?:0|[1-9][0-9]*))*\Z')
 def consume(parts):
  global count
  gene=parts[0].strip(b'"');assert gene and gene not in seen;seen.add(gene)
  assert len(parts)==n+1 and valid.fullmatch(b'\t'.join(parts[1:]));count+=n
 consume(first)
 for line in f:consume(line.rstrip(b'\r\n').split(b'\t'))
r={'reviewer_direct_host_read':True,'file':str(p),'explicit_GEO_cells':n,'unique_explicit_GEO_genes':len(seen),'all_values_lexically_nonnegative_integers':True,'values_checked':count,'RDS_correspondence':'await independent R oracle; host lexical check does not substitute','elapsed_seconds':time.time()-start}
output=b/'reviewer_direct_GEO_lexical_check_rerunnable.json'
with output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
