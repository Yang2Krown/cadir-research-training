# Independent R3 review. The implementation diagnostic scripts are not sourced.
suppressPackageStartupMessages({library(APL);library(CAdir)})
root <- '/workspace/cadir-r3-independent-20261026'
ev <- file.path(root,'evidence')
base <- '/workspace/cadir-stage1-retest/complete-entry/case-e_ilcvjv'
old <- '/workspace/cadir-r3-evidence-20261026'
repo <- '/workspace/cadir-r3-review-source/cases/tabula_muris_limb'
tol_score <- 1e-10
tol_coords <- 1e-9
js <- function(x,n) jsonlite::write_json(x,file.path(ev,n),pretty=TRUE,auto_unbox=TRUE,digits=NA,null='null')
tsv <- function(x,n) write.table(x,file.path(ev,n),sep='\t',row.names=FALSE,quote=TRUE)
bca <- readRDS(file.path(base,'ca.rds'));oca <- readRDS(file.path(old,'ca.rds'))
bo <- readRDS(file.path(base,'cadir_unranked.rds'));oo <- readRDS(file.path(old,'cadir_unranked.rds'))
stopifnot(is.null(bo@parameters$alpha_genes),is.null(oo@parameters$alpha_genes))
gene_ids <- rownames(bca@prin_coords_rows);cell_ids<-rownames(bca@prin_coords_cols)
stopifnot(!anyDuplicated(gene_ids),!anyDuplicated(cell_ids),setequal(gene_ids,rownames(oca@prin_coords_rows)),setequal(cell_ids,rownames(oca@prin_coords_cols)))
gidx <- match(gene_ids,rownames(oca@prin_coords_rows));cidx<-match(cell_ids,rownames(oca@prin_coords_cols))
original_order_identical <- identical(gidx,seq_along(gidx))&&identical(cidx,seq_along(cidx))
coordinate_slots <- c('U','V','std_coords_rows','std_coords_cols','prin_coords_rows','prin_coords_cols')
idx <- function(n) if(n %in% c('U','std_coords_rows','prin_coords_rows'))gidx else cidx
X<-bca@prin_coords_cols;Y<-oca@prin_coords_cols[cidx,,drop=FALSE]
# Infer signs solely from ID-aligned real cell coordinates, without provided axis list.
sign_vector <- sign(colSums(X*Y));stopifnot(all(abs(sign_vector)==1))
per_axis<-data.frame(axis=seq_len(ncol(X)),inferred_sign=sign_vector,raw_max_abs=apply(abs(X-Y),2,max),aligned_cell_principal_max_abs=apply(abs(sweep(Y,2,sign_vector,'*')-X),2,max))
sv <- svd(crossprod(X,Y));Q<-sv$u%*%t(sv$v)
coord_summary<-lapply(coordinate_slots,function(n){a<-slot(bca,n);b<-slot(oca,n)[idx(n),,drop=FALSE];list(slot=n,raw_max_abs=max(abs(a-b)),sign_aligned_max_abs=max(abs(a-sweep(b,2,sign_vector,'*'))))})
stopifnot(all(vapply(coord_summary,function(z)z$sign_aligned_max_abs<tol_coords,logical(1))))
cell_equal<-identical(bo@cell_clusters,oo@cell_clusters);gene_equal<-identical(bo@gene_clusters,oo@gene_clusters)
stopifnot(cell_equal,gene_equal,identical(bo@dict,oo@dict))
direction_error<-max(abs(bo@directions-sweep(oo@directions[rownames(bo@directions),,drop=FALSE],2,sign_vector,'*')))
ca_summary<-list(genes=length(gene_ids),cells=length(cell_ids),original_ID_order_identical=original_order_identical,inferred_sign_vector=sign_vector,negative_axes=which(sign_vector<0),singular_values_max_abs=max(abs(bca@D-oca@D)),coordinate_tolerance=tol_coords,coordinate_slots=coord_summary,optimal_orthogonal_map_max_difference_from_diagonal_sign=max(abs(Q-diag(sign_vector))),optimal_map_residual_max_abs=max(abs(X%*%Q-Y)),cells_factor_names_levels_identical=cell_equal,genes_factor_names_levels_identical=gene_equal,dict_identical=TRUE,direction_sign_aligned_max_abs=direction_error)
stopifnot(ca_summary$singular_values_max_abs<1e-12,ca_summary$optimal_orthogonal_map_max_difference_from_diagonal_sign<tol_coords,direction_error<tol_coords)
js(ca_summary,'independent_CA_objects.json');tsv(per_axis,'independent_axes.tsv')

