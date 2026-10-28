suppressPackageStartupMessages({library(CAdir); library(APL); library(SingleCellExperiment)})
options(warn=1)
out <- 'reviews/lm-fig3-20261027'
run <- '/workspace/cadir-lm-fig3-artifacts-20261027/hvg-only/case-htbeu88g'
render <- '/workspace/cadir-lm-fig3-artifacts-20261027/render-final'
tab <- function(n) read.delim(file.path(render,'tables',paste0(n,'.tsv')),check.names=FALSE)
write_t <- function(x,n) write.table(x,file.path(out,paste0(n,'.tsv')),sep='\t',quote=TRUE,row.names=FALSE)
ca <- readRDS(file.path(run,'ca.rds')); un <- readRDS(file.path(run,'cadir_unranked.rds'))
ck <- readRDS(file.path(run,'cadir.rds')); an <- readRDS(file.path(run,'cadir_annotated.rds'))
input <- readRDS('/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds')
stopifnot(identical(dim(input),c(13204L,1882L)),identical(dim(ca@prin_coords_rows),c(6000L,30L)),identical(dim(ca@prin_coords_cols),c(1882L,30L)))
for(s in c('cell_clusters','gene_clusters','directions','log')) stopifnot(identical(slot(un,s),slot(ck,s)))
stopifnot(identical(unname(ck@directions),unname(an@directions)),identical(ck@log,an@log))
cc <- tab('all_cell_assignments'); gc <- tab('all_gene_assignments'); ranks <- tab('all_gene_ranks')
stopifnot(!anyDuplicated(cc$cell_id),!anyDuplicated(gc$gene_id),identical(cc$cell_id,colnames(input)),identical(cc$cell_id,rownames(ca@prin_coords_cols)),
 identical(cc$reference,as.character(colData(input)[cc$cell_id,'cell_ontology_class'])),identical(cc$cluster,unname(as.character(ck@cell_clusters[cc$cell_id]))),
 identical(cc$predicted_annotation,unname(as.character(an@cell_clusters[cc$cell_id]))),identical(gc$gene_id,rownames(ca@prin_coords_rows)))
