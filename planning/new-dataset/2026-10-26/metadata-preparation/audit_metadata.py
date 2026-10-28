"""Metadata-only audit of REACQUIRED legacy 2.0.0 data. Never opens counts.rds.
The GEO count table is opened only for its first (sample-name) line.
Run with PYTHONPATH=./python-deps python audit_metadata.py.
"""
from pathlib import Path
import collections, csv, gzip, json, re
import numpy as np
import rdata

BASE = Path(__file__).resolve().parent
OUT = BASE / 'metadata-audit'
OUT.mkdir(exist_ok=True)
def deref(x):
    while x.info.type.name == 'REF': x = x.referenced_object
    return x
def string(x):
    x = deref(x)
    if x.info.type.name == 'SYM': return string(x.value)
    return x.value.decode() if isinstance(x.value, bytes) else str(x.value)
def attrs(x):
    a = deref(x).attributes
    d = {}
    while a and deref(a).info.type.name == 'LIST':
        a = deref(a); d[string(a.tag)] = deref(a.value[0]); a = a.value[1]
    return d
def strings(x): return [string(v) for v in deref(x).value]
def save(name, x): (OUT/name).write_text(json.dumps(x, indent=2, ensure_ascii=False)+'\n')
def table(name, columns, rows):
    with (OUT/name).open('w') as f:
        w=csv.writer(f, delimiter='\t'); w.writerow(columns); w.writerows(rows)

obj=rdata.parser.parse_file(BASE/'reacquired-20261026/coldata.rds').object
top=attrs(obj); ld=top['listData']
fields={}
for name, x in zip(strings(attrs(ld)['names']), ld.value):
    a=attrs(x)
    if 'Dim' in a:
        shape=tuple(a['Dim'].value); arr=np.zeros(shape)
        for j in range(shape[1]):
            lo,hi=a['p'].value[j:j+2]; arr[a['i'].value[lo:hi],j]=a['x'].value[lo:hi]
        dn=a['Dimnames']
    else:
        shape=tuple(a['dim'].value); arr=np.asarray(x.value).reshape(shape,order='F'); dn=a['dimnames']
    ids,cols=map(strings,dn.value)
    fields[name]=(arr,ids,cols)

ct,ids,labels=fields['cell.type']
# Read sample header only: no iteration through gene/count rows.
with gzip.open(BASE/'reacquired-20261026/GSE81682_HTSeq_counts.txt.gz','rt') as f:
    header=next(csv.reader([f.readline()],delimiter='\t'))
header=[s.strip('"') for s in header]
if len(header)==len(ids)+1: header=header[1:]
summary={'scope':'metadata only; counts.rds never deserialized; GEO first line only',
    'metadata_top_level_rownames':string(top['rownames']),
    'metadata_rows':int(top['nrows'].value[0]),
    'header_cells':len(header),'header_unique':len(set(header)),
    'header_identical_to_nested_ids':{},'fields':{},
    'cell_type_values':np.unique(ct).tolist(),
    'cell_type_all_zero_rows':int((ct.sum(axis=1)==0).sum())}
for name,(a,rows,cols) in fields.items():
    summary['header_identical_to_nested_ids'][name]=(header==rows)
    summary['fields'][name]={'shape':list(a.shape),'columns':cols,'unique_ids':len(set(rows)),
        'missing_by_column':dict(zip(cols,np.isnan(a).sum(axis=0).tolist())),
        'all_fields_missing_rows':int(np.isnan(a).all(axis=1).sum()),
        'partial_missing_rows':int((np.isnan(a).any(axis=1)&~np.isnan(a).all(axis=1)).sum()),
        'infinite_by_column':dict(zip(cols,np.isinf(a).sum(axis=0).tolist()))}
table('cell_type_memberships.tsv',['cell_id']+labels,([i]+v.tolist() for i,v in zip(ids,ct)))
table('cell_type_categories.tsv',['field','positive','zero','missing'],
    ([name,int((ct[:,j]==1).sum()),int((ct[:,j]==0).sum()),int(np.isnan(ct[:,j]).sum())] for j,name in enumerate(labels)))
groups={'broad':['LTHSC_broad','LMPP_broad','MPP_broad','CMP_broad','MEP_broad','GMP_broad'],
    'fine':['LTHSC','LMPP','MPP','CMP','MEP','GMP'],
    'broad_mpp':['MPP1_broad','MPP2_broad','MPP3_broad','STHSC_broad'],
    'fine_mpp':['MPP1','MPP2','MPP3','STHSC']}
