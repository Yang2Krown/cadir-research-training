# Technical recovery only: original successful scientific computations reused.
# Existing attempt remains read-only, including FAILED receipt. No algorithm runs.
a <- commandArgs(TRUE);source(a[[1]]);load_packages()
cfg_path <- a[[2]];env_path <- a[[3]];prior <- a[[4]];out <- a[[5]];snapshot <- a[[6]]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
stopifnot(!file.exists(file.path(out,"stage1-finalization-status.json")))
cfg <- jsonlite::read_json(cfg_path,simplifyVector=TRUE)
status <- list(status="RUNNING",stage="verify_existing_artifacts",forbidden_algorithms_called=FALSE)
start <- proc.time()[["elapsed"]]
tryCatch({
 assert_environment(readRDS(env_path))
 old <- jsonlite::read_json(file.path(prior,"stage1-status.json"),simplifyVector=TRUE)
 stopifnot(old$status=="FAILED",old$error=="No method asJSON S3 class: table",old$config_sha256==sha_file(cfg_path),old$environment_signature_sha256==sha_file(env_path))
 frozen <- jsonlite::read_json(snapshot,simplifyVector=FALSE)
 for(e in frozen$files) stopifnot(sha_file(file.path(prior,e$path))==e$sha256,file.info(file.path(prior,e$path))$size==e$bytes)
 for(n in names(cfg$dataset$input_files)) stopifnot(sha_file(file.path(cfg$dataset$raw_root,n))==cfg$dataset$input_files[[n]])
 qc <- read.delim(file.path(prior,"cell-qc.tsv"),stringsAsFactors=FALSE)
 gf <- read.delim(file.path(prior,"gene-filter.tsv"),stringsAsFactors=FALSE)
 ref <- read.delim(file.path(prior,"frozen-reference.tsv"),na.strings="NA",stringsAsFactors=FALSE)
 sf <- read.delim(file.path(prior,"size-factors.tsv"),stringsAsFactors=FALSE)
 cells <- readLines(file.path(prior,"final-cell-ids.txt"));genes <- readLines(file.path(prior,"eligible-gene-ids.txt"));hvg <- readLines(file.path(prior,"hvg-gene-ids.txt"))
 stopifnot(identical(qc$cell_id,ref$cell_id),identical(cells,qc$cell_id[qc$retained]),identical(cells,sf$cell_id),identical(genes,gf$gene_id[gf$eligible]),identical(readLines(file.path(prior,"evaluation-cell-ids.txt")),ref$cell_id[ref$evaluated]),identical(ref$evaluated,qc$retained&!is.na(ref$label)),identical(ref$QC_retained,qc$retained))
 stopifnot(length(cells)>=100,length(hvg)==6000,all(hvg%in%genes))
 status$stage <- "verify_saved_normalization_and_HVG"
 sce <- readRDS(file.path(prior,"eligible-normalized-sce.rds"))
 stopifnot(identical(rownames(sce),genes),identical(colnames(sce),cells),isTRUE(all.equal(as.numeric(SingleCellExperiment::sizeFactors(sce)),sf$size_factor,tolerance=1e-13)))
 expected_sf <- qc$endogenous_total[qc$retained]/mean(qc$endogenous_total[qc$retained])
 stopifnot(isTRUE(all.equal(expected_sf,sf$size_factor,tolerance=1e-13)))
 max_error <- 0
 for(i in seq(1,nrow(sce),by=256)) {
  ix <- i:min(i+255,nrow(sce));expected <- log2(sweep(as.matrix(SummarizedExperiment::assay(sce,"counts")[ix,,drop=FALSE]),2,expected_sf,"/")+1)
  max_error <- max(max_error,max(abs(expected-as.matrix(SummarizedExperiment::assay(sce,"logcounts")[ix,,drop=FALSE]))))
 }
 stopifnot(max_error<1e-12)
 shared <- readRDS(file.path(prior,"shared-hvg-sce.rds"))
 stopifnot(identical(colnames(shared),cells),identical(rownames(shared),hvg),identical(SummarizedExperiment::assay(shared,"logcounts"),SummarizedExperiment::assay(sce[hvg,],"logcounts")))
 gv <- readRDS(file.path(prior,"gene-variance.rds"));chosen <- scran::getTopHVGs(gv,n=6000,var.threshold=NULL)
 stopifnot(identical(chosen,hvg),identical(rownames(gv),genes),identical(hvg,rownames(gv)[head(order(gv$bio,decreasing=TRUE),6000)]))
 # Re-derive the frozen QC predicates from saved label-blind metrics only.
 positive <- qc$endogenous_total>0&qc$endogenous_detected_genes>0
 lower <- function(x) median(x)-3*stats::mad(x,constant=1.4826)
 upper <- function(x) median(x)+3*stats::mad(x,constant=1.4826)
 thresholds <- c(lower(log2(qc$endogenous_total[positive])),lower(log2(qc$endogenous_detected_genes[positive])),upper(qc$ERCC_percent[positive]))
 stopifnot(identical(qc$low_library,positive&log2(pmax(qc$endogenous_total,1))<thresholds[1]),identical(qc$low_detected,positive&log2(pmax(qc$endogenous_detected_genes,1))<thresholds[2]),identical(qc$high_ERCC,positive&qc$ERCC_percent>thresholds[3]),identical(qc$retained,positive&!qc$low_library&!qc$low_detected&!qc$high_ERCC))
 rc <- table(qc$reason)
 summary <- list(raw_genes=nrow(gf),raw_cells=nrow(qc),HTSeq_rows=sum(gf$feature_class=="HTSeq"),ERCC_rows=sum(gf$feature_class=="ERCC"),endogenous_rows=sum(gf$feature_class=="endogenous"),retained_cells=sum(qc$retained),excluded_cells=sum(!qc$retained),eligible_genes=sum(gf$eligible),HVG=length(hvg),reference_assigned_before=sum(!is.na(ref$label)),reference_missing_before=sum(is.na(ref$label)),evaluated_cells=sum(ref$evaluated),retained_unassigned=sum(qc$retained&is.na(ref$label)),normalization_max_error=max_error,QC_metrics_before=lapply(qc[c("endogenous_total","endogenous_detected_genes","ERCC_percent")],function(x)as.list(unclass(summary(x)))),QC_metrics_after=lapply(qc[qc$retained,c("endogenous_total","endogenous_detected_genes","ERCC_percent")],function(x)as.list(unclass(summary(x)))),exclusion_rule_counts=list(zero=sum(!positive),low_library=sum(qc$low_library),low_detected=sum(qc$low_detected),high_ERCC=sum(qc$high_ERCC)),reason_counts=as.list(setNames(as.integer(rc),names(rc))),scientific_recomputation=FALSE,technical_recovery="Reused original QC/normalized/HVG/label objects after strict artifact/hash/ID/formula verification; original failure retained")
 write_json(summary,file.path(out,"preparation-summary.json"))
 write_json(as.list(cfg$dataset$input_files),file.path(out,"raw-protection-after.json"))
 for(e in frozen$files) stopifnot(sha_file(file.path(prior,e$path))==e$sha256)
 status$status <- "COMMON_PREPARATION_FINALIZED_NO_ALGORITHMS"
},error=function(e){status$status<<-"FAILED";status$error<<-conditionMessage(e);message(conditionMessage(e))},finally={
 status$elapsed_seconds <- proc.time()[["elapsed"]]-start
 status$memory_status <- grep("^Vm(HWM|RSS):",readLines("/proc/self/status"),value=TRUE)
 status$config_sha256 <- sha_file(cfg_path);status$environment_signature_sha256 <- sha_file(env_path);status$prior_attempt_snapshot_sha256 <- sha_file(snapshot)
 write_json(status,file.path(out,"stage1-finalization-status.json"));writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
})
if(status$status=="FAILED")quit(status=1)
cat("COMMON_PREPARATION_FINALIZED_NO_ALGORITHMS\n")
