suppressPackageStartupMessages({library(CAdir); library(APL)})
r <- '/workspace/cadir-lm-fig3-artifacts-20261027/hvg-only/case-htbeu88g'
for(n in c('ca','cadir_unranked','cadir','cadir_annotated')) {cat('\nOBJECT',n,'\n'); x<-readRDS(file.path(r,paste0(n,'.rds'))); print(slotNames(x)); if(n=='ca') print(lapply(slotNames(x),function(s) list(slot=s,dim=dim(slot(x,s)))) ) else {print(x@parameters); print(names(x@log)); print(dim(x@log$clusters)); print(colnames(x@log$clusters)); print(head(x@log$directions));print(head(x@gene_ranks));} }
print(read.delim(file.path(r,'cell_clusters.tsv'))[1:3,]); print(readRDS('/workspace/cadir-lm-fig3-artifacts-20261027/render-final/objects/history_GOA.rds')[[1]][[1]][1:4,])