savedgenes <- setNames(as.character(ck@gene_clusters),names(ck@gene_clusters))
stopifnot(identical(gc$cluster,unname(savedgenes[gc$gene_id])),sum(!is.na(gc$cluster))==1200L,sum(is.na(gc$cluster))==4800L)
X <- ca@prin_coords_cols; G <- ca@prin_coords_rows; ds <- ck@directions
project <- function(points,direction,members,cellcoords=X) {
 unit <- direction/sqrt(sum(direction^2)); if(sum(colMeans(cellcoords[members,,drop=FALSE])*unit)<0) unit <- -unit
 along <- drop(points%*%unit)
 # Explicit orthogonal residual, avoiding sqrt(norm^2-dot^2) cancellation.
 resid <- points - outer(along,unit)
 cbind(x=along,y=sqrt(rowSums(resid^2)))
}
angles <- function(d) {u<-d/sqrt(rowSums(d*d)); co<-u%*%t(u); co[]<-pmin(1,pmax(-1,co)); acos(co)*180/pi}
angle <- angles(ds); diag(angle)<-0
check <- function(a,b,tol=1e-7) {e<-max(abs(as.matrix(a)-as.matrix(b)));stopifnot(is.finite(e),e<tol);e}
errs<-list()
errs$std_columns<-check(ca@std_coords_cols,sweep(X,2,ca@D,'/'))
errs$std_rows<-check(ca@std_coords_rows,sweep(G,2,ca@D,'/'))
errs$directions_principal<-check(tab('directions_principal')[,-1],ds)
errs$directions_standard<-check(tab('directions_standard')[,-1],sweep(ds,2,ca@D,'/'))
errs$singular_values<-check(tab('CA_singular_values')$D,ca@D)
errs$angle_table<-check(tab('S1A_pairwise_direction_angles_degrees')[,-1],angle,1e-5)
recomputed<-list(); tops<-list()
for(cl in rownames(ds)) {
 ids<-names(savedgenes)[savedgenes==cl]; ids<-ids[!is.na(ids)]
 # Recover original CA gene order first; ties are stable in that order.
 ids<-rownames(G)[rownames(G)%in%ids]
 xy<-project(G[ids,,drop=FALSE],ds[cl,],which(ck@cell_clusters==cl))
 score<-xy[,1]-ck@parameters$alpha_genes*xy[,2]; ord<-order(score,decreasing=TRUE)
 expect<-data.frame(cluster_id=cl,gene_id=ids[ord],Score=score[ord],Rank=seq_along(ord))
 z<-ranks[ranks$Cluster==cl,]
 stopifnot(identical(z$Rowname,expect$gene_id),identical(z$Rank,expect$Rank))
 errs[[paste0('score_',cl)]]<-check(z$Score,expect$Score,1e-10)
 recomputed[[cl]]<-expect; tops[[cl]]<-head(expect,5)
}
write_t(do.call(rbind,tops),'independent_top5')
top<-tab('top5_genes'); lab<-tab('Fig3A_actual_gene_labels')
stopifnot(nrow(top)==35,nrow(lab)==35)
for(cl in rownames(ds)) stopifnot(identical(top$Rowname[top$Cluster==cl],tops[[cl]]$gene_id),identical(lab$sample[lab$cluster_id==cl],tops[[cl]]$gene_id))
ap<-tab('Fig3A_all_APL_points')
for(cl in rownames(ds)) for(ty in c('cell','gene')) {
 z<-ap[ap$apl_cluster_id==cl & ap$type==ty,]; pts<-if(ty=='cell') ca@std_coords_cols else G
 stopifnot(nrow(z)==nrow(pts),setequal(z$sample,rownames(pts)))
 errs[[paste('A',cl,ty)]]<-check(z[,c('x','y')],project(pts[z$sample,,drop=FALSE],ds[cl,]/ca@D,which(ck@cell_clusters==cl),ca@std_coords_cols))
}
sel<-tab('panel_cluster_selection'); cid<-setNames(sel$cluster_id,sel$role); map<-tab('cluster_annotation_reference_map')
ct<-table(cc$cluster,cc$reference)
for(role in c('B_cell','T_cell','Macrophage')) {ref<-c(B_cell='B cell',T_cell='T cell',Macrophage='macrophage')[[role]]; stopifnot(cid[[role]]==rownames(ct)[which.max(ct[,ref])],sum(ct[,ref]==max(ct[,ref]))==1)}
for(role in c('Endothelial_cell','Vascular_endothelial_cell')) stopifnot(cid[[role]]==map$cluster_id[map$predicted_annotation==role])
stopifnot(!any(grepl('vascular',unique(cc$reference),ignore.case=TRUE)))
anglechecks<-list()
for(n in c('Fig3B_Bcell_principal','Fig3C_endothelial_principal','S1D_Bcell_standard','S1E_endothelial_standard')) {
 base<-if(grepl('Bcell',n))cid[['B_cell']] else cid[['Endothelial_cell']]
 std<-grepl('standard',n); pts<-if(std)ca@std_coords_cols else X; dd<-if(std)sweep(ds,2,ca@D,'/') else ds
 z<-tab(paste0(n,'_cells')); d<-tab(paste0(n,'_directions'))
 stopifnot(identical(z$cell_id,rownames(pts)),identical(d$cluster_id,rownames(dd)))
 errs[[n]]<-check(z[,c('x','y')],project(pts,dd[base,],which(ck@cell_clusters==base),pts))
 expected<-project(dd,dd[base,],which(ck@cell_clusters==base),pts)
 errs[[paste0(n,'_directions')]]<-check(d[,c('x','y')],expected)
 trans<-angles(dd)[base,]; trans[base]<-0
 projected<-atan2(expected[,2],expected[,1])*180/pi
 anglechecks[[n]]<-data.frame(panel=n,to_cluster_id=rownames(dd),principal=angle[base,],transformed=trans,projected=projected,standard_delta=abs(trans-angle[base,]))
}
ac<-do.call(rbind,anglechecks);write_t(ac,'independent_angles')
pr<-tab('S1B_all_direction_projections')
for(cl in rownames(ds)) {z<-pr[pr$base_cluster_id==cl,];stopifnot(identical(z$to_cluster_id,rownames(ds)));errs[[paste0('S1B_',cl)]]<-check(z[,c('x','y')],project(ds,ds[cl,],which(ck@cell_clusters==cl)))}
flows<-tab('S1C_reference_flows');stopifnot(sum(flows$Freq)==1882)
for(i in seq_len(nrow(flows))) stopifnot(flows$Freq[i]==sum(cc$cluster==flows$cluster_id[i]&cc$predicted_annotation==flows$predicted_annotation[i]&cc$reference==flows$reference[i]))
stopifnot(identical(as.integer(tapply(flows$Freq,flows$cluster_id,sum)),as.integer(rowSums(ct))),identical(as.integer(tapply(flows$Freq,flows$reference,sum)),as.integer(colSums(ct))))
comb2<-function(x)x*(x-1)/2
observed<-sum(comb2(ct)); rowpairs<-sum(comb2(rowSums(ct)));colpairs<-sum(comb2(colSums(ct)));allpairs<-comb2(sum(ct))
ari<-(observed-rowpairs*colpairs/allpairs)/((rowpairs+colpairs)/2-rowpairs*colpairs/allpairs)
p<-ct/sum(ct); px<-rowSums(p);py<-colSums(p);ind<-outer(px,py); nz<-p>0
mi<-sum(p[nz]*log(p[nz]/ind[nz])); entropy<-function(q)-sum(q[q>0]*log(q[q>0])); nmi<-mi/max(entropy(px),entropy(py))
# Independently rebuild retained historical events and member-overlap edges.
lc<-ck@log$clusters; stopifnot(identical(lc,readRDS(file.path(render,'objects','split_merge_full_log.rds'))$clusters))
stages<-character(); edges<-list(); detail<-list(); previous<-'root'
for(k in which(grepl('iter_0|split|merge|end',colnames(lc)))) {
 before<-as.character(lc[,k-1]); after<-as.character(lc[,k]); stage<-colnames(lc)[k]
 if(identical(before,after)) next
 overlaps<-table(before,after); ij<-which(overlaps>0,arr.ind=TRUE)
 edges[[stage]]<-data.frame(from=paste(previous,rownames(overlaps)[ij[,1]],sep='-'),to=paste(stage,colnames(overlaps)[ij[,2]],sep='-'))
 detail[[stage]]<-data.frame(stage=stage,before_stage=colnames(lc)[k-1],from_cluster=rownames(overlaps)[ij[,1]],to_cluster=colnames(overlaps)[ij[,2]],ncells=as.integer(overlaps[ij]))
 stages<-c(stages,stage);previous<-stage
}
e<-do.call(rbind,edges); actual<-tab('Fig3D_history_edges'); sortedge<-function(x)sort(paste(x$from,x$to,sep=' -> '))
stopifnot(identical(sortedge(e),sortedge(actual)),nrow(e)==23,length(unique(c(e$from,e$to)))==22)
write_t(do.call(rbind,detail),'independent_history_edge_members')
h<-tab('Fig3D_node_annotations');mem<-tab('Fig3D_all_node_cell_membership');hxy<-tab('Fig3D_all_node_APL_coordinates')
stopifnot(nrow(h)==21,setequal(h$node,setdiff(unique(c(e$from,e$to)),'root-0')))
hist_goa<-readRDS(file.path(render,'objects','history_GOA.rds'))
resource<-tab('annotation_resource_cellmarker_mouse'); sets<-split(resource$gene,gsub(' ','_',resource$cell_type,fixed=TRUE));sets<-lapply(sets,intersect,rownames(G));universe<-unique(unlist(sets)); sizes<-lengths(sets); sets<-sets[sizes>=10 & sizes<=500]
indgoa<-function(assign,stage) {
 rows<-list()
 for(cl in sort(unique(assign))) {
  genes<-intersect(names(assign)[assign==cl],universe);hits<-vapply(sets,function(s)length(intersect(s,genes)),integer(1)); keep<-hits>0
  ps<-phyper(hits[keep]-1,lengths(sets)[keep],length(universe)-lengths(sets)[keep],length(genes),lower.tail=FALSE)
  z<-data.frame(stage=stage,cluster_id=cl,gene_set=names(sets)[keep],pval=ps,padj=p.adjust(ps,'BH'),ngois_in_set=hits[keep],ngenes_in_set=lengths(sets)[keep],ngois=length(genes),ngenes_in_sets=length(universe))
  rows[[cl]]<-z[order(z$padj),]
 }
 do.call(rbind,rows)
}
goa_all<-list();goa_all[['final']]<-indgoa(savedgenes[!is.na(savedgenes)],'final')
fg<-tab('full_GOA')
goacheck<-function(expected,actual) {keys<-paste(expected$cluster_id,expected$gene_set); ai<-match(keys,paste(actual$cluster_id,actual$gene_set));stopifnot(!anyNA(ai),length(ai)==nrow(actual)); for(n in c('pval','padj','ngois_in_set','ngenes_in_set','ngois','ngenes_in_sets'))check(expected[[n]],actual[[n]][ai],1e-10)}
errs$final_GOA<-goacheck(goa_all[['final']],fg)
selected<-sqrt(rowSums(G^2))>=quantile(sqrt(rowSums(G^2)),.8)
nearest<-function(dd) {pts<-ca@std_coords_rows[selected,,drop=FALSE]; dot<-pts%*%t(dd);distance2<-outer(rowSums(pts^2),rep(1,nrow(dd)))-sweep(dot^2,2,rowSums(dd^2),'/'); distance2[dot<0]<-Inf; setNames(rownames(dd)[max.col(-distance2,ties.method='first')],rownames(pts))}
stopifnot(identical(unname(nearest(ds)),unname(savedgenes[names(nearest(ds))])))
for(stage in stages) {
 dr<-ck@log$directions; dd<-as.matrix(dr[dr$iter==stage,!names(dr)%in%c('iter','dirname'),drop=FALSE]);rownames(dd)<-dr$dirname[dr$iter==stage]
 ga<-indgoa(nearest(dd),stage);goa_all[[stage]]<-ga
 saved<-do.call(rbind,lapply(names(hist_goa[[stage]]),function(cl)cbind(cluster_id=cl,hist_goa[[stage]][[cl]])))
 errs[[paste0('GOA_',stage)]]<-goacheck(ga,saved)
 for(i in which(h$iteration==stage)) {
  cl<-h$cluster_id[i]; node<-h$node[i]; member<-as.character(lc[,stage])==cl
  z<-mem[mem$node==node,];stopifnot(identical(z$cell_id,rownames(X)),identical(z$in_cluster,member),sum(member)==h$ncells[i])
  z<-hxy[hxy$node==node,];stopifnot(identical(z$cell_id,rownames(X)))
  errs[[paste0('history_',node)]]<-check(z[,c('x','y')],project(X,dd[cl,],which(member)))
 }
}
write_t(do.call(rbind,goa_all),'independent_GOA')
write_t(data.frame(check=names(errs),max_absolute_error=unlist(errs)),'numeric_errors')
res<-list(status='PASS_INDEPENDENT_NUMERIC',implementation_sha='a33e815971f8bb89e8136ed65ee41b99a2f3a2e9',cells=nrow(X),genes=nrow(G),assigned_genes=sum(!is.na(gc$cluster)),clusters=nrow(ds),alpha=ck@parameters$alpha_genes,ARI=ari,NMImax=nmi,history_stages=stages,history_nodes=22,history_edges=23,principal_projection_max_angle_error=max(abs(ac$projected[grepl('principal',ac$panel)]-ac$principal[grepl('principal',ac$panel)])),standard_max_angle_change=max(ac$standard_delta),B_T_angle=angle[cid[['B_cell']],cid[['T_cell']]],B_Macrophage_angle=angle[cid[['B_cell']],cid[['Macrophage']]],Endothelial_Vascular_angle=angle[cid[['Endothelial_cell']],cid[['Vascular_endothelial_cell']]],strict_author_artifact_equivalence='BLOCKED')
jsonlite::write_json(res,file.path(out,'numeric_result.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
print(res);capture.output(sessionInfo(),file=file.path(out,'sessionInfo.txt'))
