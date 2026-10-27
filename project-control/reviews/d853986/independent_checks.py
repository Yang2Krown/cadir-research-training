"""Independent preparation review. Only committed source/metadata; no RDS/count access.
This script does not import or execute the implementation's audit scripts.
"""
from pathlib import Path
import csv, gzip, hashlib, json, subprocess, collections, re, datetime

SRC = Path('/workspace/cadir-hsc-prep-independent-source-20261026')
OUT = Path(__file__).resolve().parent
REL = 'planning/new-dataset/2026-10-26/metadata-preparation'
ROOT = SRC / REL
SHA = 'd853986e2e3a1cabc9f3f728f616e402432257ec'
BASE = '122fdbf2986f3791917197385f8d07ba0a75fce6'
SNAP = 'b4e2d1f8ca57f27f5a8b7f69014254a1d7bcf4e9'
def git(*args):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', '-C', str(SRC), *args])
def sha(b): return hashlib.sha256(b).hexdigest()
def readtsv(path):
    with path.open(newline='') as f: return list(csv.DictReader(f, delimiter='\t'))
def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
def require(test, message):
    if not test: raise AssertionError(message)

require(git('rev-parse','HEAD').decode().strip()==SHA, 'wrong HEAD')
require(not git('status','--porcelain'), 'source worktree dirty')
changes = git('diff','--name-status',BASE,SHA).decode().splitlines()
require(all(line.startswith('A\t'+REL+'/') for line in changes), 'changes outside preparation or non-additions')
tracked = git('ls-tree','-r','--name-only',SHA,'--',REL).decode().splitlines()
actual = {p.removeprefix(REL+'/') for p in tracked}
index = readtsv(ROOT/'bundle_sha256.tsv')
require(len({r['path'] for r in index})==len(index), 'duplicate bundle entries')
require({r['path'] for r in index} == actual-{'bundle_sha256.tsv'}, 'index not exhaustive')
integrity = []
for r in index:
    p = Path(r['path'])
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe path')
    require(p.suffix!='.rds' and p.name!='GSE81682_HTSeq_counts.txt.gz','raw included')
    data=(ROOT/p).read_bytes()
    require(len(data)==int(r['bytes']) and sha(data)==r['sha256'], 'bundle mismatch '+str(p))
    integrity.append(dict(path=str(p),bytes=len(data),sha256=sha(data),CRLF=data.count(b'\r\n')))
original_files=git('ls-tree','-r','--name-only',SNAP,'--',REL).decode().splitlines()
snapshot_changes=[]
for path in original_files:
    old=git('show',SNAP+':'+path); new=(SRC/path).read_bytes()
    if old!=new: snapshot_changes.append(path.removeprefix(REL+'/'))
require(snapshot_changes==['README.md'], 'unexpected original snapshot mutation')
hash_index_counts={}
for name in ['preparation_artifact_sha256.tsv','recovered_files_sha256.tsv']:
    rs=readtsv(ROOT/name)
    for r in rs: require(sha((ROOT/r['path']).read_bytes())==r['sha256'],name+' mismatch')
    require((ROOT/name).read_bytes()==git('show',SNAP+':'+REL+'/'+name),'original index changed')
    hash_index_counts[name]=len(rs)
recovery=[]
for r in readtsv(ROOT/'recovered_files_sha256.tsv'):
    source=r['path'].removeprefix('recovered-branch/')
    require((ROOT/r['path']).read_bytes()==git('show',BASE+':'+source),'recovered mismatch '+source)
    recovery.append(source)
require((SRC/'cases/nestorowa_hsc/scripts/audit_inputs.R').read_bytes()==(ROOT/'recovered-branch/cases/nestorowa_hsc/scripts/audit_inputs.R').read_bytes(),'current R audit changed')
draft=json.loads((ROOT/'input_label_plan.draft.json').read_text())
protocol=(SRC/'planning/new-dataset/2026-10-26/pre-registration.json').read_bytes()
require(sha(protocol)==draft['inherited_protocol']['sha256'],'inherited protocol hash mismatch')
require(not draft['formal_execution_permitted'],'draft permits execution')
manifest=json.loads((ROOT/'acquisition_manifest.json').read_text())
require(not manifest['formal_execution_permitted'],'manifest permits execution')
receipt_consistency=[]
for artifact in draft['input_artifacts_external_to_git']:
    receipt=json.loads((ROOT/artifact['receipt']).read_text())
    require(artifact['sha256']==receipt['sha256'] and artifact['bytes']==receipt['bytes'],'raw receipt inconsistency')
    require(not (ROOT/artifact['path']).exists(),'unexpected raw data in source checkout')
    receipt_consistency.append(dict(path=artifact['path'],sha256=artifact['sha256'],bytes=artifact['bytes'],
        receipt_fields_match=True,external_bytes_independently_verified=False))
