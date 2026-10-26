# Input legality only. No QC, normalization, clustering or evaluation metrics.
args <- commandArgs(trailingOnly=TRUE)
mode <- if(length(args)) args[[1]] else ""
if(!(mode %in% c("metadata-only","full")) || length(args)!=(if(mode=="metadata-only") 4L else 6L))
    stop("Usage: audit_inputs.R metadata-only COL_RDS MANIFEST NEW_OUT | full COUNTS_RDS COL_RDS GEO_GZ MANIFEST NEW_OUT")
out <- tail(args,1)
if(file.exists(out)) stop("Output exists; use a new attempt directory")
dir.create(out,recursive=TRUE)
suppressPackageStartupMessages({library(Matrix);library(S4Vectors);library(jsonlite);library(digest)})
write_json <- function(x,name) jsonlite::write_json(x,file.path(out,name),
    pretty=TRUE,auto_unbox=TRUE,digits=NA,na="null",null="null")
script_dir <- dirname(normalizePath(sub("^--file=","",grep("^--file=",commandArgs(),value=TRUE)[[1]])))
source(file.path(script_dir,"metadata_identity.R"))
counts_read <- FALSE
result <- tryCatch({
    manifest <- jsonlite::read_json(args[[length(args)-1L]],simplifyVector=FALSE)
    hashes <- list()
    verify_file <- function(path) {
        expected <- Filter(function(x) startsWith(x$path,"reacquired-") &&
            basename(x$path)==basename(path),manifest$artifacts)
        if(length(expected)!=1L) stop("Exactly one acquisition manifest entry required: ",basename(path))
        expected <- expected[[1]]
        actual <- digest::digest(file=path,algo="sha256")
        entry <- list(name=basename(path),bytes=unname(file.info(path)$size),sha256=actual,
            expected_bytes=expected$bytes,expected_sha256=expected$sha256,source_url=expected$url,
            matches=identical(actual,expected$sha256) && file.info(path)$size==expected$bytes)
        hashes[[basename(path)]] <<- entry;write_json(hashes,"file_integrity.json")
        if(!isTRUE(entry$matches)) stop("File hash/size mismatch: ",basename(path))
    }
    metadata_path <- args[[if(mode=="full") 3L else 2L]]
    verify_file(metadata_path)
    metadata <- readRDS(metadata_path)
    identity <- extract_metadata_identity(metadata)
    write_metadata_audit(identity,out)
    if(mode=="full") {
        counts_path <- args[[2]];geo_path <- args[[4]]
        verify_file(counts_path);verify_file(geo_path)
        counts <- readRDS(counts_path);counts_read <- TRUE
        if(!(is.matrix(counts)||methods::is(counts,"Matrix"))||length(dim(counts))!=2L)
            stop("Counts must be a two-dimensional matrix")
        if(methods::is(counts,"Matrix")) methods::validObject(counts)
        if(!(is.numeric(counts)||methods::is(counts,"dMatrix")||methods::is(counts,"iMatrix")))
            stop("Counts must be numeric")
        genes <- rownames(counts);cells <- colnames(counts)
        check_ids(genes,nrow(counts),"counts gene IDs");check_ids(cells,ncol(counts),"counts cell IDs")
        ix <- match_ids(cells,identity$ids,"metadata canonical cells")
        write.table(data.frame(matrix_column=seq_along(cells),cell_id=cells,metadata_canonical_row=ix),
            file.path(out,"count_metadata_alignment.tsv"),sep="\t",quote=FALSE,row.names=FALSE)
        write.table(data.frame(matrix_row=seq_along(genes),gene_id=genes),
            file.path(out,"gene_ids.tsv"),sep="\t",quote=FALSE,row.names=FALSE)
        statistics <- list(nonfinite=0,negative=0,noninteger=0,stored_values=0)
        inspect <- function(values) {
            finite <- is.finite(values);v <- values[finite]
            statistics$nonfinite <<- statistics$nonfinite+sum(!finite)
            statistics$negative <<- statistics$negative+sum(v<0)
            statistics$noninteger <<- statistics$noninteger+sum(v!=floor(v))
            statistics$stored_values <<- statistics$stored_values+length(values)
        }
        if(methods::is(counts,"sparseMatrix")) {
            if(!("x" %in% methods::slotNames(counts))) stop("Numeric sparse x slot required")
            inspect(counts@x)
        } else for(first in seq.int(1,ncol(counts),by=128L))
            inspect(as.numeric(counts[,first:min(first+127L,ncol(counts)),drop=FALSE]))
        write_json(list(class=class(counts),dimensions=dim(counts),sparse_structure_valid=TRUE,
            statistics=statistics,implicit_sparse_zeros="finite nonnegative integers; included logically",
            htseq_rows=sum(startsWith(genes,"__")),ERCC_rows=sum(grepl("^ERCC-[0-9]+$",genes)),
            ensembl_rows=sum(grepl("^ENSMUSG[0-9]+$",genes)),metadata_cell_sets_equal=TRUE,
            metadata_cell_order_identical=identical(cells,identity$ids)),"counts_legality.json")
        if(any(unlist(statistics[c("nonfinite","negative","noninteger")])!=0))
            stop("Counts contain nonfinite, negative or fractional values")
        con <- gzfile(geo_path,open="rt")
        header <- strsplit(readLines(con,n=1L),"\t",fixed=TRUE)[[1]]
        header <- gsub('^"|"$','',header)
        if(length(header)==ncol(counts)+1L) header <- header[-1]
        check_ids(header,ncol(counts),"GEO header");cix <- match_ids(header,cells,"GEO/count cells")
        geo_genes <- character();mismatch <- 0;compared <- 0
        while(length(lines <- readLines(con,n=128L,warn=FALSE))) {
            tokens <- strsplit(lines,"\t",fixed=TRUE)
            if(any(lengths(tokens)!=length(header)+1L)) stop("GEO row width mismatch")
            g <- vapply(tokens,function(x) gsub('^"|"$','',x[[1]]),character(1))
            gix <- match(g,genes)
            if(anyNA(gix)) id_issue("GEO contains unknown gene IDs",list(unknown_gene_ids=g[is.na(gix)]))
            values <- suppressWarnings(t(vapply(tokens,function(x) as.numeric(x[-1]),numeric(length(header)))))
            if(any(!is.finite(values))||any(values<0)||any(values!=floor(values)))
                stop("GEO values must be finite nonnegative integers")
            mismatch <- mismatch+sum(values!=as.matrix(counts[gix,cix,drop=FALSE]))
            compared <- compared+length(values);geo_genes <- c(geo_genes,g)
        }
        close(con)
        check_ids(geo_genes,nrow(counts),"GEO gene IDs");match_ids(genes,geo_genes,"GEO/count genes")
        write_json(list(direction="genes_by_cells",
            direction_evidence="GEO gene IDs are matrix rows; GEO sample IDs match columns and metadata",
            GEO_rows=length(geo_genes),GEO_cells=length(header),gene_sets_equal=TRUE,cell_sets_equal=TRUE,
            gene_order_identical=identical(genes,geo_genes),cell_order_identical=identical(cells,header),
            values_compared=compared,numeric_mismatches=mismatch,source_flow_table_coverage_verified=FALSE),
            "geo_correspondence.json")
        if(mismatch!=0) stop("GEO and counts.rds numeric values differ")
    }
    list(status=if(mode=="full") "INPUT_LEGALITY_VERIFIED_REVIEW_REQUIRED" else "METADATA_IDENTITY_VERIFIED_REVIEW_REQUIRED",
        mode=mode,counts_rds_read=counts_read,formal_execution_permitted=FALSE,
        QC_filtering_performed=FALSE,normalization_performed=FALSE,clustering_or_metrics_run=FALSE,
        scientific_input_lock_complete=FALSE)
},error=function(e) {
    if(inherits(e,"identity_error")) write_json(e$details,"identity_error_details.json")
    list(status="FAILED_INPUT_AUDIT",mode=mode,error=conditionMessage(e),counts_rds_read=counts_read,
        formal_execution_permitted=FALSE,QC_filtering_performed=FALSE,
        normalization_performed=FALSE,clustering_or_metrics_run=FALSE)
})
write_json(list(R=R.version.string,packages=lapply(c("Matrix","S4Vectors","jsonlite","digest"),
    function(x) list(name=x,version=as.character(packageVersion(x)))),loaded_namespaces=loadedNamespaces()),"runtime.json")
write_json(result,"audit_status.json")
if(identical(result$status,"FAILED_INPUT_AUDIT")) quit(status=1)
