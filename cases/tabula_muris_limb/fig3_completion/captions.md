# 可用图注（本轮6000-HVG限定结果）

所有图均来自一次真实 Tabula Muris Limb Muscle 数据运行（1882细胞、6000 HVG），不代表缺失的作者 marker-augmented 输入已恢复。最终簇名称为CellMarker 2.0 GOA预测；方括号为原始 cluster ID，保留未注释簇和文献型名称。原参考为输入的 `cell_ontology_class`，仅用于事后比较。

**Fig3A**（[PNG](figures/Fig3A_association_top5.png) / [PDF](figures/Fig3A_association_top5.pdf)）。7个簇的Association Plots，簇内细胞为黄绿色，共聚类基因为橙色，其他细胞为深绿、其他基因为灰色。按上游函数语义，联合显示基因时细胞使用标准坐标、基因使用主坐标，方向以D转换。标签为每簇真实保存Sα分数最高的5个基因；排名不等于全部分数显著大于零。35个实际标签及1200个完整排名另表保存。

**Fig3B**（[PNG](figures/Fig3B_Bcell_principal.png) / [PDF](figures/Fig3B_Bcell_principal.pdf)）。B cell预测簇 `cluster_3` 的主坐标Association Plot。T cell（`cluster_4`，红色）与Macrophage（`cluster_5`，蓝色）的细胞和方向叠加；等比例坐标轴保持图上角度。原参考最大重叠与预测相符，但B cell簇仍包含49个lymphocyte参考标签，不能解释为113个独立验证的B细胞。

**Fig3C**（[PNG](figures/Fig3C_endothelial_principal.png) / [PDF](figures/Fig3C_endothelial_principal.pdf)）。Endothelial cell预测簇 `cluster_7` 的主坐标Association Plot，Vascular endothelial cell预测簇 `cluster_2` 的细胞和方向以红色标出。两个预测簇共享原参考的endothelial cell类别；原参考未独立标注vascular亚型。

**Fig3D**（[PNG](figures/Fig3D_actual_split_merge_history.png) / [PDF](figures/Fig3D_actual_split_merge_history.pdf)）。根据本次保存的完整CAdir日志绘制真实split/merge图；横向层级表示初始化、合并与拆分，省略没有split/merge的迭代，包含根节点共22节点23边。每个非根节点嵌入该迭代的主坐标细胞Association Plot。忠实使用上游`sm_plot`的GOA、`cost=pval`（BH padj）中间注释；最终`cost=logpval`使用log10(padj)目标。历史名称还可能受浮点并列最优影响，并非跨求解器唯一；包括Immune cell和Bergmann glial cell等预测名称，均不作肌肉组织真值声明。`keep_end=FALSE`意味着末层是最后一次拆分状态，不是随后的最终细化状态。

**S1A**（[PNG](figures/S1A_direction_angle_heatmap.png) / [PDF](figures/S1A_direction_angle_heatmap.pdf)）。同一保存对象全部7个主坐标方向的两两夹角（度）。较低夹角表示几何上更接近；不据此单独推断新的细胞谱系或生物学关系。

**S1B**（[PNG](figures/S1B_direction_projection_matrix.png) / [PDF](figures/S1B_direction_projection_matrix.pdf)）。每行以相应簇为基准：对角线为主坐标细胞Association Plot，其他格显示另一簇方向的投影。坐标数值另表保全，矩阵图由上游`plot_results`生成；面板的视觉缩放不替代S1A数值角度。

**S1C**（[PNG](figures/S1C_reference_sankey.png) / [PDF](figures/S1C_reference_sankey.pdf)）。左侧为7簇及自动预测名称，右侧为输入的8类原参考，流宽为实际细胞数，共1882。所有类别与少量交叉流均保留；ARI=0.669518704486352，NMI（max熵归一化）=0.741885423115482。

**S1D/E**（[D PNG](figures/S1D_Bcell_standard.png) / [E PNG](figures/S1E_endothelial_standard.png)，对应PDF同名）。分别将Fig3B/C的细胞与方向转换为标准坐标，方向按`direction/D`转换，联合显示主坐标基因及同一真实top5标签；底部彩色虚线图例标明比较方向，以避免狭窄等比例面板裁切长名称。转换后的方向投影与对应标准坐标角度一致，但相对主坐标角度发生变化；本次全部两组基准方向的比较中最大变化27.5359338°，数值表列明每一方向，不能把标准坐标图角度作为原聚类角度。
