# Association Plot 图注（适用于相邻 PNG / PDF）

[Association Plot PNG](association_plots.png) / [PDF](association_plots.pdf) 的七个 panel 依次对应标题所示的 cluster_1 到 cluster_7。每个 panel 都将同一批 **1882 个细胞与 6000 个入选 HVG** 投影到该簇拟合方向（30 维 CA 空间）及其正交距离；不同 panel 的方向不同，不能把坐标当成 CA1/CA2 或基因表达量。

横坐标是点在归一化簇方向上的有符号投影；方向朝该簇细胞质心定向。纵坐标是点到该方向直线的非负正交距离，即 `sqrt(||z||² − x²)`。本次同时显示细胞与基因：细胞使用 **standard column coordinates**，基因使用 **principal row coordinates**；细胞簇的 principal 方向逐维除以相应奇异值后归一化，用于这一混合坐标图。数值是对应 CA 坐标约定下的几何量。

| 颜色 | 含义 |
| --- | --- |
| 石灰色 `#c6d325` | 当前 panel 簇的细胞 |
| 橙色 `#ef7c00` | 分配到当前簇的共聚类基因 |
| 深绿色 `#006c66` | 其他簇的细胞 |
| 灰色 `#777777` | 其余基因，包含分配到其他簇者和未分配者 |

每簇标注其 S-alpha 分数最高的五个基因。排名阶段使用 gene principal 空间及原簇 principal 方向，其分数为 `x − alpha_genes × y`，与这里细胞/基因同图的混合坐标需加以区分。排名是几何评分，不能解释为差异表达显著性或已经生物学验证的 marker。历史排序复跑差异及适用边界见[修复勘误](../review_fixes/2026-10-25/README.md)。

原图字节保持冻结；本图注补足原图中省略的轴标题、颜色图例和坐标约定。来源为固定 [CAdir cluster_apl.R](https://github.com/VingronLab/CAdir/blob/de74a008dfcd0d4fa4f7f93c57aa346892a8d935/R/cluster_apl.R) 的坐标转换、`apl_model` 与 `.highlight_cluster`。
