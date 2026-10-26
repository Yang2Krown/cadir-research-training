# b7ee233 真实输入独立复核证据索引

结论：**BLOCKED，A01 不能关闭**。先读 [独立复跑报告](独立复跑报告.md) 和 [逐项状态表](verification_matrix.tsv)。

| 内容 | 路径 |
| --- | --- |
| 来源固定与源码保全 | `fixed_refs.json`、`source_before.json`、`source_after.json`、`source_preservation.json`、`preserved-target-source/` |
| 完整任务和三份管理材料 | `scope/` |
| 自主执行脚本 | `scripts/independent_receipts.py`、`scripts/entry_startup_probes.py` |
| 真实文件搜索及前后状态 | `real_file_availability.before.json`、`real_file_search_no_follow.json`、`real_file_availability.after.json` |
| 精确目标来源 manifest | `acquisition_manifest.target.json` |
| 三次唯一官方下载收据 | `acquisition_attempts.json`、`logs/*headers.log`、`logs/counts.*`、`logs/coldata.*`、`logs/GSE81682_HTSeq_counts.txt.*` |
| 当前环境、网络及执行权限 | `environment/`、`logs/R_*`、`logs/docker_*` |
| 固定原入口实际启动失败 | `entry_startup_probes.json`、`logs/wrapper_*` |
| 预期/实际差异与未核验清单 | `difference_table.tsv`、`runtime_difference.tsv`、`verification_matrix.tsv` |
| 仅核实施记录，非本次运行 | `record-only/` |
| 机器判定 | `review_result.json` |
| 全目录字节与 SHA256 索引 | `review_hashes.tsv`（不索引自身） |

`prepare`、`acquire`、`seal` 脚本将数据目录放在仓库之外；拒绝覆盖同名准备/获取收据，获取 URL 不重试。调用 `acquire` 和本地 Docker/包装器探测时须使用平台 executor 的实际网络权限，详见 `environment/executor_permissions.json`。全部原始 stdout/stderr（包括空文件）与 argv、实际退出码保存在 `logs/`。缺失原件时脚本不制造真实输入审计结果。