save('integrity.json', dict(commit=SHA,base=BASE,snapshot=SNAP,changed_files=len(changes),
    all_changes_additions_in_scope=True,tracked_preparation_files=len(actual),bundle_indexed_files=len(index),
    bundle_exact_coverage=True,bundle_hashes_all_match=True,original_snapshot_file_count=len(original_files),
    original_snapshot_changed_files=snapshot_changes,original_artifact_indexes_unchanged=True,
    original_index_entries=hash_index_counts,recovered_files_byte_identical_to_base=len(recovery),
    inherited_protocol_hash_matches=True,formal_execution_permitted=False,
    raw_receipts_consistent=receipt_consistency,external_raw_files_read=False,files=integrity))

members=readtsv(ROOT/'metadata-audit/cell_type_memberships.tsv')
ids=[r['cell_id'] for r in members]
require(len(ids)==1920 and len(set(ids))==len(ids) and all(ids),'bad membership IDs')
fields=list(members[0])[1:]
require(len(fields)==23, 'not 23 columns')
values={r['cell_id']:{k:float(r[k]) for k in fields} for r in members}
require(all(v in (0,1) for row in values.values() for v in row.values()), 'nonbinary membership')
labels=['LTHSC','LMPP','MPP','CMP','MEP','GMP']
sub=['MPP1','MPP2','MPP3','STHSC']
groups={'broad':[x+'_broad' for x in labels],'fine':labels,
        'broad_mpp':[x+'_broad' for x in sub],'fine_mpp':sub}
level={}
for k,cols in groups.items():
    n=[sum(row[c] for c in cols) for row in values.values()]
    level[k]=dict(positive_by_label={c:sum(v[c] for v in values.values()) for c in cols},
        assigned=sum(v>0 for v in n),unassigned=n.count(0),conflicts=sum(v>1 for v in n))
hierarchy={}
for f in fields:
    if f+'_broad' in fields: hierarchy[f+'_outside_broad']=sum(v[f]>v[f+'_broad'] for v in values.values())
for k,parent in [('broad_mpp','MPP_broad'),('fine_mpp','MPP')]:
    hierarchy[k+'_outside_parent']=sum(any(v[c] for c in groups[k]) and not v[parent] for v in values.values())
    hierarchy[k+'_parent_without_child']=sum(v[parent] and not any(v[c] for c in groups[k]) for v in values.values())
categories=readtsv(ROOT/'metadata-audit/cell_type_categories.tsv')
require(len(categories)==23 and {r['field'] for r in categories}==set(fields),'category fields differ')
for r in categories:
    require(int(r['positive'])==sum(v[r['field']]==1 for v in values.values()) and int(r['zero'])==sum(v[r['field']]==0 for v in values.values()) and int(r['missing'])==0,'category mismatch')
candidate=readtsv(ROOT/'metadata-audit/candidate_broad_reference.tsv')
flags=readtsv(ROOT/'metadata-audit/cell_metadata_flags.tsv')
mapping=readtsv(ROOT/'metadata-audit/cell_id_mapping.tsv')
for table in [candidate,flags,mapping]: require([r['cell_id'] for r in table]==ids,'ID/order mismatch')
candidate_diff=[]
for r in candidate:
    chosen=[x for x in labels if values[r['cell_id']][x+'_broad']]
    label=chosen[0] if len(chosen)==1 else ''
    reason='unique_broad_membership' if len(chosen)==1 else 'no_broad_membership'
    if (r['candidate_label'],r['reason'],r['status']) != (label,reason,'DRAFT_NOT_FROZEN'): candidate_diff.append(r['cell_id'])
require(not candidate_diff,'candidate mapping mismatch')
for r in flags:
    v=values[r['cell_id']]
    require(int(r['Projected'])==v['Projected'],'projected mismatch')
    require(int(r['no_broad_label'])==int(not any(v[x] for x in groups['broad'])),'broad flag mismatch')
    require(int(r['no_fine_label'])==int(not any(v[x] for x in groups['fine'])),'fine flag mismatch')
    require(all(r[x] in ['0','1'] for x in list(r)[1:]),'nonbinary flags')
flag_counts={x:sum(int(r[x]) for r in flags) for x in list(flags[0])[1:]}
flag_cross={x:dict(projected=sum(int(r[x]) and int(r['Projected']) for r in flags),
    nonprojected=sum(int(r[x]) and not int(r['Projected']) for r in flags)) for x in ['diffusion_missing','FACS_missing']}
summary=json.loads((ROOT/'metadata-audit/metadata_summary.json').read_text())
for k,v in level.items():
    orig=summary['reference_levels'][k]
    require(orig['zero_memberships']==v['unassigned'] and orig['one_membership']==v['assigned'] and orig['multiple_memberships']==v['conflicts'] and orig['positive_by_label']==v['positive_by_label'],'reported level differs')