summary['reference_levels']={}
for name,cols in groups.items():
    a=ct[:,[labels.index(c) for c in cols]]
    summary['reference_levels'][name]={'zero_memberships':int((a.sum(axis=1)==0).sum()),
       'one_membership':int((a.sum(axis=1)==1).sum()),'multiple_memberships':int((a.sum(axis=1)>1).sum()),
       'positive_by_label':dict(zip(cols,(a==1).sum(axis=0).tolist()))}
summary['hierarchy_checks']={}
for fine in [x for x in labels if x+'_broad' in labels]:
    summary['hierarchy_checks'][fine+'_outside_broad']=int(((ct[:,labels.index(fine)]==1)&(ct[:,labels.index(fine+'_broad')]!=1)).sum())
for name in ['broad_mpp','fine_mpp']:
    parent='MPP_broad' if name=='broad_mpp' else 'MPP'
    children=ct[:,[labels.index(c) for c in groups[name]]].sum(axis=1)>0
    summary['hierarchy_checks'][name+'_outside_parent']=int((children&(ct[:,labels.index(parent)]!=1)).sum())
projected=ct[:,labels.index('Projected')]==1
table('cell_metadata_flags.tsv',['cell_id','Projected','diffusion_missing','FACS_missing','no_broad_label','no_fine_label'],
    ([i,int(projected[j]),int(np.isnan(fields['diffusion'][0][j]).any()),int(np.isnan(fields['FACS'][0][j]).any()),
      int(ct[j,:6].sum()==0),int(ct[j,10:16].sum()==0)] for j,i in enumerate(ids)))
summary['projected_crosscheck']={}
for name,(a,_,cols) in fields.items():
    missing=np.isnan(a).any(axis=1)
    summary['projected_crosscheck'][name]={'missing_rows':int(missing.sum()),
       'missing_projected':int((missing&projected).sum()),'missing_nonprojected':int((missing&~projected).sum())}

soft=gzip.open(BASE/'sources/GSE81682_family.soft.gz','rt').read()
records=[]
for block in soft.split('^SAMPLE = ')[1:]:
    lines=block.splitlines(); gsm=lines[0];d=collections.defaultdict(list)
    for l in lines[1:]:
        if ' = ' in l and l.startswith('!Sample_'):
            k,v=l.split(' = ',1);d[k].append(v)
    title=d['!Sample_title'][0]; name=title.rsplit(' ',1)[-1]
    canonical=name.replace('_Rep_','_')
    records.append({'gsm':gsm,'title':title,'source_cell_id':name,'canonical_candidate':canonical,
        'rep_name':'_Rep_' in name,'cell_type':next(v for v in d['!Sample_characteristics_ch1'] if v.startswith('cell type: ')),
        'biosample':next(v for v in d['!Sample_relation'] if v.startswith('BioSample:')),
        'sra':next(v for v in d['!Sample_relation'] if v.startswith('SRA:'))})
by_id=collections.defaultdict(list)
for r in records:by_id[r['canonical_candidate']].append(r)
table('geo_sample_records.tsv',list(records[0]),([r[k] for k in records[0]] for r in records))
table('cell_id_mapping.tsv',['matrix_column_1based','cell_id','nested_metadata_row_1based','direct_GSM','Rep_name_candidate_GSM','replicate_status'],
    ([j+1,i,ids.index(i)+1,','.join(r['gsm'] for r in by_id[i] if not r['rep_name']),
      ','.join(r['gsm'] for r in by_id[i] if r['rep_name']),'UNRESOLVED; name pairing only'] for j,i in enumerate(header)))
summary['geo']={'sample_records':len(records),'source_names_unique':len(set(r['source_cell_id'] for r in records)),
    'rep_named_records':sum(r['rep_name'] for r in records),
    'canonical_candidate_ids':len(by_id),'canonical_ids_match_metadata_set':set(by_id)==set(ids),
    'direct_name_matches':sum(any(r['source_cell_id']==i for r in by_id[i]) for i in ids),
    'candidate_records_per_id':dict(collections.Counter(len(v) for v in by_id.values())),
    'direct_gate_counts':dict(collections.Counter(re.sub(r'_[0-9]+$','',r['source_cell_id']) for r in records if not r['rep_name'])),
    'replicate_relationship':'UNRESOLVED: naming is not evidence of biological replication',
    'publication_analyzed_cells':1656,'difference_from_metadata':len(ids)-1656,
    'difference_resolution':'NOT_RESOLVED; do not infer exclusion from Projected or missing diffusion alone'}
save('metadata_summary.json',summary)
print(json.dumps(summary,indent=2))
