# Validator regression checks using the real coldata only; no count or algorithm runs.
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=2L) stop("Usage: test_metadata_identity.R REAL_COLDATA NEW_JSON")
suppressPackageStartupMessages({library(Matrix);library(S4Vectors);library(digest);library(jsonlite)})
script <- sub("^--file=","",grep("^--file=",commandArgs(),value=TRUE)[[1]])
source(file.path(dirname(normalizePath(script)),"metadata_identity.R"))
if(file.exists(args[[2]])) stop("Output exists")
md <- readRDS(args[[1]])
original <- extract_metadata_identity(md)
checks <- list()
checks$real_NULL_and_NA_preserved <- isTRUE(original$summary$raw_top_level_rownames_is_null) &&
    original$summary$fields$FACS$all_missing_rows==430 &&
    original$summary$fields$diffusion$all_missing_rows==421 &&
    original$summary$broad_unassigned==136 && isTRUE(original$summary$input_object_unchanged)
# Reproduce the old identity guard against the actual R accessor; no counts needed.
old_ids <- rownames(md)
old_valid <- !is.null(old_ids) && length(old_ids)==nrow(md) && !anyNA(old_ids) &&
    all(nzchar(old_ids)) && !anyDuplicated(old_ids)
checks$old_top_level_identity_guard_rejects_real_input <- !old_valid
mutated <- md
mutated@listData$FACS <- mutated@listData$FACS[rev(seq_len(nrow(md))),,drop=FALSE]
reordered <- extract_metadata_identity(mutated)
checks$reversed_FACS_recovers_by_ID <- identical(reordered$aligned$FACS,original$aligned$FACS) &&
    reordered$summary$fields$FACS$reordered_rows==nrow(md) &&
    identical(reordered$summary$raw_top_level_rownames,NULL)
rejections <- list()
reject <- function(name,object) {
    result <- tryCatch({extract_metadata_identity(object);NULL},identity_error=function(e) e)
    if(!inherits(result,"identity_error")) stop("Expected identity_error: ",name)
    rejections[[name]] <<- list(message=conditionMessage(result),details=result$details)
    TRUE
}
mutated <- md;rownames(mutated@listData$FACS)[2] <- rownames(mutated@listData$FACS)[1]
checks$duplicate_ID_rejected <- reject("duplicate_FACS_ID",mutated)
mutated <- md;rownames(mutated@listData$diffusion) <- NULL
checks$missing_nested_ID_rejected <- reject("missing_diffusion_IDs",mutated)
mutated <- md;mutated@listData$FACS <- mutated@listData$FACS[-1,,drop=FALSE]
checks$missing_cell_rejected <- reject("missing_FACS_cell",mutated)
mutated <- md;rownames(mutated@listData$FACS)[1] <- "deliberate_invalid_source_ID"
checks$set_conflict_rejected <- reject("FACS_ID_set_conflict",mutated)
mutated <- md;mutated@rownames <- as.character(seq_len(nrow(md)))
checks$implicit_sequence_not_used_as_cell_ID <- reject("top_level_sequence_conflict",mutated)
jsonlite::write_json(list(status=if(all(unlist(checks))) "PASS" else "FAIL",
    checks=checks,expected_rejections=rejections,source="real coldata.rds with in-memory identity mutations only",
    source_sha256=digest::digest(file=args[[1]],algo="sha256"),raw_top_slot_is_null=is.null(md@rownames),
    raw_R_accessor_is_null=is.null(old_ids),formal_execution_permitted=FALSE,
    counts_read=FALSE,QC_normalization_clustering_metrics_or_smoke_run=FALSE),
    args[[2]],pretty=TRUE,auto_unbox=TRUE,na="null",null="null")
stopifnot(all(unlist(checks)))
