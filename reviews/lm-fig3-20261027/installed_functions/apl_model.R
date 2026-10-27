list(formals = as.pairlist(alist(coords = , direction = , group = NULL)), 
    body = {
        avg_group_coords <- direction
        length_vector_group <- sqrt(drop(avg_group_coords %*% 
            avg_group_coords))
        cosangle <- 1
        if (!is.null(group)) {
            subgroup <- coords[group, ]
            if (length(group) == 1) {
                group_mean <- subgroup
            }
            else {
                group_mean <- colMeans(subgroup)
            }
            cosangle <- cosine(a = group_mean, b = direction)
            if (cosangle < 0) {
                avg_group_coords <- -avg_group_coords
            }
        }
        model <- function(vec) {
            length_vector <- row_norm(vec)
            cordx <- drop(vec %*% avg_group_coords)/length_vector_group
            cordy <- suppressWarnings(sqrt(length_vector^2 - 
                cordx^2))
            cordx[is.na(cordx)] <- 0
            cordy[is.na(cordy)] <- 0
            return(cbind(x = cordx, y = cordy))
        }
        return(model)
    })
