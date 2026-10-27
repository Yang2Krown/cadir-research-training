suppressPackageStartupMessages({library(CAdir);library(APL);library(ggplot2)})
out<-'reviews/lm-fig3-20261027/repair'
run<-'/workspace/cadir-lm-fig3-artifacts-20261027/hvg-only/case-htbeu88g'
render<-'/workspace/cadir-lm-fig3-artifacts-20261027/render-final'
sourcepath<-normalizePath(file.path(out,'repair_s1_legend.R'))
env<-new.env(parent=globalenv());captured<-list()
env$commandArgs<-function(trailingOnly=FALSE) if(trailingOnly)c(run,render,normalizePath(out)) else paste0('--file=',sourcepath)
env$ggsave<-function(filename,plot,...) {captured[[basename(filename)]]<<-plot;invisible(NULL)}
source(sourcepath,local=env)
results<-list();allpoints<-read.delim(file.path(render,'tables/Fig3A_all_APL_points.tsv'))
for(n in c('S1D_Bcell_standard','S1E_endothelial_standard')) {
 p<-captured[[paste0(n,'.png')]];base<-if(grepl('S1D',n))'cluster_3' else 'cluster_7'
 actual<-p$data;prior<-allpoints[allpoints$apl_cluster_id==base,]
 key<-function(z)paste(z$type,z$sample);prior<-prior[match(key(actual),key(prior)),]
 stopifnot(!anyNA(prior$sample),nrow(actual)==7882,identical(key(actual),key(prior)),p$coordinates$ratio==1)
 err<-max(abs(as.matrix(actual[,c('x','y')])-as.matrix(prior[,c('x','y')])))
 stopifnot(err<1e-10)
 dirlayer<-Filter(function(l)inherits(l$geom,'GeomAbline'),p$layers)
 stopifnot(length(dirlayer)==1)
 dl<-dirlayer[[1]]$data
 expected<-if(grepl('S1D',n))c('T_cell','Macrophage') else 'Vascular_endothelial_cell'
 cls<-if(grepl('S1D',n))c('cluster_4','cluster_5') else 'cluster_2'
 d<-read.delim(file.path(render,'tables',paste0(n,'_directions.tsv')))
 stopifnot(identical(as.character(dl$role),expected))
 target<-d[match(cls,d$cluster_id),];slope_error<-max(abs(dl$slope-target$y/target$x));stopifnot(slope_error<1e-10)
 colour<-p$scales$get_scales('colour')
 stopifnot(identical(colour$breaks,expected),identical(colour$labels,gsub('_',' ',expected)),p$theme$legend.position=='bottom')
 gene_labels<-Filter(function(l)inherits(l$geom,'GeomTextRepel'),p$layers)[[1]]$data
 original<-read.delim(file.path(render,'tables/top5_genes.tsv'))
 stopifnot(identical(gene_labels$sample,original$Rowname[original$Cluster==base]))
 # The comparison overlays retain the same actual member coordinate rows.
 overlays<-Filter(function(l)inherits(l$geom,'GeomPoint') && is.data.frame(l$data),p$layers)
 stopifnot(length(overlays)==length(cls))
 cells<-read.delim(file.path(render,'tables',paste0(n,'_cells.tsv')))
 for(i in seq_along(cls)) {
  expectedrows<-cells[cells$cluster_id==cls[i],]
  stopifnot(nrow(overlays[[i]]$data)==nrow(expectedrows),max(abs(as.matrix(overlays[[i]]$data[,c('x','y')])-as.matrix(expectedrows[,c('x','y')])))<1e-10)
 }
 results[[n]]<-list(points=nrow(actual),all_points_max_error=err,direction_slope_error=slope_error,legend_labels=colour$labels,coord_equal_ratio=p$coordinates$ratio,top5_IDs_unchanged=TRUE,comparison_member_coordinates_unchanged=TRUE)
}
jsonlite::write_json(list(status='PASS_INDEPENDENT_REPAIR_PLOT_DATA',scope='Constructed actual fixed-source ggplot objects with ggsave intercepted; no image regeneration or CA/clustering/GOA rerun.',panels=results),file.path(out,'plot_result.json'),pretty=TRUE,auto_unbox=TRUE,digits=17)
cat('PASS: all 7882 points per panel, highlighted members, top5 IDs, direction slopes, legend identities and coord_equal unchanged.\n')
