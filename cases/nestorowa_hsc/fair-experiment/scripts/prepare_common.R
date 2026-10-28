# Stage 1 only: common QC, normalization, HVGs and explicit ID/label locks.
# No CA/PCA, clustering, ARI or NMI is called in this file.
a <- commandArgs(TRUE); source(a[[1]]); cfg_path <- a[[2]]; env_path <- a[[3]]; out <- a[[4]]
load_packages();cfg <- jsonlite::read_json(cfg_path,simplifyVector=TRUE)
stopifnot(!file.exists(file.path(out,"stage1-status.json")))
dir.create(out,recursive=TRUE,showWarnings=FALSE)
status <- list(status="RUNNING",stage="environment",forbidden_algorithms_called=FALSE)
start <- proc.time()[["elapsed"]]
tryCatch({
 assert_environment(readRDS(env_path))
 RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(cfg$shared_preprocess_seed)
 record_rng(out,"before_preparation")
 status$stage <- "input_protection"
 raw <- cfg$dataset$raw_root
 for(n in names(cfg$dataset$input_files)) stopifnot(sha_file(file.path(raw,n))==cfg$dataset$input_files[[n]])
 write_json(as.list(cfg$dataset$input_files),file.path(out,"raw-protection-before.json"))
 status$stage <- "common_QC"
 counts <- readRDS(file.path(raw,"counts.rds"))
 stopifnot(is.matrix(counts)||methods::is(counts,"Matrix"),length(dim(counts))==2)
 source("cases/nestorowa_hsc/scripts/metadata_identity.R")
 check_ids(rownames(counts),nrow(counts),"counts genes");check_ids(colnames(counts),ncol(counts),"counts cells")
 genes <- rownames(counts);cells <- colnames(counts)
 # Full values already independently audited. No duplicate full GEO/identity test here.
 htseq <- grepl(cfg$shared_input$feature_classes$remove_alignment_statistics_regex,genes)
 ercc <- grepl(cfg$shared_input$feature_classes$separate_ERCC_regex,genes)&!htseq
 endo <- !htseq&!ercc
 stopifnot("Frozen ERCC QC requires ERCC rows"=any(ercc),any(endo))
 lib <- colSums(counts[endo,,drop=FALSE]);det <- colSums(counts[endo,,drop=FALSE]>0)
 spike <- colSums(counts[ercc,,drop=FALSE]);ercc_pct <- 100*spike/(lib+spike)
 positive <- lib>0&det>0
 stopifnot(sum(positive)>=100,all(is.finite(ercc_pct[positive])))
 lower <- function(x) median(x)-3*stats::mad(x,constant=1.4826)
 upper <- function(x) median(x)+3*stats::mad(x,constant=1.4826)
 thresholds <- c(log2_endogenous_total_lower=lower(log2(lib[positive])),log2_detected_lower=lower(log2(det[positive])),ERCC_percent_upper=upper(ercc_pct[positive]))
 low_lib <- positive & log2(pmax(lib,1))<thresholds[[1]]
 low_det <- positive & log2(pmax(det,1))<thresholds[[2]]
 high_ercc <- positive & ercc_pct>thresholds[[3]]
 keep <- positive&!low_lib&!low_det&!high_ercc
 why <- vapply(seq_along(cells),function(i) paste(c(if(!positive[i]) "zero_endogenous_library",if(low_lib[i]) "low_endogenous_library",if(low_det[i]) "low_detected_genes",if(high_ercc[i]) "high_ERCC_percent"),collapse=";"),character(1))
 why[keep] <- "retained"
 qc <- data.frame(cell_id=cells,endogenous_total=lib,endogenous_detected_genes=det,ERCC_total=spike,ERCC_percent=ercc_pct,zero_endogenous=!positive,low_library=low_lib,low_detected=low_det,high_ERCC=high_ercc,retained=keep,reason=why)
 write_tsv(qc,file.path(out,"cell-qc.tsv"));write_json(as.list(thresholds),file.path(out,"qc-thresholds.json"))
 stopifnot(sum(keep)>=100)
 detected_after <- rowSums(counts[,keep,drop=FALSE]>0)
 eligible <- endo & detected_after>=cfg$shared_input$gene_filter$detected_in_at_least_cells
 stopifnot(sum(eligible)>=cfg$shared_input$HVG$n,min(sum(eligible)-1,sum(keep)-1)>=cfg$CAdir$CA$dims)
 sf <- lib[keep]/mean(lib[keep]);stopifnot(all(is.finite(sf)),all(sf>0),abs(mean(sf)-1)<1e-12)
 status$stage <- "shared_normalization"
 # Library denominator includes all endogenous rows before low-expression filtering.
 mat <- as(counts[eligible,keep,drop=FALSE],"dgCMatrix")
 sce <- SingleCellExperiment::SingleCellExperiment(assays=list(counts=mat))
 rm(mat,counts);gc()
 sce <- scuttle::logNormCounts(sce,size.factors=sf,center.size.factors=FALSE,transform="log",pseudo.count=cfg$shared_input$normalization$pseudocount,BPPARAM=BiocParallel::SerialParam())
 stopifnot(identical(colnames(sce),cells[keep]),identical(rownames(sce),genes[eligible]),identical(as.numeric(SingleCellExperiment::sizeFactors(sce)),as.numeric(sf)))
 # Verify the explicit formula in bounded blocks (no second normalization).
 max_error <- 0
 for(i in seq(1,nrow(sce),by=256)) {
   ix <- i:min(i+255,nrow(sce)); expected <- log2(sweep(as.matrix(SummarizedExperiment::assay(sce,"counts")[ix,,drop=FALSE]),2,sf,"/")+1)
   max_error <- max(max_error,max(abs(expected-as.matrix(SummarizedExperiment::assay(sce,"logcounts")[ix,,drop=FALSE]))))
 }
 stopifnot(max_error<1e-12)
 status$stage <- "shared_HVG"
 gv <- scran::modelGeneVar(sce,assay.type="logcounts",BPPARAM=BiocParallel::SerialParam())
 stopifnot(identical(rownames(gv),genes[eligible]),all(is.finite(gv$bio)))
 chosen <- scran::getTopHVGs(gv,n=cfg$shared_input$HVG$n,var.threshold=NULL)
 expected_hvg <- rownames(gv)[head(order(gv$bio,decreasing=TRUE),cfg$shared_input$HVG$n)]
 stopifnot(identical(chosen,expected_hvg),length(chosen)==6000,!anyDuplicated(chosen))
 shared <- sce[chosen,]
 expr <- SummarizedExperiment::assay(shared,"logcounts")
 stopifnot(all(rowSums(expr)>0),all(colSums(expr)>0),all(is.finite(expr)),min(expr)>=0)
 write_tsv(cbind(gene_id=rownames(gv),as.data.frame(gv)),file.path(out,"gene-variance.tsv"))
 gene_reason <- ifelse(htseq,"HTSeq_statistics",ifelse(ercc,"ERCC_spike_in",ifelse(eligible,"eligible_endogenous","detected_in_fewer_than_3_QC_cells")))
 write_tsv(data.frame(gene_id=genes,raw_row=seq_along(genes),feature_class=ifelse(htseq,"HTSeq",ifelse(ercc,"ERCC","endogenous")),detected_after_QC=detected_after,eligible=eligible,HVG=genes%in%chosen,reason=gene_reason),file.path(out,"gene-filter.tsv"))
 write_tsv(data.frame(cell_id=cells[keep],size_factor=sf),file.path(out,"size-factors.tsv"))
 for(n in c("raw-cell-ids","raw-gene-ids","final-cell-ids","eligible-gene-ids","hvg-gene-ids")) {
   value <- switch(n,"raw-cell-ids"=cells,"raw-gene-ids"=genes,"final-cell-ids"=cells[keep],"eligible-gene-ids"=genes[eligible],"hvg-gene-ids"=chosen)
   writeLines(value,file.path(out,paste0(n,".txt")))
 }
 status$stage <- "reference_lock_after_label_blind_QC"
 # Only now read metadata. FACS/DC are never used for QC, normalization, HVG or labels.
 meta <- readRDS(file.path(raw,"coldata.rds"));identity <- extract_metadata_identity(meta)
 ix <- match_ids(cells,identity$ids,"verified metadata cell IDs")
 labels <- identity$candidate$candidate_label[ix]
 stopifnot(length(labels)==length(cells),all(is.na(labels)|labels%in%c("LTHSC","LMPP","MPP","CMP","MEP","GMP")))
 reference <- data.frame(cell_id=cells,label=labels,label_reason=ifelse(is.na(labels),"no_broad_membership","unique_published_broad_membership"),QC_retained=keep,evaluated=keep&!is.na(labels))
 write_tsv(reference,file.path(out,"frozen-reference.tsv"))
 write_tsv(identity$memberships[match(cells,identity$memberships$cell_id),c("cell_id","LTHSC_broad","LMPP_broad","MPP_broad","CMP_broad","MEP_broad","GMP_broad")],file.path(out,"frozen-broad-memberships.tsv"))
 writeLines(reference$cell_id[reference$evaluated],file.path(out,"evaluation-cell-ids.txt"))
 write_tsv(data.frame(label=c("LTHSC","LMPP","MPP","CMP","MEP","GMP","UNASSIGNED"),before=as.integer(table(factor(ifelse(is.na(labels),"UNASSIGNED",labels),levels=c("LTHSC","LMPP","MPP","CMP","MEP","GMP","UNASSIGNED")))),after=as.integer(table(factor(ifelse(is.na(labels[keep]),"UNASSIGNED",labels[keep]),levels=c("LTHSC","LMPP","MPP","CMP","MEP","GMP","UNASSIGNED"))))),file.path(out,"label-counts.tsv"))
 saveRDS(sce,file.path(out,"eligible-normalized-sce.rds"));saveRDS(shared,file.path(out,"shared-hvg-sce.rds"))
 saveRDS(gv,file.path(out,"gene-variance.rds"))
 record_rng(out,"after_preparation")
 write_json(list(raw_genes=length(genes),raw_cells=length(cells),HTSeq_rows=sum(htseq),ERCC_rows=sum(ercc),endogenous_rows=sum(endo),retained_cells=sum(keep),excluded_cells=sum(!keep),eligible_genes=sum(eligible),HVG=length(chosen),reference_assigned_before=sum(!is.na(labels)),reference_missing_before=sum(is.na(labels)),evaluated_cells=sum(reference$evaluated),retained_unassigned=sum(keep&is.na(labels)),normalization_max_error=max_error,QC_metrics_before=lapply(qc[c("endogenous_total","endogenous_detected_genes","ERCC_percent")],function(x)as.list(unclass(summary(x)))),QC_metrics_after=lapply(qc[keep,c("endogenous_total","endogenous_detected_genes","ERCC_percent")],function(x)as.list(unclass(summary(x)))),exclusion_rule_counts=list(zero=sum(!positive),low_library=sum(low_lib),low_detected=sum(low_det),high_ERCC=sum(high_ercc)),reason_counts=as.list(setNames(as.integer(table(why)),names(table(why))))),file.path(out,"preparation-summary.json"))
 status$stage <- "final_input_protection"
 for(n in names(cfg$dataset$input_files)) stopifnot(sha_file(file.path(raw,n))==cfg$dataset$input_files[[n]])
 write_json(as.list(cfg$dataset$input_files),file.path(out,"raw-protection-after.json"))
 status$status <- "COMMON_PREPARATION_COMPLETE_NO_ALGORITHMS"
},error=function(e) {status$status<<-"FAILED";status$error<<-conditionMessage(e);message(conditionMessage(e))},finally={
 status$elapsed_seconds <- proc.time()[["elapsed"]]-start
 status$memory_status <- grep("^Vm(HWM|RSS):",readLines("/proc/self/status"),value=TRUE)
 status$config_sha256 <- sha_file(cfg_path);status$environment_signature_sha256 <- sha_file(env_path)
 write_json(status,file.path(out,"stage1-status.json"))
 writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
})
if(status$status=="FAILED") quit(status=1)
cat("COMMON_PREPARATION_COMPLETE_NO_ALGORITHMS\n")
