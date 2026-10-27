suppressPackageStartupMessages({library(CAdir);library(APL)})
out<-'reviews/lm-fig3-20261027'; root<-'cases/tabula_muris_limb/fig3_completion'
run<-'/workspace/cadir-lm-fig3-artifacts-20261027/hvg-only/case-htbeu88g'
render<-'/workspace/cadir-lm-fig3-artifacts-20261027/render-final'
ca<-readRDS(file.path(run,'ca.rds'));ck<-readRDS(file.path(run,'cadir.rds'))
v<-read.delim(file.path(run,'gene_variance.tsv'))
chosen<-head(v$gene_id[order(v$bio,decreasing=TRUE)],6000)
stopifnot(setequal(chosen,rownames(ca@prin_coords_rows)),length(chosen)==6000)
RNGkind('Mersenne-Twister','Inversion','Rejection');set.seed(2358)
stopifnot(identical(.Random.seed,readRDS(file.path(render,'objects','rng_before_render.rds'))))
prov<-jsonlite::fromJSON(file.path(render,'provenance','render_provenance.json'))
stopifnot(abs(ck@parameters$alpha_genes-prov$alpha_genes)<1e-14,unname(tools::md5sum(file.path(run,'ca.rds')))==prov$CA_MD5,unname(tools::md5sum(file.path(run,'cadir.rds')))==prov$cadir_MD5)
dir.create(file.path(out,'installed_functions'),showWarnings=FALSE)
results<-list()
for(n in names(prov$function_md5)) {
 f<-get(n,envir=asNamespace('CAdir'));p<-file.path(out,'installed_functions',paste0(n,'.R'))
 dput(list(formals=formals(f),body=body(f)),file=p)
 hash<-unname(tools::md5sum(p));stopifnot(hash==prov$function_md5[[n]],hash==unname(tools::md5sum(file.path(root,'evidence/render',paste0('function_',n,'.R')))))
 results[[n]]<-hash
}
txt<-readLines(file.path(root,'scripts/render_fig3.R'))
stopifnot(!any(grepl('corral\\(|corralm\\(|dirclust_splitmerge\\(|rank_genes\\(',txt)))
jsonlite::write_json(list(status='PASS_INDEPENDENT_PROVENANCE',HVG_ids_match_saved_variance_top6000=TRUE,alpha=ck@parameters$alpha_genes,render_seed=2358,render_has_no_CA_clustering_reranking_calls=TRUE,function_md5=results),file.path(out,'provenance_result.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
cat('PASS: stored HVG IDs, CA/object hashes, alpha, renderer RNG and installed source identity.\n')
