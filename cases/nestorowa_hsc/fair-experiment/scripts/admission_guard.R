# Shared by both formal computation and ranking. No self-authored admission exists.
admission_guard <- function(gate_path,manifest_path,lock_path,config_path) {
 gate <- jsonlite::read_json(gate_path,simplifyVector=TRUE)
 stopifnot(isTRUE(gate$formal_execution_permitted),identical(gate$decision,"PASS_LIMITED_FORMAL_EXECUTION"),identical(gate$reviewer_participated_in_implementation,FALSE),identical(gate$reviewer_model,"gpt-6.1-sol"),identical(gate$reviewer_reasoning_effort,"high"),nzchar(gate$reviewer_agent_id),nzchar(gate$review_report),gate$C04_decision%in%c("ACCEPTED_LIMITED_NOVELTY_SCOPE","VERIFIED_NEW_WITH_FIRST_SOURCE"))
 stopifnot(sha_file(manifest_path)==gate$source_manifest_sha256,sha_file(lock_path)==gate$data_lock_sha256,sha_file(config_path)==gate$scientific_config_sha256)
 source_lock <- jsonlite::read_json(manifest_path,simplifyVector=FALSE)
 for(e in source_lock$files) stopifnot(sha_file(file.path(source_lock$repository_root,e$path))==e$sha256,file.info(file.path(source_lock$repository_root,e$path))$size==e$bytes)
 # The immutable image has no git executable. Host Python checks every source
 # blob in gate$source_commit before launch; this R entry independently checks
 # every admitted source byte against the reviewer-bound content manifest.
 stopifnot(is.character(gate$source_commit),length(gate$source_commit)==1,nchar(gate$source_commit)==40)
 lock <- jsonlite::read_json(lock_path,simplifyVector=FALSE)
 for(e in lock$files) stopifnot(file.info(e$path)$size==e$bytes,sha_file(e$path)==e$sha256)
 stopifnot(sha_file(lock$environment_signature_path)==gate$environment_signature_sha256)
 assert_environment(readRDS(lock$environment_signature_path))
 cfg <- jsonlite::read_json(config_path,simplifyVector=TRUE)
 stopifnot(identical(as.integer(cfg$seeds),c(2358L,101L,202L,303L,404L)))
 list(gate=gate,lock=lock,config=cfg)
}
