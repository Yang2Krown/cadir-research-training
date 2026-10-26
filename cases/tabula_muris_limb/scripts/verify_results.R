args <- commandArgs(trailingOnly = TRUE)
out <- normalizePath(args[[1]])
previous <- if (length(args) > 1) normalizePath(args[[2]]) else NULL
verification_path <- file.path(out, "verification.json")
write_verification <- function(value) {
  jsonlite::write_json(value, verification_path, pretty = TRUE, auto_unbox = TRUE, digits = NA)
}
# Replace a previous PASS before reading artifacts; every caught failure becomes FAIL.
write_verification(list(status = "RUNNING"))
verify <- function() {
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
# Reconstruct all selected genes by ID, including the unassigned NA entries.
object_gene_clusters <- setNames(as.character(cadir@gene_clusters), names(cadir@gene_clusters))
stopifnot("Object gene IDs must be unique and belong to CA" =
            !anyDuplicated(names(object_gene_clusters)) &&
            all(names(object_gene_clusters) %in% genes$gene_id),
          "Per-gene cluster/NA mismatch against cadir.rds" =
            identical(as.character(genes$cluster), unname(object_gene_clusters[genes$gene_id])))
cluster_ids <- levels(cadir@cell_clusters)
stopifnot("Cluster-size IDs mismatch" = !anyDuplicated(sizes$cluster) &&
            setequal(sizes$cluster, cluster_ids),
          "Assigned gene cluster outside cell clusters" =
            all(na.omit(genes$cluster) %in% cluster_ids))
size_index <- match(cluster_ids, sizes$cluster)
stopifnot("Per-cluster cell counts mismatch" =
            identical(as.integer(sizes$ncells[size_index]),
                      as.integer(table(factor(cells$cluster, levels = cluster_ids)))),
          "Per-cluster gene counts mismatch" =
            identical(as.integer(sizes$ngenes[size_index]),
                      as.integer(table(factor(genes$cluster, levels = cluster_ids)))))
# Match complete ranking rows to the saved object, not just membership in its genes.
expected_ranks <- do.call(rbind, Filter(is.data.frame, cadir@gene_ranks))
rank_columns <- c("Rowname", "Cluster", "Score", "Rank", "Row_num")
stopifnot("Ranking schema mismatch" = all(rank_columns %in% names(ranks)),
          "Ranking must contain every assigned gene once" =
            !anyDuplicated(ranks$Rowname) && nrow(ranks) == length(object_gene_clusters) &&
            setequal(ranks$Rowname, names(object_gene_clusters)),
          "Object ranking must contain every assigned gene once" =
            !anyDuplicated(expected_ranks$Rowname) &&
            setequal(expected_ranks$Rowname, names(object_gene_clusters)))
expected_ranks <- expected_ranks[match(ranks$Rowname, expected_ranks$Rowname), , drop = FALSE]
stopifnot("Ranking gene/cluster mismatch against cadir.rds" =
            identical(as.character(ranks$Cluster), as.character(expected_ranks$Cluster)) &&
            identical(as.character(ranks$Cluster), unname(object_gene_clusters[ranks$Rowname])),
          "Ranking Score mismatch against cadir.rds (absolute tolerance 1e-10)" =
            all(is.finite(ranks$Score)) && all(is.finite(expected_ranks$Score)) &&
            all(abs(ranks$Score - expected_ranks$Score) <= 1e-10),
          "Ranking Rank mismatch against cadir.rds" =
            identical(as.numeric(ranks$Rank), as.numeric(expected_ranks$Rank)),
          "Ranking Row_num mismatch against cadir.rds" =
            identical(as.numeric(ranks$Row_num), as.numeric(expected_ranks$Row_num)))
recomputed <- aricode::clustComp(cells$cluster, cells$reference)
stopifnot(abs(recomputed$ARI - metrics$ARI) < 1e-12, abs(recomputed$NMI - metrics$NMI) < 1e-12,
          aricode::ARI(cadir@cell_clusters, annotated@cell_clusters) == 1)
result <- list(status = "PASS", cells = nrow(cells), selected_genes = nrow(genes),
               assigned_genes = sum(!is.na(genes$cluster)), clusters = nrow(sizes),
               ARI = recomputed$ARI, NMI = recomputed$NMI,
               annotation_changes_partition = FALSE,
               per_gene_cluster_including_NA = TRUE, per_cluster_counts = TRUE,
               ranking_gene_cluster_score_rank_row_num = TRUE, score_absolute_tolerance = 1e-10)
if (!is.null(previous)) {
  prior_cells <- read.delim(file.path(previous, "cell_clusters.tsv"), stringsAsFactors = FALSE)
  prior_genes <- read.delim(file.path(previous, "gene_clusters.tsv"), stringsAsFactors = FALSE)
  stopifnot(identical(cells$cell_id, prior_cells$cell_id), identical(cells$cluster, prior_cells$cluster),
            identical(genes, prior_genes))
  result$previous_run <- previous
  result$repeat_cell_assignments_identical <- TRUE
  result$repeat_gene_assignments_identical <- TRUE
}
result
}
result <- tryCatch(verify(), error = function(e) {
  list(status = "FAIL", error = conditionMessage(e))
})
write_verification(result)
print(result)
if (!identical(result$status, "PASS")) quit(status = 1)
