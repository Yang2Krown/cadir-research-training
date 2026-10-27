#!/usr/bin/env Rscript
# One saved CA basis, fixed ranks and real split/merge log; no reclustering.
suppressPackageStartupMessages({library(CAdir); library(APL); library(ggplot2); library(patchwork)})
options(warn=1)
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
run <- normalizePath(args[1]); out <- args[2]
dir.create(out, recursive=TRUE, showWarnings=FALSE)
for (d in c('tables','figures','provenance','objects')) dir.create(file.path(out,d),showWarnings=FALSE)
wt <- function(x,n) write.table(x,file.path(out,'tables',n),sep='\t',quote=TRUE,row.names=FALSE,na='NA')
wj <- function(x,n) jsonlite::write_json(x,file.path(out,'provenance',n),pretty=TRUE,auto_unbox=TRUE,null='null',digits=17)
savefig <- function(p,n,w=10,h=7) {
  ggsave(file.path(out,'figures',paste0(n,'.png')),p,width=w,height=h,dpi=160,bg='white',limitsize=FALSE)
  ggsave(file.path(out,'figures',paste0(n,'.pdf')),p,width=w,height=h,bg='white',limitsize=FALSE)
}
# ggrepel 0.9.8 embeds a ggplot4 legend key; our fixed ggplot is 3.5.2.
# Suppress only the redundant text-label legend; point legends remain intact.
text_legend_compat <- function(p) {
 for(i in seq_along(p$layers)) if(inherits(p$layers[[i]]$geom,'GeomTextRepel') || inherits(p$layers[[i]]$geom,'GeomLabelRepel')) p$layers[[i]]$show.legend<-FALSE
 p
}
status <- list(status='RUNNING_IMPLEMENTER_SELFCHECK',strict_author_input_equivalence='BLOCKED_MISSING_AUTHOR_ARTIFACTS',independent_review='PENDING')
wj(status,'render_status.json')
options(error=function(){status$status<-'FAILED_IMPLEMENTER_RENDER';status$error<-geterrmessage();wj(status,'render_status.json');quit(status=1)})
started <- proc.time()[['elapsed']]
ca <- readRDS(file.path(run,'ca.rds'))
ck <- readRDS(file.path(run,'cadir.rds'))
ann <- readRDS(file.path(run,'cadir_annotated.rds'))
cells <- read.delim(file.path(run,'cell_clusters.tsv'),check.names=FALSE)
stopifnot(identical(cells$cell_id,rownames(ca@prin_coords_cols)), identical(names(ck@cell_clusters),cells$cell_id),
          identical(unname(as.character(ck@cell_clusters)),cells$cluster),
          identical(unname(ck@directions),unname(ann@directions)))
RNGkind('Mersenne-Twister','Inversion','Rejection'); set.seed(2358)
saveRDS(.Random.seed,file.path(out,'objects','rng_before_render.rds'))
tracked <- c('cluster_apl','apl_model','plot_clusters','plot_results','sm_plot','build_graph','assign_genes','rank_genes','get_angle','annotate_by_gse')
md5 <- list()
for(n in tracked) {
  f <- get(n,envir=asNamespace('CAdir'))
  p <- file.path(out,'provenance',paste0('function_',n,'.R'))
  dput(list(formals=formals(f),body=body(f)),file=p)
  md5[[n]] <- unname(tools::md5sum(p))
}
wj(list(run=run,CA_MD5=unname(tools::md5sum(file.path(run,'ca.rds'))),
        cadir_MD5=unname(tools::md5sum(file.path(run,'cadir.rds'))),
        alpha_genes=ck@parameters$alpha_genes,RNGkind=RNGkind(),function_md5=md5,
        rank_action='Reuse saved scores/ranks; independently verify against same CA and saved alpha. No new ranking cutoff or CA.',
        input_scope='6000 HVG-only; published Methods dimensions, unresolved extra marker CSV in author qmd.'),'render_provenance.json')