geometry <- function(ca,obj){
  ans<-lapply(levels(obj@gene_clusters),function(cl){
    d<-obj@directions[cl,];cent<-colMeans(ca@prin_coords_cols[obj@cell_clusters==cl,,drop=FALSE]);if(sum(cent*d)<0)d<- -d
    d<-d/sqrt(sum(d*d));m<-ca@prin_coords_rows
    x<-drop(m%*%d);y<-sqrt(pmax(rowSums(m*m)-x*x,0))
    use<-which(rownames(m)%in%names(obj@gene_clusters)[obj@gene_clusters==cl])
    data.frame(Rowname=rownames(m)[use],Cluster=cl,x=x[use],y=y[use],Row_num=seq_along(use))
  });do.call(rbind,ans)
}
gene_assign <- function(ca,obj){
  radii<-sqrt(rowSums(ca@prin_coords_rows^2));use<-which(radii>=quantile(radii,.8));m<-ca@std_coords_rows[use,,drop=FALSE]
  pro<-m%*%t(obj@directions);dist2<-pmax(matrix(rowSums(m*m),nrow(m),nrow(obj@directions))-pro*pro,0);dist2[pro<0]<-Inf
  setNames(rownames(obj@directions)[max.col(-dist2,ties.method='first')],rownames(m))
}
reflections <- function(ca,obj){
  z<-ca;w<-obj
  for(n in coordinate_slots)slot(z,n)<-sweep(slot(z,n),2,sign_vector,'*')
  w@directions<-sweep(w@directions,2,sign_vector,'*')
  list(ca=z,obj=w)
}
bt<-reflections(bca,bo);ot<-reflections(oca,oo)
gb<-geometry(bca,bo);go<-geometry(oca,oo);go<-go[match(gb$Rowname,go$Rowname),]
geom<-list(actual_pair_gene_IDs_identical=identical(gb$Rowname,go$Rowname),actual_pair_cluster_identical=identical(gb$Cluster,go$Cluster),actual_pair_x_max_abs=max(abs(gb$x-go$x)),actual_pair_y_max_abs=max(abs(gb$y-go$y)),interventions=list())
for(pair in list(list(name='baseline_to_review',ca=bca,obj=bo,trans=bt),list(name='review_to_baseline',ca=oca,obj=oo,trans=ot))){
  before<-geometry(pair$ca,pair$obj);after<-geometry(pair$trans$ca,pair$trans$obj)
  pre<-gene_assign(pair$ca,pair$obj);post<-gene_assign(pair$trans$ca,pair$trans$obj)
  saved<-setNames(as.character(pair$obj@gene_clusters),names(pair$obj@gene_clusters));saved_match<-identical(unname(pre[names(saved)]),unname(saved))&&setequal(names(pre),names(saved))
  a<-list(name=pair$name,cell_and_gene_assignments_unchanged=identical(pair$obj@cell_clusters,pair$trans$obj@cell_clusters)&&identical(pair$obj@gene_clusters,pair$trans$obj@gene_clusters),independently_recomputed_gene_assignments_unchanged=identical(pre,post),independently_recomputed_gene_assignments_match_saved=saved_match,max_projection_change=max(abs(before$x-after$x)),max_orthogonal_distance_change=max(abs(before$y-after$y)),max_gene_squared_norm_change=max(abs(rowSums(pair$ca@prin_coords_rows^2)-rowSums(pair$trans$ca@prin_coords_rows^2))),max_cell_squared_norm_change=max(abs(rowSums(pair$ca@prin_coords_cols^2)-rowSums(pair$trans$ca@prin_coords_cols^2))))
  stopifnot(a$cell_and_gene_assignments_unchanged,a$independently_recomputed_gene_assignments_unchanged,a$independently_recomputed_gene_assignments_match_saved,a$max_projection_change<tol_score,a$max_orthogonal_distance_change<tol_score)
  geom$interventions[[pair$name]]<-a
}
js(geom,'independent_geometry_assignments.json')
fixed<-new.env(parent=globalenv());sys.source('/workspace/cadir-env/sources/CAdir/R/apl.R',fixed);sys.source('/workspace/cadir-env/sources/CAdir/R/genes.R',fixed)
function_compare<-lapply(c('rank_genes','get_apl_cutoff','random_direction_cutoff','apl_model'),function(n){a<-get(n,fixed);b<-get(n,asNamespace('CAdir'));list(name=n,formals_identical=identical(formals(a),formals(b)),body_identical=identical(body(a),body(b)))})
stopifnot(all(vapply(function_compare,function(x)x$formals_identical&&x$body_identical,logical(1))))
read_table<-function(p)read.delim(p,stringsAsFactors=FALSE,check.names=FALSE)
frozen<-read_table(file.path(repo,'results/coclustered_gene_ranks.tsv'));historic<-read_table(file.path(old,'text-export/text/rerun/full/coclustered_gene_ranks.tsv'))
compare<-function(actual,target){
  stopifnot(nrow(actual)==1200,nrow(target)==1200,!anyDuplicated(actual$Rowname),!anyDuplicated(target$Rowname),setequal(actual$Rowname,target$Rowname))
  t<-target[match(actual$Rowname,target$Rowname),];list(gene_count=nrow(actual),gene_cluster_identical=identical(as.character(actual$Cluster),as.character(t$Cluster)),max_score_abs_error=max(abs(actual$Score-t$Score)),rank_differences=sum(actual$Rank!=t$Rank),row_num_differences=sum(actual$Row_num!=t$Row_num))
}
conditions<-list(baseline_actual=list(ca=bca,obj=bo,target=frozen),review_actual=list(ca=oca,obj=oo,target=historic),baseline_signs_to_review=list(ca=bt$ca,obj=bt$obj,target=historic),review_signs_to_baseline=list(ca=ot$ca,obj=ot$obj,target=frozen))
states<-list();answers<-list();ranks<-list()
for(n in names(conditions)){
  c<-conditions[[n]];RNGkind('Mersenne-Twister','Inversion','Rejection');set.seed(2358);pre<-.Random.seed
  ranked<-CAdir::rank_genes(cadir=c$obj,caobj=c$ca);post<-.Random.seed
  r<-do.call(rbind,Filter(is.data.frame,ranked@gene_ranks));tsv(r,paste0(n,'_ranks.tsv'));ranks[[n]]<-r
  check<-compare(r,c$target);ge<-geometry(c$ca,c$obj);ge<-ge[match(r$Rowname,ge$Rowname),];formula_scores<-ge$x-ranked@parameters$alpha_genes*ge$y
  check$alpha_genes<-unname(ranked@parameters$alpha_genes);check$independent_geometric_score_max_abs<-max(abs(r$Score-formula_scores));check$score_absolute_tolerance<-tol_score
  stopifnot(check$gene_cluster_identical,check$max_score_abs_error<=tol_score,check$rank_differences==0,check$row_num_differences==0,check$independent_geometric_score_max_abs<=tol_score)
  answers[[n]]<-check;states[[n]]<-list(note='NEW DIAGNOSTIC SNAPSHOT after explicit RNGkind and seed reset, not historical runtime snapshot',RNGkind=RNGkind(),seed=2358,before=as.integer(pre),after=as.integer(post))
  print(list(condition=n,result=check))
}
observed_diff<-compare(ranks$baseline_actual,ranks$review_actual)
stopifnot(observed_diff$rank_differences==541)
answers$actual_pair_difference<-observed_diff
answers$all_new_diagnostic_pre_RNG_identical<-all(vapply(states,function(s)identical(s$before,states[[1]]$before),logical(1)))
answers$all_new_diagnostic_post_RNG_identical<-all(vapply(states,function(s)identical(s$after,states[[1]]$after),logical(1)))
answers$fixed_source_function_comparison<-function_compare
js(states,'new_diagnostic_RNG_states.json');js(answers,'independent_ranking_results.json')
stopifnot(answers$all_new_diagnostic_pre_RNG_identical,answers$all_new_diagnostic_post_RNG_identical)
cat('INDEPENDENT R3 DIAGNOSTIC COMPLETE\n')
