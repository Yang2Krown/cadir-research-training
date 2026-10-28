# devtools::load_all("/home/kohl/gits/ClemensKohl/CAdir/")
library(CAdir)
library(APL)
library(aricode)
library(SingleCellExperiment)
library(dplyr)
library(readr)

k <- 30
n <- 30
q <- 0.999
subset_cts <- TRUE
cellpcl <- 200

# Filtering according to:
# Yu, L., Cao, Y., Yang, J. Y. H. & Yang, P.
# Benchmarking clustering algorithms on estimating the number of
# cell types from single-cell RNA-sequencing data.
# Genome Biology 23, 49 (2022).

datadir <- "./data/real/preprocessed"

sce <- readRDS(file.path(
  datadir,
  "tabula_muris_preproc/tabula_muris_preproc.rds"
))

ct_size <- table(sce$cell_ontology_class)
ct_size <- ct_size[ct_size >= 300]

ct_names <- unique(names(ct_size))
sce <- sce[, sce$cell_ontology_class %in% ct_names]
cell_types <- unique(sce$cell_ontology_class)

res <- data.frame()

set.seed(2358)

picked_cts <- sample(x = cell_types, size = n, replace = FALSE)


if (isTRUE(subset_cts)) {
  chosen_cells <- c()
  for (p in picked_cts) {
    is_ct <- which(sce$cell_ontology_class %in% p)
    is_ct <- sample(x = is_ct, size = cellpcl, replace = FALSE)
    chosen_cells <- c(chosen_cells, is_ct)
  }
  sce_sub <- sce[, chosen_cells]
} else {
  cellpcl <- 0
  sce_sub <- sce[, sce$cell_ontology_class %in% picked_cts]
}

sce_dec <- scran::modelGeneVar(sce_sub)
sce_top <- scran::getTopHVGs(sce_dec, n = 4000, var.threshold = NULL)
sce_sub <- sce_sub[sce_top, ]

ca <- cacomp(
  obj = logcounts(sce_sub),
  princ_coords = 3,
  dims = 200,
  top = nrow(sce_sub),
  residuals = "pearson",
  python = TRUE,
  clip = TRUE
)

sub_dims <- n + 20
cat("\nUsing", sub_dims, "dimensions.\n")

ca <- subset_dims(caobj = ca, dims = sub_dims)

cak <- dirclust_splitmerge(
  caobj = ca,
  k = k,
  cutoff = NULL,
  method = "random",
  apl_quant = q,
  counts = NULL,
  min_cells = 50,
  reps = 5,
  make_plots = TRUE,
  apl_cutoff_reps = 100,
  qcutoff = 0.2
)

sce_sub$cadir <- cak@cell_clusters

cak <- annotate_biclusters(
  obj = cak,
  universe = rownames(sce_sub),
  org = "mm"
)

sce_sub$anno_cadir <- cak@cell_clusters

cak <- rank_genes(cadir = cak, caobj = ca)

ari <- aricode::clustComp(sce_sub$cadir, sce_sub$cell_ontology_class)

cts_found <- length(unique(cak@cell_clusters))

res <- data.frame(
  nr_cts = n,
  cts_found = cts_found,
  ari = ari$ARI,
  nmi = ari$NMI,
  k = k,
  apl_q = q,
  dims = sub_dims,
  ncells = ncol(sce_sub),
  ngenes = nrow(sce_sub),
  cellspcl = cellpcl
)
