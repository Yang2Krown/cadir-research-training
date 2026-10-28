#' Seurat vignette and conversion to SCE
#' @export
sce_pbmc3k <- function() {
  set.seed(1234)

  sce <- TENxPBMCData::TENxPBMCData(dataset = "pbmc3k")
  rownames(sce) <- make.unique(SummarizedExperiment::rowData(sce)$Symbol_TENx)
  colnames(sce) <- SummarizedExperiment::colData(sce)$Barcode

  pbmc <- SeuratObject::CreateSeuratObject(
    counts = as.matrix(SingleCellExperiment::counts(sce)),
    assay = "RNA",
    project = "pbmc3k",
    min.cells = 3,
    min.features = 200,
    meta.data = as.data.frame(SingleCellExperiment::colData(sce))
  )

  pbmc[["percent.mt"]] <- Seurat::PercentageFeatureSet(pbmc, pattern = "^MT-")

  # Filter data
  pbmc <- subset(
    pbmc,
    subset = nFeature_RNA > 200 & nFeature_RNA < 2500 & percent.mt < 5
  )
  no_zeros_rows <- Matrix::rowSums(pbmc, slot = "counts") > 0
  pbmc <- pbmc[no_zeros_rows, ]

  # Normalization
  pbmc <- Seurat::NormalizeData(
    pbmc,
    normalization.method = "LogNormalize",
    scale.factor = 10000,
    verbose = FALSE
  )

  pbmc <- Seurat::FindVariableFeatures(
    pbmc,
    # selection.method = "vst",
    nfeatures = 2000,
    verbose = FALSE
  )

  # Scaling
  all.genes <- rownames(pbmc)
  pbmc <- Seurat::ScaleData(pbmc, features = all.genes, verbose = FALSE)

  # Run PCA
  pbmc <- Seurat::RunPCA(
    pbmc,
    features = Seurat::VariableFeatures(object = pbmc),
    verbose = FALSE
  )

  # Cell clustering
  pbmc <- Seurat::FindNeighbors(pbmc, dims = 1:10, verbose = FALSE)
  pbmc <- Seurat::FindClusters(pbmc, resolution = 0.5, verbose = FALSE)

  pbmc <- Seurat::RunUMAP(pbmc, dims = 1:10, verbose = FALSE)

  new.cluster.ids <- c(
    "0 - Naive CD4 T",
    "1 - CD14+ Mono",
    "2 - Memory CD4 T",
    "3 - B",
    "4 - CD8 T",
    "5 - FCGR3A+ Mono",
    "6 - NK",
    "7 - DC",
    "8 - Platelet"
  )

  names(new.cluster.ids) <- levels(pbmc)
  pbmc <- SeuratObject::RenameIdents(pbmc, new.cluster.ids)
  pbmc$cell_type <- SeuratObject::Idents(pbmc)

  return(Seurat::as.SingleCellExperiment(pbmc))
}

get_top_cells <- function(cadir, caobj, cluster) {
  alpha <- cadir@parameters$sa_cutoff

  if (is.null(alpha)) {
    alpha <- get_apl_cutoff(
      caobj = caobj,
      method = "random",
      group = which(cadir@cell_clusters == c),
      quant = 0.99,
      apl_cutoff_reps = 100
    )
  }
  group <- which(cadir@cell_clusters == cluster)
  direction <- cadir@directions[cadir@dict[[cluster]], ] / caobj@D

  model <- apl_model(
    coords = caobj@std_coords_cols,
    direction = direction,
    group = group
  )

  cell_coords <- model(caobj@std_coords_cols)

  cluster_cells <- names(cadir@cell_clusters)[
    which(cadir@cell_clusters == cluster)
  ]

  # subset genes to cluster genes
  cell_coords <- cell_coords[
    which(rownames(cell_coords) %in% cluster_cells),
    ,
    drop = FALSE
  ]

  # Step 3: Score by cutoff
  score <- cell_coords[, 1] - (cell_coords[, 2] * alpha)

  ranking <- data.frame(
    "Colname" = rownames(cell_coords),
    "x" = cell_coords[, 1],
    "y" = cell_coords[, 2],
    "Score" = score,
    "Col_num" = seq_len(nrow(cell_coords)),
    "Cluster" = cluster
  )

  ranking <- ranking[order(ranking$Score, decreasing = TRUE), ]
  ranking$Rank <- seq_len(nrow(ranking))

  return(ranking)
}