# The original IDs, automatic names and reference labels remain distinct.
map <- do.call(rbind,lapply(levels(ck@cell_clusters),function(cl){
 i <- which(ck@cell_clusters==cl); a<-unique(as.character(ann@cell_clusters[i])); stopifnot(length(a)==1)
 t<-sort(table(cells$reference[i]),decreasing=TRUE)
 data.frame(cluster_id=cl,predicted_annotation=a,ncells=length(i),reference_majority=names(t)[1],
            reference_majority_n=as.integer(t[1]),reference_majority_fraction=as.integer(t[1])/length(i))
}))
wt(map,'cluster_annotation_reference_map.tsv')
cells$predicted_annotation <- as.character(ann@cell_clusters)
wt(cells,'all_cell_assignments.tsv')
wt(read.delim(file.path(run,'gene_clusters.tsv')),'all_gene_assignments.tsv')
wt(cbind(cluster_id=rownames(ck@directions),as.data.frame(ck@directions)),'directions_principal.tsv')
wt(cbind(cluster_id=rownames(ck@directions),as.data.frame(sweep(ck@directions,2,ca@D,'/'))),'directions_standard.tsv')
wt(data.frame(dimension=seq_along(ca@D),D=ca@D),'CA_singular_values.tsv')

# Saved S-alpha rankings are checked numerically, including the displayed top 5.
ranks <- do.call(rbind,Filter(is.data.frame,ck@gene_ranks))
rank_err <- numeric()
for(cl in names(ck@gene_ranks)) {
 r<-ck@gene_ranks[[cl]]; if(!is.data.frame(r)) next
 m<-apl_model(ca@prin_coords_cols,ck@directions[cl,],which(ck@cell_clusters==cl))
 xy<-m(ca@prin_coords_rows[r$Rowname,,drop=FALSE])
 rank_err<-c(rank_err,max(abs(r$Score-(xy[,1]-xy[,2]*ck@parameters$alpha_genes))))
 stopifnot(identical(r$Rank,seq_len(nrow(r))),all(diff(r$Score)<=0))
}
stopifnot(max(rank_err)<1e-10)
ranks$predicted_annotation<-map$predicted_annotation[match(ranks$Cluster,map$cluster_id)]
wt(ranks,'all_gene_ranks.tsv');wt(ranks[ranks$Rank<=5,],'top5_genes.tsv')
goa<-CAdir::goa_per_cluster(ck,universe=rownames(ca@prin_coords_rows),set='CellMarker',org='mm',min_size=10,max_size=500,filter_literature=FALSE)
wt(do.call(rbind,lapply(names(goa),function(cl)cbind(cluster_id=cl,goa[[cl]]))),'full_GOA.tsv')
gs<-CAdir::load_ct_gene_set(set='CellMarker',org='mm');wt(gs,'annotation_resource_cellmarker_mouse.tsv')

# Fig3A: cells use standard coordinates when genes are drawn (upstream semantics).
pa<-CAdir::plot_clusters(ck,ca,show_genes=TRUE,label_genes=TRUE,ntop=5,title_prefix='',axis=TRUE,text_size=13,legend_pos='bottom',return_list=TRUE)
apl_data<-list();label_data<-list()
for(i in seq_along(pa)) {
 cl<-levels(ck@cell_clusters)[i]; pred<-map$predicted_annotation[match(cl,map$cluster_id)]
 pa[[i]]<-text_legend_compat(pa[[i]])+ggtitle(paste0(gsub('_',' ',pred),' [',cl,']'))
 apl_data[[cl]]<-cbind(apl_cluster_id=cl,pa[[i]]$data)
 label_layers<-Filter(function(l)inherits(l$geom,'GeomTextRepel'),pa[[i]]$layers)
 stopifnot(length(label_layers)==1)
 label_data[[cl]]<-cbind(cluster_id=cl,label_layers[[1]]$data)
}
wt(do.call(rbind,apl_data),'Fig3A_all_APL_points.tsv')
wt(do.call(rbind,label_data),'Fig3A_actual_gene_labels.tsv')
savefig(wrap_plots(pa,ncol=3,guides='collect')+plot_annotation(title='Fig3A | Limb Muscle (6000 HVG-only)',subtitle='Automatic GOA names; original cluster IDs in brackets'), 'Fig3A_association_top5',15,11)

# Choose B, T and Macrophage from the real reference contingency, then cross-check predictions.
choose_ref<-function(label) {
 tb<-table(factor(cells$cluster,levels=map$cluster_id),cells$reference)
 v<-tb[,label];stopifnot(max(v)>0,sum(v==max(v))==1)
 names(v)[which.max(v)]
}
sel<-data.frame(role=c('B_cell','T_cell','Macrophage'),cluster_id=c(choose_ref('B cell'),choose_ref('T cell'),choose_ref('macrophage')),
                basis='Unique largest overlap with original cell_ontology_class; prediction cross-check')
