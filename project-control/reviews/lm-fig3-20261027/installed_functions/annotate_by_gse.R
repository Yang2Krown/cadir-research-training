list(formals = as.pairlist(alist(obj = , gse_res = , alpha = 0.05, cost = c("logpval", 
    "pval", "NES"))), body = {
    stopifnot(methods::is(obj, "cadir"))
    if (length(cost) > 1) {
        cost <- cost[1]
    }
    if (!cost %in% c("pval", "logpval", "NES")) {
        rlang::abort("Please choose a valid 'cost'!")
    }
    dict <- obj@dict
    ccs <- obj@cell_clusters
    ccs_nm <- names(ccs)
    unccs <- levels(ccs)
    gcs <- obj@gene_clusters
    gcs_nm <- names(gcs)
    ungcs <- levels(gcs)
    allcs <- unique(c(unccs, ungcs))
    ccs <- as.character(ccs)
    unccs <- as.character(unccs)
    gcs <- as.character(gcs)
    ungcs <- as.character(ungcs)
    allcs <- as.character(allcs)
    dirs <- obj@directions
    stopifnot(nrow(dirs) == length(allcs))
    nclust <- length(gse_res)
    gse_res <- lapply(gse_res, function(x, nc = nclust) {
        subs <- min(nrow(x), nc)
        x[seq_len(subs), ]
    })
    cluster_anno <- run_hungarian(gse_res, cost = cost)
    for (c in seq_len(length(allcs))) {
        noanno <- allcs[c]
        if (!allcs[c] %in% cluster_anno$cluster) {
            ct <- noanno
        }
        else {
            ct <- cluster_anno[cluster_anno$cluster == allcs[c], 
                "cell_type"]
            cost_val <- cluster_anno[cluster_anno$cluster == 
                allcs[c], "cost"]
            if (cost == "pval") {
                if (cost_val > alpha) 
                  ct <- noanno
            }
            else if (cost == "logpval") {
                if (cost_val < (-log10(alpha))) 
                  ct <- noanno
            }
            else if (cost == "NES") {
            }
            else {
                rlang::abort()
            }
        }
        if (allcs[c] %in% ungcs) {
            sel <- which(gcs == allcs[c])
            if (length(ct) == 0) {
                gcs[sel] <- noanno
            }
            else {
                gcs[sel] <- ct
            }
        }
        if (allcs[c] %in% unccs) {
            sel <- which(ccs == allcs[c])
            if (length(ct) == 0) {
                ccs[sel] <- noanno
            }
            else {
                ccs[sel] <- ct
            }
        }
        if (c <= nrow(dirs)) {
            if (length(ct) == 0) {
                rownames(dirs)[c] <- noanno
            }
            else {
                rownames(dirs)[c] <- ct
                dict_idx <- which(names(dict) == search_dict(dict, 
                  c))
                names(dict)[dict_idx] <- ct
                dict[[ct]] <- c
            }
        }
    }
    names(gcs) <- gcs_nm
    names(ccs) <- ccs_nm
    lvls <- rownames(dirs)
    obj@cell_clusters <- factor(ccs, levels = lvls)
    obj@gene_clusters <- factor(gcs, levels = lvls)
    obj@directions <- dirs
    obj@dict <- dict
    stopifnot(methods::validObject(obj))
    return(obj)
})
