# Independently authored real-object oracle; no original audit/verifier is called.
suppressPackageStartupMessages({library(Matrix); library(S4Vectors); library(jsonlite); library(digest)})
args <- commandArgs(TRUE); out<-args[1]; dir.create(out,recursive=TRUE)
writej<-function(x,n) write_json(x,file.path(out,n),pretty=TRUE,auto_unbox=TRUE,na='null',null='null',digits=NA)
check<-function(ok,msg) if(!isTRUE(ok)) stop(msg)
ids_ok<-function(x,n) is.character(x)&&length(x)==n&&!anyNA(x)&&all(nzchar(trimws(x)))&&anyDuplicated(x)==0L
m<-readRDS('/inputs/coldata.rds'); m0<-digest(m,algo='sha256')
raw<-attr(m,'rownames',exact=TRUE); semantic<-slot(m,'rownames')
check(is.symbol(raw)&&identical(as.character(raw),'\001NULL\001'),'Expected original serialized NULL sentinel')
check(is.null(semantic),'Expected semantic NULL')
fields<-c('cell.type','diffusion','FACS'); canonical<-rownames(m[['cell.type']]);check(ids_ok(canonical,nrow(m)),'Canonical IDs invalid')
meta<-list(); aligned<-list()
for(f in fields){v<-m[[f]]; id<-rownames(v);check((is.matrix(v)||is(v,'Matrix'))&&ids_ok(id,nrow(m))&&setequal(id,canonical),paste('Explicit identity',f));aligned[[f]]<-v[match(canonical,id),,drop=FALSE];meta[[f]]<-list(class=class(v),dimensions=dim(v),columns=colnames(v),explicit_ids=TRUE,order_same=identical(id,canonical),NA_entries=sum(is.na(v)),NA_by_column=as.list(colSums(is.na(v))),all_NA_rows=sum(rowSums(is.na(v))==ncol(v)));write.table(data.frame(cell_id=canonical,missing_entries=rowSums(is.na(aligned[[f]]))),file.path(out,paste0(f,'_missing.tsv')),sep='\t',row.names=FALSE,quote=FALSE)}
ct<-as.matrix(aligned[['cell.type']]);check(ncol(ct)==23L&&!anyNA(ct)&&all(ct %in% 0:1),'23 binary membership fields')
broad<-c('LTHSC_broad','LMPP_broad','MPP_broad','CMP_broad','MEP_broad','GMP_broad');check(all(broad %in% colnames(ct)),'Broad columns')
bm<-ct[,broad,drop=FALSE];check(all(rowSums(bm)<=1),'Broad conflicts')
lab<-apply(bm,1,function(x) if(sum(x)==0) NA_character_ else sub('_broad$','',names(x)[which(x==1)]))
write.table(data.frame(cell_id=canonical,candidate_label=unname(lab)),file.path(out,'independent_candidate.tsv'),sep='\t',row.names=FALSE,quote=FALSE,na='NA')
write.table(data.frame(field=colnames(ct),members=colSums(ct)),file.path(out,'membership_counts.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
writej(list(class=class(m),rows=nrow(m),raw_attribute_type=typeof(raw),raw_symbol=as.character(raw),semantic_NULL=is.null(semantic),default_rownames_not_used=TRUE,fields=meta,broad_label_counts=as.list(table(lab,useNA='ifany')),unassigned=sum(is.na(lab)),all_23_zero=sum(rowSums(ct)==0),object_unchanged=identical(m0,digest(m,algo='sha256'))),'independent_metadata.json')
x<-readRDS('/inputs/counts.rds');check(is(x,'dgCMatrix'),'Expected numeric compressed sparse matrix');check(isTRUE(validObject(x)),'Sparse structural validity')
g<-rownames(x);c<-colnames(x);check(ids_ok(g,nrow(x))&&ids_ok(c,ncol(x)),'All matrix explicit IDs');check(setequal(c,canonical),'Matrix columns match metadata IDs')
# Check all stored values in column slices; implicit zero entries satisfy each predicate.
invalid<-c(nonfinite=0,negative=0,fractional=0);stored<-0
for(j in seq_len(ncol(x))){v<-x@x[seq.int(x@p[j]+1L,x@p[j+1L])];if(x@p[j]==x@p[j+1L]) v<-numeric();finite<-is.finite(v);invalid<-invalid+c(sum(!finite),sum(v[finite]<0),sum(v[finite]%%1!=0));stored<-stored+length(v)}
check(all(invalid==0),'Invalid count values')
write.table(data.frame(gene_id=g),file.path(out,'independent_gene_ids.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
write.table(data.frame(cell_id=c,metadata_row=match(c,canonical)),file.path(out,'independent_cell_alignment.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
con<-gzfile('/inputs/GSE81682_HTSeq_counts.txt.gz','rt');header<-scan(text=readLines(con,n=1),what='',sep='\t',quote='"',quiet=TRUE)
if(length(header)==ncol(x)+1L) header<-header[-1]
check(ids_ok(header,ncol(x))&&setequal(header,c),'GEO explicit cell IDs');cj<-match(header,c);seen<-character();compared<-0;diffs<-0;badgeo<-0;blocks<-0
while(length(lines<-readLines(con,n=64,warn=FALSE))){parts<-strsplit(lines,'\t',fixed=TRUE);check(all(lengths(parts)==ncol(x)+1L),'GEO width');genes<-sub('"$','',sub('^"','',vapply(parts,'[[','',1L)));ri<-match(genes,g);check(!anyNA(ri),'Unknown GEO gene');v<-matrix(as.numeric(unlist(lapply(parts,function(p)p[-1]),use.names=FALSE)),nrow=length(parts),byrow=TRUE);badgeo<-badgeo+sum(!is.finite(v)|v<0|v%%1!=0);d<-v!=as.matrix(x[ri,cj,drop=FALSE]);diffs<-diffs+sum(d);compared<-compared+length(v);seen<-c(seen,genes);blocks<-blocks+1L}
close(con);check(ids_ok(seen,nrow(x))&&setequal(g,seen),'All GEO explicit gene IDs');check(compared==prod(dim(x))&&diffs==0&&badgeo==0,'Full GEO value correspondence')
writej(list(class=class(x),dimensions=dim(x),direction='genes_by_cells',direction_evidence='all GEO gene IDs match rows; all GEO cell IDs match columns and explicit metadata identities',stored_values=stored,logical_values=prod(dim(x)),invalid=as.list(invalid),implicit_zeros=prod(dim(x))-stored,ensembl=sum(grepl('^ENSMUSG[0-9]+$',g)),ERCC=sum(grepl('^ERCC-',g)),htseq=sum(startsWith(g,'__')),metadata_order_same=identical(c,canonical),GEO_gene_order_same=identical(g,seen),GEO_cell_order_same=identical(c,header),GEO_stream_blocks=blocks,values_compared=compared,numeric_differences=diffs,GEO_invalid_values=badgeo),'independent_counts_geo.json')
writej(list(R=R.version.string,packages=setNames(lapply(c('Matrix','S4Vectors','jsonlite','digest'),function(p)as.character(packageVersion(p))),c('Matrix','S4Vectors','jsonlite','digest')),session=capture.output(sessionInfo())),'environment.json')
writej(list(status='PASS',formal_execution_permitted=FALSE,scope='input legality only'),'independent_status.json')
cat('Independent real-object and all-value GEO oracle PASS\n')
