list(formals = as.pairlist(alist(caobj = , cadir = , cluster = , direction = cadir@directions[cluster, 
    ], group = which(cadir@cell_clusters == cluster), show_cells = TRUE, show_genes = FALSE, show_lines = FALSE, highlight_cluster = TRUE, label_genes = FALSE, point_size = 1.5, size_factor = 2, ntop = 10, interactive = FALSE, show_cutoff = FALSE)), 
    body = {
        stopifnot(methods::is(caobj, "cacomp"))
        stopifnot(methods::is(cadir, "cadir"))
        if (is.null(cluster) && isTRUE(highlight_cluster)) {
            rlang::warn(paste0("Turning `highlight_cluster off,", 
                "because no `cluster` was specified"))
            highlight_cluster <- FALSE
        }
        all_cls <- unique(c(levels(cadir@cell_clusters), levels(cadir@gene_clusters)))
        if (!is.null(cluster)) {
            cluster <- as.character(cluster)
            if (!cluster %in% all_cls) {
                cluster <- NULL
                rlang::warn(paste0("`cluster` does not correspond to a cluster in cadir.", 
                  " Setting to NULL."))
            }
        }
        ndim <- ncol(cadir@directions)
        dir_is_vec <- is.numeric(direction)
        has_len <- length(direction) == ndim
        has_grp <- !(length(group) == 0 || is.null(group))
        if (isTRUE(has_grp) && is.null(cluster)) {
            if (isFALSE(dir_is_vec) || isFALSE(has_len)) {
                direction <- colMeans(caobj@prin_coords_cols[group, 
                  ])
                dir_is_vec <- is.numeric(direction)
                has_len <- length(direction) == ndim
            }
        }
        else if (isFALSE(has_grp)) {
            rlang::abort("`group` has length 0.")
        }
        if (!dir_is_vec || !has_len) {
            rlang::abort("A valid direction is needed!")
        }
        if (isTRUE(label_genes) && length(cadir@gene_ranks) == 
            0) {
            cadir <- rank_genes(cadir = cadir, caobj = caobj)
        }
        ang <- .get_plot_angle(directions = cadir@directions)
        bool_sum <- show_cells + show_genes
        coords <- list("prin_coords_cols", "std_coords_cols")
        coords_type <- if (bool_sum != 0) {
            coords[[bool_sum]]
        }
        else {
            "prin_coords_cols"
        }
        if (coords_type == "std_coords_cols" && !is.null(coords_type)) {
            direction <- direction/caobj@D
        }
        model <- apl_model(coords = methods::slot(caobj, name = coords_type), 
            direction = direction, group = group)
        c_coords <- if (isTRUE(show_cells)) {
            methods::slot(caobj, name = coords_type)
        }
        else {
            NULL
        }
        df <- .construct_df(cells = c_coords, genes = if (isTRUE(show_genes)) 
            caobj@prin_coords_rows
        else NULL, model = model)
        df <- .add_cluster_info(plot_df = df, cadir = cadir, 
            cluster = cluster, highlight_cluster = highlight_cluster, 
            label_genes = label_genes)
        if (nrow(df) > 0) {
            df$info <- paste0("Name: ", df$sample, "\n", "Cluster: ", 
                df$cluster, "\n", "Type: ", df$type)
        }
        p <- ggplot2::ggplot(df, ggplot2::aes(x = x, y = y, color = cluster, 
            text = info))
        p <- .cluster_apl_points(ggplt = p, plot_df = df, point_size = point_size, 
            size_factor = size_factor, highlight_cluster = highlight_cluster, 
            label_genes = label_genes, ntop = ntop)
        if (!isFALSE(show_lines)) {
            show_both <- isTRUE(show_cells && show_genes)
            dapl <- cadir@directions
            if (coords_type == "std_coords_cols") {
                dapl <- sweep(dapl, 2, caobj@D, "/")
            }
            dapl <- model(dapl)
            dapl <- .toggle_dir(apl_dirs = dapl, caobj = caobj, 
                cadir = cadir, model = model, coords_type = coords_type)
            p <- .add_lines(ggplt = p, apl_dir = dapl, highlight_cluster = highlight_cluster, 
                show_lines = show_lines, show_both = show_both)
        }
        p <- p + ggplot2::ggtitle(paste0("Cluster: ", as.character(cluster))) + 
            ggplot2::labs(x = "association strength", y = "orthogonal distance") + 
            ggplot2::theme_bw()
        if (isTRUE(show_cutoff)) {
            alpha <- cadir@parameters$sa_cutoff
            if (is.null(alpha)) {
                rlang::warn("No Cutoff angle was calculated. Cannot show line.")
            }
            else {
                tan_alpha <- tan(alpha)
                p <- p + ggplot2::geom_abline(slope = tan_alpha, 
                  linetype = "twodash", color = "#c4421a", intercept = 0, 
                  linewidth = 1)
            }
        }
        if (isTRUE(interactive)) {
            suppressWarnings({
                p <- plotly::ggplotly(p = p, tooltip = "text")
            })
        }
        return(p)
    })
