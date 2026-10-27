# Independent stage-one scientific oracle. NO CA/PCA, clustering or ARI/NMI.
args <- commandArgs(TRUE)
root <- args[[1]]; out <- args[[2]]
stopifnot(dir.exists(out), !file.exists(file.path(out,"independent-result.json")))
for(p in c("Matrix","S4Vectors","SingleCellExperiment","scran","jsonlite","digest")) suppressPackageStartupMessages(library(p,character.only=TRUE))
base <- file.path(root,"cases/nestorowa_hsc/fair-experiment")
prior <- "/workspace/hsc-fair-experiment-data-20261026/stage1/attempt-01"
raw <- "/workspace/nestorowa-metadata-preparation/reacquired-20261026"
checks <- list(); stage <- "start"
check <- function(name, predicate, detail="") {
 checks[[length(checks)+1L]] <<- data.frame(check=name,pass=isTRUE(predicate),detail=as.character(detail))
 if(!isTRUE(predicate))stop(paste("Independent check failed:",name))
}
same_numeric <- function(x,y,tol=1e-11) isTRUE(all.equal(as.numeric(x),as.numeric(y),tolerance=tol,check.attributes=FALSE))
tab <- function(name)read.delim(file.path(prior,paste0(name,".tsv")),stringsAsFactors=FALSE,na.strings="NA",check.names=FALSE)
ids <- function(name)readLines(file.path(prior,paste0(name,"-ids.txt")))
sha <- function(p)digest::digest(file=p,algo="sha256",serialize=FALSE)
result <- list(status="FAILED",forbidden_algorithms_called=FALSE)
tryCatch({
 stage <- "file_protection"
 lock <- jsonlite::read_json(file.path(base,"locks/data-input-lock.json"),simplifyVector=FALSE)
 for(e in lock$files) check(paste0("protected:",e$path),file.info(e$path)$size==e$bytes && sha(e$path)==e$sha256)
 protected_before <- vapply(lock$files,function(e)sha(e$path),character(1))
 stage <- "raw_label_blind_QC"
 x <- readRDS(file.path(raw,"counts.rds")); g <- rownames(x); c <- colnames(x)
 q <- tab("cell-qc"); gf <- tab("gene-filter")
 check("all_raw_gene_IDs",identical(g,ids("raw-gene")))
 check("all_raw_cell_IDs",identical(c,ids("raw-cell"))&&identical(c,q$cell_id))
 ercc <- grepl("^ERCC-[0-9]+",g); stat <- grepl("^__",g); endo <- !(ercc|stat)
 lib <- colSums(x[endo,,drop=FALSE]); detected <- colSums(x[endo,,drop=FALSE]>0); spike <- colSums(x[ercc,,drop=FALSE])
 pct <- 100*spike/(lib+spike); pos <- lib>0&detected>0
 check("raw_QC_metrics",same_numeric(lib,q$endogenous_total)&&same_numeric(detected,q$endogenous_detected_genes)&&same_numeric(spike,q$ERCC_total)&&same_numeric(pct,q$ERCC_percent))
 lo <- function(z)median(z)-3*mad(z,constant=1.4826)
 hi <- function(z)median(z)+3*mad(z,constant=1.4826)
 th <- c(lo(log2(lib[pos])),lo(log2(detected[pos])),hi(pct[pos]))
 lowlib <- pos&log2(pmax(lib,1))<th[1]; lowdet <- pos&log2(pmax(detected,1))<th[2]; high <- pos&pct>th[3]
 keep <- pos&!lowlib&!lowdet&!high
 reason <- vapply(seq_along(c),function(i)paste(c(if(!pos[i])"zero_endogenous_library",if(lowlib[i])"low_endogenous_library",if(lowdet[i])"low_detected_genes",if(high[i])"high_ERCC_percent"),collapse=";"),character(1));reason[keep]<-"retained"
 check("all_QC_flags_and_exclusion_reasons",identical(as.logical(keep),q$retained)&&identical(as.logical(lowlib),q$low_library)&&identical(as.logical(lowdet),q$low_detected)&&identical(as.logical(high),q$high_ERCC)&&identical(unname(reason),q$reason))
 check("thresholds",same_numeric(th,unlist(jsonlite::read_json(file.path(prior,"qc-thresholds.json")))))
 check("final_cell_IDs",identical(c[keep],ids("final-cell")))
 after <- rowSums(x[,keep,drop=FALSE]>0); eligible <- endo&after>=3
 check("all_gene_filter_IDs_and_predicates",identical(g,gf$gene_id)&&identical(as.logical(eligible),gf$eligible)&&same_numeric(after,gf$detected_after_QC)&&identical(g[eligible],ids("eligible-gene")))
 expected_class<-ifelse(stat,"HTSeq",ifelse(ercc,"ERCC","endogenous"))
 expected_reason<-ifelse(stat,"HTSeq_statistics",ifelse(ercc,"ERCC_spike_in",ifelse(eligible,"eligible_endogenous","detected_in_fewer_than_3_QC_cells")))
 check("gene_classes_and_reasons",identical(unname(expected_class),gf$feature_class)&&identical(unname(expected_reason),gf$reason))
 stage <- "raw_to_saved_all_eligible_matrix_and_normalization"
 sce <- readRDS(file.path(prior,"eligible-normalized-sce.rds")); sf <- lib[keep]/mean(lib[keep]); sftab <- tab("size-factors")
 check("SCE_IDs_and_size_factor_scope",identical(colnames(sce),c[keep])&&identical(rownames(sce),g[eligible])&&identical(sftab$cell_id,c[keep])&&same_numeric(sf,sftab$size_factor,1e-13)&&same_numeric(sf,sizeFactors(sce),1e-13))
 ce <- 0; ne <- 0; eg <- which(eligible)
 for(i in seq(1,length(eg),by=256)) {
  j <- i:min(i+255,length(eg)); original <- as.matrix(x[eg[j],keep,drop=FALSE])
  ce <- max(ce,max(abs(original-as.matrix(assay(sce,"counts")[j,,drop=FALSE]))))
  expected <- log2(sweep(original,2,sf,"/")+1)
  ne <- max(ne,max(abs(expected-as.matrix(assay(sce,"logcounts")[j,,drop=FALSE]))))
 }
 check("all_eligible_counts_exact_from_raw",ce==0)
 check("all_eligible_logcounts_formula",ne<1e-12,paste("max_abs_error",format(ne,digits=17)))
 rm(x);gc()
 stage <- "independent_HVG_recomputation"
 # Refit biological variance from the raw-verified logcounts; not from old PASS.
 RNGkind("Mersenne-Twister","Inversion","Rejection");set.seed(20261026)
 ownvar <- scran::modelGeneVar(sce,assay.type="logcounts",BPPARAM=BiocParallel::SerialParam())
 savedvar <- readRDS(file.path(prior,"gene-variance.rds"))
 check("recomputed_all_gene_variance_columns",identical(rownames(ownvar),rownames(savedvar))&&all(vapply(colnames(ownvar),function(n)same_numeric(ownvar[[n]],savedvar[[n]],1e-11),logical(1))))
 hvg <- rownames(ownvar)[head(order(ownvar$bio,decreasing=TRUE),6000)]
 check("independent_6000_HVG_exact_order",identical(hvg,ids("hvg-gene"))&&identical(hvg,scran::getTopHVGs(ownvar,n=6000,var.threshold=NULL))&&identical(gf$HVG,g%in%hvg))
 shared <- readRDS(file.path(prior,"shared-hvg-sce.rds"))
 check("shared_input_all_IDs_and_values",identical(rownames(shared),hvg)&&identical(colnames(shared),c[keep])&&identical(assay(shared,"logcounts"),assay(sce[hvg,],"logcounts"))&&identical(assay(shared,"counts"),assay(sce[hvg,],"counts")))
 check("positive_HVG_rows_columns",all(rowSums(assay(shared,"logcounts"))>0)&&all(colSums(assay(shared,"logcounts"))>0))
 stage <- "independent_broad_labels_only_after_QC"
 meta <- readRDS(file.path(raw,"coldata.rds")); ct <- meta[["cell.type"]]
 bc <- paste0(c("LTHSC","LMPP","MPP","CMP","MEP","GMP"),"_broad")
 check("explicit_metadata_ID_match",!anyDuplicated(rownames(ct))&&setequal(rownames(ct),c))
 m <- as.matrix(ct[match(c,rownames(ct)),bc,drop=FALSE]);count <- rowSums(m)
 check("binary_exclusive_broad_memberships",!anyNA(m)&&all(m%in%c(0,1))&&all(count<=1))
 lab <- rep(NA_character_,length(c)); has <- count==1;lab[has]<-sub("_broad$","",bc[max.col(m[has,,drop=FALSE],ties.method="first")])
 ref <- tab("frozen-reference");members <- tab("frozen-broad-memberships");evaluation <- keep&!is.na(lab)
 check("every_broad_membership_frozen",identical(members$cell_id,c)&&same_numeric(as.matrix(members[,bc]),m))
 check("every_reference_label_and_reason",identical(ref$cell_id,c)&&identical(ref$label,lab)&&identical(ref$label_reason,ifelse(is.na(lab),"no_broad_membership","unique_published_broad_membership")))
 check("evaluation_intersection_all_IDs",identical(ref$QC_retained,as.logical(keep))&&identical(ref$evaluated,as.logical(evaluation))&&identical(ids("evaluation-cell"),c[evaluation]))
 check("unassigned_retained_in_shared_input",all(c[keep&is.na(lab)]%in%colnames(shared)))
 counts<-table(factor(lab[keep],levels=sub("_broad$","",bc)))
 result$counts<-list(raw=length(c),retained=sum(keep),excluded=sum(!keep),eligible=sum(eligible),HVG=length(hvg),evaluated=sum(evaluation),retained_unassigned=sum(keep&is.na(lab)),reference_class_counts=as.list(setNames(as.integer(counts),names(counts))))
 result$thresholds <- as.list(setNames(th,c("log2_library_lower","log2_detected_lower","ERCC_percent_upper")))
 result$normalization_max_abs_error <- ne
 stage <- "environment_and_interface_inspection"
 source(file.path(base,"scripts/common.R"));load_packages();assert_environment(readRDS(lock$environment_signature_path))
 check("frozen_runtime_function_signature",TRUE)
 probes <- list(assign_genes=get("assign_genes",asNamespace("CAdir")),biocsingular_runPCA=get("runPCA",asNamespace("BiocSingular")),get_mat=get(".get_mat_for_reddim",asNamespace("scater")))
 for(n in names(probes))writeLines(capture.output(dput(probes[[n]])),file.path(out,paste0("interface-",n,".txt")))
 stage <- "R_entry_admission_rejections"
 # Both entry points must stop at the false template, before any data/algorithm.
 for(entry in c("formal_run.R","rank_diagnostics.R")) {
  logfile <- file.path(out,paste0(entry,"-false-template.log"))
  rc <- system2("Rscript",c(shQuote(file.path(base,"scripts",entry)),shQuote(file.path(base,"scripts/common.R")),shQuote(file.path(base,"design/admission-template.json")),shQuote(file.path(base,"locks/source-manifest.json")),shQuote(file.path(base,"locks/data-input-lock.json")),shQuote(file.path(base,"design/scientific-config.json"))),stdout=logfile,stderr=logfile)
  text <- readLines(logfile)
  check(paste0("false_template_rejected_before_algorithm:",entry),rc!=0&&any(grepl("isTRUE(gate$formal_execution_permitted)",text,fixed=TRUE)))
 }
 stage <- "final_file_protection"
 check("all_protected_files_unchanged",identical(protected_before,vapply(lock$files,function(e)sha(e$path),character(1))))
 result$status <- "PASS_STAGE1_SCIENTIFIC_ORACLE_NO_ALGORITHMS"
},error=function(e){result$error<<-conditionMessage(e)})
result$last_stage<-stage;result$reviewer_agent_id<-"/root/hsc_design_review"
result$script_sha256<-sha("/workspace/hsc-design-independent-review/reviews/hsc-design-20261026/verify_stage1.R")
write.table(do.call(rbind,checks),file.path(out,"independent-checks.tsv"),sep="\t",row.names=FALSE,quote=TRUE)
jsonlite::write_json(result,file.path(out,"independent-result.json"),pretty=TRUE,auto_unbox=TRUE,digits=NA)
writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
print(result)
if(result$status!="PASS_STAGE1_SCIENTIFIC_ORACLE_NO_ALGORITHMS")quit(status=1)
