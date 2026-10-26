# Read-only package/interface probe. Never reads expression, reduces or clusters.
a <- commandArgs(TRUE); source(a[[1]]); out <- a[[2]]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
load_packages()
sig <- environment_signature();saveRDS(sig,file.path(out,"environment-signature.rds"))
write_json(sig,file.path(out,"environment-signature.json"))
interfaces <- list(APL=c("cacomp","run_cacomp"),CAdir=c("dirclust_splitmerge","rank_genes","get_apl_cutoff","random_direction_cutoff","apl_model","plot_clusters"),scuttle=c("logNormCounts","librarySizeFactors"),scran=c("modelGeneVar","getTopHVGs","buildSNNGraph","makeSNNGraph"),scater=c("runPCA","calculatePCA"),BiocSingular="IrlbaParam",BiocNeighbors="KmknnParam",igraph="cluster_louvain")
for(p in names(interfaces)) for(n in interfaces[[p]]) {
 f <- get(n,envir=asNamespace(p));writeLines(capture.output(dput(list(formals=formals(f),body=body(f)))),file.path(out,paste0(p,"__",n,".R.txt")))
}
for(n in c("cacomp","calculatePCA","runSVD","normalizeCounts","logNormCounts","modelGeneVar","buildSNNGraph","runPCA")) capture.output(showMethods(n,includeDefs=TRUE),file=file.path(out,paste0(n,"__methods.txt")))
write_tsv(as.data.frame(installed.packages()[,c("Package","Version","Built")]),file.path(out,"installed-packages.tsv"))
writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
write_json(list(cpu_max=readLines("/sys/fs/cgroup/cpu.max"),memory_max=readLines("/sys/fs/cgroup/memory.max"),threads=2,forbidden_algorithms_called=FALSE),file.path(out,"resource-context.json"))
cat("READ_ONLY_ENVIRONMENT_PROBE_COMPLETE\n")
