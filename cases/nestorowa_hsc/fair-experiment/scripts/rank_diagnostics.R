# Separate diagnostic process. Exact stored CA basis only; no CA recomputation.
a <- commandArgs(TRUE);source(a[[1]]);load_packages()
source("cases/nestorowa_hsc/fair-experiment/scripts/admission_guard.R")
guard <- admission_guard(a[[2]],a[[3]],a[[4]],a[[5]])
seed <- as.integer(a[[6]]);core <- a[[7]];out <- a[[8]];stopifnot(seed%in%guard$config$seeds)
status <- list(status="RUNNING",seed=seed,stage="core_object_protection")
tryCatch({
 artifact_lock <- jsonlite::read_json(file.path(core,"core-artifacts-sha256.json"),simplifyVector=FALSE)
 for(e in artifact_lock$files) stopifnot(sha_file(file.path(core,e$path))==e$sha256)
 ca_path <- file.path(core,"ca.rds");unranked_path <- file.path(core,"cadir_unranked.rds")
 before_ca <- sha_file(ca_path);before_unranked <- sha_file(unranked_path)
 ca <- readRDS(ca_path);cadir <- readRDS(unranked_path)
 stopifnot(identical(rownames(ca@prin_coords_cols),names(cadir@cell_clusters)),identical(rownames(ca@prin_coords_rows),names(cadir@gene_clusters)))
 RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(seed);record_rng(out,"before_ranking")
 start <- proc.time()[["elapsed"]];status$stage <- "ranking"
 ranked <- CAdir::rank_genes(cadir=cadir,caobj=ca)
 elapsed <- proc.time()[["elapsed"]]-start;record_rng(out,"after_ranking")
 saveRDS(ranked,file.path(out,"cadir_ranked.rds"))
 ranks <- Filter(is.data.frame,ranked@gene_ranks)
 full <- if(length(ranks)) do.call(rbind,ranks) else data.frame(Rowname=character(),Score=numeric(),Row_num=integer(),Cluster=character(),Rank=integer())
 write_tsv(full,file.path(out,"complete-assigned-gene-ranks.tsv"))
 # The full upstream object includes NA/empty cluster rank entries and assignments.
 assigned <- !is.na(cadir@gene_clusters)
 expected <- names(cadir@gene_clusters)[assigned]
 stopifnot(!anyDuplicated(full$Rowname),setequal(full$Rowname,expected),all(is.finite(full$Score)))
 # Independent deterministic x-alpha*y check within this exact saved basis.
 geometry <- lapply(levels(cadir@gene_clusters),function(cluster) {
   gids <- names(cadir@gene_clusters)[which(cadir@gene_clusters==cluster)]
   if(!length(gids))return(NULL)
   d <- cadir@directions[cluster,];centroid <- colMeans(ca@prin_coords_cols[which(cadir@cell_clusters==cluster),,drop=FALSE])
   if(sum(centroid*d)<0)d <- -d
   z <- ca@prin_coords_rows[gids,,drop=FALSE];x <- drop(z%*%d)/sqrt(sum(d*d));y <- sqrt(pmax(rowSums(z*z)-x*x,0))
   data.frame(gene_id=gids,cluster=cluster,x=x,y=y)
 })
 geom <- do.call(rbind,geometry);geom <- geom[match(full$Rowname,geom$gene_id),,drop=FALSE]
 score <- geom$x-unname(ranked@parameters$alpha_genes)*geom$y
 score_error <- if(nrow(full))max(abs(score-full$Score)) else 0
 stopifnot(score_error<=1e-10)
 write_tsv(geom,file.path(out,"ranking-geometry.tsv"))
 write_json(list(seed=seed,CA_sha256=before_ca,unranked_sha256=before_unranked,alpha_genes=unname(ranked@parameters$alpha_genes),complete_ranked_genes=nrow(full),unassigned_genes=sum(!assigned),independent_score_max_error=score_error,ranking_elapsed_seconds=elapsed,memory_scope="diagnostic process VmHWM includes package and exact core-object load; separate from headline core",memory_status=grep("^Vm(HWM|RSS):",readLines("/proc/self/status"),value=TRUE),basis_scope="Only this exact stored CA basis. Seed alone is not a basis-invariance claim."),file.path(out,"ranking-provenance.json"))
 status$stage <- "plots"
 p <- CAdir::plot_clusters(cadir=ranked,caobj=ca,show_genes=TRUE,label_genes=TRUE,ntop=5,axis=TRUE,title_prefix="",ggncol=3)
 nc <- length(unique(as.character(cadir@cell_clusters)))
 for(ext in c("png","pdf")) ggplot2::ggsave(file.path(out,paste0("association-plots.",ext)),p,width=14,height=max(5,4*ceiling(nc/3)),dpi=160,bg="white")
 stopifnot(sha_file(ca_path)==before_ca,sha_file(unranked_path)==before_unranked)
 status$status <- "DIAGNOSTICS_COMPLETE_EXACT_STORED_CA"
},error=function(e) {status$status<<-"FAILED";status$error<<-conditionMessage(e);message(conditionMessage(e))},finally={
 write_json(status,file.path(out,"diagnostic-status.json"));writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
})
if(status$status=="FAILED")quit(status=1)
