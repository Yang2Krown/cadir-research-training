# One real-data case. Input integrity is checked by run_case.py before readRDS.
write_json <- function(x, path) {
  jsonlite::write_json(x, path, pretty = TRUE, auto_unbox = TRUE, null = "null", na = "null", digits = NA)
}
write_table <- function(x, path) {
  utils::write.table(x, path, sep = "\t", quote = TRUE, row.names = FALSE, na = "NA")
}

record_rng <- function(out, stage) {
  path <- file.path(out, "rng_stages.json")
  states <- if (file.exists(path)) jsonlite::read_json(path, simplifyVector = FALSE) else list()
  states[[stage]] <- list(kind = RNGkind(), state = as.integer(.Random.seed))
  write_json(states, path)
}

function_md5 <- function(fun) {
  path <- tempfile()
  on.exit(unlink(path))
  writeLines(capture.output(dput(list(formals = formals(fun), body = body(fun)))), path)
  unname(tools::md5sum(path))
}

audit_object <- function(sce, out) {
  writeLines(capture.output(str(sce, max.level = 2)), file.path(out, "object_structure.txt"))
  audit <- list(class = class(sce), dimensions = dim(sce))
  if (!methods::is(sce, "SingleCellExperiment")) {
    write_json(audit, file.path(out, "data_audit.json"))
    stop("Input is not SingleCellExperiment; container/assay semantics need review.")
  }
  cd <- SummarizedExperiment::colData(sce)
  rd <- SummarizedExperiment::rowData(sce)
  flat_columns <- function(df) {
    keep <- vapply(df, function(x) is.atomic(x) || is.factor(x), logical(1))
    as.data.frame(df[, keep, drop = FALSE])
  }
  write_table(cbind(cell_id = colnames(sce), flat_columns(cd)), file.path(out, "cell_metadata.tsv"))
  write_table(cbind(gene_id = rownames(sce), flat_columns(rd)), file.path(out, "gene_metadata.tsv"))
  capture.output(S4Vectors::metadata(sce), file = file.path(out, "metadata.txt"))
  sf <- SingleCellExperiment::sizeFactors(sce)
  audit$assays <- lapply(SummarizedExperiment::assayNames(sce), function(nm) {
    m <- SummarizedExperiment::assay(sce, nm)
    list(name = nm, class = class(m), dimensions = dim(m),
         finite = all(is.finite(m)), min = min(m), max = max(m),
         nonzero = sum(m != 0), zero_fraction = 1 - sum(m != 0) / prod(dim(m)))
  })
  audit$colData_columns <- colnames(cd)
  audit$rowData_columns <- colnames(rd)
  audit$reduced_dimensions <- SingleCellExperiment::reducedDimNames(sce)
  audit$size_factor_summary <- if (is.null(sf)) NULL else as.list(unclass(summary(sf)))
  audit$gene_ids_unique <- !anyDuplicated(rownames(sce))
  audit$cell_ids_unique <- !anyDuplicated(colnames(sce))
  audit$normalization_action <- "None. Existing logcounts are used unchanged. Presence is not proof of exact original preprocessing provenance."
  audit$preprocessing_evidence <- list()
  if (all(c("counts", "logcounts") %in% SummarizedExperiment::assayNames(sce)) && !is.null(sf)) {
    rr <- unique(round(seq(1, nrow(sce), length.out = min(100, nrow(sce)))))
    cc <- unique(round(seq(1, ncol(sce), length.out = min(100, ncol(sce)))))
    raw_sample <- as.matrix(SummarizedExperiment::assay(sce, "counts")[rr, cc])
    log_sample <- as.matrix(SummarizedExperiment::assay(sce, "logcounts")[rr, cc])
    expected <- log2(sweep(raw_sample, 2, sf[cc], "/") + 1)
    audit$preprocessing_evidence$logcounts_consistency <- list(
      checked_entries = length(raw_sample), formula = "log2(counts / existing sizeFactor + 1)",
      max_absolute_error = max(abs(log_sample - expected)),
      scope = "Diagnostic calculation on a deterministic grid only; existing assays were not changed.")
  }
  for (field in intersect(c("discard", "scDblFinder.class"), colnames(cd))) {
    audit$preprocessing_evidence[[field]] <- as.list(table(as.character(cd[[field]]), useNA = "ifany"))
  }
  audit$reference_source <- "Only the original cell_ontology_class column is eligible; clusters and predicted annotation are never reference labels."
  if ("cell_ontology_class" %in% colnames(cd)) {
    truth <- as.character(cd$cell_ontology_class)
    write_table(as.data.frame(table(truth, useNA = "ifany")), file.path(out, "reference_label_counts.tsv"))
    audit$reference_nonmissing <- sum(!is.na(truth) & nzchar(trimws(truth)))
    audit$reference_classes <- length(unique(truth[!is.na(truth) & nzchar(trimws(truth))]))
  }
  if ("tissue" %in% colnames(cd)) audit$tissue_counts <- as.list(table(as.character(cd$tissue), useNA = "ifany"))
  write_json(audit, file.path(out, "data_audit.json"))
  audit
}

