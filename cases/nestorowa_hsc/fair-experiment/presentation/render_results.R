# Results-only presentation. No expression RDS, reduction, clustering or metrics code.
# Usage: Rscript render_results.R RUN_ROOT DATA_INPUT_LOCK NEW_OUTPUT_DIRECTORY
args <- commandArgs(TRUE)
stopifnot(length(args)==3L)
suppressPackageStartupMessages(library(ggplot2))
run_root <- normalizePath(args[[1]],mustWork=TRUE)
lock_path <- normalizePath(args[[2]],mustWork=TRUE)
out <- args[[3]]
dir.create(out,recursive=TRUE,showWarnings=FALSE)
stopifnot(!file.exists(file.path(out,"presentation-status.json")))
sha <- function(p) digest::digest(file=p,algo="sha256",serialize=FALSE)
read_json <- function(p) jsonlite::read_json(p,simplifyVector=FALSE)
write_json <- function(x,p) jsonlite::write_json(x,p,pretty=TRUE,auto_unbox=TRUE,null="null",na="null",digits=NA)
write_tsv <- function(x,p) write.table(x,p,sep="\t",quote=TRUE,row.names=FALSE,na="NA")
inputs <- list()
track <- function(p) {
 p <- normalizePath(p,mustWork=TRUE)
 inputs[[p]] <<- list(path=p,bytes=unname(file.info(p)$size),sha256=sha(p))
 p
}
read_tracked_json <- function(p) read_json(track(p))
read_tracked_tsv <- function(p) read.delim(track(p),stringsAsFactors=FALSE,na.strings="NA",check.names=FALSE)
seeds <- c(2358L,101L,202L,303L,404L)
methods <- c("cadir","pca_snn_louvain")
method_labels <- c(cadir="CAdir",pca_snn_louvain="PCA + SNN/Louvain")
colors <- c("CAdir"="#315A86","PCA + SNN/Louvain"="#B3772A")
status <- list(status="RUNNING",stage="validate_consumed_results",algorithms_or_new_metrics_computed=FALSE,fixed_example_seed=2358L)
tryCatch({
 admission <- read_tracked_json(file.path(run_root,"admission-used.json"))
 stopifnot(isTRUE(admission$formal_execution_permitted),admission$decision=="PASS_LIMITED_FORMAL_EXECUTION",sha(lock_path)==admission$data_lock_sha256)
 lock <- read_tracked_json(lock_path)
 locked <- setNames(lock$files,vapply(lock$files,function(e)e$path,character(1)))
 locked_path <- function(p) {
  e <- locked[[p]];stopifnot(!is.null(e),file.info(p)$size==e$bytes,sha(p)==e$sha256)
  track(p)
 }
 reference <- read.delim(locked_path(lock$reference_path),stringsAsFactors=FALSE,na.strings="NA")
 final_ids <- readLines(locked_path(lock$final_cell_ids_path))
 eval_ids <- readLines(locked_path(lock$evaluation_ids_path))
 hvg_ids <- readLines(locked_path(lock$HVG_ids_path))
 qc_path <- file.path(dirname(lock$shared_input_path),"cell-qc.tsv")
 qc <- read.delim(locked_path(qc_path),stringsAsFactors=FALSE)
 thresholds <- read_json(locked_path(file.path(dirname(lock$shared_input_path),"qc-thresholds.json")))
 summary_entries <- Filter(function(e)basename(e$path)=="preparation-summary.json",lock$files)
 stopifnot(length(summary_entries)==1L)
 prep <- read_json(locked_path(summary_entries[[1]]$path))
 stopifnot(identical(final_ids,qc$cell_id[qc$retained]),identical(eval_ids,reference$cell_id[reference$evaluated]),length(hvg_ids)==6000L,!anyDuplicated(reference$cell_id))
 n_total <- length(final_ids);n_eval <- length(eval_ids);n_unknown <- n_total-n_eval
 receipts <- read_tracked_json(file.path(run_root,"attempt-receipts.json"))
 keys <- vapply(receipts,function(r)paste(r$method,r$seed,sep=":"),character(1))
 expected_keys <- as.vector(outer(methods,seeds,paste,sep=":"))
 stopifnot(!anyDuplicated(keys),setequal(keys,expected_keys),length(keys)==10L)
 rows <- list();partitions <- list()
 numeric_value <- function(x) if(is.null(x)) NA_real_ else as.numeric(x)
 for(seed in seeds) for(method in methods) {
  r <- receipts[[match(paste(method,seed,sep=":"),keys)]]
  attempt <- normalizePath(r$attempt_directory,mustWork=TRUE)
  stopifnot(startsWith(attempt,paste0(run_root,"/")))
  success <- identical(as.integer(r$exit_code),0L)
  row <- list(method=method,method_label=unname(method_labels[method]),seed=seed,exit_code=as.integer(r$exit_code),success=success,status=if(success)"COMPLETE" else "FAILED",denominator=5L,n_total=n_total,n_evaluated=n_eval,ARI=NA_real_,NMI_max_entropy=NA_real_,inferred_clusters=NA_real_,core_elapsed_seconds=NA_real_,sampled_peak_rss_GiB=NA_real_,process_VmHWM_KiB=NA_real_,core_scope=NA_character_,diagnostic_exit_code=if(is.null(r$diagnostic_exit_code))NA_integer_ else as.integer(r$diagnostic_exit_code))
  if(success) {
   artifact <- read_tracked_json(file.path(attempt,"core-artifacts-sha256.json"))
   core_path <- function(name) {
    e <- Filter(function(e)e$path==name,artifact$files);stopifnot(length(e)==1L)
    p <- file.path(attempt,name);stopifnot(file.info(p)$size==e[[1]]$bytes,sha(p)==e[[1]]$sha256)
    track(p)
   }
   metric <- read_json(core_path("metrics.json"))
   resource <- read_json(core_path("core-resources.json"))
   part <- read.delim(core_path("cell-partition.tsv"),stringsAsFactors=FALSE,colClasses=c(cell_id="character",cluster="character"))
   stopifnot(identical(part$cell_id,final_ids),!anyNA(part$cluster),!anyDuplicated(part$cell_id),metric$n_total==n_total,metric$n_evaluated==n_eval,metric$n_excluded==n_unknown,metric$status=="COMPUTED_FROZEN_EVALUATION_INTERSECTION")
   row$ARI <- numeric_value(metric$ARI);row$NMI_max_entropy <- numeric_value(metric$NMI_max_entropy)
   stopifnot(is.finite(row$ARI),row$ARI>=-1-1e-10,row$ARI<=1+1e-10,is.finite(row$NMI_max_entropy),row$NMI_max_entropy>=-1e-10,row$NMI_max_entropy<=1+1e-10)
   row$inferred_clusters <- numeric_value(metric$inferred_clusters)
   row$core_elapsed_seconds <- numeric_value(resource$core_elapsed_seconds)
   row$sampled_peak_rss_GiB <- numeric_value(resource$sampled_peak_rss_KiB)/1024^2
   memory <- unlist(resource$process_memory_at_core_end,use.names=FALSE)
   hwm <- grep("^VmHWM:",memory,value=TRUE)
   if(length(hwm))row$process_VmHWM_KiB <- as.numeric(sub("^VmHWM:\\s*([0-9]+).*","\\1",hwm[[1]]))
   row$core_scope <- resource$scope
   partitions[[paste(method,seed,sep=":")]] <- part
  }
  rows[[length(rows)+1L]] <- as.data.frame(row,stringsAsFactors=FALSE)
 }
 results <- do.call(rbind,rows)
 results$method_label <- factor(results$method_label,levels=unname(method_labels))
 results$seed_label <- factor(results$seed,levels=seeds)
 write_tsv(results,file.path(out,"all-seed-presented-values.tsv"))
 write_tsv(results[c("method","seed","success","core_elapsed_seconds","sampled_peak_rss_GiB","process_VmHWM_KiB","core_scope","diagnostic_exit_code")],file.path(out,"resource-scopes.tsv"))
 successes <- vapply(methods,function(m)sum(results$success[results$method==m]),integer(1))
 success_caption <- paste(paste0(unname(method_labels),": ",successes,"/5 successful core runs"),collapse="; ")
 theme_set(theme_bw(base_size=12)+theme(panel.grid.minor=element_blank(),panel.grid.major.x=element_blank(),plot.title=element_text(face="bold"),plot.caption=element_text(hjust=0,size=9),legend.position="bottom",strip.background=element_rect(fill="#F0F2F4")))
 save_plot <- function(p,name,width=9,height=7) {
  for(ext in c("png","pdf"))ggsave(file.path(out,paste0(name,".",ext)),p,width=width,height=height,dpi=300,bg="white",limitsize=FALSE)
 }
 # Every declared seed is visible; a failed seed receives a failure label, not a score.
 metric_long <- do.call(rbind,lapply(c("ARI","NMI_max_entropy"),function(metric) {
  x <- results;x$metric <- if(metric=="ARI")"ARI" else "NMI / max entropy";x$value <- x[[metric]];x$failure_y <- if(metric=="ARI")-.9 else .06;x
 }))
 metric_long$metric <- factor(metric_long$metric,levels=c("ARI","NMI / max entropy"))
 limits <- data.frame(seed_label=factor(rep(2358L,4),levels=seeds),metric=factor(c("ARI","ARI","NMI / max entropy","NMI / max entropy"),levels=levels(metric_long$metric)),value=c(-1,1,0,1))
 p <- ggplot(metric_long,aes(seed_label,value,color=method_label,group=method_label))+geom_blank(data=limits,aes(x=seed_label,y=value),inherit.aes=FALSE)+geom_point(position=position_dodge(width=.36),size=2.8,na.rm=TRUE)+geom_text(data=metric_long[!metric_long$success,,drop=FALSE],aes(y=failure_y,label="FAILED"),position=position_dodge(width=.36),size=2.7,show.legend=FALSE)+facet_grid(metric~.,scales="free_y")+scale_color_manual(values=colors,drop=FALSE)+scale_x_discrete(drop=FALSE)+labs(title="HSC: all five predeclared seeds",x="Predeclared random seed (not biological replicates)",y="Frozen external metric",color=NULL,caption=paste0(success_caption,"\nSame ",n_eval," evaluated cells per method/seed; NMI uses max-entropy normalization. No best-seed selection."))
 save_plot(p,"01-all-seed-ARI-NMI",9,7)
 # Fixed seed2358 only. Cluster IDs are sorted as identifiers; no label matching.
 ref_levels <- c("LTHSC","LMPP","MPP","CMP","MEP","GMP")
 for(method in methods) {
  key <- paste(method,2358L,sep=":");part <- partitions[[key]]
  if(is.null(part)) {
   writeLines(paste(method,"seed2358 failed; fixed-example heatmap not replaced by another seed."),file.path(out,paste0("02-",method,"-seed2358-UNAVAILABLE.txt")))
   next
  }
  pred <- as.character(part$cluster[match(eval_ids,part$cell_id)])
  truth <- reference$label[match(eval_ids,reference$cell_id)]
  clusters <- unique(pred);numeric_clusters <- suppressWarnings(as.numeric(clusters))
  clusters <- if(all(is.finite(numeric_clusters)))clusters[order(numeric_clusters,clusters)] else sort(clusters)
  contingency <- as.data.frame(table(predicted=factor(pred,levels=clusters),reference=factor(truth,levels=ref_levels)),stringsAsFactors=FALSE)
  contingency$predicted <- factor(contingency$predicted,levels=clusters)
  contingency$reference <- factor(contingency$reference,levels=ref_levels)
  stopifnot(sum(contingency$Freq)==n_eval)
  contingency$share_within_reference <- contingency$Freq/as.numeric(table(factor(truth,levels=ref_levels)))[match(contingency$reference,ref_levels)]
  write_tsv(contingency,file.path(out,paste0("02-",method,"-seed2358-contingency.tsv")))
  for(normalized in c(FALSE,TRUE)) {
   contingency$fill <- if(normalized)contingency$share_within_reference else contingency$Freq
   contingency$tile_label <- if(normalized)ifelse(contingency$Freq>0,sprintf("%.1f%%",100*contingency$share_within_reference),"") else ifelse(contingency$Freq>0,as.character(contingency$Freq),"")
   p <- ggplot(contingency,aes(reference,predicted,fill=fill))+geom_tile(color="white",linewidth=.3)+geom_text(aes(label=tile_label),size=2.7,color="#111111")+scale_fill_gradient(low="#F7FBFF",high="#6BAED6",name=if(normalized)"Within-reference\nshare" else "Cells")+labs(title=paste0(unname(method_labels[method]),": fixed first seed 2358"),subtitle=if(normalized)"Each reference column sums to 100%" else "Counts on the frozen evaluation intersection",x="Published broad immunophenotype reference",y="Predicted cluster ID",caption=paste0("Example fixed before results; not selected by score. n = ",n_eval,".\n",n_unknown," QC-retained cells without a reference remain clustered and are excluded here."))+theme(panel.grid=element_blank())
   save_plot(p,paste0("02-",method,"-seed2358-",if(normalized)"reference-share" else "counts"),9,max(5,3+.26*length(clusters)))
  }
 }
 # Technical QC histograms use locked metrics and cutoffs only, never labels.
 qc_long <- rbind(data.frame(cell_id=qc$cell_id,metric="log2 endogenous read count",value=ifelse(qc$endogenous_total>0,log2(pmax(qc$endogenous_total,1)),NA_real_),decision=ifelse(qc$retained,"Retained","Excluded")),data.frame(cell_id=qc$cell_id,metric="log2 detected endogenous genes",value=ifelse(qc$endogenous_detected_genes>0,log2(pmax(qc$endogenous_detected_genes,1)),NA_real_),decision=ifelse(qc$retained,"Retained","Excluded")),data.frame(cell_id=qc$cell_id,metric="ERCC percent",value=qc$ERCC_percent,decision=ifelse(qc$retained,"Retained","Excluded")))
 cutoffs <- data.frame(metric=c("log2 endogenous read count","log2 detected endogenous genes","ERCC percent"),cutoff=c(thresholds$log2_endogenous_total_lower,thresholds$log2_detected_lower,thresholds$ERCC_percent_upper))
 write_tsv(qc_long,file.path(out,"QC-plotted-values.tsv"))
 write_tsv(cutoffs,file.path(out,"QC-frozen-cutoffs.tsv"))
 p <- ggplot(qc_long,aes(value,fill=decision))+geom_histogram(bins=50,position="identity",alpha=.65,na.rm=TRUE)+geom_vline(data=cutoffs,aes(xintercept=cutoff),inherit.aes=FALSE,linetype=2,color="#111111")+facet_wrap(~metric,scales="free_x",ncol=3)+scale_fill_manual(values=c(Retained="#315A86",Excluded="#C5C5C5"))+labs(title="Shared technical QC, frozen before clustering",x="Locked QC metric",y="Cells",fill=NULL,caption="Dashed lines: pooled one-sided median +/- 3 standardized MAD cutoffs.\nNo reference label, FACS/DC value, or mitochondrial-ID guess was used for QC; these are not claimed author QC rules.")
 save_plot(p,"03-shared-QC",12,4.8)
 cohort <- data.frame(stage=factor(c("Candidate input","QC retained","Frozen evaluation"),levels=c("Candidate input","QC retained","Frozen evaluation")),cells=c(nrow(qc),n_total,n_eval))
 write_tsv(data.frame(candidate_cells=nrow(qc),QC_retained=n_total,QC_excluded=nrow(qc)-n_total,evaluation_cells=n_eval,QC_retained_unassigned=n_unknown,eligible_genes=prep$eligible_genes,shared_HVG=length(hvg_ids)),file.path(out,"cohort-summary.tsv"))
 p <- ggplot(cohort,aes(stage,cells))+geom_col(fill="#315A86",width=.6)+geom_text(aes(label=cells),vjust=-.5,size=4)+scale_y_continuous(expand=expansion(mult=c(0,.12)))+labs(title="One shared cohort and feature set",x=NULL,y="Cells",caption=paste0(nrow(qc)-n_total," cells excluded by label-blind QC. ",n_unknown," retained cells have no valid broad reference and remain in clustering.\n",prep$eligible_genes," eligible endogenous genes; ",length(hvg_ids)," HVGs shared by both methods and all seeds.\nA retained count of 1656 does not establish identity with the original-paper 1656-cell cohort."))
 save_plot(p,"04-common-cohort",9,5.4)
 resource_long <- rbind(transform(results,resource="Core elapsed time (seconds)",value=core_elapsed_seconds),transform(results,resource="Core sampled peak RSS (GiB)",value=sampled_peak_rss_GiB))
 p <- ggplot(resource_long,aes(seed_label,value,color=method_label,group=method_label))+geom_point(position=position_dodge(width=.36),size=2.8,na.rm=TRUE)+geom_text(data=resource_long[!resource_long$success,,drop=FALSE],aes(y=0,label="FAILED"),position=position_dodge(width=.36),vjust=-.6,size=2.7,show.legend=FALSE)+facet_grid(resource~.,scales="free_y")+scale_y_continuous(limits=c(0,NA),expand=expansion(mult=c(.02,.1)))+scale_color_manual(values=colors,drop=FALSE)+scale_x_discrete(drop=FALSE)+labs(title="Resource measurements with explicit scope",x="Predeclared random seed",y=NULL,color=NULL,caption=paste0(success_caption,"\nCore: CA + splitmerge versus PCA + SNN + Louvain; common preprocessing, loading, serialization and ranking excluded.\nRSS sampled every 50 ms can miss spikes. Process VmHWM includes startup/loading and is separately tabulated; no RAM-superiority claim."))
 save_plot(p,"05-core-resources",10,7)
 captions <- c("# HSC正式输出的图表说明（待独立结果复验）","",paste0("来源：正式根 `",run_root,"`；独立准入绑定源码 `",admission$source_commit,"`。脚本只读分区/指标/锁表，不读取表达RDS，不新增降维、聚类或ARI/NMI计算。"),"",paste0("1. **01-all-seed-ARI-NMI**：全部五个预设种子，两方法均用同一",n_eval,"细胞评价交集。失败仍占分母5，无分数补值；种子不是生物学重复。NMI为MI/max(Hpred,Href)。"),"2. **02-*-seed2358-counts / reference-share**：预先固定首种子2358示例，展示原始计数和每个参考类别内的分区比例。不按得分选seed，不将预测簇重命名为参考类别。若2358失败，不改用其他seed。参考是发布的broad免疫表型，不能视为功能谱系真值。",paste0("3. **03-shared-QC**：锁定技术指标及单侧3MAD阈值。保留",n_total,"、筛除",nrow(qc)-n_total,"；未按标签删细胞。"),paste0("4. **04-common-cohort**：共同队列及一次HVG选择；",n_unknown,"无参考但QC合格细胞仍参与聚类，仅排除标签指标。数量恰为1656不能证明恢复原文队列。"),"5. **05-core-resources**：预设核心阶段耗时与50ms采样RSS，资源范围见resource-scopes.tsv。不同方法的核心步骤不同；加载/序列化/额外排名不混入核心。VmHWM包含启动及读入，单列，不据不匹配范围宣称内存优势。","","研究范围：单研究描述性比较；未知donor/Rep，不作生物学重复或跨供者推断。参考为发布免疫表型。C04新增性仅按独立设计审查限定范围接受，S1全文来源限制保留，不宣称绝对未被原论文使用。", "", "全部PNG为300dpi，PDF保留矢量元素。图表不代表独立结果审查已通过，后续科学结论须由新的独立Sol High签署。")
 writeLines(captions,file.path(out,"逐图说明.md"))
 write_json(list(run_root=run_root,fixed_example_seed=2358L,declared_seeds=seeds,source_commit=admission$source_commit,inputs=unname(inputs),shared_input_RDS_read=FALSE,new_reduction_or_clustering=FALSE,ARI_NMI_recomputed=FALSE),file.path(out,"presentation-inputs.json"))
 status$status <- "PRESENTATION_COMPLETE_PENDING_INDEPENDENT_RESULT_REVIEW"
},error=function(e){status$status<<-"FAILED";status$error<<-conditionMessage(e);message(conditionMessage(e))},finally={
 status$script_sha256 <- sha(sub("^--file=","",grep("^--file=",commandArgs(),value=TRUE)[[1]]))
 write_json(status,file.path(out,"presentation-status.json"))
 writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
})
if(status$status=="FAILED")quit(status=1)
