suppressPackageStartupMessages(library(jsonlite))
cfg <- jsonlite::read_json(commandArgs(trailingOnly = TRUE)[[1]], simplifyVector = TRUE)
cat(R.version.string, "\nBiocVersion:", as.character(packageVersion("BiocVersion")), "\n")
cat("Library paths:\n", paste(.libPaths(), collapse = "\n"), "\n")
actual <- vapply(names(cfg$required_versions), function(p) {
  suppressPackageStartupMessages(library(p, character.only = TRUE))
  as.character(packageVersion(p))
}, character(1))
print(data.frame(package = names(actual), expected = unlist(cfg$required_versions), actual = actual))
print(sessionInfo())
stopifnot(getRversion() == "4.4.1", startsWith(as.character(packageVersion("BiocVersion")), "3.19."),
          all(actual == unlist(cfg$required_versions)))
