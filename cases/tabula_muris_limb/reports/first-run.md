# 首轮执行记录

记录时间：2026-10-25，Asia/Shanghai。机器日志使用 UTC，并保留原始时间戳。

**结论：指定环境验收受阻，真实案例未运行，论文复现未完成。** 不能用旧环境合成检查通过替代其中任何一项。

## 已实际执行

1. 等待云环境启动，读取云环境技能、网络与 Docker 说明，核实网络策略；GitHub 文本访问通过。没有关闭 TLS 或修改网络策略。
2. 搜索本轮要求的设置目录、文档、数据与本机路径。`/workspace/.cadir-setup`、`/setup`、本机 `/Users/...` 与 `/Volumes` 都不存在。用户补传的两份文本已下载、读取并保存在 `evidence/task.md` 与 `evidence/paper_page23.txt`。
3. 在附件补传前，发现并复用了旧环境，运行 `/workspace/cadir-env/run-smoke.py`，通过全部原有合成检查。读到附件明确“不使用旧环境”后，停止使用该环境作为正式入口，将运行入口改为强制要求指定 Docker 设置。
4. 获得 Docker 本地服务的只读检查权限，确认服务可用、镜像数为 0。最初沙箱内 socket 检查失败，随后获准的只读检查成功；这不属于自动审批拒绝。没有启动新 daemon 或重建来源不明的镜像。
5. 保留旧作者算法 checkout，取得 CAdir_results 的稀疏文本 checkout（约 1.8 MiB，未下载其全量数据），检查论文对应 Figure 2 和原始/预处理代码，并记录提交和脚本哈希。
6. 创建分支 `case/tabula-muris-limb-first-run`，编写完整案例编排、环境检查、输入合并与校验脚本，补充数据忽略规则，实际运行正式预检并保存失败状态。

## 资源与版本

本实例可见 3 个 CPU，但 `cpu.max=200000 100000`，实际配额为 **2 核**；`memory.max=8589934592`，即 **8 GiB**；无 swap。旧环境文档的 4 核 / 32 GiB 不能沿用。本轮 `df` 的工作区视图可用约 29.83 GiB，不能将其等同于额外平台配额保证。原始输出为 `evidence/resources.txt`。

| 项目 | 附件指定的 Docker 环境 | 本次实际恢复的旧环境 |
| --- | --- | --- |
| R | 4.4.1 | 4.4.1 |
| Bioconductor | 3.19 | BiocVersion 3.19.1 |
| APL | 1.2.0（cabinet-freeze） | **1.9.1** |
| aricode | 1.1.0 | **1.0.3** |
| CAbiNet | 0.99.2 | 0.99.2 |
| CAdir | 0.0.99 | 0.0.99 |
| SingleCellExperiment | 1.26.0 | 1.26.0 |
| scran | 1.32.0 | 1.32.0 |
| scater | 1.32.1 | 1.32.1 |
| scuttle | 1.14.0 | 1.14.0 |

旧环境的 org.Mm.eg.db 3.19.1 与 AnnotationDbi 1.66.0 可加载。这不证明缺失 Docker 镜像内拥有这些资源，也不证明已完成真实细胞注释。目标 SOFTWARE.md 缺失，无法核对 APL cabinet-freeze 精确来源与私有包目录。

旧环境合成检查使用种子 2358、120 基因 × 60 细胞，包含归一化、CA、CAdir、RDS 往返、评价包调用和 PNG 输出；结果退出码 0，耗时 **12.68 秒**，整个 Rscript 峰值 RSS **1,186,356 KiB（约 1.13 GiB）**。PNG 已打开检查。原始目录为 `/workspace/cadir-env/runs/smoke-6w7818zg`；日志、包清单、sessionInfo、资源与 PNG 已复制为 `evidence/legacy-smoke-*`。合成数据的自比较不构成真实数据准确率结果。

## 数据阻塞

指定附件 `file_00000000be4881f59168d31b9c451dcb` 的下载返回原始错误：