for(role in c('Endothelial_cell','Vascular_endothelial_cell')) {
 z<-which(map$predicted_annotation==role);stopifnot(length(z)==1)
 sel<-rbind(sel,data.frame(role=role,cluster_id=map$cluster_id[z],basis='Exact automatic GOA prediction; original reference has no vascular endothelial subtype'))
}
sel<-merge(sel,map,by='cluster_id',sort=FALSE)
stopifnot(length(unique(sel$cluster_id))==5)
wt(sel,'panel_cluster_selection.tsv')
cid<-setNames(sel$cluster_id,sel$role)

# This model exactly follows author principal/standard coordinate conversions.
proj_tables<-list();angle_checks<-list();plot_objects<-list()
pairplot<-function(base_role,other_roles,kind,filename) {
 cl<-unname(cid[base_role]); ids<-unname(cid[other_roles])
 coords<-if(kind=='principal')ca@prin_coords_cols else ca@std_coords_cols
 dirs<-if(kind=='principal')ck@directions else sweep(ck@directions,2,ca@D,'/')
 model<-apl_model(coords,dirs[cl,],which(ck@cell_clusters==cl))
 xy<-model(coords);dp<-model(dirs)
 wt(cbind(cell_id=rownames(coords),cluster_id=as.character(ck@cell_clusters),as.data.frame(xy)),paste0(filename,'_cells.tsv'))
 wt(cbind(cluster_id=rownames(dirs),as.data.frame(dp)),paste0(filename,'_directions.tsv'))
 p<-CAdir::cluster_apl(ca,ck,cluster=cl,direction=ck@directions[cl,],group=which(ck@cell_clusters==cl),
                      highlight_cluster=TRUE,show_genes=kind=='standard',label_genes=kind=='standard',show_lines=FALSE,size_factor=.5,ntop=5)
 p<-text_legend_compat(p)
 displayed_cells<-p$data[p$data$type=='cell',]
 stopifnot(max(abs(as.matrix(displayed_cells[,c('x','y')])-xy[displayed_cells$sample,,drop=FALSE]))<1e-8)
 cols<-c('#d44a3d','#00b1ea')
 for(i in seq_along(ids)) {
   j<-ids[i]; dd<-data.frame(x=dp[j,1],y=dp[j,2]); take<-ck@cell_clusters==j
   p<-p+geom_point(data=as.data.frame(xy[take,,drop=FALSE]),aes(x,y),inherit.aes=FALSE,color=cols[i],size=1.2)+
       geom_abline(intercept=0,slope=dd$y/dd$x,color=cols[i],linetype='dashed',linewidth=.8)+
       annotate('text',x=dd$x*(2+i),y=dd$y*(2+i),label=gsub('_',' ',other_roles[i]),color=cols[i],size=3.6)
 }
 p<-p+coord_equal()+theme_bw(base_size=13)+theme(legend.position='none')+
      ggtitle(paste0(gsub('_',' ',base_role),' [',cl,'] | ',kind,' coordinates'))+
      labs(subtitle='6000 HVG-only | GOA predictions; see cluster selection table')
 savefig(p,filename,10,7)
 plot_objects[[filename]]<<-p
 for(j in rownames(dirs)) {
  raw<-as.numeric(CAdir:::rad2deg(CAdir:::get_angle(ck@directions[cl,],ck@directions[j,])))
  transformed<-as.numeric(CAdir:::rad2deg(CAdir:::get_angle(dirs[cl,],dirs[j,])))
  projected<-atan2(dp[j,2],dp[j,1])*180/pi
  angle_checks[[paste(filename,j)]]<<-data.frame(panel=filename,base_cluster_id=cl,to_cluster_id=j,coordinate_type=kind,
       principal_angle_deg=raw,coordinate_angle_deg=transformed,APL_projected_angle_deg=projected,
       error_vs_principal_deg=abs(projected-raw),projection_error_deg=abs(projected-transformed))
 }
 p
}
pb<-pairplot('B_cell',c('T_cell','Macrophage'),'principal','Fig3B_Bcell_principal')
pc<-pairplot('Endothelial_cell','Vascular_endothelial_cell','principal','Fig3C_endothelial_principal')
psd<-pairplot('B_cell',c('T_cell','Macrophage'),'standard','S1D_Bcell_standard')
pse<-pairplot('Endothelial_cell','Vascular_endothelial_cell','standard','S1E_endothelial_standard')
angles<-do.call(rbind,angle_checks);wt(angles,'principal_standard_projection_angle_checks.tsv')
stopifnot(max(angles$projection_error_deg)<1e-4,max(angles$error_vs_principal_deg[angles$coordinate_type=='principal'])<1e-4)

