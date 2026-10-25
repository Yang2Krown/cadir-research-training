# GitHub 同步说明

状态保持为：**真实案例运行与验收完成，严格论文复现尚未完成**。没有改变指标、聚类分配或参数。ARI 0.669518704486352、NMI 0.741885423115482；两次同种子一致只证明本环境可复跑，不是多种子稳健性或独立生物学验证。

本轮在原 `case/tabula-muris-limb-first-run` 分支提交并推送自己的脚本、配置、轻量结果、主要图、关键日志、中文报告和来源记录；不合并 main，不强制推送。先前冻结清单中的 HEAD、未提交代码状态以及旧报告反映各自记录时点，不被重写为本轮提交状态。

## 阅读入口

- [案例运行与复跑说明](../README.md)。
- [中文验收报告](../acceptance/2026-10-25/report/结果解读报告.md)；HTML 是离线阅读版，GitHub 上优先读 Markdown。
- [7簇×8类计数](../acceptance/2026-10-25/tables/counts_7x8.tsv)、[按簇归一化热图](../acceptance/2026-10-25/figures/confusion_within_cluster.png)、[按参考类别归一化热图](../acceptance/2026-10-25/figures/confusion_within_reference.png)。
- [细胞分配](../results/cell_clusters.tsv)、[共聚类基因](../results/gene_clusters.tsv)、[评价指标](../results/metrics.json)。
- [注释显著性与支持基因](../acceptance/2026-10-25/annotation/annotation_decisions.tsv)、[Figure 2 流程对照](../acceptance/2026-10-25/tables/figure2_comparison.tsv)。
- [本次实际提交文件清单](COMMITTED_FILES.txt)；它取代旧验收包 `report/GIT_FILES.txt` 的提交建议，后者作为历史记录保留。本次范围明确排除上游源码全文和含源码 diff 的 API 原响应。

## 不进入此次 Git 提交的制品

原始表达数据、两个成功运行中的大型 RDS、完整原始运行目录、运行库、安装缓存和上游源码全文均保留原处，没有删除或移动。[外部资源索引](external_resources.json) 和原 [冻结清单](../acceptance/2026-10-25/freeze/baseline_manifest.json) 记录路径、字节数、SHA256及固定来源。

### 原始数据

云端路径：`/workspace/cadir-research-training/data/tabula_muris_limb_preproc.rds`，43,383,527字节，SHA256：

```text
af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b
```

获取方式是由数据保管人提供原任务已使用的文件，或下列两个原始分片，按 part01、part02 二进制拼接。**没有核实过的公开同哈希下载地址，GitHub 不托管该 RDS。**

| 分片 | 字节数 | SHA256 |
| --- | ---: | --- |
| tabula_muris_limb_preproc.rds.part01.bin | 25165824 | 410503d2dcbf11b3a1d01a3971cbd64e33e244d5f659e0c8dfd53a18ba739fde |
| tabula_muris_limb_preproc.rds.part02.bin | 18217703 | 6523a4aadfb9e11c877eff817f46410e1c8d474bca1d3160673e622a2ed9c53e |

用 [assemble_input.py](../scripts/assemble_input.py) 合并并检查最终哈希，不把两段分别当 RDS 读取。作者 TabulaMurisData 原始下载脚本可作来源参考，但未证明重新预处理能产生完全相同的输入字节，不能冒充本文件的替代下载。

### 大型中间结果与历史记录

最终成功运行：`/workspace/cadir-research-training/cases/tabula_muris_limb/runs/case-ppkaow9s/`；首次成功：同目录下 `case-5los7t_s/`。CA、CAdir、未排序对象及注释对象的 RDS 在这些目录，路径与哈希见外部资源索引。早期失败与审计目录也完整保留；Git 中提供 [关键历史日志副本](../acceptance/2026-10-25/freeze/history_logs/index.json)。

### 环境、缓存与上游代码

现有安装为 `/workspace/cadir-env/`，运行入口是本仓库 [run-r.sh](../scripts/run-r.sh)，依赖该环境的 `activate.sh`。R库、Conda环境和缓存不提交。参考 [Conda精确URL与校验清单](../acceptance/2026-10-25/freeze/conda-explicit-linux-64.txt)、[实际R包锁](../acceptance/2026-10-25/freeze/runtime-renv.lock)、[来源记录](../acceptance/2026-10-25/freeze/sources.json) 和 sessionInfo。它们是来源与版本证据；未把空机器上完整恢复环境当作已验证步骤。

上游代码按固定提交从作者仓库获取，原 checkout 在 `/workspace/cadir-env/sources/`。本地 `source_check/` 和 `evidence/` 中的完整上游文本副本被新增局部忽略规则排除；不删除它们。对应的作者仓库、固定提交、精确文件URL和SHA256在 `external_resources.json`，上游许可记录保留。旧报告提及“来源快照”时，指这些本地副本或原成果包；GitHub 读者请从固定URL获取并校验。

## 复跑与共享盘

当前云端保留输入和环境时：

```bash
bash /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/rerun.sh
```

只复核已有分配、不重跑完整实验：

```bash
bash /workspace/cadir-research-training/cases/tabula_muris_limb/acceptance/2026-10-25/scripts/review_only.sh
```

共享盘不是前置条件。上述命令依赖已保留的云端输入、RDS和运行环境；它们不从共享盘读取、不自动安装或购买资源。本轮同步没有调用完整实验入口。

## 原成果包

原包仍为 `/workspace/cadir-deliverables/tabula_muris_limb_acceptance_20261025.zip`，4,570,357字节（4.36 MiB），SHA256：

```text
6a0bbd76176bba85e9d5242bb032498f8a3ab87f4f2b32490b519130fef9798f
```

该包保持原样，用于本地备份；不入 Git。包内可含本地核查时保存的上游文本，和本次 Git 提交的范围不同。
