list(formals = as.pairlist(alist(cadir = , caobj = , rm_redund = TRUE, show_cells = TRUE, show_genes = FALSE, highlight_cluster = FALSE, annotate_clusters = FALSE, org = "mm", keep_end = TRUE, inlet_side = 0.1, title_size = 10, show_axis = FALSE, n_wrap = Inf, layout = "tree", rotate = TRUE, show_apl = TRUE, annotate_leafs = FALSE)), 
    body = {
        base::stopifnot(`Set either \`show_cells\` or \`show_genes\` to TRUE.` = isTRUE(show_cells) || 
            isTRUE(show_genes))
        if (isTRUE(annotate_leafs) && isTRUE(show_apl)) {
            rlang::warn("annotate_leafs can only be used when `show_apl = FALSE. Turning param off.")
            annotate_leafs <- FALSE
        }
        if (isTRUE(show_axis)) {
            plot_theme <- theme_axis_only
        }
        else {
            plot_theme <- theme_blank
        }
        graph <- build_graph(cadir = cadir, rm_redund = rm_redund, 
            keep_end = keep_end)
        if (layout == "tree") {
            lgraph <- ggraph::create_layout(graph, layout = "tree")
        }
        else if (layout == "dendrogram") {
            lgraph <- ggraph::create_layout(graph, layout = "igraph", 
                algorithm = "sugiyama", )
        }
        lgraph$leaf <- (lgraph$y == min(lgraph$y))
        ggraph::set_graph_style(plot_margin = ggplot2::margin(0, 
            0, 0, 0))
        bg <- ggraph::ggraph(lgraph, layout = layout)
        if (layout == "tree") {
            bg <- bg + ggraph::geom_edge_link()
        }
        else if (layout == "dendrogram") {
            bg <- bg + ggraph::geom_edge_elbow(check_overlap = TRUE)
        }
        bg <- bg + ggraph::geom_node_point(alpha = 1)
        if (isTRUE(rotate)) {
            bg <- bg + ggplot2::coord_flip() + ggplot2::scale_y_reverse()
        }
        bg_coords <- get_x_y_values(bg)
        cls <- cadir@log$clusters
        dirs <- cadir@log$directions
        nodes <- lgraph$name
        lgraph$annotation <- NA
        old_iter_nm <- ""
        for (i in seq_len(length(nodes))) {
            node_nm <- nodes[i]
            name_elems <- base::strsplit(node_nm, "-", fixed = TRUE)[[1]]
            if (name_elems[1] == "root") {
                next
            }
            iter_nm <- name_elems[1]
            cluster <- name_elems[2]
            grp_idx <- base::which(cls[, iter_nm] == cluster)
            is_iter_dirs <- dirs$iter == iter_nm
            coord_column <- !colnames(dirs) %in% c("iter", "dirname")
            tmp_dirs <- dirs[is_iter_dirs, coord_column]
            rownames(tmp_dirs) <- dirs[is_iter_dirs, "dirname"]
            cluster_idx <- base::which(rownames(tmp_dirs) == 
                cluster)
            dir <- tmp_dirs[cluster_idx, ]
            if (iter_nm != old_iter_nm) {
                tmp_ccs <- x2f(cls[, iter_nm])
                names(tmp_ccs) <- rownames(caobj@prin_coords_cols)
                tmp_cadir <- methods::new("cadir", cell_clusters = tmp_ccs, 
                  directions = as.matrix(tmp_dirs))
                if (is.null(cadir@parameters$qcutoff)) {
                  cadir@parameters$qcutoff <- 0.8
                }
                tmp_cadir@gene_clusters <- assign_genes(caobj = caobj, 
                  cadir = tmp_cadir, qcutoff = cadir@parameters$qcutoff)
                if (isTRUE(annotate_clusters)) {
                  if (isTRUE(annotate_leafs) && isFALSE(lgraph$leaf[i])) {
                    next
                  }
                  tryCatch({
                    suppressWarnings({
                      tmp_cadir <- annotate_biclusters(obj = tmp_cadir, 
                        universe = rownames(caobj@std_coords_rows), 
                        org = org, alpha = 0.05, min_size = 10, 
                        max_size = 500, method = "goa", cost = "pval", 
                        filter_literature = FALSE)
                    })
                  }, error = function(e) {
                    rlang::warn("Could not annotate iteration.")
                  })
                }
                old_iter_nm <- iter_nm
            }
            if (isTRUE(annotate_clusters)) {
                lgraph$annotation[i] <- rownames(tmp_cadir@directions)[cluster_idx]
            }
            if (isTRUE(show_apl)) {
                cluster <- rownames(tmp_cadir@directions)[cluster_idx]
                rownames(dir) <- cluster
                p <- cluster_apl(caobj = caobj, cadir = tmp_cadir, 
                  direction = as.numeric(dir), group = grp_idx, 
                  cluster = cluster, show_cells = show_cells, 
                  show_genes = show_genes, highlight_cluster = highlight_cluster, 
                  show_lines = FALSE, point_size = 0.3)
                if (isTRUE(annotate_clusters)) {
                  cluster_title <- gsub(pattern = "_", replacement = " ", 
                    cluster)
                  p <- p + ggplot2::ggtitle(paste(strwrap(cluster_title, 
                    width = n_wrap), collapse = "\n")) + plot_theme(title = ggplot2::element_text(color = "black", 
                    size = title_size), text = ggplot2::element_text())
                }
                else {
                  p <- p + plot_theme()
                }
                lradj <- tbadj <- 0
                mid_length <- inlet_side/2
                if (bg_coords[i, 1] < mid_length) {
                  lradj <- mid_length - bg_coords[i, 1]
                }
                if ((bg_coords[i, 1] + mid_length) > 1) {
                  lradj <- 1 - (mid_length + bg_coords[i, 1])
                }
                if (bg_coords[i, 2] < mid_length) {
                  tbadj <- mid_length - bg_coords[i, 2]
                }
                if ((bg_coords[i, 2] + mid_length) > 1) {
                  tbadj <- 1 - (mid_length + bg_coords[i, 2])
                }
                bg <- bg + patchwork::inset_element(p, left = bg_coords[i, 
                  1] - mid_length + lradj, right = bg_coords[i, 
                  1] + mid_length + lradj, top = bg_coords[i, 
                  2] + mid_length + tbadj, bottom = bg_coords[i, 
                  2] - mid_length + tbadj, align_to = "panel")
            }
        }
        if (isTRUE(annotate_clusters) && isFALSE(show_apl)) {
            bg <- ggraph::ggraph(lgraph, layout = layout)
            if (layout == "tree") {
                bg <- bg + ggraph::geom_edge_link()
            }
            else if (layout == "dendrogram") {
                bg <- bg + ggraph::geom_edge_elbow(check_overlap = TRUE)
            }
            if (isTRUE(annotate_leafs)) {
                bg <- bg + ggraph::geom_node_text(aes(label = ifelse(leaf, 
                  annotation, NA)), size = title_size, repel = TRUE)
            }
            else {
                bg <- bg + ggraph::geom_node_text(aes(label = annotation), 
                  size = title_size, repel = TRUE)
            }
            bg <- bg + ggraph::geom_node_point(alpha = 1)
            if (isTRUE(rotate)) {
                bg <- bg + ggplot2::coord_flip() + ggplot2::scale_y_reverse()
            }
        }
        return(bg)
    })