export_results <- function(ca, cadir, sce, cfg, out) {
  ids <- rownames(ca@prin_coords_cols)
  stopifnot(identical(ids, colnames(sce)), length(cadir@cell_clusters) == ncol(sce))
  if (!identical(names(cadir@cell_clusters), ids)) stop("Cluster/cell order mismatch.")
  ref <- rep(NA_character_, length(ids))
  if (cfg$reference_column %in% colnames(SummarizedExperiment::colData(sce))) {
    ref <- as.character(SummarizedExperiment::colData(sce)[[cfg$reference_column]])
  }
  cell_results <- data.frame(cell_id = ids, cluster = as.character(cadir@cell_clusters), reference = ref)
  write_table(cell_results, file.path(out, "cell_clusters.tsv"))
  gene_cl <- setNames(as.character(cadir@gene_clusters), names(cadir@gene_clusters))
  gene_results <- data.frame(gene_id = rownames(ca@prin_coords_rows),
                            cluster = unname(gene_cl[rownames(ca@prin_coords_rows)]))
  write_table(gene_results, file.path(out, "gene_clusters.tsv"))
  sizes <- data.frame(cluster = levels(cadir@cell_clusters))
  sizes$ncells <- as.integer(table(cadir@cell_clusters)[sizes$cluster])
  sizes$ngenes <- as.integer(table(factor(cadir@gene_clusters, levels = sizes$cluster)))
  write_table(sizes, file.path(out, "cluster_sizes.tsv"))
  write_table(cbind(cell_id = ids, as.data.frame(ca@prin_coords_cols)), file.path(out, "ca_cell_coordinates.tsv"))
  write_table(cbind(gene_id = rownames(ca@prin_coords_rows), as.data.frame(ca@prin_coords_rows)), file.path(out, "ca_gene_coordinates.tsv"))
  set.seed(cfg$seed)
  record_rng(out, "before_ranking")
  ranked <- CAdir::rank_genes(cadir = cadir, caobj = ca)
  record_rng(out, "after_ranking")
  tracked_functions <- c("rank_genes", "get_apl_cutoff", "random_direction_cutoff", "apl_model")
  function_hashes <- setNames(lapply(tracked_functions, function(name) {
    function_md5(get(name, envir = asNamespace("CAdir")))
  }), tracked_functions)
  pivots <- apply(abs(ca@prin_coords_cols), 2, which.max)
  write_json(list(seed = cfg$seed, RNGkind = RNGkind(),
                  alpha_genes = unname(ranked@parameters$alpha_genes),
                  installed_CAdir_function_md5 = function_hashes,
                  ca_cell_pivot_ids = rownames(ca@prin_coords_cols)[pivots],
                  ca_cell_pivot_signs = sign(ca@prin_coords_cols[cbind(pivots, seq_along(pivots))]),
                  tie_rule = "Upstream decreasing Score order; exact ties retain CA row order (R stable order).",
                  historical_ranking_equivalence = "not_established; original CA/unranked objects unavailable"),
             file.path(out, "ranking_provenance.json"))
  ranks <- Filter(is.data.frame, ranked@gene_ranks)
  if (length(ranks)) {
    write_table(do.call(rbind, ranks), file.path(out, "coclustered_gene_ranks.tsv"))
  } else {
    write_table(data.frame(Rowname = character(), Score = numeric(), Row_num = integer(), Cluster = character(), Rank = integer()),
                file.path(out, "coclustered_gene_ranks.tsv"))
  }
  capture.output(ranked@parameters, file = file.path(out, "effective_cadir_parameters.txt"))
  saveRDS(ca, file.path(out, "ca.rds"))
  saveRDS(ranked, file.path(out, "cadir.rds"))
  write_table(cadir@log$clusters, file.path(out, "split_merge_cluster_history.tsv"))
  valid <- !is.na(ref) & nzchar(trimws(ref))
  metrics <- list(reference_column = cfg$reference_column, n_total = length(ref), n_evaluated = sum(valid),
                  n_excluded_missing_reference = sum(!valid), status = "SKIPPED_NO_RELIABLE_REFERENCE")
  if (sum(valid) > 1 && length(unique(ref[valid])) > 1) {
    m <- aricode::clustComp(as.character(cadir@cell_clusters[valid]), ref[valid])
    metrics$status <- "COMPUTED_ON_ORIGINAL_REFERENCE_LABELS"
    metrics$ARI <- m$ARI
    metrics$NMI <- m$NMI
    metrics$definition <- paste("aricode::clustComp ARI and NMI; package", packageVersion("aricode"), "; original reference labels only")
    write_table(as.data.frame(table(cluster = cell_results$cluster[valid], reference = ref[valid])),
                file.path(out, "cluster_reference_contingency.tsv"))
  }
  write_json(metrics, file.path(out, "metrics.json"))
  p <- CAdir::plot_clusters(cadir = ranked, caobj = ca, show_genes = TRUE,
       label_genes = TRUE, ntop = 5, axis = TRUE, title_prefix = "", ggncol = 3)
  ggplot2::ggsave(file.path(out, "association_plots.png"), plot = p, width = 14, height = max(5, 4 * ceiling(nrow(sizes) / 3)), dpi = 160, bg = "white")
  ggplot2::ggsave(file.path(out, "association_plots.pdf"), plot = p, width = 14, height = max(5, 4 * ceiling(nrow(sizes) / 3)), bg = "white")
  pc <- data.frame(CA1 = ca@prin_coords_cols[, 1], CA2 = ca@prin_coords_cols[, 2], cluster = cell_results$cluster)
  pca <- ggplot2::ggplot(pc, ggplot2::aes(CA1, CA2, colour = cluster)) + ggplot2::geom_point(size = 0.8) + ggplot2::theme_bw()
  ggplot2::ggsave(file.path(out, "ca_clusters.png"), plot = pca, width = 8, height = 6, dpi = 160, bg = "white")
  invisible(ranked)
}

