# Display-only helper shared by the complete renderer and the minimal S1 repair.
# The legend replaces in-panel direction names; point/direction data stay intact.
add_standard_direction_legend <- function(p, projected_directions, role_names, colours) {
  for (i in seq_along(p$layers)) p$layers[[i]]$show.legend <- FALSE
  lines <- data.frame(role = factor(role_names, levels = role_names),
                      slope = projected_directions[, 2] / projected_directions[, 1])
  values <- c(cell_cluster = '#c6d325', cell_other = '#006c66',
              gene_cluster = '#ef7c00', gene_other = '#777777',
              stats::setNames(colours[seq_along(role_names)], role_names))
  p + ggplot2::geom_abline(data = lines,
       ggplot2::aes(slope = slope, intercept = 0, colour = role),
       linetype = 'dashed', linewidth = .8, show.legend = TRUE) +
    ggplot2::scale_colour_manual(values = values, breaks = role_names,
       labels = gsub('_', ' ', role_names), name = 'Compared direction') +
    ggplot2::guides(size = 'none', shape = 'none') +
    ggplot2::theme(legend.position = 'bottom', legend.direction = 'horizontal')
}
