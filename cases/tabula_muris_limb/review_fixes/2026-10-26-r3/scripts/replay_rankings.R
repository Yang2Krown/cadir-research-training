# Read-only historical inputs; reflections and all outputs are diagnostics only.
args <- commandArgs(trailingOnly=TRUE)
for (pkg in c("SingleCellExperiment","scran","APL","CAdir","aricode","ggplot2")) {
  suppressPackageStartupMessages(library(pkg,character.only=TRUE))
}
base_dir <- args[[1]]; review_dir <- args[[2]]; out <- args[[3]]
cfg <- jsonlite::read_json(file.path(review_dir,"text-export/text/rerun/runtime_config.json"),simplifyVector=TRUE)
base_ca <- readRDS(file.path(base_dir,"ca.rds"))
base_unranked <- readRDS(file.path(base_dir,"cadir_unranked.rds"))
review_ca <- readRDS(file.path(review_dir,"ca.rds"))
review_unranked <- readRDS(file.path(review_dir,"cadir_unranked.rds"))
base_ranks <- read.delim(file.path(base_dir,"coclustered_gene_ranks.tsv"),stringsAsFactors=FALSE)
review_ranks <- read.delim(file.path(review_dir,"text-export/text/rerun/full/coclustered_gene_ranks.tsv"),stringsAsFactors=FALSE)
signs <- sign(colSums(base_ca@prin_coords_cols*review_ca@prin_coords_cols))
stopifnot(!any(signs==0),identical(names(base_unranked@cell_clusters),names(review_unranked@cell_clusters)),
          identical(names(base_unranked@gene_clusters),names(review_unranked@gene_clusters)))
reflect <- function(ca,cadir) {
  for(n in c("U","V","std_coords_rows","std_coords_cols","prin_coords_rows","prin_coords_cols")) {
    methods::slot(ca,n) <- sweep(methods::slot(ca,n),2,signs,"*")
  }
  cadir@directions <- sweep(cadir@directions,2,signs,"*")
  list(ca=ca,cadir=cadir)
}
base_reflected <- reflect(base_ca,base_unranked)
review_reflected <- reflect(review_ca,review_unranked)
variants <- list(baseline_observed=list(ca=base_ca,cadir=base_unranked),
                 review_observed=list(ca=review_ca,cadir=review_unranked),
                 baseline_reflected_to_review=base_reflected,
                 review_reflected_to_baseline=review_reflected)
compare_ranks <- function(x,y) {
  y <- y[match(x$Rowname,y$Rowname),,drop=FALSE]
  list(genes=nrow(x),same_gene_cluster_pairs=identical(x$Rowname,y$Rowname) && identical(x$Cluster,y$Cluster),
       maximum_score_absolute_error=max(abs(x$Score-y$Score)),
       scores_within_1e_10=all(abs(x$Score-y$Score)<=1e-10),rank_changes=sum(x$Rank!=y$Rank),
       full_rank_identical=identical(x$Rank,y$Rank))
}
geometry <- function(ca,cadir) {
  result <- lapply(levels(cadir@gene_clusters),function(cluster) {
    d <- cadir@directions[cluster,]
    centroid <- colMeans(ca@prin_coords_cols[which(cadir@cell_clusters==cluster),,drop=FALSE])
    if(sum(centroid*d)<0)d <- -d
    genes <- names(cadir@gene_clusters)[which(cadir@gene_clusters==cluster)]
    z <- ca@prin_coords_rows[genes,,drop=FALSE]
    x <- drop(z%*%d)/sqrt(sum(d*d)); y <- sqrt(pmax(rowSums(z*z)-x*x,0))
    data.frame(Rowname=genes,Cluster=cluster,x=x,y=y)
  })
  do.call(rbind,result)
}
results <- list(); ranked_tables <- list(); geometries <- list(); rng_states <- list()
for(name in names(variants)) {
  v <- variants[[name]]
  stopifnot(is.null(v$cadir@parameters$alpha_genes))
  RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(cfg$seed)
  rng_states[[paste0(name,"_before")]] <- as.integer(.Random.seed)
  ranked <- CAdir::rank_genes(cadir=v$cadir,caobj=v$ca)
  rng_states[[paste0(name,"_after")]] <- as.integer(.Random.seed)
  table <- do.call(rbind,Filter(is.data.frame,ranked@gene_ranks))
  ranked_tables[[name]] <- table
  geom <- geometry(v$ca,v$cadir);geom <- geom[match(table$Rowname,geom$Rowname),,drop=FALSE]
  geometries[[name]] <- geom
  independent_scores <- geom$x-unname(ranked@parameters$alpha_genes)*geom$y
  results[[name]] <- list(alpha=unname(ranked@parameters$alpha_genes),
                         comparison_to_frozen_baseline=compare_ranks(table,base_ranks),
                         comparison_to_old_review=compare_ranks(table,review_ranks),
                         independent_geometry_score_max_error=max(abs(independent_scores-table$Score)))
  write.table(table,file.path(out,paste0(name,"_ranks.tsv")),sep="\t",quote=TRUE,row.names=FALSE)
}
review_geom <- geometries$review_observed[match(geometries$baseline_observed$Rowname,geometries$review_observed$Rowname),]
slot_comparison <- lapply(methods::slotNames(base_unranked),function(n) {
  x <- methods::slot(base_unranked,n);y <- methods::slot(review_unranked,n)
  list(slot=n,identical=identical(x,y),class=class(x))
})
result <- list(seed=cfg$seed,RNGkind=RNGkind(),flipped_axes=which(signs == -1),
  cell_assignments_identical=identical(as.character(base_unranked@cell_clusters),as.character(review_unranked@cell_clusters)),
  gene_assignments_identical=identical(as.character(base_unranked@gene_clusters),as.character(review_unranked@gene_clusters)),
  direction_error_after_sign_alignment=max(abs(sweep(base_unranked@directions,2,signs,"*")-review_unranked@directions)),
  observed_gene_projection_max_difference=max(abs(geometries$baseline_observed$x-review_geom$x)),
  observed_gene_orthogonal_distance_max_difference=max(abs(geometries$baseline_observed$y-review_geom$y)),
  ranking_replays=results,unranked_slot_comparison=slot_comparison,
  old_runtime_RNG_snapshot_received=FALSE,
  actual_old_unranked_received=TRUE,
  scope="Historical CA and unranked objects read directly. Counterfactual reflections affect diagnostic copies only; no CA recomputation, original-data pipeline, parameter search or algorithm modification.")
jsonlite::write_json(result,file.path(out,"ranking_replays.json"),pretty=TRUE,auto_unbox=TRUE,digits=NA)
jsonlite::write_json(rng_states,file.path(out,"diagnostic_rng_states.json"),pretty=TRUE,auto_unbox=TRUE,digits=NA)
# Check the two factual replays and the two sign-only counterfactual predictions.
stopifnot(result$cell_assignments_identical,result$gene_assignments_identical,
          results$baseline_observed$comparison_to_frozen_baseline$scores_within_1e_10,
          results$baseline_observed$comparison_to_frozen_baseline$full_rank_identical,
          results$review_observed$comparison_to_old_review$scores_within_1e_10,
          results$review_observed$comparison_to_old_review$full_rank_identical,
          results$baseline_reflected_to_review$comparison_to_old_review$scores_within_1e_10,
          results$baseline_reflected_to_review$comparison_to_old_review$full_rank_identical,
          results$review_reflected_to_baseline$comparison_to_frozen_baseline$scores_within_1e_10,
          results$review_reflected_to_baseline$comparison_to_frozen_baseline$full_rank_identical)
print(result[1:9])
