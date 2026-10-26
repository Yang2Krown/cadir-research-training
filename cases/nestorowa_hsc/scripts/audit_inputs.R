# Raw structural audit only. No normalization, filtering, clustering or metrics.
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=3L) stop("Usage: audit_inputs.R COUNTS_RDS COLDATA_RDS NEW_OUTPUT_DIRECTORY")
if(dir.exists(args[[3]]))stop("Audit output exists; use a fresh output directory.")
dir.create(args[[3]],recursive=TRUE)
out <- args[[3]]
write_json <- function(x,name)jsonlite::write_json(x,file.path(out,name),pretty=TRUE,auto_unbox=TRUE,digits=NA,na="null",null="null")
missing <- args[1:2][!file.exists(args[1:2])]
if(length(missing)) {
  write_json(list(status="BLOCKED_INPUTS_NOT_ACQUIRED",missing_inputs=missing,
                 matrix_version_shape_QC_labels="NOT_VERIFIED",clustering_or_evaluation_run=FALSE),"audit_status.json")
  quit(status=2)
}
result <- tryCatch({
  suppressPackageStartupMessages({library(Matrix);library(SingleCellExperiment)})
  counts <- readRDS(args[[1]]); metadata <- readRDS(args[[2]])
  stopifnot(is.matrix(counts)||inherits(counts,"Matrix"),length(dim(counts))==2L,
            is.data.frame(metadata)||methods::is(metadata,"DataFrame"))
  genes <- rownames(counts);cells <- colnames(counts);metadata_ids <- rownames(metadata)
  valid_ids <- function(x,n)!is.null(x)&&length(x)==n&&!anyNA(x)&&all(nzchar(x))&&!anyDuplicated(x)
  stopifnot("Unique, nonempty explicit gene/cell IDs required"=valid_ids(genes,nrow(counts))&&valid_ids(cells,ncol(counts)),
            "Explicit metadata IDs must align by ID, not assumed position"=valid_ids(metadata_ids,nrow(metadata))&&setequal(cells,metadata_ids))
  index <- match(cells,metadata_ids)
  # Inspect every stored value, counting implicit sparse zeros separately.
  statistics <- list(nonfinite=0,negative=0,noninteger=0,nonzero=0,minimum=Inf,maximum=-Inf)
  inspect_values <- function(values) {
    finite <- is.finite(values);v <- values[finite]
    statistics$nonfinite <<- statistics$nonfinite+sum(!finite)
    statistics$negative <<- statistics$negative+sum(v<0)
    statistics$noninteger <<- statistics$noninteger+sum(abs(v-round(v))>1e-8)
    statistics$nonzero <<- statistics$nonzero+sum(v!=0)
    if(length(v)) {
      statistics$minimum <<- min(statistics$minimum,v)
      statistics$maximum <<- max(statistics$maximum,v)
    }
  }
  if(inherits(counts,"sparseMatrix")) {
    inspect_values(counts@x)
    if(length(counts@x)<prod(dim(counts))) {
      statistics$minimum <- min(statistics$minimum,0)
      statistics$maximum <- max(statistics$maximum,0)
    }
  } else {
    for(first in seq.int(1,ncol(counts),by=128L))inspect_values(as.numeric(counts[,first:min(first+127L,ncol(counts)),drop=FALSE]))
  }
  statistics$zero_fraction <- 1-statistics$nonzero/prod(dim(counts))
  write_json(list(class=class(counts),dimensions=dim(counts),orientation="genes_by_cells",
                  statistics=statistics,htseq_rows=sum(grepl("^__",genes)),ercc_rows=sum(grepl("^ERCC-[0-9]+",genes)),
                  raw_count_assay_only=TRUE,logcounts_received=FALSE,
                  prior_QC_normalization_history="NOT_VERIFIED; counts label alone is not provenance"),"matrix_audit.json")
  stopifnot("Counts must be finite, nonnegative integers"=statistics$nonfinite==0&&statistics$negative==0&&statistics$noninteger==0)
  write.table(data.frame(gene_id=genes),file.path(out,"gene_ids.tsv"),sep="\t",quote=TRUE,row.names=FALSE)
  write.table(data.frame(cell_id=cells,metadata_row=index),file.path(out,"cell_id_alignment.tsv"),sep="\t",quote=TRUE,row.names=FALSE)
  fields <- lapply(names(metadata),function(name){
    value <- metadata[[name]]
    list(name=name,class=class(value),dimensions=dim(value),subfields=colnames(value),
         missing_entries=tryCatch(sum(is.na(value)),error=function(e)NULL))
  })
  write_json(list(fields=fields,metadata_ids_order_identical=identical(cells,metadata_ids),
                  aligned_by_explicit_ids=TRUE,
                  reference_label_mapping_status="NOT_VERIFIED; author broad/narrow FACS gates overlap",
                  unique_reference_field="NOT_FROZEN",donor_sample_condition_mapping="NOT_VERIFIED"),"metadata_audit.json")
  flat <- data.frame(cell_id=cells)
  for(name in names(metadata)) {
    value <- metadata[[name]]
    if((is.atomic(value)&&is.null(dim(value)))||is.factor(value))flat[[name]] <- value[index]
    # Matrices/DataFrames remain nested; their field names are audited above.
  }
  write.table(flat,file.path(out,"flat_cell_metadata.tsv"),sep="\t",quote=TRUE,row.names=FALSE)
  list(status="STRUCTURAL_AUDIT_COMPLETE_REVIEW_REQUIRED",genes=nrow(counts),cells=ncol(counts),
       matrix_version_shape_QC_labels="RAW_STRUCTURE_INSPECTED; QC/version/unique-label review still required",
       scientific_input_lock_complete=FALSE,clustering_or_evaluation_run=FALSE)
},error=function(e)list(status="FAILED_STRUCTURE",error=conditionMessage(e),clustering_or_evaluation_run=FALSE))
write_json(result,"audit_status.json")
if(identical(result$status,"FAILED_STRUCTURE"))quit(status=1)
