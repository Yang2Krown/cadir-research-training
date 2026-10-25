# 验收交付入口

本目录只新增验收材料，保留当前分支和基线，不覆盖原 scripts/config/results/figures/latest 或任何历史运行。未重新运行HVG、CA、CAdir，未调参或引入新数据；只在已保存分配上重建GOA证据。

先阅读 [中文结果解读报告 HTML](report/结果解读报告.html)（图像已内嵌，可离线阅读），也提供 [Markdown](report/结果解读报告.md)。关键文件：

- `freeze/baseline_manifest.json`：输入、代码、配置、所有旧运行的路径/大小/SHA256与代码状态。
- `freeze/baseline_preservation_check.json`：冻结的240个既有文件是否保持不变。
- `tables/counts_7x8.tsv`、`fraction_within_cluster.tsv`、`fraction_within_reference.tsv`：完整计数与两种归一化。
- `figures/confusion_within_cluster.png/.pdf`、`confusion_within_reference.png/.pdf`：中文热图。
- `tables/cluster_composition.tsv`、`reference_distribution.tsv`：簇组成和各参考类别拆分情况。
- `annotation/annotation_decisions.tsv`、`goa_all.tsv`、`support_genes_long.tsv`：原预测、显著性、支持基因；不使用参考标签生成注释。
- `annotation/schwalie_resource_records.tsv`：文献命名集合的原始资源记录，保留组织、PMID与文章名。
- `tables/figure2_comparison.tsv`：逐项配置、证据、影响边界；`source_check/marker_search.json`：一次有范围的来源核查。
- `report/GIT_FILES.txt`：建议提交Git的精确路径，未执行git add/commit/push。
- `report/external_artifacts.json`：未入包的数据与大型RDS的原路径和哈希。

复核当前保留云环境中的验收材料（不会重新聚类）：

```bash
bash /workspace/cadir-research-training/cases/tabula_muris_limb/acceptance/2026-10-25/scripts/review_only.sh
```

上述脚本只重新生成本验收目录中的表、图、报告及固定分配GOA，不重新检查网络来源；本轮两次HTTP核查结果已保存。需要保留当前R环境以及基线CAdir RDS，包中不包含这些大型制品。代码的Python图表依赖版本在 `freeze/review_software.json`，R分析版本在 `annotation/sessionInfo.txt`。

仅阅读HTML、表和图不需要原始RDS。只重画混淆矩阵可运行 `scripts/cluster_review.py`，使用包中 `case/results/cell_clusters.tsv`；重建GOA需从外部制品索引找到保存的RDS与CAdir环境。冻结检查使用原云端绝对路径，脱离该环境时不能冒充已核验这些文件。

基线完整实验入口仍是原 `case/scripts/rerun.sh`，它会重新执行完整实验，**本轮没有调用**。它依赖 `/workspace/cadir-env` 和原始RDS，不是从零安装脚本。两次同种子一致仅证明可复跑，未进行多种子稳健性实验。

压缩包排除原始表达数据、所有中间RDS/RDA、运行库、缓存和Git目录；保留基线小型成果、关键历史日志、当前验收成果与来源。原始数据与两次成功运行均留在原处。本报告尚不构成严格Figure 2复现或独立生物学验证。
