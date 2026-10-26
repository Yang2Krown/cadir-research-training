# Metadata identities only. Never accepts a counts file or imputes IDs/NA.
id_issue <- function(message, details=list()) {
    stop(structure(list(message=message,call=NULL,details=details),
        class=c("identity_error","error","condition")))
}
check_ids <- function(ids,n,source) {
    if(is.null(ids)) id_issue(paste(source,"has no explicit IDs"),list(source=source))
    if(length(ids)!=n || anyNA(ids) || any(!nzchar(trimws(ids))) || anyDuplicated(ids))
        id_issue(paste(source,"has invalid IDs"),list(source=source,expected_rows=n,
            id_count=length(ids),missing_rows=which(is.na(ids)),
            blank_rows=which(!is.na(ids)&!nzchar(trimws(ids))),
            duplicate_ids=unique(ids[duplicated(ids)])))
    invisible(TRUE)
}
match_ids <- function(target,source,name) {
    if(!setequal(target,source)) id_issue(paste(name,"ID set differs"),
        list(source=name,missing_from_source=setdiff(target,source),extra_in_source=setdiff(source,target)))
    match(target,source)
}
extract_metadata_identity <- function(metadata) {
    if(!methods::is(metadata,"DataFrame")) id_issue("Expected an S4 DataFrame")
    required <- c("cell.type","diffusion","FACS")
    if(!all(required %in% names(metadata))) id_issue("Required nested fields absent",
        list(missing_fields=setdiff(required,names(metadata))))
    before <- digest::digest(metadata,algo="sha256")
    # Legacy serialized DataFrame can carry attributes absent from the current
    # virtual class's slotNames(). Inspect the original attribute, not an
    # updated object's accessor or a guessed sequence of row numbers.
    top <- attr(metadata,"rownames",exact=TRUE)
    canonical <- rownames(metadata[["cell.type"]])
    check_ids(canonical,nrow(metadata),"cell.type rownames")
    alignment <- list(); aligned <- list(); info <- list()
    if(!is.null(top)) {
        check_ids(top,nrow(metadata),"raw top-level rownames")
        ix <- match_ids(canonical,top,"raw top-level rownames")
        alignment$top_level <- data.frame(field="top_level",cell_id=canonical,
            canonical_row=seq_along(canonical),source_row=ix)
    }
    for(name in required) {
        value <- metadata[[name]]
        if(!(is.matrix(value)||methods::is(value,"Matrix"))||length(dim(value))!=2L)
            id_issue(paste(name,"is not a nested matrix"))
        ids <- rownames(value);check_ids(ids,nrow(value),paste(name,"rownames"))
        ix <- match_ids(canonical,ids,name)
        view <- value[ix,,drop=FALSE]
        stopifnot(identical(rownames(view),canonical))
        aligned[[name]] <- view
        alignment[[name]] <- data.frame(field=name,cell_id=canonical,
            canonical_row=seq_along(canonical),source_row=ix)
        missing <- is.na(value)
        info[[name]] <- list(class=class(value),dimensions=dim(value),columns=colnames(value),
            original_order_identical=identical(ids,canonical),reordered_rows=sum(ix!=seq_along(ix)),
            missing_entries=sum(missing),
            missing_by_column=as.list(stats::setNames(colSums(missing),colnames(value))),
            all_missing_rows=sum(rowSums(missing)==ncol(value)))
    }
    ct <- as.matrix(aligned$cell.type)
    if(anyNA(ct)||!all(ct %in% c(0,1))) id_issue("cell.type must contain only 0/1 memberships")
    broad <- c("LTHSC_broad","LMPP_broad","MPP_broad","CMP_broad","MEP_broad","GMP_broad")
    if(!all(broad %in% colnames(ct))) id_issue("Broad membership columns absent")
    membership <- rowSums(ct[,broad,drop=FALSE])
    if(any(membership>1)) id_issue("Conflicting broad memberships",list(cell_ids=canonical[membership>1]))
    labels <- rep(NA_character_,length(canonical))
    for(column in broad) labels[ct[,column]==1] <- sub("_broad$","",column)
    unchanged <- identical(before,digest::digest(metadata,algo="sha256"));stopifnot(unchanged)
    list(ids=canonical,aligned=aligned,alignment=do.call(rbind,alignment),
        memberships=data.frame(cell_id=canonical,ct,check.names=FALSE),
        candidate=data.frame(cell_id=canonical,candidate_label=labels,status="DRAFT_NOT_FROZEN"),
        summary=list(identity_source="explicit nested cell.type rownames",
            raw_top_level_rownames_attribute_present="rownames" %in% names(attributes(metadata)),
            raw_top_level_rownames_is_null=is.null(top),raw_top_level_rownames=top,rows=nrow(metadata),
            fields=info,input_object_unchanged=unchanged,NA_imputed=FALSE,positional_ID_fill=FALSE,
            broad_assigned=sum(!is.na(labels)),broad_unassigned=sum(is.na(labels)),
            broad_conflicts=sum(membership>1),all_memberships_zero=sum(rowSums(ct)==0)))
}
write_metadata_audit <- function(result,out) {
    jsonlite::write_json(result$summary,file.path(out,"metadata_identity.json"),
        pretty=TRUE,auto_unbox=TRUE,na="null",null="null",digits=NA)
    for(item in c("alignment","memberships","candidate"))
        write.table(result[[item]],file.path(out,paste0("metadata_",item,".tsv")),
            sep="\t",quote=FALSE,row.names=FALSE,na="NA")
    flags <- data.frame(cell_id=result$ids,
        diffusion_missing=rowSums(is.na(result$aligned$diffusion))>0,
        FACS_missing=rowSums(is.na(result$aligned$FACS))>0,
        Projected=as.numeric(result$aligned$cell.type[,"Projected"]))
    write.table(flags,file.path(out,"metadata_flags.tsv"),sep="\t",quote=FALSE,row.names=FALSE)
}
