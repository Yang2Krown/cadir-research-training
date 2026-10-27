#!/usr/bin/env python3
import json,hashlib,csv,struct
from pathlib import Path
repo=Path('/workspace/hsc-results-independent-review');base=repo/'cases/nestorowa_hsc/fair-experiment';r=base/'results/6cc7b3d-20261027-attempt-01';out=repo/'reviews/hsc-results-20261027'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,ok):
 assert ok,name
 checks.append({'check':name,'passed':True})
authroot=Path('/workspace/hsc-fair-experiment-handoff-20261026');auth=json.loads((authroot/'authority.json').read_text())
for e in auth['documents']:ck('management_document_'+e['path'],sha(authroot/Path(e['path']).name)==e['sha256'])
expected={f'{m}-seed-{s}-attempt-01' for m in ['cadir','pca_snn_louvain'] for s in [2358,101,202,303,404]};formal=Path('/workspace/hsc-fair-experiment-data-20261026/formal/6cc7b3d-20261027-attempt-01');ck('no_replaced_attempt_in_fixed_run',expected=={p.name for p in formal.iterdir() if p.is_dir()})
status=json.loads((r/'presentation/presentation-status.json').read_text());ck('presentation_script_SHA',sha(base/'presentation/render_results.R')==status['script_sha256'])
for e in json.loads((r/'presentation/presentation-inputs.json').read_text())['inputs']:ck('presentation_consumed_file_'+e['path'],sha(Path(e['path']))==e['sha256'])
cutoffs=json.loads(Path('/workspace/hsc-fair-experiment-data-20261026/stage1/attempt-01/qc-thresholds.json').read_text());cmap={'log2 endogenous read count':'log2_endogenous_total_lower','log2 detected endogenous genes':'log2_detected_lower','ERCC percent':'ERCC_percent_upper'}
for e in csv.DictReader((r/'presentation/QC-frozen-cutoffs.tsv').open(),delimiter='\t'):ck('presented_frozen_cutoff_'+e['metric'],abs(float(e['cutoff'])-cutoffs[cmap[e['metric']]])<1e-12)
imgs=[]
for p in sorted((r/'presentation').glob('*.png')):
 data=p.read_bytes();ck('PNG_signature_'+p.name,data[:8]==b'\x89PNG\r\n\x1a\n');width,height=struct.unpack('>II',data[16:24]);i=8;dpi=None
 while i<len(data):
  n=struct.unpack('>I',data[i:i+4])[0];kind=data[i+4:i+8];payload=data[i+8:i+8+n]
  if kind==b'pHYs':x,y,unit=struct.unpack('>IIB',payload);dpi=[x*.0254,y*.0254] if unit==1 else None
  i+=n+12
 ck('PNG_300dpi_'+p.name,dpi and all(abs(x-300)<.1 for x in dpi));ck('PDF_pair_'+p.stem,p.with_suffix('.pdf').read_bytes().startswith(b'%PDF-'))
 imgs.append(dict(path=str(p.relative_to(repo)),sha256=sha(p),width=width,height=height,dpi=dpi,actually_viewed_with_tool=True))
ck('eight_presentation_pairs',len(imgs)==8)
p=r/'formal/cadir-seed-2358-attempt-01/diagnostics/association-plots.png';imgs.append(dict(path=str(p.relative_to(repo)),sha256=sha(p),actually_viewed_with_tool=True,observation='Eleven panels with real cluster IDs; Ensembl top-five labels overlap, axis titles absent. Retain as native diagnostic only; geometry interpretation checked against saved basis and TSV.'))
repair=Path('/workspace/hsc-design-independent-review/reviews/hsc-design-20261026/evidence-independent-repair-02/repair-checks.tsv');rows=list(csv.DictReader(repair.open(),delimiter='\t'));ck('prior_independent_39_check_repair_evidence_retained',len(rows)==39)
(out/'figure-view-evidence.json').write_text(json.dumps({'reviewer':'/root/hsc_results_independent_review','view_method':'tools.view_image returned actual PNG pixels; all eight presentation figures plus seed2358 native diagnostic','figures':imgs,'interpretation':'Main figures legible and values checked against TSV and independently recomputed metrics/contingencies. Native label overlap is disclosed and limits gene-label reading.'},indent=2,ensure_ascii=False)+'\n')
(out/'presentation-context-checks.json').write_text(json.dumps({'status':'PASS','checks':checks,'prior_repair_evidence_sha256':sha(repair),'prior_repair_review_not_reperformed':True},indent=2,ensure_ascii=False)+'\n');print('PASS',len(checks),'additional presentation/context checks')
