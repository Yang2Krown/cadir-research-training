# HSC course results delivery

The bounded scientific results review and Chinese text-consistency review have passed. This delivery branch packages the frozen results, provenance, signed reviews, and a small ZIP. It does not claim course-wide acceptance or complete user-local data backup.

## Frozen source and review commits

- Admitted implementation: [6cc7b3da67c193da11a67c45a75167d6521438b0](https://github.com/Yang2Krown/cadir-research-training/commit/6cc7b3da67c193da11a67c45a75167d6521438b0)
- Independent design review: [2d2565c24b3958260d7232ff03f211c06bd2e845](https://github.com/Yang2Krown/cadir-research-training/commit/2d2565c24b3958260d7232ff03f211c06bd2e845)
- Frozen result archive: [091a8a4585cabc59a5504380398892bac49044f4](https://github.com/Yang2Krown/cadir-research-training/commit/091a8a4585cabc59a5504380398892bac49044f4)
- Signed scientific result acceptance: commit [faa7cd80a9e9b5bee0bed9835146dbca0d18cede](https://github.com/Yang2Krown/cadir-research-training/commit/faa7cd80a9e9b5bee0bed9835146dbca0d18cede); final text-review tip [b48066cba0bf4cd308f2f75b1134c12f85c576ef](https://github.com/Yang2Krown/cadir-research-training/commit/b48066cba0bf4cd308f2f75b1134c12f85c576ef).

The final ZIP is [HSC-course-results-091a8a4-20261027.zip](HSC-course-results-091a8a4-20261027.zip) (23,185,119 bytes; SHA-256 `034f08ff08f57961cc12db09b0c3dd2e13b7893ea09f793f1cea00f79166023c`). The same digest is recorded in the adjacent `.zip.sha256` sidecar. CRC and every member SHA-256 passed; see [package-build-verification.json](package-build-verification.json). The ZIP's `results/` directory maps to `cases/nestorowa_hsc/fair-experiment/results/6cc7b3d-20261027-attempt-01/` in the frozen result commit. It includes that tree's non-RDS files once, with all 15 RNG RDS and all raw/common-preparation/run RDS excluded and listed in `external-objects.tsv`.

The result tree preserves files exactly as committed at 091a8a4. Its report and presentation metadata may say review was pending when generated; the signed reviews in `reviews/result-review/` supersede that historical status. No signed reviewer file was edited. The Chinese result text and PPT notes contain only the permitted status/citation update and preserve the reviewed values and limitations.

## Backup and current status

`task-status.json` records `HSC-EXPORT=completed_read_only`, while `HSC-LOCAL-BACKUP=not_started`. The Mac board is not synced and no complete user-local raw/object backup has been verified. The ZIP is not a full data backup; export the 63 external objects separately and verify each path, byte count, and SHA-256 in `external-objects.tsv`.

The package manifest, deterministic assembly script, task-status schema, result narrative, PPT notes, and backup checklist are alongside this README. The expanded ZIP contents used for verification remain at `/workspace/hsc-course-results-expanded-20261027` outside the Git worktree.
