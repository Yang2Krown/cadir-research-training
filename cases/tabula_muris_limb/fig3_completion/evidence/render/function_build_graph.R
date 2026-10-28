list(formals = as.pairlist(alist(cadir = , rm_redund = FALSE, keep_end = TRUE)), 
    body = {
        graph_list <- list()
        cls <- cadir@log$clusters
        cls_nodes <- colnames(cls)
        node_pattern <- c("iter_0|split|merge|end")
        sel <- which(grepl(node_pattern, cls_nodes))
        for (i in seq_len(length(sel))) {
            bef_cls <- cls[, sel[i] - 1]
            aft_cls <- cls[, sel[i]]
            is_end <- (i == length(sel) && keep_end)
            if (!is_end && all(f2c(bef_cls) == f2c(aft_cls)) && 
                isTRUE(rm_redund)) {
                next
            }
            graph_list[[i]] <- build_sub_graph(before = bef_cls, 
                after = aft_cls, before_nm = ifelse(i == 1, "root", 
                  cls_nodes[sel[last_i]]), after_nm = cls_nodes[sel[i]])
            last_i <- i
        }
        graph <- do.call(rbind, graph_list)
        rownames(graph) <- NULL
        graph <- igraph::graph_from_data_frame(graph, directed = TRUE)
        return(graph)
    })
