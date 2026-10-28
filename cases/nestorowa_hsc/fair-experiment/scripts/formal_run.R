# This is a formal runner, not a smoke-test. Admission is required before data access.
a <- commandArgs(TRUE);source(a[[1]]);load_packages()
source("cases/nestorowa_hsc/fair-experiment/scripts/admission_guard.R")
guard <- admission_guard(a[[2]],a[[3]],a[[4]],a[[5]])
source("cases/nestorowa_hsc/fair-experiment/scripts/gene_partition.R")
cfg <- guard$config;lock <- guard$lock;method <- a[[6]];seed <- as.integer(a[[7]]);out <- a[[8]]
stopifnot(method%in%c("cadir","pca_snn_louvain"),seed%in%cfg$seeds,!file.exists(file.path(out,"run-status.json")))
status <- list(status="RUNNING",method=method,seed=seed,stage="shared_input_load")
ca <- cadir <- pca <- graph <- community <- NULL;rng <- list()
rec <- function(n) rng[[n]] <<- list(kind=RNGkind(),state=.Random.seed)
tryCatch({
 sce <- readRDS(lock$shared_input_path);cells <- colnames(sce);genes <- rownames(sce)
 stopifnot(identical(cells,readLines(lock$final_cell_ids_path)),identical(genes,readLines(lock$HVG_ids_path)),length(genes)==cfg$shared_input$HVG$n)
 expr <- SummarizedExperiment::assay(sce,"logcounts")
 stopifnot(all(is.finite(expr)),min(expr)>=0,all(rowSums(expr)>0),all(colSums(expr)>0))
 RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(seed)
 status$stage <- "core"
 sentinel <- file.path(out,"core.running");file.create(sentinel)
 sampler <- "cases/nestorowa_hsc/fair-experiment/scripts/sample_rss.sh"
 system2("sh",c(shQuote(sampler),Sys.getpid(),shQuote(sentinel)),stdout=file.path(out,"core-rss-KiB.txt"),stderr=file.path(out,"core-sampler.log"),wait=FALSE)
 write_json(list(start_utc=format(Sys.time(),tz="UTC",usetz=TRUE),method=method,seed=seed),file.path(out,"core-start.json"))
 t0 <- proc.time()[["elapsed"]]
 if(method=="cadir") {
  set.seed(seed);rec("before_CA")
  ca <- do.call(APL::cacomp,c(list(obj=expr),cfg$CAdir$CA));rec("after_CA")
  stopifnot(identical(rownames(ca@prin_coords_cols),cells),identical(rownames(ca@prin_coords_rows),genes),ncol(ca@prin_coords_cols)==cfg$CAdir$CA$dims,all(is.finite(ca@prin_coords_cols)),min(ca@D)>1e-6)
  z <- cfg$CAdir$dirclust_splitmerge;set.seed(seed);rec("before_CAdir")
  # Symbolic caobj call keeps an entire CA object out of match.call metadata.
  cadir <- CAdir::dirclust_splitmerge(caobj=ca,k=z$k,cutoff=z$cutoff,method=z$method,apl_quant=z$apl_quant,counts=z$counts,min_cells=z$min_cells,epochs=z$epochs,reps=z$reps,make_plots=z$make_plots,qcutoff=z$qcutoff,convergence_thr=z$convergence_thr,max_iter=z$max_iter,init=z$init,keep_log=z$keep_log,apl_cutoff_reps=z$apl_cutoff_reps)
  rec("after_CAdir");pred <- cadir@cell_clusters
  stopifnot(identical(names(pred),cells),length(pred)==length(cells),!anyNA(pred))
 } else {
  rec("before_PCA")
  sce <- scater::runPCA(sce,assay.type="logcounts",ncomponents=cfg$baseline$PCA$ncomponents,ntop=Inf,subset_row=seq_len(nrow(sce)),scale=FALSE,BSPARAM=BiocSingular::IrlbaParam(deferred=FALSE,fold=Inf,extra.work=7,tol=1e-5,maxit=1000),BPPARAM=BiocParallel::SerialParam())
  pca <- SingleCellExperiment::reducedDim(sce,"PCA");rec("after_PCA")
  stopifnot(identical(rownames(pca),cells),ncol(pca)==30,all(is.finite(pca)),length(attr(pca,"varExplained"))==30,min(attr(pca,"varExplained"))>1e-12)
  rec("before_SNN");graph <- scran::buildSNNGraph(pca,d=NA,transposed=TRUE,k=cfg$baseline$SNN$k,type=cfg$baseline$SNN$type,BNPARAM=BiocNeighbors::KmknnParam(),BPPARAM=BiocParallel::SerialParam());rec("after_SNN")
  stopifnot(igraph::vcount(graph)==length(cells));igraph::V(graph)$name <- cells
  rec("before_Louvain");community <- igraph::cluster_louvain(graph,weights=igraph::E(graph)$weight,resolution=cfg$baseline$Louvain$resolution);rec("after_Louvain")
  pred <- igraph::membership(community);stopifnot(identical(names(pred),cells),!anyNA(pred))
 }
 elapsed <- proc.time()[["elapsed"]]-t0
 memory <- grep("^Vm(HWM|RSS):",readLines("/proc/self/status"),value=TRUE)
 unlink(sentinel)
 rss <- suppressWarnings(as.numeric(readLines(file.path(out,"core-rss-KiB.txt"),warn=FALSE)));rss <- rss[is.finite(rss)]
 write_json(list(core_elapsed_seconds=elapsed,sampled_peak_rss_KiB=if(length(rss)) max(rss) else NULL,rss_samples=length(rss),process_memory_at_core_end=memory,scope=if(method=="cadir") "CA+splitmerge and lightweight RNG/shape checks; output serialization and ranking excluded" else "PCA+rank-SNN+Louvain and lightweight RNG/shape checks; output serialization excluded",memory_note="50ms sampled stage RSS can miss spikes. VmHWM includes packages and input loading; no unmatched-scope RAM superiority claim."),file.path(out,"core-resources.json"))
 writeLines(format(Sys.time(),tz="UTC",usetz=TRUE),file.path(out,"core-complete.txt"))
 status$stage <- "save_core_outputs"
 saveRDS(rng,file.path(out,"rng.rds"));saveRDS(pred,file.path(out,"cell-partition.rds"))
 write_tsv(data.frame(cell_id=cells,cluster=as.character(pred)),file.path(out,"cell-partition.tsv"))
 write_tsv(as.data.frame(table(cluster=as.character(pred))),file.path(out,"cluster-sizes.tsv"))
 if(method=="cadir") {
  saveRDS(ca,file.path(out,"ca.rds"));saveRDS(cadir,file.path(out,"cadir_unranked.rds"))
  gene_partition <- map_gene_partition(cadir@gene_clusters,genes,rownames(cadir@directions))
  write_gene_partition(gene_partition,out,cfg$CAdir$dirclust_splitmerge$qcutoff)
  pivots <- apply(abs(ca@prin_coords_cols),2,which.max)
  write_json(list(axis_names=colnames(ca@prin_coords_cols),cell_pivot_ids=cells[pivots],cell_pivot_signs=sign(ca@prin_coords_cols[cbind(pivots,seq_along(pivots))]),singular_values=ca@D,CA_basis_sha256=sha_file(file.path(out,"ca.rds")),ranking_scope="Reuse this exact CA object; no independent CA recomputation or sign/rotation claims"),file.path(out,"ca-basis.json"))
  write_tsv(cadir@log$clusters,file.path(out,"splitmerge-history.tsv"));capture.output(cadir@parameters,file=file.path(out,"effective-cadir-parameters.txt"))
 } else {saveRDS(pca,file.path(out,"pca.rds"));saveRDS(graph,file.path(out,"snn-graph.rds"));saveRDS(community,file.path(out,"louvain.rds"))}
 status$stage <- "evaluation"
 source("cases/nestorowa_hsc/fair-experiment/scripts/evaluate.R")
 reference <- read.delim(lock$reference_path,na.strings="NA",stringsAsFactors=FALSE)
 eval_ids <- readLines(lock$evaluation_ids_path)
 stopifnot(identical(eval_ids,reference$cell_id[reference$evaluated]),all(eval_ids%in%cells))
 evaluate_partitions(pred,reference,eval_ids,out)
 status$status <- "FORMAL_CORE_COMPLETE"
},error=function(e) {status$status<<-"FAILED";status$error<<-conditionMessage(e);message(conditionMessage(e))},finally={
 unlink(file.path(out,"core.running"))
 # Preserve partial objects and RNG on all failures; never overwrite an older attempt.
 if(status$status=="FAILED") {
  for(n in c("ca","cadir","pca","graph","community")) if(!is.null(get(n))) saveRDS(get(n),file.path(out,paste0("partial-",n,".rds")))
  saveRDS(rng,file.path(out,"partial-rng.rds"))
 }
 write_json(status,file.path(out,"run-status.json"));writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
})
if(status$status=="FAILED") quit(status=1)