```text
file exceeds the executor transfer limit of 32 MiB
```

预期大小 43,383,527 字节，预期 SHA256：

```text
af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b
```

未获取到文件字节，因此未声称校验匹配，未 readRDS，不能报告对象类型、实际细胞/基因数、归一化历史或参考标签。文件名不能证明内容。需将文件分为小于 32 MiB 的片段上传，再按原顺序合并验证；无需修改数据或购买资源。

## 作者脚本与论文差异

- CAdir 实际参考提交：`de74a008dfcd0d4fa4f7f93c57aa346892a8d935`。
- CAdir_results 实际参考提交：`c15b49578bde38b42fd5db2c9830c10dd441ee4c`。
- 本轮核实两者远端 HEAD 与上述提交一致。精确脚本链接与哈希在 `evidence/source_manifest.json`，远端输出在 `evidence/*remote-head.txt`。

对应的 `results/figure2.qmd` 读取的是 `data/real/discussed/preprocessed/tabula_muris_preprocessed_filtered.rds`，不是附件同名文件。其 `modelGeneVar(logcounts)` / `getTopHVGs(n=6000,var.threshold=NULL)` 之后，还将 `tabula_muris_marker_genes.csv` 中已表达的 marker 与 HVG 合并去重，所以实际使用基因数可能超过 6000。用户提供的论文页描述为 1882 细胞 × 6000 HVG，CA 保留 30 维，k=8、55°，使用 CellMarker 2.0 注释。

该脚本还明确设置 seed=2358、method=random、apl_quant=0.99、counts=NULL、min_cells=20、reps=NULL、make_plots=TRUE、qcutoff=0.8、convergence_thr=0.001；本案例配置保留这些参数，并固定当前 CAdir 的默认 max_iter=50、init=kmeanspp、keep_log=TRUE。CA 采用 Pearson residuals、princ_coords=3。

本轮准备的 CA 路径为 `python=FALSE`（CPU R）；Figure 2 为 `python=TRUE`，因此即使将来成功运行，也必须记录后端差异。缺失 marker CSV 时的 HVG-only 路径是明确记录的最小案例变体，不能据此声称完整复现 Figure 2。

原始数据脚本 `download_raw_data/tabula_muris/tabula_muris_limb_save_RAW_data.R` 使用 TabulaMurisData 的 SmartSeq2，筛选 `tissue == "Limb_Muscle"` 并删除缺失 `cell_ontology_class` 的细胞。通用预处理脚本包括零表达基因过滤、细胞 QC、表达比例过滤、scran size factors、logNormCounts、PCA/UMAP 和 scDblFinder 评分；最后并未启用删除 doublet 的那行。旧提交脚本中的 Limb 设置被注释，默认是完整 Tabula Muris；它不足以证明附件与 Figure 2 的 filtered 文件逐项一致。本轮没有运行原始下载或重新预处理。

## 验证范围与下一步所需条件

Python 脚本语法、JSON 解析和 Shell 语法检查已通过。环境检查器实际返回 `BLOCKED_SETUP_MISSING`；正式案例预检实际返回 `BLOCKED_INPUT_MISSING`。脚本保留这些真实失败目录。R 编排脚本因目标环境缺失而尚未执行，不能称为已验证的端到端流程。

解除阻塞需要：（1）可传入云端的同一份 RDS 字节；（2）本轮指定的新版 Docker 设置目录、来源说明与可恢复镜像/安装材料。marker CSV 则影响与作者 Figure 2 的一致性，但不阻止明确标记差异的最小 HVG 案例。恢复后先完整性与对象审计，再按真实内容运行，不调整细胞数以凑论文目标。

当前没有真实聚类、共聚类基因表、Association Plot 或 ARI/NMI，因而不能比较论文定量结果，也不能判断该真实数据案例是否会触及 8 GiB 内存上限。复跑命令和成功后输出清单见案例 README。