load_platelet_gs <- function() {
  df <- readr::read_tsv(
    "./platelets_marker_genes.tsv",
    show_col_types = FALSE,
    progress = FALSE
  )
  colnames(df) <- gsub(" ", "_", colnames(df))
  df <- df %>%
    filter(cell_type == "Platelets") %>%
    filter(species %in% c("Hs", "Mm Hs"))

  return(list("Platelets" = df$official_gene_symbol))
}


plot_clusters_custom <- function(
  cadir,
  caobj,
  point_size = 1,
  size_factor = 1,
  show_genes = FALSE,
  label_genes = FALSE,
  ntop = 5,
  text_size = 16,
  ggncol = NULL,
  ggnrow = NULL,
  outlier_cluster,
  axis = FALSE,
  title_prefix = "_",
  gsub_title = NULL,
  legend_pos = "none",
  return_list = FALSE
) {
  pls <- list()
  cls <- levels(cadir@cell_clusters)

  if (isFALSE(axis)) {
    plot_theme <- ggplot2::theme(
      legend.position = legend_pos,
      axis.title.x = ggplot2::element_blank(),
      axis.text.x = ggplot2::element_blank(),
      axis.ticks.x = ggplot2::element_blank(),
      axis.title.y = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_blank(),
      axis.ticks.y = ggplot2::element_blank(),
      plot.title = ggplot2::element_text(size = text_size)
    )
  } else {
    plot_theme <- ggplot2::theme(
      legend.position = legend_pos,
      axis.title.x = ggplot2::element_blank(),
      axis.title.y = ggplot2::element_blank(),
      plot.title = ggplot2::element_text(size = text_size)
    )
  }

  for (i in seq_along(cls)) {
    if (!is.null(gsub_title)) {
      cls_title <- gsub(
        pattern = gsub_title,
        replacement = " ",
        x = cls[i]
      )
    } else {
      cls_title <- cls[i]
    }
    p <- cluster_apl(
      caobj = caobj,
      cadir = cadir,
      direction = cadir@directions[cls[i], ],
      cluster = as.character(cls[i]),
      group = which(cadir@cell_clusters == cls[i]),
      show_cells = TRUE,
      show_genes = show_genes,
      show_lines = FALSE,
      highlight_cluster = TRUE,
      # colour_by_group = FALSE,
      label_genes = label_genes,
      point_size = point_size,
      size_factor = size_factor,
      ntop = ntop
    ) +
      ggplot2::ggtitle(paste0(title_prefix, cls_title)) +
      plot_theme

    if (cls[i] == outlier_cluster) {
      cell_rnk <- get_top_cells(
        cadir = cadir,
        caobj = caobj,
        cluster = outlier_cluster
      )
      p <- p +
        geom_point(
          data = cell_rnk[cell_rnk$Score >= 0, ],
          aes(x = x, y = y, text = NULL),
          color = "#d44a3d",
        )
    }

    pls[[i]] <- p
  }

  if (isTRUE(return_list)) {
    fig <- pls
  } else {
    fig <- ggpubr::ggarrange(
      plotlist = pls,
      nrow = ifelse(
        test = is.null(ggnrow),
        yes = ceiling(sqrt(length(cls))),
        no = ggnrow
      ),
      ncol = ifelse(
        test = is.null(ggncol),
        yes = ceiling(sqrt(length(cls))),
        no = ggncol
      )
    )
  }
  return(suppressWarnings(fig))
}


