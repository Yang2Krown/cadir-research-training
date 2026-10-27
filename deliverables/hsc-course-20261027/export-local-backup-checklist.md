# 导出与本机备份核对清单

**本机状态：未完成。** Mac 看板没有同步，用户本机未提供完整 raw/common-preparation/RDS 副本路径或 SHA 核验记录。最终 ZIP 是小结果与来源记录包，不包含任何 RDS，不能替代数据备份。

## 已锁定来源输入

| 文件 | 绝对路径 | 字节数 | SHA-256 | 用户本机状态 |
|---|---|---:|---|---|
| GEO HTSeq counts | `/workspace/nestorowa-metadata-preparation/reacquired-20261026/GSE81682_HTSeq_counts.txt.gz` | 30,236,635 | `e12745e4087823ae868c6fe82a38510c15730e82ee74e1983def85ed3b7df68a` | 未导出 / 未核验 |
| counts RDS | `/workspace/nestorowa-metadata-preparation/reacquired-20261026/counts.rds` | 90,044,893 | `6bf8a84f4db185eb6021ceb53b7d6d33083410e02a6ee7a6df2191f0bbb90563` | 未导出 / 未核验 |
| metadata RDS | `/workspace/nestorowa-metadata-preparation/reacquired-20261026/coldata.rds` | 182,319 | `16d9e3ee62d27aac74591ccddd064eb2be9b86836591c8ec99d39e1af0bf35bc` | 未导出 / 未核验 |

`planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json` 记录原目录缺失，这些来源材料在本会话重新取得，不是恢复出来的历史原件。该收据以原样文件包含于 ZIP。

## ZIP 与外置对象

最终小包 ZIP 位于本交付目录，SHA-256 在同目录 `.zip.sha256` sidecar。ZIP 内 `external-objects.tsv` 有 63 项：实施已锁的 48 条 large-object 清单（raw/common-preparation/SCE 与 40 个正式运行 RDS），以及结果归档中 15 个小型 RNG RDS。每项记录精确绝对路径、字节数、SHA-256、哈希来源；所有这些对象均不进入 ZIP。

ZIP 中的 `results/` 是结果归档提交 `091a8a4585cabc59a5504380398892bac49044f4` 的一次性非 RDS 文件集（274 个文件，34,175,354 字节）。15 个被排除的 RDS 已在 `external-objects.tsv` 引用，结果树中 `archive-copy-sha256.json` 和 `large-objects-export-manifest.tsv/json` 原件也在包内。签署的独立结果报告、决策和文稿一致性记录位于 `reviews/result-review/`。

## 后续本机导出和核验

1. 按 ZIP 中 `external-objects.tsv` 分别导出全部 63 个外置文件；不要只下载代码/结果 ZIP。
2. 在 Mac 上逐项核对字节数和 SHA-256。macOS 可用 `stat -f '%z %N' '/path/to/file'` 与 `shasum -a 256 '/path/to/file'`；把本机路径、实测大小和 SHA、核验人、时间及时区写回 `export-manifest.tsv`。
3. ZIP 自身 SHA-256 由 `.zip.sha256` 验证；外置对象仍要解包/下载后逐项核对，不能以 ZIP 哈希替代。
4. 当前没有 Mac 访问或自动同步记录；在取得真实本机核验前，保持 `HSC-LOCAL-BACKUP=not_started` 与 `Mac board=not_synced`。
