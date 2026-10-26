args <- commandArgs(trailingOnly=TRUE)
suppressPackageStartupMessages({library(Matrix);library(S4Vectors);library(jsonlite)})
x <- readRDS(args[[1]])
raw <- attr(x,"rownames",exact=TRUE)
resolved <- tryCatch(methods::slot(x,"rownames"),error=function(e) conditionMessage(e))
print(list(class=class(x),declared_slots=slotNames(x),raw_type=typeof(raw),
    raw_symbol=if(is.symbol(raw)) as.character(raw) else NULL,
    resolved_type=typeof(resolved),resolved_is_null=is.null(resolved),
    accessor_is_null=is.null(rownames(x))))
