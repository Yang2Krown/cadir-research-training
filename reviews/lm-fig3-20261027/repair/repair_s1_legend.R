#!/usr/bin/env Rscript
# Repaint only S1D/E from the same saved objects. No CA, clustering or GOA call.
suppressPackageStartupMessages({library(CAdir);library(APL);library(ggplot2)})
options(warn=1)
args<-commandArgs(trailingOnly=TRUE);stopifnot(length(args)==3)
run<-args[1];oldrender<-args[2];out<-args[3]
script<-sub('^--file=','',grep('^--file=',commandArgs(),value=TRUE)[1])
source(file.path(dirname(normalizePath(script)),'direction_legend.R'))
dir.create(out,recursive=TRUE,showWarnings=FALSE)
ca<-readRDS(file.path(run,'ca.rds'));ck<-readRDS(file.path(run,'cadir.rds'))
selection<-read.delim(file.path(oldrender,'tables/panel_cluster_selection.tsv'),check.names=FALSE)
cid<-setNames(selection$cluster_id,selection$role)
RNGkind('Mersenne-Twister','Inversion','Rejection');set.seed(2358)
checks<-list()
for(spec in list(list(base='B_cell',others=c('T_cell','Macrophage'),name='S1D_Bcell_standard'),
                 list(base='Endothelial_cell',others='Vascular_endothelial_cell',name='S1E_endothelial_standard'))) {
 cl<-unname(cid[spec$base]);ids<-unname(cid[spec$others]);colours<-c('#d44a3d','#00b1ea')
 dirs<-sweep(ck@directions,2,ca@D,'/')
 model<-CAdir::apl_model(ca@std_coords_cols,dirs[cl,],which(ck@cell_clusters==cl))
 xy<-model(ca@std_coords_cols);dp<-model(dirs)
 original_cells<-read.delim(file.path(oldrender,'tables',paste0(spec$name,'_cells.tsv')),check.names=FALSE)
 original_dirs<-read.delim(file.path(oldrender,'tables',paste0(spec$name,'_directions.tsv')),check.names=FALSE)
 stopifnot(identical(original_cells$cell_id,rownames(xy)),identical(original_dirs$cluster_id,rownames(dp)))
 cell_error<-max(abs(as.matrix(original_cells[,c('x','y')])-xy))
 direction_error<-max(abs(as.matrix(original_dirs[,c('x','y')])-dp))
 stopifnot(cell_error<1e-10,direction_error<1e-10)
 p<-CAdir::cluster_apl(ca,ck,cluster=cl,direction=ck@directions[cl,],group=which(ck@cell_clusters==cl),
     highlight_cluster=TRUE,show_genes=TRUE,label_genes=TRUE,show_lines=FALSE,size_factor=.5,ntop=5)
 displayed<-p$data[p$data$type=='cell',]
 stopifnot(max(abs(as.matrix(displayed[,c('x','y')])-xy[displayed$sample,,drop=FALSE]))<1e-10)
 for(i in seq_along(ids)) {
   j<-ids[i]
   p<-p+geom_point(data=as.data.frame(xy[ck@cell_clusters==j,,drop=FALSE]),
                  aes(x,y),inherit.aes=FALSE,color=colours[i],size=1.2)
 }
 p<-p+coord_equal()+theme_bw(base_size=13)+
      ggtitle(paste0(gsub('_',' ',spec$base),' [',cl,'] | standard coordinates'))+
      labs(subtitle='6000 HVG-only | GOA predictions; see cluster selection table')
 p<-add_standard_direction_legend(p,dp[ids,,drop=FALSE],spec$others,colours)
 for(ext in c('png','pdf'))ggsave(file.path(out,paste0(spec$name,'.',ext)),p,width=10,height=7,dpi=160,bg='white')
 checks[[spec$name]]<-list(cell_coordinate_max_error_vs_saved_table=cell_error,
       direction_coordinate_max_error_vs_saved_table=direction_error,
       cells=nrow(xy),directions=nrow(dp),legend_labels=gsub('_',' ',spec$others),
       equal_coordinate_ratio=p$coordinates$ratio)
}
jsonlite::write_json(list(status='DISPLAY_ONLY_REPAIR_IMPLEMENTER_SELFCHECK',
 source_run=normalizePath(run),unchanged_data_directory=normalizePath(file.path(oldrender,'tables')),
 CA_MD5=unname(tools::md5sum(file.path(run,'ca.rds'))),
 cadir_MD5=unname(tools::md5sum(file.path(run,'cadir.rds'))),checks=checks,
 independent_review='PENDING_DISPLAY_RECHECK'),file.path(out,'repair_checks.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
capture.output(sessionInfo(),file=file.path(out,'sessionInfo.txt'))
cat('Only S1D/E repainted; points, directions and coord_equal preserved.\n')
