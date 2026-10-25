# Recompute GOA only on saved assignments. No feature selection, CA or CAdir run.
args <- commandArgs(trailingOnly=TRUE)
review <- normalizePath(args[[1]])
case <- normalizePath(file.path(review,"../.."))
run <- file.path(case,"runs/case-ppkaow9s")
if (!file.exists(file.path(run,"cadir.rds"))) {
  run <- jsonlite::read_json(file.path(review,"freeze/baseline_manifest.json"))$final_run
}
suppressPackageStartupMessages({library(CAdir); library(jsonlite)})
write_tsv <- function(x,name) write.table(x,file.path(review,"annotation",name),sep="\t",quote=TRUE,row.names=FALSE,na="NA")
cadir <- readRDS(file.path(run,"cadir.rds"))
saved <- readRDS(file.path(run,"cadir_annotated.rds"))
genes <- read.delim(file.path(run,"gene_clusters.tsv"),stringsAsFactors=FALSE)
universe <- genes$gene_id
gs <- CAdir::load_ct_gene_set(set="CellMarker",org="mm")
frozen_gs <- read.delim(file.path(run,"annotation_cellmarker_mouse.tsv"),stringsAsFactors=FALSE)
stopifnot(identical(as.character(gs$cell_type), frozen_gs$cell_type), identical(as.character(gs$gene),frozen_gs$gene))
goa <- CAdir::goa_per_cluster(cadir=cadir,universe=universe,org="mm",set="CellMarker",min_size=10,max_size=500,filter_literature=FALSE)
sets <- getFromNamespace("make_gene_set_list","CAdir")(gs,filter_literature=FALSE)
sets <- lapply(sets,intersect,universe)
resource_universe <- unique(unlist(sets))
all_results <- list()
for (cluster in names(goa)) {
  df <- goa[[cluster]]
  df$cluster <- cluster
  df$rank_within_cluster <- seq_len(nrow(df))
  cg <- names(cadir@gene_clusters)[as.character(cadir@gene_clusters)==cluster]
  df$support_genes <- vapply(df$gene_set,function(s) paste(sort(intersect(cg,sets[[s]])),collapse=";"),character(1))
  support_n <- vapply(df$gene_set,function(s) length(intersect(cg,sets[[s]])),integer(1))
  stopifnot(all(support_n==df$ngois_in_set))
  all_results[[cluster]] <- df
}
all_df <- do.call(rbind,all_results)
write_tsv(all_df,"goa_all.tsv")
write_tsv(all_df[all_df$rank_within_cluster<=10,],"goa_top10.tsv")
# Match annotate_by_gse: retain the first nclusters candidates, then solve the
# joint assignment, then apply alpha. Do not replace with independent best hits.
top_candidates <- lapply(goa,function(x) x[seq_len(min(nrow(x),length(goa))),,drop=FALSE])
assignment <- CAdir::run_hungarian(top_candidates,cost="logpval")
write_tsv(assignment,"hungarian_assignments.tsv")
reproduced <- CAdir::annotate_by_gse(cadir,gse_res=goa,alpha=.05,cost="logpval")
stopifnot(identical(as.character(reproduced@cell_clusters),as.character(saved@cell_clusters)),
          identical(as.character(reproduced@gene_clusters),as.character(saved@gene_clusters)))
decisions <- list()
support_long <- list()
for (cluster in names(goa)) {
  df <- all_results[[cluster]]
  a <- assignment[assignment$cluster==cluster,,drop=FALSE]
  predicted <- unique(as.character(saved@cell_clusters[as.character(cadir@cell_clusters)==cluster]))
  stopifnot(length(predicted)==1)
  assigned_set <- if(nrow(a)) as.character(a$cell_type[1]) else NA_character_
  assigned_row <- df[df$gene_set==assigned_set & !is.na(assigned_set),,drop=FALSE]
  cg <- names(cadir@gene_clusters)[as.character(cadir@gene_clusters)==cluster]
  decisions[[cluster]] <- data.frame(cluster=cluster,original_prediction=predicted,
    coclustered_genes=length(cg),resource_mapped_genes=length(intersect(cg,resource_universe)),
    tested_sets_with_overlap=nrow(df),significant_sets_BH_005=sum(df$padj<=.05,na.rm=TRUE),
    best_gene_set=df$gene_set[1],best_pval=df$pval[1],best_padj=df$padj[1],best_support_genes=df$support_genes[1],
    hungarian_gene_set=assigned_set, hungarian_cost=if(nrow(a)) a$cost[1] else NA_real_,
    hungarian_candidate_tested=nrow(assigned_row)>0,
    hungarian_pval=if(nrow(assigned_row)) assigned_row$pval[1] else NA_real_,
    hungarian_padj=if(nrow(assigned_row)) assigned_row$padj[1] else NA_real_,
    hungarian_support_genes=if(nrow(assigned_row)) assigned_row$support_genes[1] else NA_character_,
    annotation_accepted=predicted!=cluster)
  for (role in c("best_candidate","hungarian_candidate")) {
    set <- if(role=="best_candidate") as.character(df$gene_set[1]) else assigned_set
    support <- if(is.na(set)) character() else sort(intersect(cg,sets[[set]]))
    if(length(support)) support_long[[paste(cluster,role)]] <- data.frame(cluster=cluster,role=role,gene_set=set,gene=support)
  }
}
write_tsv(do.call(rbind,decisions),"annotation_decisions.tsv")
write_tsv(do.call(rbind,support_long),"support_genes_long.tsv")
raw <- CAdir::cellmarker_v2
raw_match <- raw[raw$species=="Mouse" & gsub(" ","_",raw$cell_name)=="Schwalie_et_al.Nature.P1",,drop=FALSE]
flat <- vapply(raw_match,function(x) is.atomic(x) || is.factor(x),logical(1))
write_tsv(raw_match[,flat,drop=FALSE],"schwalie_resource_records.tsv")
capture.output(sessionInfo(),file=file.path(review,"annotation/sessionInfo.txt"))
write_json(list(status="PASS",saved_annotations_reproduced=TRUE,clustering_repeated=FALSE,
  resource_records=nrow(gs),supplied_universe=length(universe),resource_union_in_universe=length(resource_universe),
  alpha=.05,min_size=10,max_size=500,filter_literature=FALSE,cost="logpval",top_candidates_per_cluster=length(goa),
  significance_scope="Upstream compute_goa: BH within each cluster over eligible gene sets with positive overlap; background is union of all resource genes intersected with the supplied universe before size filtering.",
  hungarian_scope="Missing cluster/set entries in the joint candidate matrix have cost 0; assignment is followed by alpha=0.05 gating."
),file.path(review,"annotation/review_status.json"),pretty=TRUE,auto_unbox=TRUE,digits=NA)
print(do.call(rbind,decisions))
