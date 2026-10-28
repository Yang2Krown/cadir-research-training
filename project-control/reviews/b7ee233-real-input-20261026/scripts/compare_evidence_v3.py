#!/usr/bin/env python3
"""Independent comparison of independently computed evidence and fresh original runs."""
import csv, hashlib, json, pathlib
B=pathlib.Path(__file__).resolve().parents[1]; O=B/'execution-attempt-02'; A=B/'execution-attempt-01'; I=A/'independent-oracle/results'; N=O/'real-metadata-negatives/results'
rows=[]
def ck(name,a,b): rows.append({'check':name,'independent_or_expected':json.dumps(a,ensure_ascii=False,sort_keys=True),'original_or_actual':json.dumps(b,ensure_ascii=False,sort_keys=True),'pass':a==b})
def j(p):return json.loads(p.read_text())
def t(p):
 with p.open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
pre=j(O/'before.json');post=j(O/'after.json');ck('attempt02 input and source hashes unchanged',pre,post);ck('attempt01 input and source hashes unchanged',j(A/'before.json'),j(A/'after.json'));ck('inputs same between attempts',j(A/'after.json')['inputs'],pre['inputs'])
ck('reviewer direct input hashes match runner',j(B/'reviewer_direct_preflight.json')['files'],pre['inputs'])
ck('all four runner commands exit zero',[0,0,0,0],[j(A/'commands.json')[0]['exit_code']]+[x['exit_code'] for x in j(O/'commands.json')])
ck('independent oracle PASS','PASS',j(I/'independent_status.json')['status']);ck('real metadata negatives PASS','PASS',j(N/'negative_status.json')['status'])
ind=j(I/'independent_counts_geo.json');md=j(I/'independent_metadata.json')
for mode in ['metadata-only','full']:
 d=O/('original-'+mode);s=j(d/'audit_status.json');rec=j(O/('original-'+mode+'.execution.json'))
 ck(mode+' original exit',0,rec['exit_code']);ck(mode+' formal execution prohibited',False,s['formal_execution_permitted']);ck(mode+' counts read flag',mode=='full',s['counts_rds_read'])
 ck(mode+' exact image',j(O/'provenance.json')['image_id'],rec['image_id'])
 for n,h in rec['source_sha256'].items():ck(mode+' executed source '+n,pre['sources']['cases/nestorowa_hsc/scripts/'+n],h)
 mount_sources=[a for a in rec['command'] if a.startswith('type=bind,src=')]
 if mode=='metadata-only':ck('metadata-only no raw count/GEO mounts',False,any('/reacquired-20261026/counts.rds' in a or '/reacquired-20261026/GSE81682_HTSeq_counts.txt.gz' in a for a in mount_sources))
 ck(mode+' candidate cell IDs and labels',[(r['cell_id'],r['candidate_label']) for r in t(I/'independent_candidate.tsv')],[(r['cell_id'],r['candidate_label']) for r in t(d/'metadata_candidate.tsv')])
 mm=j(d/'metadata_identity.json');ck(mode+' raw NULL symbol',md['raw_symbol'],mm['raw_top_level_rownames_encoding']['symbol']);ck(mode+' semantic NULL',True,mm['raw_top_level_rownames_is_null']);ck(mode+' unassigned',md['unassigned'],mm['broad_unassigned'])
 for field in ['cell.type','diffusion','FACS']:
  for key1,key2 in [('dimensions','dimensions'),('columns','columns'),('NA_entries','missing_entries'),('NA_by_column','missing_by_column'),('all_NA_rows','all_missing_rows')]:ck(mode+' '+field+' '+key1,md['fields'][field][key1],mm['fields'][field][key2])
 counts={r['field']:int(r['members']) for r in t(I/'membership_counts.tsv')}
 original=t(d/'metadata_memberships.tsv');ck(mode+' all 23 membership totals',counts,{k:sum(1 if r[k]=='TRUE' else 0 if r[k]=='FALSE' else int(r[k]) for r in original) for k in counts})
 if mode=='full':
  c=j(d/'counts_legality.json');g=j(d/'geo_correspondence.json')
  for key in ['class','dimensions']:
   av=ind[key];bv=c[key];ck('full count '+key,av if isinstance(av,list) else [av],bv if isinstance(bv,list) else [bv])
  ck('full stored values',ind['stored_values'],c['statistics']['stored_values'])
  ck('full all values compared',ind['values_compared'],g['values_compared']);ck('full numeric differences',ind['numeric_differences'],g['numeric_mismatches'])
  ck('full all gene ID ordering',[r['gene_id'] for r in t(I/'independent_gene_ids.tsv')],[r['gene_id'] for r in t(d/'gene_ids.tsv')])
  ck('full all cell ID alignment',[(r['cell_id'],r['metadata_row']) for r in t(I/'independent_cell_alignment.tsv')],[(r['cell_id'],r['metadata_canonical_row']) for r in t(d/'count_metadata_alignment.tsv')])
# Large arrays do not need to be duplicated into the summary table; their artifact hashes remain indexed.
with (B/'difference_table.tsv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['check','independent_or_expected','original_or_actual','pass'],delimiter='\t');w.writeheader()
 for r in rows:
  for k in ['independent_or_expected','original_or_actual']:
   if len(r[k])>500:r[k]='sha256:'+hashlib.sha256(r[k].encode()).hexdigest()
  w.writerow(r)
(B/'comparison_status.json').write_text(json.dumps({'checks':len(rows),'passes':sum(r['pass'] for r in rows),'all_pass':all(r['pass'] for r in rows),'comparison_script_independently_authored':True},indent=2)+'\n')
print(json.dumps({'checks':len(rows),'passes':sum(r['pass'] for r in rows),'failures':[r['check'] for r in rows if not r['pass']]}))
raise SystemExit(0 if all(r['pass'] for r in rows) else 1)
