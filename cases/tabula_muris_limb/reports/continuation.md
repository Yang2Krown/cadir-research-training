# 继续执行结果：Tabula Muris Limb Muscle

日期：2026-10-25，Asia/Shanghai；机器日志为 UTC。

**环境检查通过，单案例运行成功，严格论文结果复现尚未建立。** 数据与环境阻塞按用户继续执行说明解除；保留原分支、前轮脚本和全部失败证据，未重置工作区或重新安装环境。

## 数据完整性与内容

分片按 part01、part02 二进制拼接。每片及最终文件均匹配清单：

| 文件 | 字节数 | SHA256 |
| --- | ---: | --- |
| part01 | 25165824 | 410503d2dcbf11b3a1d01a3971cbd64e33e244d5f659e0c8dfd53a18ba739fde |
| part02 | 18217703 | 6523a4aadfb9e11c877eff817f46410e1c8d474bca1d3160673e622a2ed9c53e |
| 合并 RDS | 43383527 | af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b |

合并 manifest 为 `evidence/assembly-*.json`。运行后重新校验输入，字节数和哈希未改变，见 `evidence/postrun-input-integrity.json`。

实际为 **SingleCellExperiment，13204 基因 × 1882 细胞**。counts 和 logcounts 均为 dgCMatrix，每个有 4,312,220 个非零条目。基因 ID 为小鼠符号，基因/细胞 ID 均唯一。1882 个细胞全部来自 Limb_Muscle；已有 size factors、QC、discard、scDblFinder、PCA、UMAP。

10,000 个确定性网格条目的 logcounts 与 `log2(counts/已有sizeFactor+1)` 最大绝对差为 1.77635683940025e-15，支持已有对数归一化。没有修改 assay、重新归一化或重新 QC。discard 全为 FALSE；已有双细胞标记为 55 doublet、1827 singlet，全部按原输入保留。

参考字段为原始 `cell_ontology_class`，1882 个均非缺失，共 8 类：B cell 63、endothelial cell 206、lymphocyte 59、macrophage 73、mesenchymal stem cell 495、skeletal muscle satellite cell 534、skeletal muscle satellite stem cell 419、T cell 33。没有使用 scDblFinder.cluster、CAdir 分组或预测注释作为参考。

## 环境与固定来源

重新读取 `/workspace/cadir-env/provenance.md`、`upstream-renv.lock` 及启动方式，核实 4 个固定源码 checkout 的提交、DESCRIPTION 哈希及已跟踪文件无改动。复验目录为 `runs/environment-lvscv1j4/`；核心加载成功，新合成检查退出码 0，约 12.54 秒、峰值 RSS 1,186,356 KiB。

| 项目 | 本次实际 | 作者锁或来源比较 |
| --- | --- | --- |
| R / Bioconductor | 4.4.1 / 3.19 | 一致；BiocVersion 3.19.1 |
| APL | 1.9.1 | 一致；d4d1f40d9ea9f1d9a95b224d45de843334cd617d |
| aricode | 1.0.3 | 一致 |
| CAbiNet | 0.99.2 | 一致；329c03298c5afc31a2b1fe3fa19b0fdd9f816d0b |
| CAdir | 0.0.99 | 版本相同，公开提交 de74a008dfcd0d4fa4f7f93c57aa346892a8d935；作者锁没有公开 SHA |
| SingleCellExperiment | 1.26.0 | 一致 |
| scran / scuttle | 1.32.0 / 1.14.0 | 一致 |
| scater | 1.32.1 | 锁为 1.32.0 |

CAdir_results 参考提交为 c15b49578bde38b42fd5db2c9830c10dd441ee4c。Figure 2、原始获取与预处理脚本哈希见 `evidence/source_manifest.json`。上游源码与已有许可证保留在 `/workspace/cadir-env/sources/`，未改算法。

没有完整恢复作者全部依赖：锁中 496 个包，85 个版本匹配、197 个版本不同、214 个未安装。逐包记录为 `evidence/author-lock-version-comparison.tsv`，实际安装清单随原始运行保留。许多缺失包属于本轮未执行的数据加载、基准或分析路径，不影响已成功的案例。matrixStats、aricode、ggplot2 报告由 R 4.4.3 构建，在当前 R 4.4.1 下实际加载和执行成功，警告原样保留。

资源为 CPU 配额 2 核、内存上限 8 GiB、无 swap。使用 Conda 的真实宿主路径，无 Docker 映射，也未使用 /Volumes。新版 Docker 路径缺失不再构成本轮阻塞。

## 实际参数与结果

现有 logcounts 上执行 `modelGeneVar`、`getTopHVGs(n=6000,var.threshold=NULL)`，得到恰好 6000 HVG。参考标签未参与特征选择、CA 或 CAdir。没有调整 1882 个细胞。CA 为 Pearson residuals、princ_coords=3、dims=30、top=6000、python=FALSE。

