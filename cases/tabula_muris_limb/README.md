# Tabula Muris Limb Muscle：真实数据案例

**当前成果：LM Fig3/S1九项分析及独立复验已完成，R3已通过最终独立复验。** [九图交付](fig3_completion/README.md) · [独立报告](../../reviews/lm-fig3-20261027/report.md) · [阶段结论](../../project-control/LM首案例图表补齐阶段结论-2026-10-27.md)。

以下保留首轮案例与R3修复的过程说明。 原始输入、细胞指标及基因分配已有独立审查支持；新检出入口和验证器已按审查意见修复。当前环境两次新鲜运行的完整排序与冻结基线一致；补件后已用两端实际 CA/未排序对象重现旧评审差异，并由八个 CA 轴的符号双向反事实复现全部排名变化。见[最新 R3 诊断](review_fixes/2026-10-26-r3/README.md)与[历史修复勘误](review_fixes/2026-10-25/README.md)。完整排名等价仅在固定 CA 基底或已验证对齐条件内成立，不能只凭相同 seed 推论跨任意基底等价。作者 `figure2.qmd` 对应正式论文 **Fig 3 Limb Muscle 案例**；严格论文复现尚未建立。

历史分支 `case/tabula-muris-limb-first-run` 保留；本轮在独立修复 worktree 和分支执行。[继续执行说明](evidence/continuation-task.md) 授权使用已恢复 Conda，修正此前 Docker 限制。前轮报告、脚本副本、失败目录均保留，见 [首轮记录](reports/first-run.md) 与 `evidence/pre-continuation-scripts/`。当前详细结论见 [继续执行报告](reports/continuation.md)。

| 项目 | 实际结果 |
| --- | --- |
| 原始 RDS | 43,383,527 字节与 SHA256 均匹配；13204 基因 × 1882 细胞 |
| 分析输入 | 6000 HVG × 1882 细胞；保留现有 logcounts，未重复归一化 |
| CA / CAdir | 30 维、初始 k=8、55°、seed=2358，最终 7 簇 |
| 共聚类基因 | 1200 个被分配；4800 个未分配，在表中保留 NA |
| 评价 | 原始 cell_ontology_class，1882 个完整标签；ARI 0.669518704486352、NMI（max 熵归一化）0.741885423115482 |
| 自动注释 | CellMarker 2.0 GOA 执行成功；1 个簇未获显著标签，预测名称未人工校正 |
| 最终主流程资源 | 31.32 秒；R 峰值 RSS 2,274,360 KiB，约 2.17 GiB |
| 重复运行核验 | 历史两次分配一致为原实施记录；本轮新鲜复跑及加强验证器结果见修复记录 |

## 查看成果

- [Association Plot PNG](figures/association_plots.png) / [PDF](figures/association_plots.pdf)、[CA 聚类图](figures/ca_clusters.png)、[完整 Association Plot 图注](figures/association_plots.caption.md)。
- [细胞聚类](results/cell_clusters.tsv)、[基因共聚类](results/gene_clusters.tsv)、[基因排名](results/coclustered_gene_ranks.tsv)、[簇规模](results/cluster_sizes.tsv)。
- [预测注释](results/cluster_annotations.tsv)、[评价指标](results/metrics.json)、[参考标签列联表](results/cluster_reference_contingency.tsv)。
- [对象审计](results/data_audit.json)、[配置](results/config.json)、[实际参数](results/effective_cadir_parameters.txt)、[软件版本](results/sessionInfo.txt)、[阶段资源](results/stage_times_seconds.json)、[核验](results/verification.json)。
- [完整原始输出索引及 SHA256](results/result_index.json)。

`results/` 和原有 `figures/` 是冻结的历史交付物，不由新入口覆盖。下列原始 runs 路径是历史记录，不保证在其他会话存在。历史完整最终运行在 `runs/case-ppkaow9s/`，包含 CA/CAdir RDS、全部坐标、基因方差、元数据、CellMarker 基因集、内存采样与日志。首次成功运行 `runs/case-5los7t_s/`、独立审计 `runs/case-hrj6sx0g/` 和所有失败目录也保留。

