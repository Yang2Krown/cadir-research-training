list(formals = as.pairlist(alist(cadir = , caobj = , highlight_cluster = TRUE, show_cells = TRUE, show_genes = FALSE, title_prefix = "Cluster: ", gsub_title = "", return_list = FALSE, ... = )), 
    body = {
        base::stopifnot(`Set either \`show_cells\` or \`show_genes\` to TRUE.` = isTRUE(show_cells) || 
            isTRUE(show_genes))
        size <- 1
        pls <- list()
        cls <- levels(cadir@cell_clusters)
        anno_dirs <- all(rownames(cadir@directions) %in% cls)
        for (i in seq_along(cls)) {
            for (j in seq_along(cls)) {
                if (!is.null(gsub_title)) {
                  cls_title <- gsub(pattern = gsub_title, replacement = " ", 
                    x = cls[i])
                }
                else {
                  cls_title <- cls[i]
                }
                sel <- which(cadir@cell_clusters == cls[i] | 
                  cadir@cell_clusters == cls[j])
                if (anno_dirs) {
                  sel_dir <- which(rownames(cadir@directions) %in% 
                    unique(c(cls[i], cls[j])))
                  dir_idx <- which(rownames(cadir@directions) == 
                    cls[i])
                }
                else {
                  sel_dir <- search_dict(cadir@dict, c(cls[i], 
                    cls[j]))
                  dir_idx <- search_dict(cadir@dict, cls[i])
                }
                sub_cak <- methods::new("cadir", cell_clusters = cadir@cell_clusters[sel], 
                  directions = cadir@directions[sel_dir, , drop = FALSE])
                if (show_cells) {
                  sc <- i == j
                }
                else {
                  sc <- FALSE
                }
                if (show_genes) {
                  sg <- i == j
                }
                else {
                  sg <- FALSE
                }
                p <- cluster_apl(caobj = caobj, cadir = sub_cak, 
                  direction = cadir@directions[dir_idx, ], group = which(cadir@cell_clusters == 
                    cls[i]), cluster = cls[i], show_cells = sc, 
                  show_genes = sg, show_lines = i != j, highlight_cluster = highlight_cluster, 
                  ...) + ggplot2::ggtitle(ifelse(i == j, paste0(title_prefix, 
                  cls_title), "")) + ggplot2::theme(legend.position = "none", 
                  axis.title.x = ggplot2::element_blank(), axis.text.x = ggplot2::element_blank(), 
                  axis.ticks.x = ggplot2::element_blank(), axis.title.y = ggplot2::element_blank(), 
                  axis.text.y = ggplot2::element_blank(), axis.ticks.y = ggplot2::element_blank())
                if (isFALSE(sc) && isFALSE(sg)) {
                  p <- p + ggplot2::scale_color_manual(values = c("black", 
                    "#006c66"))
                }
                if (i == j) {
                  p$layers[[1]]$aes_params$size <- size
                }
                else {
                  p$layers[[2]]$aes_params$size <- size
                }
                pls[[paste0(i, "_", j)]] <- p
            }
        }
        if (isTRUE(return_list)) {
            fig <- pls
        }
        else {
            fig <- ggpubr::ggarrange(plotlist = pls, nrow = length(cls), 
                ncol = length(cls))
        }
        return(fig)
    })
