# Read-only function-body export, no plots or algorithm calls.
a <- commandArgs(TRUE);stopifnot(length(a)==2L)
out <- a[[1]];signature_path <- a[[2]]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
ns <- asNamespace("CAdir")
expected <- jsonlite::read_json(signature_path,simplifyVector=FALSE)$packages$CAdir$functions
for(n in c("plot_clusters","cluster_apl","apl_model")) {
 f <- get(n,envir=ns,inherits=FALSE)
 lines <- capture.output(dput(list(formals=formals(f),body=body(f))))
 actual <- digest::digest(paste(lines,collapse="\n"),algo="sha256",serialize=FALSE)
 stopifnot(identical(actual,expected[[n]]))
 writeLines(lines,file.path(out,paste0("installed-CAdir-",n,".txt")))
}
cat("READ_ONLY_NATIVE_PLOT_INTERFACE_MATCHES_FROZEN_SIGNATURE\n")
