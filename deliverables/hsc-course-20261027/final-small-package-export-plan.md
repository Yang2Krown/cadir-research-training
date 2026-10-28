# HSC 结果小包归档记录

## 状态

科学结果复验已签署 `PASS_LIMITED_RESULT_ACCEPTANCE`；两份中文草稿的限定范围一致性检查也已签署。该接受绑定源实现 commit `6cc7b3da67c193da11a67c45a75167d6521438b0` 和结果归档 commit `091a8a4585cabc59a5504380398892bac49044f4`，不等同于课程整体验收。正式 ZIP 仅在所有成员 SHA 与 ZIP CRC 验证通过后标记导出完成。

## 来源和包内路径

- [结果归档 commit](https://github.com/Yang2Krown/cadir-research-training/commit/091a8a4585cabc59a5504380398892bac49044f4) 的仓库目录 `cases/nestorowa_hsc/fair-experiment/results/6cc7b3d-20261027-attempt-01/` 映射为 ZIP 内 `results/`。
- 独立设计审查 commit `2d2565c24b3958260d7232ff03f211c06bd2e845` 的原报告、admission 与 C04 限定说明均在该结果树 `results/design-admission/`，只放一份。
- 结果复验报告、decision、文稿一致性记录和逐项审查材料以 review tip `b48066cba0bf4cd308f2f75b1134c12f85c576ef` 原样位于 `reviews/result-review/`；科学签字 commit 为 `faa7cd80a9e9b5bee0bed9835146dbca0d18cede`。
- 阶段一报告、锁、共同预处理收尾、原样 acquisition manifest、runner/evaluation/presentation 源码、共同评价 ID/QC 锁表、中文结果段落和讲稿、任务状态及本机导出清单均放在对应 `provenance/`、`results/`、`status/`、`backup/` 路径。

## 打包和外置规则

结果树 289 个 Git 文件中 274 个非 RDS 文件（34,175,354 bytes）进入 ZIP 一次。15 个小 RNG RDS 不放入 ZIP；40 个正式运行 RDS、raw inputs、共同预处理/SCE 与其他外置对象也不放入 ZIP。ZIP 的 `external-objects.tsv` 合并实施 `large-objects-export-manifest.tsv` 的 48 项和结果归档 `archive-copy-sha256.json` 中的 15 个 RNG RDS 项，沿用锁定绝对路径、字节数和 SHA-256；打包只检查外置文件存在和大小，不反序列化或重算大对象 SHA。

实际展开验证目录保留在 `/workspace/hsc-course-results-expanded-20261027`，不提交到 Git。交付 ZIP 位于 `deliverables/hsc-course-20261027/HSC-course-results-091a8a4-20261027.zip`，大小 23,185,119 bytes，SHA-256 `034f08ff08f57961cc12db09b0c3dd2e13b7893ea09f793f1cea00f79166023c`；相邻 `.zip.sha256` sidecar 固定相同摘要。ZIP CRC 和逐成员 SHA-256 均通过，完整核验记录见 `package-build-verification.json`.

## 未完成事项

Mac 看板未同步，用户本机的全部 63 项外置对象备份未验证。小结果 ZIP 不是完整数据备份；`HSC-LOCAL-BACKUP` 保持 `not_started`。
