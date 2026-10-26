list(formals = as.pairlist(alist(cadir = , caobj = , cluster_only = TRUE)), 
    body = {
        alpha <- cadir@parameters$alpha_genes
        gcs_lvls <- levels(cadir@gene_clusters)
        all_ranks <- list()
        for (c in gcs_lvls) {
            ngenes <- sum(cadir@gene_clusters == c)
            if (ngenes < 1) {
                all_ranks[[c]] <- NA
                if (isTRUE(cluster_only)) 
                  next
            }
            if (is.null(alpha)) {
                alpha <- get_apl_cutoff(caobj = caobj, method = "random", 
                  group = which(cadir@cell_clusters == c), quant = 0.99, 
                  apl_cutoff_reps = 100, axis = "rows")
                cadir@parameters$alpha_genes <- alpha
            }
            direction <- cadir@directions[c, ]
            model <- apl_model(coords = caobj@prin_coords_cols, 
                direction = direction, group = which(cadir@cell_clusters == 
                  c))
            gene_coords <- model(caobj@prin_coords_rows)
            if (isTRUE(cluster_only)) {
                cluster_genes <- names(cadir@gene_clusters)[which(cadir@gene_clusters == 
                  c)]
                gene_coords <- gene_coords[which(rownames(gene_coords) %in% 
                  cluster_genes), , drop = FALSE]
            }
            score <- gene_coords[, 1] - (gene_coords[, 2] * alpha)
            ranking <- data.frame(Rowname = rownames(gene_coords), 
                Score = score, Row_num = seq_len(nrow(gene_coords)), 
                Cluster = c)
            ranking <- ranking[order(ranking$Score, decreasing = TRUE), 
                ]
            ranking$Rank <- seq_len(nrow(ranking))
            all_ranks[[c]] <- ranking
        }
        cadir@gene_ranks <- all_ranks
        return(cadir)
    })
