# Tabula Muris Limb Muscle：真实数据案例

**环境复验通过、单案例运行成功；严格论文 Figure 2 复现尚未建立。** 已完成数据完整性校验、对象审计、6000 HVG、30 维 CA、CAdir、Association Plot、结果表、ARI/NMI、CellMarker 2.0 预测注释及结果核验。

原分支 `case/tabula-muris-limb-first-run` 保留，未新建或重置工作区。[继续执行说明](evidence/continuation-task.md) 授权使用已恢复 Conda，修正此前 Docker 限制。前轮报告、脚本副本、失败目录均保留，见 [首轮记录](reports/first-run.md) 与 `evidence/pre-continuation-scripts/`。当前详细结论见 [继续执行报告](reports/continuation.md)。

| 项目 | 实际结果 |
| --- | --- |
| 原始 RDS | 43,383,527 字节与 SHA256 均匹配；13204 基因 × 1882 细胞 |
| 分析输入 | 6000 HVG × 1882 细胞；保留现有 logcounts，未重复归一化 |
| CA / CAdir | 30 维、初始 k=8、55°、seed=2358，最终 7 簇 |
| 共聚类基因 | 1200 个被分配；4800 个未分配，在表中保留 NA |
| 评价 | 原始 cell_ontology_class，1882 个完整标签；ARI 0.669518704486352、NMI 0.741885423115482 |
| 自动注释 | CellMarker 2.0 GOA 执行成功；1 个簇未获显著标签，预测名称未人工校正 |
| 最终主流程资源 | 31.32 秒；R 峰值 RSS 2,274,360 KiB，约 2.17 GiB |
| 重复运行核验 | 两次细胞与共聚类基因分配逐项一致；导出表与保存对象一致，重算 ARI/NMI 通过 |

## 查看成果

- [Association Plot PNG](figures/association_plots.png) / [PDF](figures/association_plots.pdf)、[CA 聚类图](figures/ca_clusters.png)。
- [细胞聚类](results/cell_clusters.tsv)、[基因共聚类](results/gene_clusters.tsv)、[基因排名](results/coclustered_gene_ranks.tsv)、[簇规模](results/cluster_sizes.tsv)。
- [预测注释](results/cluster_annotations.tsv)、[评价指标](results/metrics.json)、[参考标签列联表](results/cluster_reference_contingency.tsv)。
- [对象审计](results/data_audit.json)、[配置](results/config.json)、[实际参数](results/effective_cadir_parameters.txt)、[软件版本](results/sessionInfo.txt)、[阶段资源](results/stage_times_seconds.json)、[核验](results/verification.json)。
- [完整原始输出索引及 SHA256](results/result_index.json)。

`results/` 和 `figures/` 是小型交付物。完整最终运行在 `runs/case-ppkaow9s/`，包含 CA/CAdir RDS、全部坐标、基因方差、元数据、CellMarker 基因集、内存采样与日志。首次成功运行 `runs/case-5los7t_s/`、独立审计 `runs/case-hrj6sx0g/` 和所有失败目录也保留。

原始数据为 `/workspace/cadir-research-training/data/tabula_muris_limb_preproc.rds`。输入、原始 runs、RDS、运行库和缓存均被 Git 排除；未推送或购买资源。

## 复跑

保留当前输入与 Conda 安装时，一条命令依次复验环境、运行案例、核验结果、收集成果：

```bash
bash /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/rerun.sh
```

这不是从零安装器；需保留 `/workspace/cadir-env` 的运行库、固定源码与启动脚本。本轮验证的是已恢复安装可以使用，没有验证空机器完整恢复作者环境。

也可分步运行：

```bash
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/check_environment.py
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/run_case.py --audit-only
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/run_case.py
```

`run_case.py` 每次打印新的独立运行目录。对该路径执行 `scripts/verify_results.R`（通过 `bash scripts/run-r.sh` 启动），再执行 `scripts/collect_outputs.py` 即可更新成果入口。`latest-environment.json`、`latest-case.json` 与各次 `status.json` 是状态证据；不要只看旧图是否存在。

配置为 [config/case.json](config/case.json)。如取得作者 marker CSV，可使用 `--marker-csv /实际云端路径/tabula_muris_marker_genes.csv`；需有 `gene` 列，记录文件哈希，并作为另一轮明确参数的运行。本轮没有虚构列表。

## 与严格论文复现的区别

Figure 2 使用另一名称的 filtered RDS，并在 6000 HVG 外加入 marker CSV 中的已表达基因；该 CSV 未在核对过的作者提交或本轮材料中找到。本轮恰好使用 6000 HVG，且使用 `python=FALSE` 的 CPU R CA，作者脚本为 `python=TRUE`。因此虽匹配论文页中的细胞数、HVG 数、CA 维度、k 与角度，仍未证明完整输入、扩充基因集和后端等价。

APL 1.9.1、aricode 1.0.3 与作者锁文件一致；scater 1.32.1 对照锁文件 1.32.0 有补丁差异。CAdir 0.0.99 使用另行固定的公开提交；作者锁指向本地目录，没有公开 SHA。完整依赖锁未全部恢复。见 [来源与脚本哈希](evidence/source_manifest.json)、[固定源码复验](evidence/continuation-sources-verification.json)、[逐包版本比较](evidence/author-lock-version-comparison.tsv)。

参考标签仅在聚类结束后用于评价；自动注释不作为参考。没有额外删除输入中标记的 55 个 doublet，没有改变已有 QC 或归一化。未运行全量基准、其他真实案例或方法改进，不据此声称算法优越。
