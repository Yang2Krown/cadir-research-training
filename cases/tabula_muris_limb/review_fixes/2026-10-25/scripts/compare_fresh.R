args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({library(CAdir); library(APL)})
a <- args[[1]]; b <- args[[2]]; output <- args[[3]]
read_rank <- function(path) read.delim(file.path(path, "coclustered_gene_ranks.tsv"), stringsAsFactors = FALSE)
x <- read_rank(a); y <- read_rank(b)
y <- y[match(x$Rowname, y$Rowname), , drop = FALSE]
p <- readRDS(file.path(a, "cadir.rds")); q <- readRDS(file.path(b, "cadir.rds"))
ca <- readRDS(file.path(a, "ca.rds")); cb <- readRDS(file.path(b, "ca.rds"))
result <- list(run_a = a, run_b = b, alpha_a = unname(p@parameters$alpha_genes),
               alpha_b = unname(q@parameters$alpha_genes),
               alpha_absolute_difference = abs(unname(p@parameters$alpha_genes - q@parameters$alpha_genes)),
               all_1200_gene_cluster_pairs_identical = identical(x$Rowname, y$Rowname) && identical(x$Cluster, y$Cluster),
               maximum_score_absolute_difference = max(abs(x$Score - y$Score)),
               all_scores_within_1e_10 = all(abs(x$Score - y$Score) <= 1e-10),
               all_ranks_identical = identical(x$Rank, y$Rank),
               rank_changes = sum(x$Rank != y$Rank),
               cell_principal_coordinates_maximum_difference = max(abs(ca@prin_coords_cols - cb@prin_coords_cols)),
               gene_principal_coordinates_maximum_difference = max(abs(ca@prin_coords_rows - cb@prin_coords_rows)),
               scope = "Two fresh runs in the preserved current runtime; historical alpha discrepancy is unresolved.")
jsonlite::write_json(result, output, pretty = TRUE, auto_unbox = TRUE, digits = NA)
stopifnot(result$alpha_absolute_difference <= 1e-10, result$all_1200_gene_cluster_pairs_identical,
          result$all_scores_within_1e_10, result$all_ranks_identical)