sm_plot_custom <- function(
  cadir,
  caobj,
  rm_redund = TRUE,
  show_cells = TRUE,
  show_genes = FALSE,
  highlight_cluster = FALSE,
  annotate_clusters = FALSE,
  org = "mm",
  keep_end = TRUE
) {
  # TODO: Simplify function.
  base::stopifnot(
    "Set either `show_cells` or `show_genes` to TRUE." = isTRUE(show_cells) ||
      isTRUE(show_genes)
  )

  graph <- build_graph(
    cadir = cadir,
    rm_redund = rm_redund,
    keep_end = keep_end
  )

  lgraph <- ggraph::create_layout(graph, layout = "tree")

  ggraph::set_graph_style(plot_margin = ggplot2::margin(0, 0, 0, 0))
  bg <- ggraph::ggraph(lgraph) +
    ggraph::geom_edge_link() +
    ggraph::geom_node_point(alpha = 1)

  bg_coords <- get_x_y_values(bg)

  cls <- cadir@log$clusters
  dirs <- cadir@log$directions

  nodes <- names(igraph::V(graph))

  old_iter_nm <- ""
  for (i in seq_len(nrow(lgraph))) {
    node_nm <- nodes[i]

    name_elems <- base::strsplit(node_nm, "-", fixed = TRUE)[[1]]
    # name_elems <- stringr::str_split_1(node_nm, "-")

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

    cluster_idx <- base::which(rownames(tmp_dirs) == cluster)
    dir <- tmp_dirs[cluster_idx, ]

    if (iter_nm != old_iter_nm) {
      tmp_ccs <- x2f(cls[, iter_nm])
      names(tmp_ccs) <- rownames(caobj@prin_coords_cols)

      tmp_cadir <- methods::new(
        "cadir",
        cell_clusters = tmp_ccs,
        directions = as.matrix(tmp_dirs)
      )

      if (is.null(cadir@parameters$qcutoff)) {
        cadir@parameters$qcutoff <- 0.8
      }

      tmp_cadir@gene_clusters <- assign_genes(
        caobj = caobj,
        cadir = tmp_cadir,
        qcutoff = cadir@parameters$qcutoff
      )

      if (isTRUE(annotate_clusters)) {
        suppressWarnings({
          tmp_cadir <- annotate_biclustering(
            obj = tmp_cadir,
            universe = rownames(caobj@std_coords_rows),
            org = org,
            alpha = 0.05,
            min_size = 10,
            max_size = 500
          )
        })
      }
      old_iter_nm <- iter_nm
    }

    cluster <- rownames(tmp_cadir@directions)[cluster_idx]
    rownames(dir) <- cluster

    # colour_by_group <- !highlight_cluster

    p <- cluster_apl(
      caobj = caobj,
      cadir = tmp_cadir,
      direction = as.numeric(dir),
      group = grp_idx,
      cluster = cluster,
      show_cells = show_cells,
      show_genes = show_genes,
      highlight_cluster = highlight_cluster,
      show_lines = FALSE,
      point_size = 0.3
    )
    if (isTRUE(annotate_clusters)) {
      p <- p +
        ggplot2::ggtitle(cluster) +
        theme_blank(
          title = ggplot2::element_text(
            color = "black",
            size = 10,
            face = "bold"
          ),
          text = ggplot2::element_text()
        )
    } else {
      # TODO: We need to pick a color palette for a large number of clusters
      # scale_color_mpimg(name = "mpimg") +
      p <- p + theme_blank()
    }

    bg <- bg +
      patchwork::inset_element(
        p,
        left = bg_coords[i, 1] - 0.07,
        right = bg_coords[i, 1] + 0.07,
        top = bg_coords[i, 2] + 0.07,
        bottom = bg_coords[i, 2] - 0.07,
        align_to = "panel"
      )
  }

  return(bg)
}
