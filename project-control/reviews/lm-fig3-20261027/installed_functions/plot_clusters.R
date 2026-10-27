list(formals = as.pairlist(alist(cadir = , caobj = , point_size = 1, size_factor = 1, show_genes = FALSE, label_genes = FALSE, ntop = 5, text_size = 16, title_prefix = "Cluster: ", ggncol = NULL, ggnrow = NULL, axis = FALSE, gsub_title = NULL, legend_pos = "none", return_list = FALSE)), 
    body = {
        pls <- list()
        cls <- levels(cadir@cell_clusters)
        if (isFALSE(axis)) {
            plot_theme <- ggplot2::theme(legend.position = legend_pos, 
                axis.title.x = ggplot2::element_blank(), axis.text.x = ggplot2::element_blank(), 
                axis.ticks.x = ggplot2::element_blank(), axis.title.y = ggplot2::element_blank(), 
                axis.text.y = ggplot2::element_blank(), axis.ticks.y = ggplot2::element_blank(), 
                plot.title = ggplot2::element_text(size = text_size))
        }
        else {
            plot_theme <- ggplot2::theme(legend.position = legend_pos, 
                axis.title.x = ggplot2::element_blank(), axis.title.y = ggplot2::element_blank(), 
                plot.title = ggplot2::element_text(size = text_size))
        }
        for (i in seq_along(cls)) {
            if (!is.null(gsub_title)) {
                cls_title <- gsub(pattern = gsub_title, replacement = " ", 
                  x = cls[i])
            }
            else {
                cls_title <- cls[i]
            }
            p <- cluster_apl(caobj = caobj, cadir = cadir, direction = cadir@directions[cls[i], 
                ], cluster = as.character(cls[i]), group = which(cadir@cell_clusters == 
                cls[i]), show_cells = TRUE, show_genes = show_genes, 
                show_lines = FALSE, highlight_cluster = TRUE, 
                label_genes = label_genes, point_size = point_size, 
                size_factor = size_factor, ntop = ntop) + ggplot2::ggtitle(paste0(title_prefix, 
                cls_title)) + plot_theme
            pls[[i]] <- p
        }
        if (isTRUE(return_list)) {
            fig <- pls
        }
        else {
            fig <- ggpubr::ggarrange(plotlist = pls, nrow = ifelse(test = is.null(ggnrow), 
                yes = ceiling(sqrt(length(cls))), no = ggnrow), 
                ncol = ifelse(test = is.null(ggncol), yes = ceiling(sqrt(length(cls))), 
                  no = ggncol))
        }
        return(suppressWarnings(fig))
    })