# S1A/B: full pairwise numeric geometry and direction projections.
am<-CAdir:::rad2deg(CAdir:::get_angle(ck@directions,ck@directions))
wt(cbind(cluster_id=rownames(am),as.data.frame(am)),'S1A_pairwise_direction_angles_degrees.tsv')
hm<-as.data.frame(as.table(am));names(hm)<-c('from','to','angle')
hm$from_label<-paste(map$cluster_id[match(hm$from,map$cluster_id)],map$predicted_annotation[match(hm$from,map$cluster_id)],sep=': ')
hm$to_label<-paste(map$cluster_id[match(hm$to,map$cluster_id)],map$predicted_annotation[match(hm$to,map$cluster_id)],sep=': ')
phm<-ggplot(hm,aes(from_label,to_label,fill=angle))+geom_tile()+coord_equal()+scale_fill_gradient(low='#ef7c00',high='#29485d',name='Angle (degrees)')+
     theme_bw(base_size=10)+theme(axis.text.x=element_text(angle=60,hjust=1))+labs(x=NULL,y=NULL,title='S1A | Pairwise principal direction angles')
savefig(phm,'S1A_direction_angle_heatmap',12,10)
pr<-CAdir::plot_results(ck,ca,highlight_cluster=TRUE,title_prefix='',return_list=TRUE)
for(i in seq_len(nrow(map)))pr[[paste(i,i,sep='_')]]<-pr[[paste(i,i,sep='_')]]+
 ggtitle(paste0(map$cluster_id[i],'\n',gsub('_',' ',map$predicted_annotation[i])))+
 theme(plot.title=element_text(size=8))
savefig(wrap_plots(pr,nrow=nrow(map),ncol=nrow(map))+plot_annotation(title='S1B | Each row: APL diagonal, other cluster directions'), 'S1B_direction_projection_matrix',18,18)
projs<-do.call(rbind,lapply(map$cluster_id,function(cl){
 m<-apl_model(ca@prin_coords_cols,ck@directions[cl,],which(ck@cell_clusters==cl))
 cbind(base_cluster_id=cl,to_cluster_id=rownames(ck@directions),as.data.frame(m(ck@directions)))
}));wt(projs,'S1B_all_direction_projections.tsv')

# S1C: retain every reference category; no hand-authored biological re-labelling.
flows<-as.data.frame(table(cluster_id=cells$cluster,predicted_annotation=cells$predicted_annotation,reference=cells$reference))
flows<-flows[flows$Freq>0,];wt(flows,'S1C_reference_flows.tsv')
sd<-data.frame(CAdir=paste0(cells$cluster,': ',cells$predicted_annotation),Reference=cells$reference)
long<-ggsankey::make_long(sd,CAdir,Reference)
psank<-ggplot(long,aes(x=x,next_x=next_x,node=node,next_node=next_node,fill=factor(node),label=node))+
 ggsankey::geom_sankey(flow.alpha=.35,node.color='gray40')+ggsankey::geom_sankey_label(size=3)+
 ggsankey::theme_sankey(base_size=13)+theme(legend.position='none')+labs(x=NULL,title='S1C | Automatic prediction to original reference annotation')
savefig(psank,'S1C_reference_sankey',13,10)