main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  cfg <- jsonlite::read_json(args[[1]], simplifyVector = TRUE)
  out <- args[[2]]
  script_file <- sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)[[1]])
  monitor_script <- file.path(dirname(normalizePath(script_file)), "sample_rss.sh")
  status <- list(status = "RUNNING", data_audit = "not_started", single_case = "not_started", paper_reproduction = "not_established")
  stage <- "load_packages"
  times <- list()
  timed <- function(name, code) {
    t0 <- proc.time()[["elapsed"]]
    sentinel <- file.path(out, paste0(name, ".sampling"))
    samples <- file.path(out, paste0(name, "_rss_samples_KiB.txt"))
    file.create(sentinel)
    system2("sh", args = c(shQuote(monitor_script),
                            as.character(Sys.getpid()), shQuote(sentinel)),
            stdout = samples, stderr = file.path(out, paste0(name, "_sampler.log")), wait = FALSE)
    on.exit({
      unlink(sentinel)
      rss <- if (file.exists(samples)) suppressWarnings(as.numeric(readLines(samples, warn = FALSE))) else numeric()
      rss <- rss[is.finite(rss)]
      times[[name]] <<- list(elapsed_seconds = proc.time()[["elapsed"]] - t0,
                             sampled_peak_rss_KiB = if (length(rss)) max(rss) else NULL,
                             rss_samples = length(rss),
                             process_memory_status = if (file.exists("/proc/self/status")) grep("^Vm(HWM|RSS):", readLines("/proc/self/status"), value = TRUE) else NULL,
                             memory_scope = "Stage RSS sampled every 50 ms; short spikes can be missed. VmHWM is cumulative process high-water RSS.")
      write_json(times, file.path(out, "stage_times_seconds.json"))
    })
    value <- force(code)
    value
  }
  ok <- tryCatch({
    for (pkg in c("SingleCellExperiment", "scran", "APL", "CAdir", "aricode", "ggplot2")) {
      suppressPackageStartupMessages(library(pkg, character.only = TRUE))
    }
    stopifnot("R 4.4.1 required by task" = getRversion() == "4.4.1",
              "Bioconductor 3.19 required" = startsWith(as.character(packageVersion("BiocVersion")), "3.19."))
    actual_versions <- vapply(names(cfg$required_versions), function(p) as.character(packageVersion(p)), character(1))
    write_table(data.frame(package = names(actual_versions), expected = unlist(cfg$required_versions), actual = actual_versions),
                file.path(out, "required_version_check.tsv"))
    stopifnot("Runtime package versions differ from verified continuation configuration" = all(actual_versions == unlist(cfg$required_versions)))
    RNGkind("Mersenne-Twister", "Inversion", "Rejection")
    set.seed(cfg$seed)
    stage <- "read_and_audit"
    sce <- timed("readRDS", readRDS(cfg$data_path))
    audit <- timed("audit", audit_object(sce, out))
    status$data_audit <- "PASS"
    if (isTRUE(cfg$audit_only)) {
      status$status <- "AUDIT_ONLY_COMPLETE"
      return(invisible(TRUE))
    }
    stopifnot("Existing logcounts required; no automatic renormalization" = cfg$assay %in% assayNames(sce))
    stopifnot("Unique named gene/cell identifiers required" = isTRUE(audit$gene_ids_unique) && isTRUE(audit$cell_ids_unique))
    if ("tissue" %in% colnames(colData(sce))) {
      tissue <- as.character(sce$tissue)
      stopifnot("Non-Limb_Muscle tissue found; do not silently subset" = all(!is.na(tissue) & tissue == "Limb_Muscle"))
    }
    expr <- assay(sce, cfg$assay)
    stopifnot(all(is.finite(expr)), min(expr) >= 0, all(rowSums(expr) > 0), all(colSums(expr) > 0))
    differences <- c("Author figure2.qmd corresponds to the formal paper Fig 3 Limb Muscle case (Fig 2 is the method overview).",
                     "python=FALSE here versus TRUE in author figure2.qmd; fixed APL at dims=30 uses R/irlba for both parameter values.",
                     "Input name differs from author figure2.qmd; exact preprocessing equivalence requires source documentation.")
    if (ncol(sce) != cfg$expected_cells_context_only) differences <- c(differences, paste("Observed cells", ncol(sce), "versus paper target", cfg$expected_cells_context_only, "; no cell filtering or padding performed."))
    stage <- "select_features"
    gv <- timed("modelGeneVar", scran::modelGeneVar(sce, assay.type = cfg$assay))
    chosen <- scran::getTopHVGs(gv, n = cfg$hvg_n, var.threshold = NULL)
    hvg_count <- length(chosen)
    write_table(cbind(gene_id = rownames(gv), as.data.frame(gv)), file.path(out, "gene_variance.tsv"))
    write_table(data.frame(gene_id = chosen), file.path(out, "hvg_genes.tsv"))
    if (!is.null(cfg$marker_csv)) {
      markers <- read.csv(cfg$marker_csv)
      stopifnot("Marker CSV must have gene column" = "gene" %in% colnames(markers))
      chosen <- unique(c(chosen, markers$gene[markers$gene %in% rownames(sce)]))
    } else {
      differences <- c(differences, "Author tabula_muris_marker_genes.csv unavailable: HVGs only; marker augmentation not reproduced.")
    }
    writeLines(differences, file.path(out, "paper_differences.txt"))
    write_json(list(original_cells = ncol(sce), original_genes = nrow(sce), hvg_count = hvg_count,
                    actual_selected_genes = length(chosen), seed = cfg$seed, renormalized = FALSE), file.path(out, "selection.json"))
    write_table(data.frame(gene_id = chosen), file.path(out, "selected_genes.tsv"))
    sce_sub <- sce[chosen, ]
    stage <- "CA"
    set.seed(cfg$seed)
    record_rng(out, "before_CA")
    ca <- timed("CA", do.call(APL::cacomp, c(list(obj = assay(sce_sub, cfg$assay), top = nrow(sce_sub)), cfg$ca)))
    record_rng(out, "after_CA")
    stopifnot(nrow(ca@prin_coords_cols) == ncol(sce), ncol(ca@prin_coords_cols) == cfg$ca$dims, all(is.finite(ca@prin_coords_cols)))
    saveRDS(ca, file.path(out, "ca.rds"))
    stage <- "CAdir"
    set.seed(cfg$seed)
    record_rng(out, "before_CAdir")
    # Keep a symbolic caobj in match.call(), avoiding serialization/printing of
    # the whole CA object inside CAdir's call metadata when using do.call().
    cadir <- timed("CAdir", CAdir::dirclust_splitmerge(
      caobj = ca, k = cfg$cadir$k, cutoff = cfg$cadir$cutoff,
      method = cfg$cadir$method, apl_quant = cfg$cadir$apl_quant,
      counts = cfg$cadir$counts, min_cells = cfg$cadir$min_cells,
      epochs = cfg$cadir$epochs, reps = cfg$cadir$reps,
      make_plots = cfg$cadir$make_plots, qcutoff = cfg$cadir$qcutoff,
      convergence_thr = cfg$cadir$convergence_thr, max_iter = cfg$cadir$max_iter,
      init = cfg$cadir$init, keep_log = cfg$cadir$keep_log,
      apl_cutoff_reps = cfg$cadir$apl_cutoff_reps))
    record_rng(out, "after_CAdir")
    saveRDS(cadir, file.path(out, "cadir_unranked.rds"))
    stage <- "export_results"
    ranked <- timed("exports_ranking_plots", export_results(ca, cadir, sce_sub, cfg, out))
    status$single_case <- "PASS"
    stage <- "annotation"
    if (isTRUE(cfg$annotation$enabled)) {
      annotation_ok <- tryCatch({
        gs <- CAdir::load_ct_gene_set(set = cfg$annotation$set, org = cfg$annotation$organism)
        write_table(gs, file.path(out, "annotation_cellmarker_mouse.tsv"))
        write_json(list(set = cfg$annotation$set, organism = cfg$annotation$organism,
                        source_object = "CAdir::cellmarker_v2", package_version = as.character(packageVersion("CAdir")),
                        records = nrow(gs), overlapping_selected_genes = sum(rownames(sce_sub) %in% gs$gene)),
                   file.path(out, "annotation_resources.json"))
        an <- timed("annotation", CAdir::annotate_biclusters(obj = ranked, caobj = ca,
             universe = rownames(sce_sub), org = cfg$annotation$organism, method = "goa", set = cfg$annotation$set,
             cost = "logpval", filter_literature = FALSE))
        write_table(data.frame(cell_id = colnames(sce_sub), cluster = as.character(cadir@cell_clusters),
                              predicted_annotation = as.character(an@cell_clusters)), file.path(out, "predicted_annotations.tsv"))
        saveRDS(an, file.path(out, "cadir_annotated.rds"))
        TRUE
      }, error = function(e) {
        writeLines(conditionMessage(e), file.path(out, "annotation_failure.txt"))
        FALSE
      })
      status$annotation <- if (annotation_ok) "COMPLETE_PREDICTED_ONLY" else "FAILED_SEE_ANNOTATION_FAILURE"
    }
    status$status <- "SINGLE_CASE_COMPLETE_WITH_DOCUMENTED_DIFFERENCES"
    TRUE
  }, error = function(e) {
    status$status <<- "FAILED"
    status$failed_stage <<- stage
    status$error <<- conditionMessage(e)
    message("FAILED at ", stage, ": ", conditionMessage(e))
    FALSE
  }, finally = {
    if (file.exists("/proc/self/status")) {
      hwm <- grep("^VmHWM:", readLines("/proc/self/status"), value = TRUE)
      status$r_peak_rss_KiB_linux <- if (length(hwm)) as.numeric(regmatches(hwm, regexpr("[0-9]+", hwm))) else NULL
    }
    capture.output(sessionInfo(), file = file.path(out, "sessionInfo.txt"))
    write_table(as.data.frame(installed.packages()[, c("Package", "Version", "Built")]), file.path(out, "installed_packages.tsv"))
    write_json(status, file.path(out, "r_status.json"))
  })
  if (!isTRUE(ok)) quit(status = 1)
}
if (sys.nframe() == 0L) main()
