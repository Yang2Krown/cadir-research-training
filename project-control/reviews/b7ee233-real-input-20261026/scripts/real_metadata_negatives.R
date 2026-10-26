suppressPackageStartupMessages({library(S4Vectors);library(Matrix);library(digest);library(jsonlite)})
source('/repo/cases/nestorowa_hsc/scripts/metadata_identity.R')
out<-commandArgs(TRUE)[1];dir.create(out,recursive=TRUE)
m<-readRDS('/inputs/coldata.rds');original<-digest(m,algo='sha256');base<-extract_metadata_identity(m);rows<-list()
record<-function(name,mutate,expected,oracle=NULL){z<-unserialize(serialize(m,NULL));z<-mutate(z);before<-digest(z,algo='sha256');error<-NULL;v<-tryCatch(extract_metadata_identity(z),error=function(e){error<<-e;NULL});passed<-if(expected=='reject')inherits(error,'identity_error') else is.null(error)&&isTRUE(oracle(v));unchanged<-identical(before,digest(z,algo='sha256'));rows[[length(rows)+1L]]<<-data.frame(case=name,expected=expected,observed=if(is.null(error))'accept' else class(error)[1],object_unchanged=unchanged,pass=passed&&unchanged,message=if(is.null(error))'' else conditionMessage(error));}
setfield<-function(z,f,v){ld<-slot(z,'listData');ld[[f]]<-v;slot(z,'listData')<-ld;z}
record('reverse_each_nested',function(z){for(f in c('cell.type','diffusion','FACS'))z<-setfield(z,f,z[[f]][nrow(z):1,,drop=FALSE]);z},'accept',function(v){ix<-match(base$ids,v$ids);all(vapply(names(base$aligned),function(f)identical(base$aligned[[f]],v$aligned[[f]][ix,,drop=FALSE]),logical(1)))&&identical(base$candidate$candidate_label,v$candidate$candidate_label[ix])})
record('reverse_FACS_only',function(z)setfield(z,'FACS',z[['FACS']][nrow(z):1,,drop=FALSE]),'accept',function(v)identical(v$aligned$FACS,base$aligned$FACS))
for(f in c('cell.type','diffusion','FACS')){
 record(paste0(f,'_duplicate_ID'),local({field<-f;function(z){v<-z[[field]];rownames(v)[2]<-rownames(v)[1];setfield(z,field,v)}}),'reject')
 record(paste0(f,'_missing_explicit_ID'),local({field<-f;function(z){v<-z[[field]];rownames(v)<-NULL;setfield(z,field,v)}}),'reject')
 record(paste0(f,'_foreign_ID'),local({field<-f;function(z){v<-z[[field]];rownames(v)[2]<-'independent_unknown_cell';setfield(z,field,v)}}),'reject')
}
record('broad_membership_conflict',function(z){v<-z[['cell.type']];v[1,c('LTHSC_broad','LMPP_broad')]<-1;setfield(z,'cell.type',v)},'reject')
record('membership_NA',function(z){v<-z[['cell.type']];v[1,1]<-NA;setfield(z,'cell.type',v)},'reject')
record('top_level_conflicting_ID',function(z){attr(z,'rownames')<-c('independent_unknown_cell',base$ids[-1]);z},'reject')
record('top_level_implicit_sequence',function(z){attr(z,'rownames')<-seq_len(nrow(z));z},'reject')
res<-do.call(rbind,rows);write.table(res,file.path(out,'real_metadata_negative_cases.tsv'),sep='\t',row.names=FALSE,quote=TRUE)
stopifnot(identical(original,digest(m,algo='sha256')))
write_json(list(status=if(all(res$pass))'PASS' else 'FAIL',cases=nrow(res),passes=sum(res$pass),real_metadata_only=TRUE,source_RDS_unchanged=TRUE,counts_or_simulated_matrix_used=FALSE),file.path(out,'negative_status.json'),pretty=TRUE,auto_unbox=TRUE)
if(!all(res$pass))quit(status=1)
cat('Real metadata in-memory adversarial cases PASS\n')
