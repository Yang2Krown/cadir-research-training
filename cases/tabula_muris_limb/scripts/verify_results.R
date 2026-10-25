args <- commandArgs(trailingOnly = TRUE)
out <- normalizePath(args[[1]])
previous <- if (length(args) > 1) normalizePath(args[[2]]) else NULL
suppressPackageStartupMessages({library(CAdir); library(APL); library(aricode)})
read_tsv <- function(name) read.delim(file.path(out, name), check.names = FALSE, stringsAsFactors = FALSE)
cfg <- jsonlite::read_json(file.path(out, "config.json"), simplifyVector = TRUE)
metrics <- jsonlite::read_json(file.path(out, "metrics.json"), simplifyVector = TRUE)
cells <- read_tsv("cell_clusters.tsv")
genes <- read_tsv("gene_clusters.tsv")
sizes <- read_tsv("cluster_sizes.tsv")
ranks <- read_tsv("coclustered_gene_ranks.tsv")
selected <- read_tsv("selected_genes.tsv")
ca <- readRDS(file.path(out, "ca.rds"))
cadir <- readRDS(file.path(out, "cadir.rds"))
annotated <- readRDS(file.path(out, "cadir_annotated.rds"))
stopifnot(methods::validObject(cadir), methods::validObject(annotated),
          nrow(cells) == cfg$expected_cells_context_only, nrow(genes) == cfg$hvg_n,
          sum(sizes$ncells) == nrow(cells), sum(sizes$ngenes) == sum(!is.na(genes$cluster)),
          !anyDuplicated(cells$cell_id), !anyDuplicated(genes$gene_id),
          identical(cells$cell_id, rownames(ca@prin_coords_cols)),
          ncol(ca@prin_coords_cols) == cfg$ca$dims,
          identical(genes$gene_id, rownames(ca@prin_coords_rows)),
          setequal(selected$gene_id, genes$gene_id),
          identical(cells$cluster, as.character(cadir@cell_clusters)),
          setequal(genes$gene_id[!is.na(genes$cluster)], names(cadir@gene_clusters)),
          all(ranks$Rowname %in% names(cadir@gene_clusters)),
          !anyNA(cells$reference), metrics$n_evaluated == nrow(cells))
recomputed <- aricode::clustComp(cells$cluster, cells$reference)
stopifnot(abs(recomputed$ARI - metrics$ARI) < 1e-12, abs(recomputed$NMI - metrics$NMI) < 1e-12,
          aricode::ARI(cadir@cell_clusters, annotated@cell_clusters) == 1)
result <- list(status = "PASS", cells = nrow(cells), selected_genes = nrow(genes),
               assigned_genes = sum(!is.na(genes$cluster)), clusters = nrow(sizes),
               ARI = recomputed$ARI, NMI = recomputed$NMI,
               annotation_changes_partition = FALSE)
if (!is.null(previous)) {
  prior_cells <- read.delim(file.path(previous, "cell_clusters.tsv"), stringsAsFactors = FALSE)
  prior_genes <- read.delim(file.path(previous, "gene_clusters.tsv"), stringsAsFactors = FALSE)
  stopifnot(identical(cells$cell_id, prior_cells$cell_id), identical(cells$cluster, prior_cells$cluster),
            identical(genes, prior_genes))
  result$previous_run <- previous
  result$repeat_cell_assignments_identical <- TRUE
  result$repeat_gene_assignments_identical <- TRUE
}
jsonlite::write_json(result, file.path(out, "verification.json"), pretty = TRUE,
                     auto_unbox = TRUE, digits = NA)
print(result)