原始数据为 `/workspace/cadir-research-training/data/tabula_muris_limb_preproc.rds`。输入、原始 runs、RDS、运行库和缓存均被 Git 排除；未推送或购买资源。

## 复跑

保留 `/workspace/cadir-env` 的运行库、固定源码与启动脚本后，从新检出目录运行（以实际路径替换示例）：

```bash
case_dir=/workspace/cadir-stage1-fix/cases/tabula_muris_limb
output_dir=/workspace/my-cadir-rerun
bash "$case_dir/scripts/rerun.sh" \
  --data /workspace/cadir-handover/input/tabula_muris_limb_preproc.rds \
  --output-root "$output_dir"
```

一条命令依次检查环境、运行案例、核验结果并收集新成果。入口创建缺失的输出父目录。所有新状态指针（`latest-environment.json`、`latest-case.json`）、每次独立运行目录和 `deliverables/results/`、`deliverables/figures/` 都写在 `--output-root` 下；省略该选项时默认是案例 `runs/`。请使用专用目录，不将其指向冻结案例根目录。历史案例根目录里的 latest 文件只作历史记录，已不作为新运行的前置依据。

这不是从零安装器；只验证已有 Conda 安装可用，未证明空机器完整恢复作者环境。也可分步运行，所有步骤使用同一输出根：

```bash
python "$case_dir/scripts/check_environment.py" --output-root "$output_dir"
python "$case_dir/scripts/run_case.py" --data /实际路径/input.rds --output-root "$output_dir"
# 从 output_dir/latest-case.json 取 run_directory，替换下行 NEW_RUN_DIR。
bash "$case_dir/scripts/run-r.sh" "$case_dir/scripts/verify_results.R" NEW_RUN_DIR
python "$case_dir/scripts/collect_outputs.py" --output-root "$output_dir"
```

`run_case.py --audit-only` 仅审计输入，`rerun.sh --audit-only` 审计完成后即退出，不尝试收集完整成果。验证器逐基因比较 cluster/NA、逐簇计数及排名 gene/cluster/Score/Rank/Row_num，Score 绝对容差为 `1e-10`；每次先写 RUNNING，错误时写 FAIL，避免误用旧 PASS。PASS 只表示该次表格与保存对象一致，不是独立科研评审，也不保证任意环境重现历史排序。

配置为 [config/case.json](config/case.json)。如取得作者 marker CSV，可使用 `--marker-csv /实际云端路径/tabula_muris_marker_genes.csv`；需有 `gene` 列，记录文件哈希，并作为另一轮明确参数的运行。本轮没有虚构列表。

## 与严格论文复现的区别

作者 `figure2.qmd`（对应正式论文 Fig 3 案例）使用另一名称的 filtered RDS，并在 6000 HVG 外加入 marker CSV 中的已表达基因；该 CSV 未在核对过的作者提交或本轮材料中找到。本轮恰好使用 6000 HVG。`python=FALSE` 与作者 TRUE 是参数值差异；固定 APL 的当前 30 维路径对两值都执行 R/irlba，不能据此推断后端不同。完整输入、扩充基因集、作者私有 CAdir 及完整环境的等价性仍未证明。正式论文 Fig 2 是方法流程概览。

APL 1.9.1、aricode 1.0.3 与作者锁文件一致；scater 1.32.1 对照锁文件 1.32.0 有补丁差异。CAdir 0.0.99 使用另行固定的公开提交；作者锁指向本地目录，没有公开 SHA。完整依赖锁未全部恢复。见 [来源与脚本哈希](evidence/source_manifest.json)、[固定源码复验](evidence/continuation-sources-verification.json)、[逐包版本比较](evidence/author-lock-version-comparison.tsv)。

参考标签仅在聚类结束后用于评价；自动注释不作为参考。没有额外删除输入中标记的 55 个 doublet，没有改变已有 QC 或归一化。未运行全量基准、其他真实案例或方法改进，不据此声称算法优越。