save('metadata_recalculation.json',dict(commit=SHA,source='committed memberships/flags/candidate TSV; raw RDS not opened',
    cells=len(ids),unique_nonempty_ids=True,membership_columns=23,all_values_binary=True,
    all_23_zero=sum(not any(v.values()) for v in values.values()),levels=level,hierarchy=hierarchy,
    candidate_rows_compared=len(candidate),candidate_differences=candidate_diff,
    category_counts_match=True,flag_counts=flag_counts,flag_crosschecks=flag_cross,
    flags_limitation='FACS/DC missing flags independently summed, but raw missingness was not re-extracted',
    raw_top_level_NULL_and_nested_IDs='implementation records/static code reviewed; no independent RDS verification'))

# Parse SOFT's sample metadata independently as a state machine. No count file opened.
records=[]; record=None; series=[]; tables=[]
with gzip.open(ROOT/'sources/GSE81682_family.soft.gz','rt') as stream:
    for line in stream:
        line=line.rstrip('\r\n')
        if line.startswith('^'):
            if record is not None: records.append(record)
            record={'gsm':line.split(' = ',1)[1], 'fields':collections.defaultdict(list)} if line.startswith('^SAMPLE = ') else None
        elif record is not None and line.startswith('!Sample_') and ' = ' in line:
            key,value=line.split(' = ',1); record['fields'][key].append(value)
        elif line.startswith('!Series_'): series.append(line)
        if 'sample_table_begin' in line: tables.append(line)
if record is not None: records.append(record)
require(not tables,'unexpected sample data table')
derived=[]
for r in records:
    f=r['fields']; name=f['!Sample_title'][0].split()[-1]
    rep='_Rep_' in name
    # Exact pattern used only as candidate name relation; no biological interpretation.
    canonical=re.sub(r'_Rep_(\d+)$',r'_\1',name)
    derived.append(dict(gsm=r['gsm'],title=f['!Sample_title'][0],source_cell_id=name,
        canonical_candidate=canonical,rep_name=str(rep),
        cell_type=next(v for v in f['!Sample_characteristics_ch1'] if v.startswith('cell type: ')),
        biosample=next(v for v in f['!Sample_relation'] if v.startswith('BioSample:')),
        sra=next(v for v in f['!Sample_relation'] if v.startswith('SRA:'))))
saved_geo=readtsv(ROOT/'metadata-audit/geo_sample_records.tsv')
require(derived==saved_geo, 'SOFT derived TSV differs')
by_id=collections.defaultdict(list)
for r in derived: by_id[r['canonical_candidate']].append(r)
require(len(records)==3840 and len({r['gsm'] for r in derived})==3840,'GSM count/uniqueness')
require(len({r['source_cell_id'] for r in derived})==3840,'source name uniqueness')
require(set(by_id)==set(ids),'GEO candidate sets differ')
for i,row in enumerate(mapping,1):
    rs=by_id[row['cell_id']]
    direct=[r for r in rs if r['rep_name']=='False']; rep=[r for r in rs if r['rep_name']=='True']
    require(len(direct)==len(rep)==1,'not one direct and one Rep')
    require(int(row['matrix_column_1based'])==int(row['nested_metadata_row_1based'])==i,'ordinal record differs')
    require(row['direct_GSM']==direct[0]['gsm'] and row['Rep_name_candidate_GSM']==rep[0]['gsm'],'mapping GSM differs')
    require(row['replicate_status']=='UNRESOLVED; name pairing only','rep assertion changed')
save('geo_recalculation.json',dict(commit=SHA,source='committed GEO SOFT sample metadata',records=len(records),
    unique_gsms=3840,unique_source_names=3840,candidate_canonical_ids=len(by_id),
    direct_records=sum(r['rep_name']=='False' for r in derived),Rep_named_records=sum(r['rep_name']=='True' for r in derived),
    direct_and_rep_each_once_for_all_1920=True,exact_geo_TSV_comparison=True,exact_mapping_TSV_comparison=True,
    direct_prefix_counts=dict(collections.Counter(re.sub(r'_\d+$','',r['source_cell_id']) for r in derived if r['rep_name']=='False')),
    series_metadata=series,biological_replication_established=False,
    raw_count_header_independently_checked=False,raw_flow_source_independently_checked=False))
save('review_run.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),commit=SHA,
    independent_script=True,implementation_audit_scripts_executed=False,raw_RDS_or_counts_accessed=False,
    experiments_simulation_smoke_clustering_metrics_run=False,source_worktree_clean=not bool(git('status','--porcelain')),
    checks_completed=['integrity','metadata_recalculation','geo_recalculation']))
print('Independent committed-artifact checks complete: 61 indexed files; 1920 membership IDs; 3840 GEO records. No raw data accessed.')
