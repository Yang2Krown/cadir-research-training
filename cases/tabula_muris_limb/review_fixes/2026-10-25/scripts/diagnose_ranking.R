# Diagnostic only: never writes modified CA/CAdir objects or changes pipeline results.
args <- commandArgs(trailingOnly = TRUE)
suppressPackageStartupMessages({library(CAdir); library(APL)})
run <- args[[1]]; historical <- args[[2]]; output <- args[[3]]
ca <- readRDS(file.path(run, "ca.rds"))
p <- readRDS(file.path(run, "cadir.rds"))
u <- readRDS(file.path(run, "cadir_unranked.rds"))
current <- read.delim(file.path(run, "coclustered_gene_ranks.tsv"), stringsAsFactors = FALSE)
old <- read.delim(file.path(historical, "coclustered_gene_ranks.tsv"), stringsAsFactors = FALSE)
old <- old[match(current$Rowname, old$Rowname), , drop = FALSE]
source_env <- new.env(parent = asNamespace("CAdir"))
for (f in c("genes.R", "apl.R")) sys.source(file.path("/workspace/cadir-env/sources/CAdir/R", f), source_env)
fnames <- c("rank_genes", "get_apl_cutoff", "random_direction_cutoff", "apl_model")
source_comparison <- setNames(lapply(fnames, function(n) {
  installed <- get(n, asNamespace("CAdir")); source <- get(n, source_env)
  list(formals_identical = identical(formals(installed), formals(source)),
       body_identical = identical(body(installed), body(source)))
}), fnames)
# A simultaneous orthogonal reflection preserves dot products and distances,
# but positive-orthant random directions need not preserve the cutoff.
perturbation <- lapply(c("unchanged", "first_axis_reflected", "all_axes_reflected"), function(label) {
  signs <- rep(1, ca@dims)
  if (label == "first_axis_reflected") signs[1] <- -1
  if (label == "all_axes_reflected") signs[] <- -1
  reflected <- ca
  for (slot_name in c("U", "V", "std_coords_rows", "std_coords_cols", "prin_coords_rows", "prin_coords_cols")) {
    m <- methods::slot(reflected, slot_name)
    if (length(m)) methods::slot(reflected, slot_name) <- sweep(m, 2, signs, "*")
  }
  reflected_u <- u
  reflected_u@directions <- sweep(u@directions, 2, signs, "*")
  reflected_u@parameters$alpha_genes <- NULL
  RNGkind("Mersenne-Twister", "Inversion", "Rejection"); set.seed(2358)
  z <- CAdir::rank_genes(reflected_u, reflected)
  zr <- do.call(rbind, Filter(is.data.frame, z@gene_ranks))
  zr <- zr[match(current$Rowname, zr$Rowname), , drop = FALSE]
  list(variant = label, alpha = unname(z@parameters$alpha_genes),
       max_score_difference_from_fresh = max(abs(zr$Score - current$Score)),
       rank_changes_from_fresh = sum(zr$Rank != current$Rank))
})
result <- list(source_comparison = source_comparison,
  fresh_vs_frozen = list(all_gene_cluster_pairs_identical = identical(current$Rowname, old$Rowname) && identical(current$Cluster, old$Cluster),
                        maximum_score_absolute_difference = max(abs(current$Score - old$Score)),
                        all_scores_within_1e_10 = all(abs(current$Score - old$Score) <= 1e-10),
                        rank_changes = sum(current$Rank != old$Rank)),
  orthogonal_reflection_experiment = perturbation,
  upstream_mechanism = "random_direction_cutoff samples runif(0,q99) in each CA dimension; random directions occupy one orthant and are not invariant to CA axis sign changes.",
  historical_cause = "UNRESOLVED: neither original historical CA/unranked object nor independent-review CA/RNG objects were supplied; synthetic reflections do not prove the observed review discrepancy's cause.")
jsonlite::write_json(result, output, pretty = TRUE, auto_unbox = TRUE, digits = NA)
