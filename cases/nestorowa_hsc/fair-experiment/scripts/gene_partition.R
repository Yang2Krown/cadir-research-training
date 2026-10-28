# Export-only mapping. Never expand, reorder or modify the upstream S4 slot.
# assign_genes() returns the ca_sphere_idx(qcutoff) subset of CA gene IDs.
map_gene_partition <- function(gene_clusters, genes, direction_ids) {
 valid_ids <- function(x) is.character(x)&&!anyNA(x)&&all(nzchar(trimws(x)))&&!anyDuplicated(x)
 stopifnot(valid_ids(genes),valid_ids(direction_ids))
 ids <- names(gene_clusters)
 if(!length(gene_clusters)&&is.null(ids)) ids <- character()
 stopifnot(valid_ids(ids),length(ids)==length(gene_clusters),all(ids%in%genes))
 labels <- as.character(gene_clusters)
 stopifnot(all(is.na(labels)|(!is.na(labels)&nzchar(trimws(labels))&labels%in%direction_ids)))
 ix <- match(genes,ids)
 present <- !is.na(ix)
 cluster <- labels[ix]
 assigned <- present&!is.na(cluster)
 reason <- ifelse(!present,"excluded_by_upstream_ca_sphere_qcutoff",ifelse(assigned,"assigned_by_upstream","retained_but_unassigned_by_upstream"))
 data.frame(gene_id=genes,cluster=cluster,in_upstream_gene_subset=present,assigned=assigned,reason=reason,stringsAsFactors=FALSE)
}
write_gene_partition <- function(partition,out,qcutoff) {
 write_tsv(partition,file.path(out,"gene-partition.tsv"))
 write_tsv(partition[!partition$assigned,,drop=FALSE],file.path(out,"gene-exclusions.tsv"))
 writeLines(partition$gene_id[!partition$assigned],file.path(out,"unassigned-gene-ids.txt"))
 reasons <- table(partition$reason)
 write_json(list(input_genes=nrow(partition),upstream_retained_genes=sum(partition$in_upstream_gene_subset),assigned_genes=sum(partition$assigned),unassigned_genes=nrow(partition)-sum(partition$assigned),qcutoff=qcutoff,reason_counts=as.list(setNames(as.integer(reasons),names(reasons))),internal_slot_action="Original upstream subset retained unchanged; NA exists only in the full-universe export for absent IDs or upstream missing assignments"),file.path(out,"gene-assignment-summary.json"))
 invisible(partition)
}
