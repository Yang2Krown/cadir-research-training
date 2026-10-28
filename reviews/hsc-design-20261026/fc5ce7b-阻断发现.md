# 首次设计审查阻断：基因子集契约

被审提交：`fc5ce7b4911a3ee42bca9099dec8700fd974d23b`。本次真实共同QC/归一化/HVG/参考交集的独立oracle通过，但该提交尚不能准入正式计算。

独立读取实际已安装CAdir函数体发现：`assign_genes()`先用`ca_sphere_idx(...,qcutoff)`取得基因索引，然后从坐标矩阵`[idx,]`构造`gene_nms`，最终返回只以这些基因为names的factor。预设qcutoff=.8是合法科学参数，其语义包含基因子集选择，不是给6000全部基因填完整长度的factor。

`formal_run.R:53`却要求`names(cadir@gene_clusters)`与CA的6000个输入gene ID完全一致。正常子集返回会在保存核心对象后、评价前误判失败；紧接着直接按6000个ID构造分区表也不正确。`rank_diagnostics.R:13`再次作同样全集等同检查；第40行仅对内部子集统计NA，会遗漏根本没有出现在该子集内的未分配基因。

最小修复：保留原生CAdir对象的gene_clusters子集；验证names唯一、非空、属于固定CA全集及合法细胞簇。导出时以完整6000输入ID为主键match，未入原生子集者明确NA及原因，同时保存原生已分配基因清单。排名入口接受经验证的子集，完整rank覆盖核对子集实际分配者；未分配数量和ID由CA全集与实际分配者差集给出。不得为使检查通过而修改qcutoff、强行给全部基因分配、填补内部factor、删HVG或另算CA。

这不是运行后根据指标改参数：阶段一没有执行CA/PCA、CAdir、聚类、ARI/NMI或算法smoke。证据是独立oracle导出的实际函数源码，而非预跑失败。具体源码见[evidence-independent-01/interface-assign_genes.txt](evidence-independent-01/interface-assign_genes.txt)，独立真实数据成功结果另见[independent-result.json](evidence-independent-01/independent-result.json)。已通知协调者交原实现者修复，固定新提交后由本评审者复验。初次阻断不覆盖后续结论。
