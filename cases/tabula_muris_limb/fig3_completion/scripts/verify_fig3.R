#!/usr/bin/env Rscript
# Implementation self-check only; independent review is a separate required step.
suppressPackageStartupMessages({library(CAdir);library(APL)})
args<-commandArgs(trailingOnly=TRUE);stopifnot(length(args)==2)
run<-args[1];out<-args[2]
readt<-function(n)read.delim(file.path(out,'tables',n),check.names=FALSE)
statusfile<-file.path(out,'provenance','verification.json')
write_status<-function(x)jsonlite::write_json(x,statusfile,pretty=TRUE,auto_unbox=TRUE,digits=17)
write_status(list(status='RUNNING_IMPLEMENTER_SELFCHECK',independent_review='PENDING'))
ok<-tryCatch({
 ca<-readRDS(file.path(run,'ca.rds'));ck<-readRDS(file.path(run,'cadir.rds'));an<-readRDS(file.path(run,'cadir_annotated.rds'))
 cc<-readt('all_cell_assignments.tsv');gc<-readt('all_gene_assignments.tsv')
 stopifnot(nrow(cc)==1882,nrow(gc)==6000,identical(cc$cell_id,rownames(ca@prin_coords_cols)),
 identical(cc$cluster,unname(as.character(ck@cell_clusters))),identical(cc$predicted_annotation,unname(as.character(an@cell_clusters))))
 genes<-setNames(as.character(ck@gene_clusters),names(ck@gene_clusters))
 stopifnot(identical(gc$gene_id,rownames(ca@prin_coords_rows)),identical(gc$cluster,unname(genes[gc$gene_id])))
 # Explicit projection and distance formula, independent of apl_model.
 project<-function(coords,dir,idx,orientation_coords=ca@prin_coords_cols){
   u<-dir/sqrt(sum(dir^2));if(sum(colMeans(orientation_coords[idx,,drop=FALSE])*dir)<0)u<- -u
   x<-drop(coords%*%u);y<-sqrt(pmax(0,rowSums(coords^2)-x^2));cbind(x=x,y=y)
 }
 tolerance<-1e-7;errs<-c()
 ap<-readt('Fig3A_all_APL_points.tsv')
 for(cl in levels(ck@cell_clusters)) {
   z<-ap[ap$apl_cluster_id==cl,];idx<-which(ck@cell_clusters==cl);dir<-ck@directions[cl,]/ca@D
   for(type in c('cell','gene')) {
     zz<-z[z$type==type,];coords<-if(type=='cell')ca@std_coords_cols else ca@prin_coords_rows
     expected<-project(coords[zz$sample,,drop=FALSE],dir,idx,ca@std_coords_cols)
     errs<-c(errs,max(abs(as.matrix(zz[,c('x','y')])-expected)))
   }
 }
 stopifnot(max(errs)<tolerance)
 ranks<-readt('all_gene_ranks.tsv');top<-readt('top5_genes.tsv')
 stopifnot(nrow(ranks)==1200,nrow(top)==35,identical(top$Rowname,ranks$Rowname[ranks$Rank<=5]))
 labels<-readt('Fig3A_actual_gene_labels.tsv');stopifnot(nrow(labels)==35)
 for(cl in levels(ck@cell_clusters))stopifnot(identical(labels$sample[labels$cluster_id==cl],top$Rowname[top$Cluster==cl]))
 score_err<-c()
 for(cl in levels(ck@cell_clusters)) {
  z<-ranks[ranks$Cluster==cl,];xy<-project(ca@prin_coords_rows[z$Rowname,,drop=FALSE],ck@directions[cl,],which(ck@cell_clusters==cl))
  score_err<-c(score_err,max(abs(z$Score-(xy[,1]-xy[,2]*ck@parameters$alpha_genes))))
 }
 stopifnot(max(score_err)<1e-10)
 selection<-readt('panel_cluster_selection.tsv');cid<-setNames(selection$cluster_id,selection$role)
 # Panels use the exact same saved basis, with no CA calls in the renderer.
 for(n in c('Fig3B_Bcell_principal','Fig3C_endothelial_principal','S1D_Bcell_standard','S1E_endothelial_standard')) {
   cl<-if(grepl('Bcell',n))cid[['B_cell']] else cid[['Endothelial_cell']]
   isstd<-grepl('standard',n);coords<-if(isstd)ca@std_coords_cols else ca@prin_coords_cols
   dirs<-if(isstd)sweep(ck@directions,2,ca@D,'/') else ck@directions
   z<-readt(paste0(n,'_cells.tsv'));d<-readt(paste0(n,'_directions.tsv'))
   stopifnot(identical(z$cell_id,rownames(coords)),max(abs(as.matrix(z[,c('x','y')])-project(coords,dirs[cl,],which(ck@cell_clusters==cl),coords)))<tolerance,
      max(abs(as.matrix(d[,c('x','y')])-project(dirs,dirs[cl,],which(ck@cell_clusters==cl),coords)))<tolerance)
 }
 a<-readt('S1A_pairwise_direction_angles_degrees.tsv');amat<-as.matrix(a[,-1]);stopifnot(max(abs(amat-t(amat)))<1e-10)
 flows<-readt('S1C_reference_flows.tsv');stopifnot(sum(flows$Freq)==1882)
 for(i in seq_len(nrow(flows)))stopifnot(flows$Freq[i]==sum(cc$cluster==flows$cluster_id[i]&cc$predicted_annotation==flows$predicted_annotation[i]&cc$reference==flows$reference[i]))
 h<-readt('Fig3D_node_annotations.tsv');mem<-readt('Fig3D_all_node_cell_membership.tsv');xy<-readt('Fig3D_all_node_APL_coordinates.tsv')
 for(i in seq_len(nrow(h))) {
   z<-mem[mem$node==h$node[i],];ref<-as.character(ck@log$clusters[,h$iteration[i]])==h$cluster_id[i]
   stopifnot(nrow(z)==1882,identical(z$cell_id,rownames(ca@prin_coords_cols)),identical(z$in_cluster,ref),sum(ref)==h$ncells[i])
   dirs<-ck@log$directions;dir<-as.numeric(dirs[dirs$iter==h$iteration[i]&dirs$dirname==h$cluster_id[i],!colnames(dirs)%in%c('iter','dirname')])
   q<-xy[xy$node==h$node[i],];stopifnot(max(abs(as.matrix(q[,c('x','y')])-project(ca@prin_coords_cols,dir,which(ref))))<tolerance)
 }
 files<-list.files(file.path(out,'figures'),full.names=TRUE)
 stopifnot(length(files)==18,all(file.info(files)$size>5000))
 write_status(list(status='PASS_IMPLEMENTER_SELFCHECK_ONLY',independent_review='PENDING',cells=nrow(cc),genes=nrow(gc),ranks=nrow(ranks),top5_labels=nrow(top),
   panels=9,PNG_PDF_files=length(files),history_annotated_nodes=nrow(h),APL_coordinate_max_error=max(errs),score_max_error=max(score_err),
   strict_author_input_equivalence='BLOCKED_MISSING_MARKER_FILTERED_RDS_PRIVATE_PACKAGE_IDENTITY'))
 TRUE
},error=function(e){write_status(list(status='FAIL_IMPLEMENTER_SELFCHECK',error=conditionMessage(e),independent_review='PENDING'));message(conditionMessage(e));FALSE})
if(!ok)quit(status=1)
cat('PASS implementation self-check; independent review remains pending.\n')
