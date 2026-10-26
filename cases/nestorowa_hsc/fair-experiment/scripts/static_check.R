# Syntax and executable availability only; never source or execute parsed code.
a <- commandArgs(TRUE);root <- a[[1]];out <- a[[2]]
files <- list.files(file.path(root,"scripts"),pattern="\\.R$",full.names=TRUE)
result <- lapply(files,function(p) {parse(file=p,keep.source=FALSE);data.frame(file=p,syntax="PASS")})
write.table(do.call(rbind,result),file.path(out,"R-syntax-check.tsv"),sep="\t",quote=TRUE,row.names=FALSE)
writeLines(capture.output(Sys.which(c("git","sh","awk","sleep","Rscript"))),file.path(out,"required-executables.txt"))
stopifnot(all(nzchar(Sys.which(c("sh","awk","sleep","Rscript")))))
cat("STATIC_R_PARSE_AND_EXECUTABLE_CHECK_COMPLETE_NO_ALGORITHMS\n")
