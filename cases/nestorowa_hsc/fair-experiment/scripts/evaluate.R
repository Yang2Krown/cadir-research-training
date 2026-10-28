# Called only after independently admitted formal method computation.
evaluate_partitions <- function(pred,reference,evaluation_ids,out) {
 stopifnot(!anyNA(names(pred)),!anyDuplicated(names(pred)),all(evaluation_ids%in%names(pred)),all(evaluation_ids%in%reference$cell_id))
 ref <- reference$label[match(evaluation_ids,reference$cell_id)];p <- as.character(pred[evaluation_ids])
 stopifnot(!anyNA(ref),!anyNA(p),all(nzchar(ref)),all(nzchar(p)))
 t <- table(predicted=p,reference=ref)
 write_tsv(as.data.frame(t),file.path(out,"evaluation-contingency.tsv"))
 result <- list(n_total=length(pred),n_evaluated=length(ref),n_excluded=length(pred)-length(ref),inferred_clusters=length(unique(as.character(pred))),status="SKIPPED_INSUFFICIENT_REFERENCE",definition="ARI combinatorial; NMI=MI/max(Hpred,Href), natural logs")
 if(length(ref)>=2&&length(unique(ref))>=2) {
  ch <- function(z) z*(z-1)/2;n <- sum(t);A <- sum(ch(rowSums(t)));B <- sum(ch(colSums(t)));observed <- sum(ch(t));expected <- A*B/ch(n);denom <- (A+B)/2-expected
  if(abs(denom)<.Machine$double.eps*max(1,A,B)) {ari <- if(observed==A&&observed==B) 1 else 0;result$ARI_degenerate_denominator <- TRUE} else ari <- (observed-expected)/denom
  joint <- t/n;pa <- rowSums(joint);pb <- colSums(joint);ind <- outer(pa,pb);nz <- joint>0
  mi <- sum(joint[nz]*log(joint[nz]/ind[nz]));ha <- -sum(pa[pa>0]*log(pa[pa>0]));hb <- -sum(pb[pb>0]*log(pb[pb>0]))
  result$ARI <- ari;result$NMI_max_entropy <- if(max(ha,hb)==0) 1 else mi/max(ha,hb)
  result$MI <- mi;result$H_predicted <- ha;result$H_reference <- hb;result$status <- "COMPUTED_FROZEN_EVALUATION_INTERSECTION"
 }
 write_json(result,file.path(out,"metrics.json"));result
}
