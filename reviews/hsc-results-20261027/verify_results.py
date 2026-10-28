#!/usr/bin/env python3
"""Independent standard-library verification. Does not import implementation code."""
import csv,json,math,hashlib,subprocess,statistics,collections,datetime
from pathlib import Path
repo=Path('/workspace/hsc-results-independent-review'); base=repo/'cases/nestorowa_hsc/fair-experiment'
archive=base/'results/6cc7b3d-20261027-attempt-01'; formal=Path('/workspace/hsc-fair-experiment-data-20261026/formal/6cc7b3d-20261027-attempt-01');stage=Path('/workspace/hsc-fair-experiment-data-20261026/stage1/attempt-01');out=repo/'reviews/hsc-results-20261027'
checks=[];inputs={}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
 return h.hexdigest()
def ck(name,ok,detail=''):
 checks.append(dict(check=name,passed=bool(ok),detail=str(detail)))
 if not ok: raise AssertionError(name+': '+str(detail))
def js(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
def tab(p):inputs[str(p)]=sha(p);return list(csv.DictReader(p.open(),delimiter='\t'))
def lines(p): inputs[str(p)]=sha(p);return p.read_text().splitlines()
def close(a,b,tol=1e-12): return abs(float(a)-float(b))<=tol
commit='091a8a4585cabc59a5504380398892bac49044f4';source='6cc7b3da67c193da11a67c45a75167d6521438b0'
ck('result_commit_ancestor',subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',commit,'HEAD']).returncode==0)
ck('result_tree_unchanged',subprocess.run(['git','-C',str(repo),'diff','--quiet',commit,'--','cases/nestorowa_hsc/fair-experiment']).returncode==0)
a=js(archive/'design-admission/admission.json'); used=js(formal/'admission-used.json');execution=js(archive/'terminal-capture/coordinator-execution.json')
ck('admission_copy_semantically_identical',a==used)
ck('admission_original_SHA',sha(archive/'design-admission/admission.json')=='5c0834c3150129980c1c372b9593be43e489a2ed42f9e9667abf131ebf4e1d0a')
ck('admission_precedes_formal_execution',datetime.datetime.fromisoformat(a['signed_at_utc'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(execution['started_utc']))
ck('admitted_source_commit',a['source_commit']==source==execution['source_commit'])
for rel,key in [('locks/source-manifest.json','source_manifest_sha256'),('locks/data-input-lock.json','data_lock_sha256'),('design/scientific-config.json','scientific_config_sha256'),('locks/runtime-library-lock.json','runtime_library_lock_sha256')]:ck('binding_'+key,sha(base/rel)==a[key])
manifest=js(base/'locks/source-manifest.json');lock=js(base/'locks/data-input-lock.json');cfg=js(base/'design/scientific-config.json')
for e in manifest['files']:
 p=repo/e['path'];blob=subprocess.check_output(['git','-C',str(repo),'show',source+':'+e['path']]);ck('source_blob_'+e['path'],p.stat().st_size==e['bytes'] and sha(p)==e['sha256']==hashlib.sha256(blob).hexdigest())
for e in lock['files']:
 p=Path(e['path']);ck('data_'+str(p),p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
ck('env_signature_binding',sha(Path(lock['environment_signature_path']))==a['environment_signature_sha256'])
lib=js(base/'locks/runtime-library-lock.json');lr=Path(lib['library_root']);actual={str(p.relative_to(lr)) for p in lr.rglob('*') if p.is_file() and (p.suffix in ['.so','.rdb','.rdx'] or p.name in ['DESCRIPTION','NAMESPACE'])}
ck('runtime_library_file_set',actual=={e['path'] for e in lib['files']})
for e in lib['files']:
 p=lr/e['path'];ck('runtime_'+e['path'],p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
for doc in Path('/workspace/hsc-fair-experiment-handoff-20261026').glob('*'):
 if doc.is_file(): inputs[str(doc)]=sha(doc)
for label,entries,mode in [('archive',js(archive/'archive-copy-sha256.json')['files'],'archive'),('external',js(archive/'external-artifacts-sha256.json')['files'],'absolute'),('large_objects',js(archive/'large-objects-export-manifest.json')['files'],'absolute')]:
 for e in entries:
  p=repo/e['archive_path'] if mode=='archive' else Path(e['path']);ck(label+'_'+str(p),p.stat().st_size==e['bytes'] and sha(p)==e['sha256'])
  if mode=='archive':ck('archive_source_'+str(p),sha(Path(e['source_path']))==e['sha256'])
cells=lines(stage/'final-cell-ids.txt');ev=lines(stage/'evaluation-cell-ids.txt');genes=lines(stage/'hvg-gene-ids.txt');ref=tab(stage/'frozen-reference.tsv');rd={x['cell_id']:x for x in ref}
ck('unique_fixed_ID_sets',len(cells)==len(set(cells))==1656 and len(ev)==len(set(ev))==1641 and len(genes)==len(set(genes))==6000 and len(rd)==len(ref)==1920)
ck('reference_explicit_ID_intersection',ev==[x['cell_id'] for x in ref if x['evaluated']=='TRUE'] and set(ev)=={x for x in cells if rd[x]['label']!='NA'})
counts=collections.Counter(rd[x]['label'] for x in ev);ck('six_reference_classes',counts=={'LTHSC':287,'LMPP':246,'MPP':326,'CMP':310,'MEP':354,'GMP':118},dict(counts))
ck('missing_15_retained_no_imputation',len(set(cells)-set(ev))==15 and all(rd[x]['label']=='NA' and rd[x]['label_reason']=='no_broad_membership' for x in set(cells)-set(ev)))
receipts=js(formal/'attempt-receipts.json');ck('exact_ten_attempts',[(r['seed'],r['method']) for r in receipts]==[(s,m) for s in cfg['seeds'] for m in ['cadir','pca_snn_louvain']])
ck('all_attempts_success',all(r['exit_code']==0 and r['success'] for r in receipts) and [r.get('diagnostic_exit_code') for r in receipts if r['method']=='cadir']==[0]*5)
terminal=(archive/'terminal-capture/terminal.typescript').read_text();events=[]
for line in terminal.splitlines():
 try:
  obj=json.loads(line)
  if 'event' in obj:events.append(obj)
 except (json.JSONDecodeError,TypeError):pass
ck('real_terminal_ten_starts_ten_core_five_diagnostics',collections.Counter(x['event'] for x in events)=={'METHOD_SEED_START':10,'METHOD_SEED_EXIT':10,'DIAGNOSTIC_EXIT':5})
ck('real_terminal_exit_codes',all(x['exit_code']==0 for x in events if 'exit_code' in x) and execution['exit_code']==0)
alltab={(x['method'],int(x['seed'])):x for x in tab(formal/'all-seed-results.tsv')};ptab={(x['method'],int(x['seed'])):x for x in tab(archive/'presentation/all-seed-presented-values.tsv')};resources={(x['method'],int(x['seed'])):x for x in tab(archive/'presentation/resource-scopes.tsv')};computed=[];cont_all=[]
choose2=lambda x:x*(x-1)/2
for rec in receipts:
 method=rec['method'];seed=rec['seed'];key=(method,seed);tag=f'{method}_{seed}';p=Path(rec['attempt_directory'])
 part=tab(p/'cell-partition.tsv');pred={x['cell_id']:x['cluster'] for x in part}
 ck(tag+'_prediction_complete_unique',len(pred)==len(part)==1656 and set(pred)==set(cells) and all(x not in ('','NA') for x in pred.values()))
 # Deliberately align by explicit IDs even if table order changes.
 pairs=collections.Counter((pred[x],rd[x]['label']) for x in ev);pc=collections.Counter(pred[x] for x in ev);rc=collections.Counter(rd[x]['label'] for x in ev);n=len(ev)
 s2=sum(choose2(v) for v in pairs.values());a2=sum(choose2(v) for v in pc.values());b2=sum(choose2(v) for v in rc.values());expected=a2*b2/choose2(n);ari=(s2-expected)/((a2+b2)/2-expected)
 hp=-sum(v/n*math.log(v/n) for v in pc.values());hr=-sum(v/n*math.log(v/n) for v in rc.values());mi=sum(v/n*math.log(v*n/(pc[c]*rc[r])) for (c,r),v in pairs.items());nmi=mi/max(hp,hr)
 metrics=dict(ARI=ari,NMI_max_entropy=nmi,MI=mi,H_predicted=hp,H_reference=hr);saved=js(p/'metrics.json');at=alltab[key];presentation=ptab[key]
 for name,value in metrics.items():ck(tag+'_'+name,close(value,saved[name]) and close(value,at[name]),value)
 for name in ['ARI','NMI_max_entropy']:ck(tag+'_presented_'+name,close(metrics[name],presentation[name]))
 nk=len(set(pred.values()));ck(tag+'_cluster_count',nk==saved['inferred_clusters']==int(at['inferred_clusters'])==int(presentation['inferred_clusters']))
 ck(tag+'_denominators',all(int(at[k])==v for k,v in [('success_denominator',5),('n_total',1656),('n_evaluated',1641),('n_excluded',15)]))
 ct=tab(p/'evaluation-contingency.tsv');observed={(x['predicted'],x['reference']):int(x['Freq']) for x in ct};ck(tag+'_full_contingency',len(ct)==nk*6 and observed=={(c,r):pairs[c,r] for c in set(pred.values()) for r in counts})
 sizes=tab(p/'cluster-sizes.tsv');ck(tag+'_all_cell_cluster_sizes',{x['cluster']:int(x['Freq']) for x in sizes}==dict(collections.Counter(pred.values())))
 status=js(p/'run-status.json');ck(tag+'_run_status',status['status']=='FORMAL_CORE_COMPLETE' and status['method']==method and status['seed']==seed)
 core=js(p/'core-resources.json');rss=[int(x) for x in lines(p/'core-rss-KiB.txt')];ck(tag+'_measured_rss',max(rss)==core['sampled_peak_rss_KiB'] and len(rss)==core['rss_samples'])
 for name in ['core_elapsed_seconds','sampled_peak_rss_KiB']:ck(tag+'_resource_'+name,close(core[name],at[name]))
 ck(tag+'_resource_presentation',close(core['core_elapsed_seconds'],resources[key]['core_elapsed_seconds']) and close(core['sampled_peak_rss_KiB']/1024**2,resources[key]['sampled_peak_rss_GiB']))
 for e in js(p/'core-artifacts-sha256.json')['files']:ck(tag+'_core_unchanged_'+e['path'],sha(p/e['path'])==e['sha256'])
 computed.append(dict(method=method,seed=seed,n_total=1656,n_evaluated=1641,n_excluded=15,inferred_clusters=nk,**metrics,core_elapsed_seconds=core['core_elapsed_seconds'],sampled_peak_rss_KiB=core['sampled_peak_rss_KiB']))
 cont_all.extend(dict(method=method,seed=seed,predicted=c,reference=r,Freq=pairs[c,r]) for c in sorted(set(pred.values())) for r in sorted(counts))
 if seed==2358:
  pct=tab(archive/f'presentation/02-{method}-seed2358-contingency.tsv');ck(tag+'_presentation_contingency',len(pct)==nk*6 and all(int(x['Freq'])==pairs[x['predicted'],x['reference']] and close(x['share_within_reference'],pairs[x['predicted'],x['reference']]/counts[x['reference']]) for x in pct))
 if method=='cadir':
  gp=tab(p/'gene-partition.tsv');assigned={x['gene_id']:x['cluster'] for x in gp if x['assigned']=='TRUE'};excluded=tab(p/'gene-exclusions.tsv');ranks=tab(p/'diagnostics/complete-assigned-gene-ranks.tsv');geom={x['gene_id']:x for x in tab(p/'diagnostics/ranking-geometry.tsv')};prov=js(p/'diagnostics/ranking-provenance.json')
  ck(tag+'_6000_gene_partition',len(gp)==6000 and [x['gene_id'] for x in gp]==genes and len(assigned)==1200)
  ck(tag+'_4800_explicit_exclusions',len(excluded)==4800 and {x['gene_id'] for x in excluded}==set(genes)-set(assigned) and all(x['reason']=='excluded_by_upstream_ca_sphere_qcutoff' and x['cluster']=='NA' for x in excluded) and set(lines(p/'unassigned-gene-ids.txt'))==set(genes)-set(assigned))
  ck(tag+'_actual_subset_rank_coverage',len(ranks)==len({x['Rowname'] for x in ranks})==1200 and {x['Rowname'] for x in ranks}==set(assigned) and all(x['Cluster']==assigned[x['Rowname']] for x in ranks))
  err=max(abs(float(geom[x['Rowname']]['x'])-prov['alpha_genes']*float(geom[x['Rowname']]['y'])-float(x['Score'])) for x in ranks);ck(tag+'_saved_geometry_score',err<1e-10,err)
  ck(tag+'_diagnostic_protected_objects',sha(p/'ca.rds')==prov['CA_sha256'] and sha(p/'cadir_unranked.rds')==prov['unranked_sha256'] and js(p/'diagnostics/diagnostic-status.json')['status']=='DIAGNOSTICS_COMPLETE_EXACT_STORED_CA')
summary=[]
for old in js(formal/'summary.json'):
 m=old['method'];rows=[x for x in computed if x['method']==m];ck(m+'_success_denominator5',len(rows)==old['successes']==old['denominator']==5)
 new=dict(method=m,successes=5,denominator=5)
 for metric in ['ARI','NMI_max_entropy','inferred_clusters','core_elapsed_seconds','sampled_peak_rss_KiB']:
  values=sorted(x[metric] for x in rows);new[metric]=dict(n=5,median=values[2],IQR=values[3]-values[1],min=values[0],max=values[4])
  for k,v in new[metric].items():ck(m+'_summary_'+metric+'_'+k,close(v,old[metric][k]))
 summary.append(new)
# Verify QC presentation against already accepted frozen QC tables; no raw re-QC.
qc={x['cell_id']:x for x in tab(stage/'cell-qc.tsv')};qplot=tab(archive/'presentation/QC-plotted-values.tsv');ck('QC_plot_all_1920_three_metrics',len(qplot)==5760)
for x in qplot:
 q=qc[x['cell_id']];value={'log2 endogenous read count':math.log2(float(q['endogenous_total'])),'log2 detected endogenous genes':math.log2(float(q['endogenous_detected_genes'])),'ERCC percent':float(q['ERCC_percent'])}[x['metric']]
 ck('QC_plot_'+x['cell_id']+'_'+x['metric'],close(value,x['value']) and x['decision']==('Retained' if q['retained']=='TRUE' else 'Excluded'))
cutoffs=js(stage/'qc-thresholds.json');cohort=tab(archive/'presentation/cohort-summary.tsv')[0];ck('cohort_presentation',cohort==dict(candidate_cells='1920',QC_retained='1656',QC_excluded='264',evaluation_cells='1641',QC_retained_unassigned='15',eligible_genes='40721',shared_HVG='6000'))
def write_rows(name,rows):
 with (out/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
write_rows('independently-recomputed-metrics.tsv',computed);write_rows('independent-contingencies.tsv',cont_all);write_rows('host-checks.tsv',checks)
(out/'independent-summary.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'reviewed-input-sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
result=dict(status='PASS_INDEPENDENT_HOST_RECOMPUTATION',result_commit=commit,source_commit=source,checks=len(checks),max_ARI_difference=max(abs(x['ARI']-float(alltab[x['method'],x['seed']]['ARI'])) for x in computed),max_NMI_difference=max(abs(x['NMI_max_entropy']-float(alltab[x['method'],x['seed']]['NMI_max_entropy'])) for x in computed),source_files=len(manifest['files']),data_files=len(lock['files']),runtime_files=len(lib['files']),raw_full_GEO_comparison_repeated=False)
(out/'host-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
