# Independent pure ID/export contract verification. No algorithm packages loaded.
a <- commandArgs(TRUE);root <- a[[1]];out <- a[[2]]
stopifnot(dir.exists(out),!file.exists(file.path(out,"repair-result.json")))
base <- file.path(root,"cases/nestorowa_hsc/fair-experiment")
source(file.path(base,"scripts/gene_partition.R"))
write_tsv <- function(x,p)write.table(x,p,sep="\t",row.names=FALSE,quote=TRUE,na="NA")
write_json <- function(x,p)jsonlite::write_json(x,p,pretty=TRUE,auto_unbox=TRUE,digits=NA)
checks <- list();check <- function(n,p){checks[[length(checks)+1L]]<<-data.frame(check=n,pass=isTRUE(p));if(!isTRUE(p))stop(n)}
result <- list(status="FAILED",forbidden_algorithms_called=FALSE)
tryCatch({
 # Actual frozen gene IDs, hand-authored assignments; no expression/CA is read.
 genes <- readLines("/workspace/hsc-fair-experiment-data-20261026/stage1/attempt-01/hvg-gene-ids.txt")
 check("frozen_6000_IDs",length(genes)==6000&&!anyDuplicated(genes))
 directions <- c("direction_A","direction_B")
 take <- c(6000,1,251,19)
 native <- factor(c("direction_B",NA,"direction_A","direction_B"),levels=directions)
 names(native)<-genes[take];before<-serialize(native,NULL)
 mapped <- map_gene_partition(native,genes,directions)
 # Oracle places hand-authored values at known row numbers, not match().
 expected_cluster <- rep(NA_character_,6000);expected_cluster[take]<-as.character(native)
 expected_present <- rep(FALSE,6000);expected_present[take]<-TRUE
 expected_assigned <- rep(FALSE,6000);expected_assigned[c(6000,251,19)]<-TRUE
 expected_reason <- rep("excluded_by_upstream_ca_sphere_qcutoff",6000)
 expected_reason[expected_assigned]<-"assigned_by_upstream";expected_reason[1]<-"retained_but_unassigned_by_upstream"
 check("all_6000_rows_in_frozen_order",identical(mapped$gene_id,genes))
 check("every_mapped_label_and_NA",identical(mapped$cluster,expected_cluster))
 check("every_membership_assignment_and_reason",identical(mapped$in_upstream_gene_subset,expected_present)&&identical(mapped$assigned,expected_assigned)&&identical(mapped$reason,expected_reason))
 check("original_upstream_factor_untouched",identical(before,serialize(native,NULL)))
 check("native_order_not_required",identical(map_gene_partition(native[c(4,2,1,3)],genes,directions),mapped))
 rejected <- function(n,x= native,g= genes,d= directions)check(n,inherits(try(map_gene_partition(x,g,d),silent=TRUE),"try-error"))
 bad<-native;names(bad)[2]<-names(bad)[1];rejected("reject_duplicate_native_ID",bad)
 bad<-native;names(bad)[2]<-"FOREIGN_ID";rejected("reject_foreign_native_ID",bad)
 bad<-native;names(bad)[2]<-NA_character_;rejected("reject_missing_native_ID",bad)
 bad<-native;names(bad)[2]<-" ";rejected("reject_blank_native_ID",bad)
 bad<-native;names(bad)<-NULL;rejected("reject_unnamed_assignment",bad)
 bad<-as.character(native);names(bad)<-names(native);bad[1]<-"FOREIGN_DIRECTION";rejected("reject_foreign_cluster",bad)
 bad[1]<-" ";rejected("reject_blank_cluster",bad)
 badgenes<-genes;badgenes[2]<-badgenes[1];rejected("reject_duplicate_universe_ID",g=badgenes)
 rejected("reject_duplicate_direction_ID",d=c(directions,directions[1]))
 check_export <- function(part,subdir,assigned,retained) {
  target<-file.path(out,subdir);dir.create(target)
  write_gene_partition(part,target,.8)
  # Pin types: all-NA character columns and zero-row tables otherwise become logical.
  cls<-c("character","character","logical","logical","character")
  full<-read.delim(file.path(target,"gene-partition.tsv"),stringsAsFactors=FALSE,na.strings="NA",colClasses=cls)
  ex<-read.delim(file.path(target,"gene-exclusions.tsv"),stringsAsFactors=FALSE,na.strings="NA",colClasses=cls)
  summary<-jsonlite::read_json(file.path(target,"gene-assignment-summary.json"),simplifyVector=TRUE)
  check(paste0(subdir,":full_IDs_labels_and_reasons"),identical(full$gene_id,genes)&&identical(full$cluster,part$cluster)&&identical(full$reason,part$reason))
  check(paste0(subdir,":exclusion_IDs_and_reasons"),identical(ex$gene_id,genes[!part$assigned])&&identical(ex$reason,part$reason[!part$assigned])&&identical(readLines(file.path(target,"unassigned-gene-ids.txt")),genes[!part$assigned]))
  check(paste0(subdir,":all_summary_denominators"),summary$input_genes==6000&&summary$upstream_retained_genes==retained&&summary$assigned_genes==assigned&&summary$unassigned_genes==6000-assigned&&summary$qcutoff==.8&&sum(unlist(summary$reason_counts))==6000)
 }
 check_export(mapped,"scrambled-subset",3,4)
 empty<-map_gene_partition(factor(character(),levels=directions),genes,directions)
 check("empty_subset_all_NA",nrow(empty)==6000&&all(!empty$assigned)&&all(is.na(empty$cluster)))
 check_export(empty,"empty-subset",0,0)
 allassigned<-setNames(factor(rep(directions[1],6000),levels=directions),genes)
 full<-map_gene_partition(allassigned,genes,directions)
 check_export(full,"full-assignment",6000,6000)
 check("helper_export_did_not_modify_native",identical(before,serialize(native,NULL)))
 # Parse every current R source without running its expressions.
 for(p in list.files(file.path(base,"scripts"),pattern="\\.R$",full.names=TRUE)) {parse(file=p);check(paste0("R_parse:",basename(p)),TRUE)}
 # Both actual entry points still reject the false template before input or helper.
 for(entry in c("formal_run.R","rank_diagnostics.R")) {
  logfile<-file.path(out,paste0(entry,"-false-template.log"))
  rc<-system2("Rscript",c(shQuote(file.path(base,"scripts",entry)),shQuote(file.path(base,"scripts/common.R")),shQuote(file.path(base,"design/admission-template.json")),shQuote(file.path(base,"locks/source-manifest.json")),shQuote(file.path(base,"locks/data-input-lock.json")),shQuote(file.path(base,"design/scientific-config.json"))),stdout=logfile,stderr=logfile)
  check(paste0("revised_entry_false_template:",entry),rc!=0&&any(grepl("isTRUE(gate$formal_execution_permitted)",readLines(logfile),fixed=TRUE)))
 }
 result$status<-"PASS_INDEPENDENT_GENE_SUBSET_REPAIR_NO_ALGORITHMS"
},error=function(e){result$error<<-conditionMessage(e)})
result$source_commit<-"6cc7b3da67c193da11a67c45a75167d6521438b0"
result$script_sha256<-digest::digest(file="/workspace/hsc-design-independent-review/reviews/hsc-design-20261026/verify_gene_subset_repair_v2.R",algo="sha256",serialize=FALSE)
write_tsv(do.call(rbind,checks),file.path(out,"repair-checks.tsv"));write_json(result,file.path(out,"repair-result.json"));print(result)
if(result$status!="PASS_INDEPENDENT_GENE_SUBSET_REPAIR_NO_ALGORITHMS")quit(status=1)
