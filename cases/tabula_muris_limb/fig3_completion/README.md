# Limb Muscle Fig3/S1 补齐（实施自检，待独立复验）

本轮只处理 DOI [10.1371/journal.pcbi.1014418](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014418) 的 Fig3 A–D 及直接关联的 S1 A–E。作者固定提交 `VingronLab/CAdir_results@c15b49578bde38b42fd5db2c9830c10dd441ee4c` 的 `results/figure2.qmd` 对应正式 **Fig3**；正式 Fig2 是方法示意图。旧 6000-HVG 单案例及已闭合的 R3 因果诊断保留，不重复该实验。

## 验收矩阵（运行前固定）

| 项目 | 原文/固定代码要求 | 旧版覆盖 | 本轮交付与严格等价条件 |
| --- | --- | --- | --- |
| 输入 | filtered RDS；6000 HVG 加 marker CSV 中已表达基因 | 已核对输入 SHA；6000 HVG-only | 保留原 logcounts、全1882细胞；权威 CSV/filtered 对象缺失时严格等价 BLOCKED |
| Fig3A | 7方向；GOA预测名称；每簇 Sα-score top5 | 数字簇 Association Plot、排名和另表预测 | 自动名称图、完整排名、top5、预测/原参考/cluster ID 映射，预测不手改 |
| Fig3B | B cell APL；Macrophage/T cell 与方向；主坐标 | 未完成对应图 | 按 cluster ID 与原参考映射选择；导出坐标和方向角；映射有歧义即报告 |
| Fig3C | Endothelial APL；Vascular endothelial 方向；主坐标 | 未完成对应图 | 原参考只有一个 endothelial 类时，用真实预测作候选并明示证据，不能伪造独立参考亚型 |
| Fig3D | 真实 split/merge 历史；中间节点自动注释及主坐标 APL | 保存历史表，未完整绘图 | 复用同一 CA 和 log；保存完整 log、节点/边表和真实历史图；不要求本次历史恰与论文相同 |
| S1A | 簇间方向角矩阵 | 未完成对应图 | 同一保存方向的数值表与热图 |
| S1B | 每簇 APL 与其他方向投影矩阵 | 未完成对应图 | 同一 CA/directions 的方向矩阵及数值投影 |
| S1C | 自动注释到原实验标签 Sankey | 已有列联表/混淆图 | 保存1882细胞对应、完整流量表及 Sankey；ARI/NMI仅对原参考 |
| S1D/E | B/endothelial 标准坐标；与Fig3B/C主坐标比较 | 未完成 | 用方向/D转换；数值报告标准坐标角度不保真，主坐标保真误差 |
| 来源/运行 | 固定源码、版本、参数、RNG、资源和真实终端 | 旧例已有，作者环境非完整等价 | 本轮独立配置、来源SHA、调用源码、RNG/alpha及日志；大RDS外置索引 |

PASS/PARTIAL/BLOCKED 是实施自检状态；本轮不签署独立通过。图表实现完成与严格原文输入等价分别判定。

## 输入及参数差异（运行前固定）

| 项目 | 作者固定代码 | 本轮既定路径 | 科学边界 |
| --- | --- | --- | --- |
| 数据 | `data/real/discussed/preprocessed/tabula_muris_preprocessed_filtered.rds` | `/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds`；43,383,527 bytes；SHA256 `af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b` | 名称/来源链不同，1882细胞相同不足以证明等价 |
| 基因 | 6000HVG + 已表达 marker，去重 | 6000HVG-only，暂缺权威CSV | 不以CellMarker注释资源、结果或自编清单替代CSV |
| CA | logcounts/Pearson，30维，princ_coords=3，python=TRUE | 同调用但 python=FALSE；固定APL的30维路径均为R/irlba | 同已验证配置；不能由调用近似推断作者对象等价 |
| 随机数 | CAdir前seed2358；CA前未见显式seed | CA/CAdir/排序分别seed2358，固定RNGkind | 保存实际CA基底、RNG和alpha；图复用对象，不再计算CA |
| 聚类 | k8、55°、random、apl_quant=.99、min_cells20、qcutoff=.8、convergence_thr=.001 | 同显式参数，固定公开实现默认值 | 不按预期7簇调参，不改上游 |
| 软件 | R4.4.1，APL1.9.1；CAdir本地私有路径 | R4.4.1/APL1.9.1；公开固定CAdir0.0.99；scater1.32.1对1.32.0 | 不能声称完整恢复作者锁 |
| 预处理链 | TabulaMurisSmartSeq2，Limb_Muscle，去缺标签；通用QC/归一化脚本 | 使用已预处理输入；不重复QC/归一化，保留doublet标记 | 通用脚本不能证明另名filtered对象的生成链 |

## 入口

先用原已验证 `scripts/rerun.sh --data ... --output-root ...` 产生一次新运行；随后本目录 `scripts/render_fig3.R RUN_DIRECTORY OUTPUT_DIRECTORY` 仅读取同一运行的保存对象绘图。具体命令、固定配置和源码哈希放在 `evidence/`。原 `results/figures` 均不改动。