完整配置在 `results/config.json`：seed=2358；RNG 为 Mersenne-Twister/Inversion/Rejection；CA、CAdir、排序前分别重置。CAdir 使用 k=8、cutoff=55°、min_cells=20、method=random、apl_quant=0.99、counts=NULL、epochs=NULL、reps=NULL、max_iter=50、convergence_thr=0.001、init=kmeanspp、qcutoff=0.8、keep_log=TRUE、make_plots=TRUE、apl_cutoff_reps=100。

最终 **7 簇、1200 个共聚类基因**。导出表保留全部 6000 个输入基因，未分配的 4800 个记 NA。

| 簇 | 细胞 | 共聚类基因 | 自动预测标签 |
| --- | ---: | ---: | --- |
| cluster_1 | 940 | 45 | 未获显著标签，保留 cluster_1 |
| cluster_2 | 28 | 184 | Vascular_endothelial_cell |
| cluster_3 | 113 | 200 | B_cell |
| cluster_4 | 48 | 192 | T_cell |
| cluster_5 | 76 | 203 | Macrophage |
| cluster_6 | 490 | 106 | Schwalie_et_al.Nature.P1 |
| cluster_7 | 187 | 270 | Endothelial_cell |

按全部 1882 个原始标签评价，**ARI=0.669518704486352，NMI=0.741885423115482**。使用 aricode 1.0.3 的 clustComp，与作者脚本调用相同。自动预测标签另存，不替换评价参考。

注释使用固定 CAdir 内置 `cellmarker_v2`，即 CellMarker 2.0（Hu 等，DOI 10.1093/nar/gkac947），Mouse 子集 35,197 条记录，3366 个入选基因与资源有交集。实际集合导出到最终运行的 `annotation_cellmarker_mouse.tsv`，哈希见结果索引。GOA、cost=logpval、filter_literature=FALSE 及默认 alpha=0.05 与 Figure 2 一致。因此保留文献命名标签，不人工更名或声称预测已获生物学验证。

## 耗时、内存、结果核验

最终运行 `runs/case-ppkaow9s/` 退出码 0，总耗时 **31.322 秒**，R 进程峰值 RSS **2,274,360 KiB，约 2.17 GiB**。单次诊断包含加载、审计与输出，不作为方法性能基准。

| 阶段 | 秒 | 采样峰值 RSS（KiB） |
| --- | ---: | ---: |
| readRDS | 1.281 | 1086720 |
| 对象审计 | 2.380 | 1277324 |
| modelGeneVar | 0.237 | 1359128 |
| CA | 5.698 | 1856468 |
| CAdir | 3.056 | 2100704 |
| 排名、导出、绘图 | 4.757 | 2142404 |
| GOA 注释 | 1.054 | 2274304 |

阶段 RSS 每 50 ms 采样，可能漏掉短暂尖峰，表示该阶段进程总驻留内存，不是增量分配。全程峰值取 Linux VmHWM。阶段时间不含全部加载与中间写入，求和不必等于总耗时。

首次成功运行 `runs/case-5los7t_s/` 保留。修正参数日志展开整个 CA 对象和 PNG 透明空白后进行了最终复跑，算法与配置不变。核验脚本实际读取最终 RDS 和导出表，检查维度、ID、细胞分配、簇规模、共聚类基因及注释分区，重算 ARI/NMI，确认两次细胞和基因分配逐项一致。见 `results/verification.json`。PNG 已打开检查，PDF 和表格完整存在。

## 严格论文复现的边界

本轮匹配论文页所述的 1882 细胞、6000 HVG、30 维、初始 k=8、55°，并完成当前真实案例最小流程；以下差距仍存在：

1. Figure 2 读取 `tabula_muris_preprocessed_filtered.rds`，附件名称不同。对象证据、组织与细胞数相符，但未证明两份对象及完整预处理完全相同。
2. Figure 2 在 HVG 外还加入 `tabula_muris_marker_genes.csv`。核对作者整个固定提交文件树与已提供材料后未找到该 CSV，见 `evidence/marker_resource_search.json`。本轮明确运行 HVG-only 变体，没有虚构列表或静默省略。
3. 本轮为 CPU R CA，Figure 2 为 python=TRUE；未配置或验证 Python/PyTorch 后端，未做后端数值等同性实验。
4. CAdir 公共提交无法与作者本地路径建立 SHA 等同性，依赖环境也未逐项完整还原。
5. 自动注释仍有未命名簇和文献命名标签，未人工生物学审阅。没有完全等价输入、配置和作者数值目标，不能声称复现论文 ARI/NMI 或完整 Figure 2。

这些是与严格复现的剩余差距，不再阻塞已完成案例。未运行全量基准、其他真实案例或方法改进，未购买资源。

## 输出与复跑

小型成果在 `results/` 与 `figures/`。完整输出、RDS 与全部失败记录在 `runs/`；它们和输入、运行库在 Git 之外。脚本、配置、来源、小型日志、表格和图表在当前独立分支整理，未推送。

```bash
bash /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/rerun.sh
```

该命令复用保留安装，不下载全量数据或重新归一化。需保留原始 RDS 和 `/workspace/cadir-env`；具体输出链接和分步说明见案例 README。
