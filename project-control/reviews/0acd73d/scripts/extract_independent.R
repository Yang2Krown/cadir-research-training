suppressPackageStartupMessages(library(SingleCellExperiment))
root <- '/workspace/cadir-stage1-retest'
out <- jsonlite::read_json(file.path(root,'complete-entry/latest-case.json'))$run_directory
sce <- readRDS('/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds')
write.table(data.frame(cell_id=colnames(sce),reference=as.character(colData(sce)$cell_ontology_class)),file.path(root,'evidence/original_labels.tsv'),sep='\t',quote=TRUE,row.names=FALSE)
suppressPackageStartupMessages({library(APL);library(CAdir)})
obj <- readRDS(file.path(out,'cadir.rds'))
ca <- readRDS(file.path(out,'ca.rds'))
genes <- read.delim(file.path(out,'gene_clusters.tsv'))
ranks <- read.delim(file.path(out,'coclustered_gene_ranks.tsv'))
expected <- setNames(as.character(obj@gene_clusters),names(obj@gene_clusters))[genes$gene_id]
eq_na <- (is.na(expected)&is.na(genes$cluster)) | (!is.na(expected)&!is.na(genes$cluster)&expected==genes$cluster)
er <- do.call(rbind,obj@gene_ranks); er <- er[match(ranks$Rowname,er$Rowname),]
env <- new.env(parent=globalenv())
sys.source('/workspace/cadir-env/sources/CAdir/R/apl.R',env)
sys.source('/workspace/cadir-env/sources/CAdir/R/genes.R',env)
funcheck <- lapply(c('rank_genes','get_apl_cutoff','random_direction_cutoff','apl_model'),function(n){a<-get(n,env);b<-get(n,asNamespace('CAdir'));list(name=n,formals_identical=identical(formals(a),formals(b)),body_identical=identical(body(a),body(b)))})
evidence <- list(alpha_genes=obj@parameters$alpha_genes,all_6000_gene_cluster_NA_identical=all(eq_na),gene_rows=nrow(genes),assigned=sum(!is.na(genes$cluster)),unassigned=sum(is.na(genes$cluster)),ranking_rows=nrow(ranks),ranking_clusters_identical=identical(as.character(ranks$Cluster),as.character(er$Cluster)),ranking_score_max_abs=max(abs(ranks$Score-er$Score)),ranking_rank_identical=identical(as.numeric(ranks$Rank),as.numeric(er$Rank)),ranking_row_num_identical=identical(as.numeric(ranks$Row_num),as.numeric(er$Row_num)),ca_dimensions=dim(ca@prin_coords_cols),installed_functions_vs_fixed_source=funcheck)
stopifnot(evidence$all_6000_gene_cluster_NA_identical,evidence$ranking_score_max_abs<=1e-10,evidence$ranking_rank_identical,evidence$ranking_row_num_identical)
jsonlite::write_json(evidence,file.path(root,'evidence/independent_object_check.json'),pretty=TRUE,auto_unbox=TRUE,digits=NA)
