# Independent read-only verification of saved objects, without decomposition/clustering/ranking calls.
args <- commandArgs(TRUE)
root <- args[1]; stage <- args[2]; out <- args[3]
suppressPackageStartupMessages({library(APL);library(CAdir);library(SingleCellExperiment);library(igraph);library(jsonlite)})
readtab <- function(p) read.delim(p,stringsAsFactors=FALSE,check.names=FALSE)
checks <- list(); k <- 0L
check <- function(n,ok,detail='') { k <<- k+1L; checks[[k]] <<- data.frame(check=n,passed=isTRUE(ok),detail=as.character(detail)); if(!isTRUE(ok))stop(n) }
cells <- readLines(file.path(stage,'final-cell-ids.txt')); genes <- readLines(file.path(stage,'hvg-gene-ids.txt'))
sce <- readRDS(file.path(stage,'shared-hvg-sce.rds'))
check('shared_SCE_dimensions_and_explicit_IDs',identical(dim(sce),c(6000L,1656L))&&identical(colnames(sce),cells)&&identical(rownames(sce),genes))
rows <- list()
for(seed in c(2358,101,202,303,404)) for(method in c('cadir','pca_snn_louvain')) {
 tag <- paste(method,seed,sep='_'); p <- file.path(root,paste0(method,'-seed-',seed,'-attempt-01'))
 part <- readRDS(file.path(p,'cell-partition.rds')); tab <- readtab(file.path(p,'cell-partition.tsv'))
 check(paste0(tag,'_partition_RDS_TSV'),identical(names(part),cells)&&identical(as.character(part),as.character(tab$cluster))&&identical(tab$cell_id,cells))
 rng <- readRDS(file.path(p,'rng.rds')); expected <- if(method=='cadir') c('before_CA','after_CA','before_CAdir','after_CAdir') else c('before_PCA','after_PCA','before_SNN','after_SNN','before_Louvain','after_Louvain')
 check(paste0(tag,'_RNG_state_records'),identical(names(rng),expected)&&all(vapply(rng,function(x) identical(x$kind,c('Mersenne-Twister','Inversion','Rejection'))&&is.integer(x$state)&&length(x$state)==626L,logical(1))))
 set.seed(seed); starting <- .Random.seed
 check(paste0(tag,'_RNG_matches_seed'),identical(rng[[1]]$state,starting))
 if(method=='pca_snn_louvain') {
  pc <- readRDS(file.path(p,'pca.rds')); g <- readRDS(file.path(p,'snn-graph.rds')); com <- readRDS(file.path(p,'louvain.rds'))
  check(paste0(tag,'_PCA_graph_community'),identical(dim(pc),c(1656L,30L))&&identical(rownames(pc),cells)&&all(is.finite(pc))&&identical(V(g)$name,cells)&&vcount(g)==1656&&all(is.finite(E(g)$weight))&&all(E(g)$weight>=0)&&identical(membership(com),part))
 } else {
  ca <- readRDS(file.path(p,'ca.rds')); u <- readRDS(file.path(p,'cadir_unranked.rds')); z <- readRDS(file.path(p,'diagnostics/cadir_ranked.rds'))
  check(paste0(tag,'_CA_IDs_dimensions_finiteness'),identical(dim(ca@prin_coords_rows),c(6000L,30L))&&identical(dim(ca@prin_coords_cols),c(1656L,30L))&&identical(rownames(ca@prin_coords_rows),genes)&&identical(rownames(ca@prin_coords_cols),cells)&&all(is.finite(ca@prin_coords_rows))&&all(is.finite(ca@prin_coords_cols))&&all(ca@D>1e-6))
  check(paste0(tag,'_ranked_preserves_native_partitions_directions'),identical(u@cell_clusters,z@cell_clusters)&&identical(u@gene_clusters,z@gene_clusters)&&identical(u@directions,z@directions)&&identical(u@cell_clusters,part))
  gp <- readtab(file.path(p,'gene-partition.tsv')); native <- u@gene_clusters
  matched <- match(genes,names(native)); cls <- as.character(native)[matched]
  check(paste0(tag,'_full_gene_partition_native_ID_match'),identical(gp$gene_id,genes)&&identical(gp$cluster,cls)&&identical(gp$in_upstream_gene_subset,!is.na(matched))&&identical(gp$assigned,!is.na(cls))&&length(native)==1200&&sum(gp$assigned)==1200)
  check(paste0(tag,'_excluded_gene_reason'),all(gp$reason[!gp$assigned]=='excluded_by_upstream_ca_sphere_qcutoff')&&sum(!gp$assigned)==4800)
  ranks <- readtab(file.path(p,'diagnostics/complete-assigned-gene-ranks.tsv')); geom <- readtab(file.path(p,'diagnostics/ranking-geometry.tsv'))
  check(paste0(tag,'_rank_coverage_clusters'),nrow(ranks)==1200&&!anyDuplicated(ranks$Rowname)&&setequal(ranks$Rowname,names(native)[!is.na(native)])&&identical(as.character(ranks$Cluster),as.character(native[match(ranks$Rowname,names(native))])))
  rdsr <- do.call(rbind,Filter(is.data.frame,z@gene_ranks))
  check(paste0(tag,'_rank_RDS_TSV'),identical(as.character(rdsr$Rowname),ranks$Rowname)&&max(abs(rdsr$Score-ranks$Score))<1e-12)
  alpha <- unname(z@parameters$alpha_genes); check(paste0(tag,'_alpha_finite'),length(alpha)==1&&is.finite(alpha)&&alpha>0,alpha)
  # Normalize direction and compute orthogonal residual directly for every assigned gene.
  independent <- lapply(seq_len(nrow(ranks)),function(i){
   cl <- as.character(ranks$Cluster[i]); d <- as.numeric(u@directions[cl,]); unit <- d/sqrt(sum(d^2))
   centroid <- colMeans(ca@prin_coords_cols[as.character(part)==cl,,drop=FALSE])
   if(sum(unit*centroid)<0) unit <- -unit
   v <- as.numeric(ca@prin_coords_rows[ranks$Rowname[i],]); x <- sum(v*unit); y <- sqrt(sum((v-x*unit)^2))
   c(x=x,y=y,score=x-alpha*y)
  })
  independent <- do.call(rbind,independent); err <- max(abs(independent[,'score']-ranks$Score)); gidx <- match(ranks$Rowname,geom$gene_id)
  check(paste0(tag,'_independent_saved_basis_geometry'),all(is.finite(independent))&&err<1e-10&&max(abs(independent[,'x']-geom$x[gidx]))<1e-10&&max(abs(independent[,'y']-geom$y[gidx]))<1e-10,format(err,digits=16))
  for(cl in unique(ranks$Cluster)) {q<-ranks[ranks$Cluster==cl,];check(paste0(tag,'_rank_order_',cl),identical(as.integer(q$Rank),seq_len(nrow(q)))&&all(diff(q$Score)<=1e-12))}
  drng <- readRDS(file.path(p,'diagnostics/rng.rds')); check(paste0(tag,'_diagnostic_RNG_present'),length(drng)>0)
  rows[[length(rows)+1L]] <- data.frame(seed=seed,alpha=alpha,assigned=length(native),excluded=6000-length(native),score_max_error=err)
 }
}
write.table(do.call(rbind,checks),file.path(out,'object-checks.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write.table(do.call(rbind,rows),file.path(out,'independent-geometry.tsv'),sep='\t',quote=FALSE,row.names=FALSE)
write_json(list(status='PASS_READ_ONLY_SAVED_OBJECTS',checks=k,recomputed_decomposition=FALSE,recomputed_clustering=FALSE,recomputed_ranking=FALSE),file.path(out,'object-result.json'),pretty=TRUE,auto_unbox=TRUE)
writeLines(capture.output(sessionInfo()),file.path(out,'sessionInfo.txt'))