# Fig3D: native graph from the actual saved log, with upstream intermediate GOA.
saveRDS(ck@log,file.path(out,'objects','split_merge_full_log.rds'))
for(n in names(ck@log)) if(is.matrix(ck@log[[n]])||is.data.frame(ck@log[[n]])) {
 wt(cbind(row_id=rownames(ck@log[[n]]),as.data.frame(ck@log[[n]])),paste0('history_',n,'.tsv'))
}
graph<-CAdir:::build_graph(ck,rm_redund=TRUE,keep_end=FALSE)
wt(igraph::as_data_frame(graph,what='edges'),'Fig3D_history_edges.tsv')
nodes<-igraph::as_data_frame(graph,what='vertices')
node_anno<-list();node_cells<-list();node_xy<-list();history_goa<-list()
for(iter in unique(sub('-.*$','',nodes$name))) {
 if(iter=='root') next
 cls<-ck@log$clusters[,iter];dirs<-ck@log$directions
 keep<-!colnames(dirs)%in%c('iter','dirname')
 d<-as.matrix(dirs[dirs$iter==iter,keep,drop=FALSE]);rownames(d)<-dirs[dirs$iter==iter,'dirname']
 f<-CAdir:::x2f(cls);names(f)<-rownames(ca@prin_coords_cols)
 tmp<-methods::new('cadir',cell_clusters=f,directions=d)
 tmp@gene_clusters<-CAdir::assign_genes(ca,tmp,qcutoff=ck@parameters$qcutoff)
 g<-CAdir::goa_per_cluster(tmp,universe=rownames(ca@std_coords_rows),org='mm',min_size=10,max_size=500,filter_literature=FALSE)
 history_goa[[iter]]<-g
 a<-CAdir::annotate_by_gse(tmp,g,alpha=.05,cost='pval')
 for(j in seq_len(nrow(d))) {
  node<-paste(iter,rownames(d)[j],sep='-');if(!node%in%nodes$name)next
  idx<-which(cls==rownames(d)[j]);m<-apl_model(ca@prin_coords_cols,d[j,],idx)
  node_anno[[node]]<-data.frame(node=node,iteration=iter,cluster_id=rownames(d)[j],automatic_annotation=rownames(a@directions)[j],ncells=length(idx),cost='pval (upstream sm_plot)')
  node_cells[[node]]<-data.frame(node=node,cell_id=rownames(ca@prin_coords_cols),in_cluster=seq_len(nrow(ca@prin_coords_cols))%in%idx)
  node_xy[[node]]<-cbind(node=node,cell_id=rownames(ca@prin_coords_cols),as.data.frame(m(ca@prin_coords_cols)))
 }
}
wt(do.call(rbind,node_anno),'Fig3D_node_annotations.tsv');wt(do.call(rbind,node_cells),'Fig3D_all_node_cell_membership.tsv')
wt(do.call(rbind,node_xy),'Fig3D_all_node_APL_coordinates.tsv')
saveRDS(history_goa,file.path(out,'objects','history_GOA.rds'))
sm<-CAdir::sm_plot(ck,ca,rm_redund=TRUE,keep_end=FALSE,highlight_cluster=TRUE,show_genes=FALSE,annotate_clusters=TRUE,
                  org='mm',inlet_side=.11,title_size=8,show_axis=FALSE,layout='tree',rotate=TRUE,n_wrap=20)
savefig(sm,'Fig3D_actual_split_merge_history',18,12)
saveRDS(list(A=lapply(pa,function(p)p$data),actual_gene_labels=label_data,cell_assignments=cells,annotation_map=map,
 selection=sel,angle_checks=angles,direction_projections=projs,history_node_annotations=node_anno),file.path(out,'objects','figure_data.rds'))
saveRDS(.Random.seed,file.path(out,'objects','rng_after_render.rds'))
capture.output(sessionInfo(),file=file.path(out,'provenance','sessionInfo.txt'))
status$status<-'COMPLETE_IMPLEMENTER_SELFCHECK_ONLY';status$clusters<-nrow(map)
status$rank_score_max_absolute_error<-max(rank_err)
status$principal_projection_max_angle_error_deg<-max(angles$error_vs_principal_deg[angles$coordinate_type=='principal'])
status$standard_coordinate_max_angle_change_deg<-max(angles$error_vs_principal_deg[angles$coordinate_type=='standard'])
status$history_nodes<-nrow(nodes);status$history_edges<-igraph::ecount(graph)
status$elapsed_seconds<-proc.time()[['elapsed']]-started
status$peak_rss_KiB<-as.numeric(regmatches(grep('^VmHWM:',readLines('/proc/self/status'),value=TRUE),regexpr('[0-9]+',grep('^VmHWM:',readLines('/proc/self/status'),value=TRUE))))
wj(status,'render_status.json');print(status)
