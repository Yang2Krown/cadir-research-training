# Tabula Muris Limb Muscle：首轮真实数据案例

当前状态：**尚未完成真实数据运行**。已实际完成资源检查、旧环境恢复诊断、作者脚本核对、独立分支与运行代码整理；正式数据和指定 Docker 环境均有阻塞。

本案例位于分支 `case/tabula-muris-limb-first-run`。本目录中的 `runs/` 每次执行创建独立目录，失败记录不覆盖。`latest-environment.json` 和 `latest-case.json` 是入口索引；详细结论见 [reports/first-run.md](reports/first-run.md)。

| 层次 | 本次证据与结论 |
| --- | --- |
| 指定 Docker 环境恢复检查 | 未通过：`/workspace/.cadir-setup` 缺失，本地 Docker 镜像列表为空 |
| 旧 Conda 环境诊断 | 已运行并通过合成检查；只能证明旧环境恢复可用，不能替代上面的验收 |
| RDS 完整性、内容审计 | 尚未完成：下载工具拒绝超过 32 MiB 的附件，原 RDS 为 43,383,527 字节 |
| 单案例 CA / CAdir / Association Plot / ARI / NMI | 未运行；没有真实数据结果或指标 |
| 论文结果复现 | 未建立；另有作者数据文件名、marker 扩充及 CA 后端差异需要核对 |

## 恢复输入和环境

需恢复包含 `START_SKILL.md`、`SOFTWARE.md`、`run-r.sh` 和安装说明的 `/workspace/.cadir-setup`，按其来源恢复指定 Docker 镜像与包目录。没有这些材料时，不把旧 Conda 安装替换为指定环境。本案例脚本不会安装或升级包。

RDS 单文件超过工具传输上限，需先在本机拆分，上传各段后在云端合并。例如 Mac：

```bash
split -b 24m "/原文件路径/tabula_muris_limb_preproc.rds" ~/Desktop/limb_part_
```

云端已下载各段后，按 `aa`、`ab` 的顺序执行（将下面路径替换成实际云端路径）：

```bash
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/assemble_input.py \
  /workspace/attachments/实际目录/limb_part_aa \
  /workspace/attachments/实际目录/limb_part_ab
```

合并器只接受精确的字节数与 SHA256；失败时保留合并文件与 manifest，不覆盖不同的现有文件。默认合并到研究仓库的 `data/`，该目录已加入 Git 忽略。RDS 不重新压缩、不修改内容。

## 复跑

恢复目标环境与数据后执行：

```bash
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/check_environment.py
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/run_case.py --audit-only
python /workspace/cadir-research-training/cases/tabula_muris_limb/scripts/run_case.py
```

核对每个命令的退出码与该次 `status.json`。环境检查调用任务指定的 `/workspace/.cadir-setup/run-r.sh Rscript /setup/smoke-test.R`。它不会自动使用 `/workspace/cadir-env/activate.sh`。

如输入已存在于另一云端路径，可使用 `--data /实际路径/tabula_muris_limb_preproc.rds`。只有通过完整性检查且目标设置存在后，才会复制仓库外的输入到仓库 `data/`，在容器配置中映射到 `/repo/data/`。宿主脚本/输出参数也转换成 `/repo/...`；不假定 Docker 可见宿主 `/workspace` 或本机 `/Volumes`。

如取得作者用于 Figure 2 的 marker CSV，可加 `--marker-csv /实际路径/tabula_muris_marker_genes.csv`，要求有 `gene` 列；记录其哈希。没有该文件时只使用 HVG，并在 `paper_differences.txt` 中记录未复现 marker 扩充。

配置为 [config/case.json](config/case.json)。固定种子 2358，RNG 为 Mersenne-Twister / Inversion / Rejection，CA 与 CAdir 开始前分别重置。读取现有 `logcounts`；不重新 QC、不去双细胞、不重新归一化、不为满足 1882 个细胞而筛选或补齐。`1882` 只是比较目标，不是调整数据的指令。非 SCE、缺少 logcounts、无效表达矩阵、重复 ID 或非 Limb_Muscle 组织会停止，保留审计文件。

## 运行成功后才会产生的真实结果

`pipeline.R` 编排对象审计、`modelGeneVar`、`getTopHVGs(n=6000,var.threshold=NULL)`、CA、CAdir、基因排序、Association Plot 和单独的预测注释步骤。主要输出为：

- `data_audit.json`、对象结构、基因/细胞元数据与参考标签分布。
- `gene_variance.tsv`、HVG 与实际使用基因清单、`selection.json`。
- `cell_clusters.tsv`、`gene_clusters.tsv`（未分配的基因保留 NA）、`cluster_sizes.tsv`、共聚类基因排名与 split/merge 历史。
- CA 坐标表、`ca_clusters.png`、`association_plots.png/.pdf`、供复查的 CA/CAdir RDS（RDS 被 Git 忽略）。
- 有原始 `cell_ontology_class` 且至少两个有效类别时的 `metrics.json`、列联表；排除缺失标签并记录评价样本数。预测注释单独输出，不作为参考标签。
- `sessionInfo.txt`、实际包版本、实际 CAdir 参数、阶段耗时、R 进程峰值内存和日志。

全程峰值来自容器内部 R 的 `/proc/self/status` VmHWM；阶段 RSS 每 50 ms 采样，只报告采样峰值，可能漏掉很短的瞬时峰。Docker 启动器子进程的内存另记，不能冒充 R 的内存。上述均是单次工程诊断，不是性能基准。

本轮 Python / Shell / JSON 已作静态检查；**R 流程尚未在指定 Docker 环境执行或验证**。恢复后仍需根据真实数据和目标 APL 接口排查运行错误，不能把已有脚本当作已成功案例。

## 来源与保留范围

作者脚本、提交、精确链接和 SHA256 在 [evidence/source_manifest.json](evidence/source_manifest.json)。上游源码保留在 `/workspace/cadir-env/sources/`，没有修改算法源码；本仓库只新增本案例的编排代码与小型证据。CAdir/APL/CAbiNet 的 DESCRIPTION 声明 GPL >= 3，已有许可证随上游 checkout 保留。CAdir_results 根目录未找到许可证，不自行赋予其研究材料许可证。

大数据、序列化结果、运行库和安装缓存都在 Git 之外；未推送仓库，未购买资源，未运行全量基准。
