args <- commandArgs(trailingOnly=TRUE)
suppressPackageStartupMessages({library(CAdir);library(APL)})
baseline <- readRDS(args[[1]]); reviewed <- readRDS(args[[2]])
stopifnot(identical(rownames(baseline@prin_coords_rows), rownames(reviewed@prin_coords_rows)),
          identical(rownames(baseline@prin_coords_cols), rownames(reviewed@prin_coords_cols)))
a <- baseline@prin_coords_cols; b <- reviewed@prin_coords_cols
signs <- sign(colSums(a*b)); signs[signs == 0] <- 1
per_axis <- data.frame(axis=seq_len(ncol(a)), sign=signs,
   raw_max_error=apply(abs(a-b),2,max),
   aligned_cell_max_error=apply(abs(sweep(a,2,signs,"*")-b),2,max),
   aligned_gene_max_error=apply(abs(sweep(baseline@prin_coords_rows,2,signs,"*")-reviewed@prin_coords_rows),2,max),
   cell_correlation=vapply(seq_len(ncol(a)),function(i) cor(a[,i],b[,i]),numeric(1)))
sv <- svd(crossprod(a,b)); Q <- sv$u %*% t(sv$v)
slots <- lapply(methods::slotNames(baseline),function(n) {
  x <- methods::slot(baseline,n); y <- methods::slot(reviewed,n)
  list(slot=n, class=class(x), dimensions=dim(x), length=length(x), identical=identical(x,y))
})
result <- list(baseline_path=args[[1]], reviewed_path=args[[2]],
  gene_ids_order_identical=TRUE,cell_ids_order_identical=TRUE,
  dimensions=dim(a), singular_value_max_error=max(abs(baseline@D-reviewed@D)),
  sign_vector=signs, flipped_axes=which(signs == -1),
  max_cell_error_after_sign_alignment=max(per_axis$aligned_cell_max_error),
  max_gene_error_after_sign_alignment=max(per_axis$aligned_gene_max_error),
  maximum_rotation_off_diagonal=max(abs(Q-diag(diag(Q)))),
  maximum_rotation_difference_from_sign_matrix=max(abs(Q-diag(signs))),
  rotation_cell_max_error=max(abs(a%*%Q-b)), slot_comparison=slots)
jsonlite::write_json(result,args[[3]],pretty=TRUE,auto_unbox=TRUE,digits=NA)
write.table(per_axis,args[[4]],sep="\t",row.names=FALSE,quote=FALSE)
print(result[1:12])
