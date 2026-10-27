# Formal-output-only presentation

`render_results.R RUN_ROOT DATA_INPUT_LOCK NEW_OUTPUT_DIRECTORY` consumes formal partitions, frozen metric JSONs, core resource receipts and common-QC/ID tables. It never reads expression RDS, runs reductions/clustering, or recomputes ARI/NMI.

The script waits for all 10 predeclared method/seed attempt receipts. It checks the independent admission/data-lock binding, consumed locked-file and core-artifact hashes, exact partition cell order and identical evaluation counts. It plots all five seeds (including failures), and fixes seed2358 as the sole contingency example before result inspection. A failed2358 is marked unavailable and never replaced by a better seed. Predicted cluster identifiers receive no label matching or class-name substitution.

Outputs are 300dpi PNG and vector PDF, exact plotted-value/resource/contingency/QC tables, a consumed-input hash manifest, status receipt, and Chinese figure descriptions. Resource figures distinguish core steps, 50ms sampled RSS, cumulative process VmHWM, and separately recorded diagnostic failures. Random seeds are not biological replicates. The figures and presentation status do not constitute independent scientific result acceptance.

Use the existing fixed read-only container wrapper after the admitted formal run finishes. The destination must be a fresh presentation directory under `/workspace/hsc-fair-experiment-data-20261026/`; keep this new script separate from the 59 admitted core-source files. The script and figures will be committed as result-support artifacts without altering those core files, the scientific config, or the common-input lock.
