library(TabulaMurisData)

sce <- TabulaMurisSmartSeq2()
sce <- sce[, sce$tissue == "Limb_Muscle"]
sce <- sce[, !is.na(sce$cell_ontology_class)]

outdir <- "./data/real/raw/"
# outdir <- "../../data/raw/real"

dir.create(path = outdir, recursive = TRUE)
saveRDS(sce, file.path(outdir, "tabula_muris_limb_raw.rds"))
