library(TabulaMurisData)

sce <- TabulaMurisSmartSeq2()
sce <- sce[, !is.na(sce$cell_ontology_class)]
sce <- sce[, !is.na(sce$tissue)]


outdir <- "./data/real/raw/"
# outdir <- "../../data/raw/"

dir.create(path = outdir, recursive = TRUE)
saveRDS(sce, file.path(outdir, "tabula_muris_raw.rds"))
