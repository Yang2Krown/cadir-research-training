write_json <- function(x,p) jsonlite::write_json(x,p,pretty=TRUE,auto_unbox=TRUE,null="null",na="null",digits=NA)
write_tsv <- function(x,p) write.table(x,p,sep="\t",quote=TRUE,row.names=FALSE,na="NA")
sha_file <- function(p) digest::digest(file=p,algo="sha256",serialize=FALSE)
sha_text <- function(x) digest::digest(paste(x,collapse="\n"),algo="sha256",serialize=FALSE)
tracked_packages <- c("Matrix","S4Vectors","jsonlite","digest","SingleCellExperiment","SummarizedExperiment","scuttle","scran","scater","APL","CAdir","igraph","BiocNeighbors","BiocSingular","BiocParallel","BiocVersion","irlba","ggplot2")
load_packages <- function() for(p in tracked_packages) suppressPackageStartupMessages(library(p,character.only=TRUE))
function_signature <- function(f) sha_text(capture.output(dput(list(formals=formals(f),body=body(f)))))
environment_signature <- function() {
  namespaces <- setNames(lapply(tracked_packages,function(p) {
    ns <- asNamespace(p); nms <- sort(ls(ns,all.names=TRUE)); hashes <- list()
    for(n in nms) {v <- get(n,envir=ns,inherits=FALSE);if(is.function(v)) hashes[[n]] <- function_signature(v)}
    list(version=as.character(packageVersion(p)),namespace_function_hash=sha_text(capture.output(dput(hashes))),functions=hashes)
  }),tracked_packages)
  dispatch <- setNames(lapply(c("cacomp","runPCA","calculatePCA","runSVD","normalizeCounts","logNormCounts","modelGeneVar","buildSNNGraph"),function(n) sha_text(capture.output(showMethods(n,includeDefs=TRUE)))),c("cacomp","runPCA","calculatePCA","runSVD","normalizeCounts","logNormCounts","modelGeneVar","buildSNNGraph"))
  list(R=as.character(getRversion()),platform=R.version$platform,dispatch=dispatch,
       BLAS=unname(extSoftVersion()["BLAS"]),LAPACK=La_version(),packages=namespaces,
       thread_env=as.list(Sys.getenv(c("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"))))
}
assert_environment <- function(expected) {
  actual <- environment_signature()
  stopifnot("Actual package/function/R/BLAS signature differs from frozen probe"=identical(actual,expected))
  invisible(actual)
}
record_rng <- function(out,stage) {
  p <- file.path(out,"rng.rds");x <- if(file.exists(p)) readRDS(p) else list()
  x[[stage]] <- list(kind=RNGkind(),state=.Random.seed);saveRDS(x,p)
}
