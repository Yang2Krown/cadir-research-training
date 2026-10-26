# Nestorowa metadata preparation snapshot

This directory preserves the non-experimental preparation from 2026-10-26.
See 核对报告.md and preparation_status.json. Formal execution remains prohibited.

The original missing audit directory was NOT recovered. The files were reacquired from official storage; acquisition_manifest.json and reacquired-20261026/*.json preserve the new receipts. Raw RDS files, the count table and Python dependencies are deliberately excluded from Git. Their local copies remain at /workspace/nestorowa-metadata-preparation/reacquired-20261026/.

recovered-branch/ is an unchanged historical copy from commit 122fdbf2986f3791917197385f8d07ba0a75fce6. Its old failure/NOT_VERIFIED records are not current receipts. The same commit is this branch's base.

preparation_artifact_sha256.tsv covers the original report, script and metadata outputs. acquisition_manifest.json references both committed evidence and external raw files; a missing raw file in this checkout is expected. These hashes are artifact integrity records, not permission to run any experiment.

The metadata script reads only coldata.rds and the first sample-ID line of the GEO count table; it never deserializes counts.rds. The old audit_inputs.R is retained as historical source and must NOT be run within the current boundary because it inspects count values.
