# HSC 正式结果中文草稿（待独立结果复验）

**状态：** 独立结果复验通过限定范围验收（`PASS_LIMITED_RESULT_ACCEPTANCE`）。决策与报告绑定结果提交 `091a8a4585cabc59a5504380398892bac49044f4`；signed decision SHA-256 为 `dc54cfe9ba4a6cd751e0ccd2ab356326c56290ff441d5047a37613a78672ad63`，报告 SHA-256 为 `9ad5bacad654f05773098b7f54e1c61e7efc1a2406e54aa0a34e625449403366`。文稿一致性记录 `PASS_LIMITED_SCIENTIFIC_TEXT_CONSISTENCY` 在 review tip `b48066cba0bf4cd308f2f75b1134c12f85c576ef`；只更新状态和引用，保留原有数值与限制。

## 聚类与外部评价

在冻结的共同聚类输入中，两种方法均运行五个预设随机种子，全部 10 个核心运行成功；五项 CAdir 诊断也成功，均无重试。两种方法均在同一 1,641 个有参考标签的细胞上计算 ARI 和 NMImax。另有 15 个通过共同 QC、但无参考标签的细胞保留在无监督聚类中，未进入外部指标；聚类输入共 1,656 个细胞。

CAdir 的 ARI 中位数为 0.291506（IQR 0.004115，范围 0.288542–0.294305），基线为 0.269345（IQR 0.000716，范围 0.266975–0.269799）。NMImax 方向相反：CAdir 中位数为 0.343414（IQR 0.002919，范围 0.335759–0.346271），基线为 0.356464（IQR 0.002364，范围 0.356192–0.359383）。因此，这组结果在 ARI 与 NMImax 上给出不同方向，不能概括为 CAdir 全面优于基线。

CAdir 推断簇数中位数为 10（范围 9–11）；基线五次均为 7 个簇。参数没有根据参考标签分数调节。五个种子刻画计算运行对随机初始化的变化，不是五个生物学重复。ARI 使用冻结的组合定义；NMImax 为 `MI / max(Hpredicted, Hreference)`，熵使用自然对数。逐种子数值见正式 `all-seed-results.tsv`。

## 队列、图表与资源说明

共同 QC 保留 1,656 个细胞、筛除 264 个；筛选没有依赖标签。固定的示例种子为 2358，两种方法的计数图和参考类别内占比图按预设选择，不按得分挑选。参考标签是发布的 broad 免疫表型候选，不等同于功能谱系真值，也不把预测簇重新命名为参考类别。

资源图报告各方法预先界定的核心阶段耗时：CAdir 的 CA+split-merge 中位数为 13.321 秒，基线 PCA+rank-SNN+Louvain 为 5.331 秒；序列化和基因排名不在相应核心计时内。不同方法的计时阶段不完全相同，因此不将其解释为全流程速度结论。峰值 RSS 为 50 ms 采样，可能漏掉瞬时峰值；进程 HWM 还包括启动和输入加载，本稿不据此主张内存优势。

实际展示输出包括八组 PNG/PDF 图表及配套 TSV；具体用途、参考范围和解释限制见正式目录中的 `逐图说明.md`。所有图表均只读取冻结分区、指标和锁表，不重新计算降维、聚类或 ARI/NMI。

## 适用范围

这是单研究的描述性比较。donor/Rep 信息未知，不能据此作跨供者或批次推断；也不声称重现原文的 1,656 细胞队列。C04 新数据范围仅按独立设计审查已接受的限定范围描述，仍不声称原论文绝未在未核来源中使用 GSE81682。该结果复验属于限定范围的科学结果接受，不等同于课程整体验收；Mac 看板和用户本机完整备份仍未同步/核验。

## 结果来源

- 汇总：`/workspace/hsc-fair-experiment-data-20261026/formal/6cc7b3d-20261027-attempt-01/summary.json`，SHA-256 `6d3e2675b906741e73e9d7d6541e814ca8a1815a15ba501968a01f0573602ced`。
- 逐种子数据：`/workspace/hsc-fair-experiment-data-20261026/formal/6cc7b3d-20261027-attempt-01/all-seed-results.tsv`，SHA-256 `548dda19dde7a6c695a348dfd399f543517d86d5a144268029d80a087f3bccd3`。
- 运行收据：`/workspace/hsc-fair-experiment-data-20261026/formal/6cc7b3d-20261027-attempt-01/attempt-receipts.json`，SHA-256 `4e56cac65d1f97b89efe61d3c3e4968eaa4ecd67f0b619295ba720f889c0dab2`。
- 展示来源与图注：`/workspace/hsc-fair-experiment-data-20261026/presentation/6cc7b3d-20261027-attempt-01/presentation-inputs.json`、`presentation-status.json` 与 `逐图说明.md`。展示状态文件明确写明待独立结果复验。
