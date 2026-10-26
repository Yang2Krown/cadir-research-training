suppressPackageStartupMessages({library(S4Vectors); library(digest); library(jsonlite)})
identity_path <- '/workspace/cadir-hsc-a03-review-source-20261026/cases/nestorowa_hsc/scripts/metadata_identity.R'
source(identity_path)
ids <- c('cell-A', 'cell-B', 'cell-C')
broad <- c('LTHSC_broad','LMPP_broad','MPP_broad','CMP_broad','MEP_broad','GMP_broad')
ct <- matrix(0L, nrow=3L, ncol=7L, dimnames=list(ids,c(broad,'Projected')))
ct[1,'LTHSC_broad'] <- 1L
ct[2,'MPP_broad'] <- 1L
ct[1,'Projected'] <- 1L
diffusion <- matrix(as.numeric(c(3,2,1)), ncol=1L, dimnames=list(rev(ids),'score'))
facs <- matrix(as.numeric(1:6), nrow=3L, ncol=2L, dimnames=list(ids,c('x','y')))
facs[1,2] <- NA_real_
md <- new('DFrame', listData=list(cell.type=ct, diffusion=diffusion, FACS=facs),
          nrows=3L, rownames=NULL, elementType='ANY', metadata=list())
before <- digest::digest(md, algo='sha256')
base <- extract_metadata_identity(md)
checks <- list(
  explicit_nested_IDs_are_canonical=identical(base$ids,ids),
  reversed_nested_rows_align_by_ID=identical(rownames(base$aligned$diffusion),ids) &&
    identical(unname(as.numeric(base$aligned$diffusion[,1])),c(1,2,3)) &&
    base$summary$fields$diffusion$reordered_rows==2L,
  original_input_and_existing_NA_preserved=identical(before,digest::digest(md,algo='sha256')) &&
    base$summary$input_object_unchanged && base$summary$fields$FACS$missing_entries==1L,
  no_position_based_identity_fill=!base$summary$positional_ID_fill,
  no_NA_imputation=!base$summary$NA_imputed,
  no_conflicting_broad_memberships=base$summary$broad_conflicts==0L
)
dup <- updateObject(md,verbose=FALSE)
rownames(dup@listData$FACS)[2] <- rownames(dup@listData$FACS)[1]
dup_result <- tryCatch({extract_metadata_identity(dup); 'accepted'}, identity_error=function(e) 'rejected')
checks$duplicate_nested_ID_rejected <- identical(dup_result,'rejected')
conflict <- updateObject(md,verbose=FALSE)
rownames(conflict) <- c('1','2','3')
top_result <- tryCatch({extract_metadata_identity(conflict); 'accepted'}, identity_error=function(e) 'rejected')
checks$nonNULL_top_level_ID_conflict_rejected <- identical(top_result,'rejected')
result <- list(status=if(all(unlist(checks))) 'PASS' else 'FAIL', checks=checks,
  fixture='synthetic in-memory S4Vectors::DFrame with nested matrices',
  actual_RDS_read=FALSE, count_or_GEO_data_used=FALSE, scientific_pipeline_or_smoke_run=FALSE,
  source_commit='b7ee2335dc25ffab3a60d1feab44272d6d5a45cb',
  source_sha256=digest::digest(file=identity_path,algo='sha256'),
  runtime=list(R=R.version.string,S4Vectors=as.character(packageVersion('S4Vectors')),
    digest=as.character(packageVersion('digest'))))
jsonlite::write_json(result,'/workspace/cadir-hsc-a03-independent-review-20261026/independent_identity_check.json',
  pretty=TRUE,auto_unbox=TRUE,na='null',null='null')
cat(result$status, 'synthetic in-memory identity checks:', length(checks), '\n')
stopifnot(all(unlist(checks)))
