# Pure bookkeeping tests with synthetic IDs/factors; no packages or algorithms.
a <- commandArgs(TRUE);source(a[[1]])
genes <- paste0("gene",seq_len(6000));directions <- c("1","2")
subset <- factor(c("2","1",NA_character_),levels=directions)
names(subset) <- genes[c(7,3,10)]
original <- subset
p <- map_gene_partition(subset,genes,directions)
stopifnot(identical(subset,original),nrow(p)==6000,identical(p$gene_id,genes),sum(p$in_upstream_gene_subset)==3,sum(p$assigned)==2,sum(!p$assigned)==5998,p$cluster[3]=="1",p$cluster[7]=="2",is.na(p$cluster[1]),is.na(p$cluster[10]),p$reason[1]=="excluded_by_upstream_ca_sphere_qcutoff",p$reason[10]=="retained_but_unassigned_by_upstream",all(p$reason[p$assigned]=="assigned_by_upstream"))
reject <- function(x) inherits(try(map_gene_partition(x,genes,directions),silent=TRUE),"try-error")
bad <- subset;names(bad)[2] <- names(bad)[1];stopifnot(reject(bad))
bad <- subset;names(bad)[1] <- "foreign_gene";stopifnot(reject(bad))
bad <- subset;names(bad)[1] <- "";stopifnot(reject(bad))
bad <- subset;names(bad)[1] <- NA_character_;stopifnot(reject(bad))
bad <- subset;names(bad) <- NULL;stopifnot(reject(bad))
bad <- c(gene3="unknown_direction");stopifnot(reject(bad))
empty <- map_gene_partition(factor(character(),levels=directions),genes,directions)
stopifnot(nrow(empty)==6000,sum(empty$assigned)==0,all(is.na(empty$cluster)))
cat("PURE_GENE_PARTITION_MAPPING_CHECKS_PASS_NO_ALGORITHMS\n")
