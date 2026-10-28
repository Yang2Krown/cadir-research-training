# Limb Muscle Fig3/S1 实施报告

本轮补齐9项图表路径、数据和解释，实施自检完成，**待未参与实施的独立复验**。采用现有已验证输入的6000-HVG配置，只执行一次新的真实CA/CAdir运行；未改上游算法、未扩展其他数据、未重复归一化。原冻结交付和R3诊断保持。

## 逐项状态

| 项目 | 可用输入上的实现/自检 | 对原文与作者特定制品的结论 |
| --- | --- | --- |
| Fig3A | PASS：7簇GOA名称、35真实标签、1200完整排名 | PARTIAL：簇数和方法对应；缺作者扩展基因列表/对象，未作逐基因或像素等价声明 |
| Fig3B | PASS：按原参考最大重叠选择B/T/Macrophage，主坐标和真实方向 | PARTIAL：对应方向比较完成；不要求本次角度等于未提供的作者数值 |
| Fig3C | PASS：按真实GOA预测选择两个endothelial方向 | PARTIAL：原参考只有一个endothelial类别，vascular预测无独立亚型真值 |
| Fig3D | PASS：完整真实历史、22节点23边、21节点真实GOA与APL | PARTIAL：真实合并后重拆与论文定性过程可对照；上游pval历史标签可与最终logpval标签不同 |
| S1A | PASS：7×7真实方向角矩阵及热图 | PARTIAL：数值自洽，作者具体方向对象未取得 |
| S1B | PASS：全部49方向/对角面板和投影表 | PARTIAL：保留上游图形语义；角度定量结论取数值表 |
| S1C | PASS：1882细胞、8原参考类别、完整流量和Sankey | PARTIAL：参考对应完整；预测名称不替代真实标签 |
| S1D/E | PASS：方向/D转换、标准/主坐标数值比较 | PARTIAL：完成标准坐标不保真原角度的实际验证；未假设与作者几何完全相同 |
| 作者输入/执行环境严格等价 | BLOCKED | 缺marker CSV、作者filtered RDS及私有本地CAdir执行身份/完整依赖等价证据 |

PASS只指本轮实现者的自检。没有自行签署科研独立通过，也未把“发表Methods描述的流程实现”与“作者特定制品严格等价”合并为一个状态。

## 实际结果及可复查数值

真实输入为13204基因×1882细胞，SHA256 `af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b`；保留所有细胞、原logcounts与55个doublet标记。6000 HVG经30维CA、k=8/55°/seed2358流程得到7簇，1200个基因被分配，4800个保留NA。ARI=0.669518704486352，NMI=0.741885423115482，均仅对原`cell_ontology_class`计算。

| 原cluster ID | 真实GOA预测 | 细胞数 | 原参考多数及数量 |
| --- | --- | ---: | --- |
| cluster_1 | 未注释cluster_1 | 940 | skeletal muscle satellite cell，526；该簇混合两个satellite参考类 |
| cluster_2 | Vascular_endothelial_cell | 28 | endothelial cell，19 |
| cluster_3 | B_cell | 113 | B cell，63（另49为lymphocyte） |
| cluster_4 | T_cell | 48 | T cell，33 |
| cluster_5 | Macrophage | 76 | macrophage，73 |
| cluster_6 | Schwalie_et_al.Nature.P1 | 490 | mesenchymal stem cell，488 |
| cluster_7 | Endothelial_cell | 187 | endothelial cell，187 |

B cell到T cell主坐标夹角63.9984377°，到Macrophage为72.6956194°；Endothelial到Vascular endothelial为66.1100659°。这些方向比该基准簇到多数非相关簇更近，但没有把“相对较小”夸成接近零。投影对原主坐标角度的最大误差约2.84×10⁻¹⁴°；标准坐标转换相对原主坐标角度的最大变化27.5359338°。全部值见[逐方向比较表](tables/principal_standard_projection_angle_checks.tsv)。

图A的实际35个标签来自保存排名，完整细胞/基因分配、全部分数、预测/原参考映射、选择证据均在[tables](tables/)。坐标自检采用显式投影与正交距离公式，按sample ID核对上游重排的绘图行；分数用保存alpha与原CA核对。没有重新随机估计alpha或为单张图重新CA。

## 来源冲突、历史注释和误差边界

官方Methods的Discussed data明确6000 HVG、1882细胞和6000基因；固定`figure2.qmd`却额外并入`tabula_muris_marker_genes.csv`中的已表达基因，并读取另一名称的filtered RDS。本轮HVG-only路径与发表Methods的这些维度对应，但仅有尺寸相同不能证明与作者filtered对象逐细胞逐基因相同。下载/预处理脚本给出TabulaMurisSmartSeq2、Limb_Muscle、去缺标签及通用QC/归一化的代码链，尚未证明本输入与另名对象经过完全相同过滤。

本轮直接读取固定代码和官方正文，来源URL/提交/SHA已保全；主控另核296个可达Git提交，精确两个缺失文件名历史查无返回。Zenodo及其API/DOI官方制品访问失败，未取得清单或字节；这一有界检查不证明制品不存在。缺口最小补件为权威marker原文件或可验证生成链、作者filtered对象或逐元素等价证据，以及作者私有本地包的执行身份/环境对应证据。不存在用CellMarker资源代替marker CSV、从期望结果反推基因、或按七簇调参的行为。

Fig3D严格保留真实split/merge日志与上游`sm_plot`：内部历史注释使用`cost=pval`，最终注释使用`cost=logpval`。在实际`run_hungarian`实现中，pval目标是BH校正的`padj`，logpval目标是`log10(padj)`，后者返回时再乘以−1供显著性门控。Hungarian全局匹配、目标变换及数值并列均可能影响名称，不能把全部名称差异只归因于cost变换。本轮独立SciPy复核已重现最终七个名称；历史pval目标中Immune_cell/Macrophage存在浮点并列最优，约束实际保存的历史名称仍取得同一双精度最优目标，因此历史标签不具有跨求解器唯一性。我们忠实保留历史中Immune cell、Bergmann glial cell等预测，以及不同阶段可交换的两个endothelial名称；这些不是独立生物学发现。`keep_end=FALSE`省略最后无split/merge的细化，末层25个细胞的分支与最终28个细胞也不应混为同一个状态。每节点的迭代、细胞数量、真实方向、GOA表和成员均保存在外置完整证据；未改名冒充作者历史。

图形采用上游Association Plot语义，联合细胞/基因图使用细胞标准坐标、基因主坐标；故它与只显示细胞的Fig3B/C主坐标图本来就不应逐点相同。B/C额外使用等比例轴以保留可见方向角；S1B保留上游面板缩放，定量判断依数值表。没有原论文CA/方向数值，无法计算“对作者对象的数值误差”或据相似图像证明严格重现。

## 资源、工程限制与重放

cgroup实限2CPU、8GiB；保持2线程。新真实运行36.37秒，R峰值2278652KiB，CA阶段6.535秒、CAdir3.770秒。最终绘图33.29秒、R峰值1376168KiB，均为单次机器上的实际诊断，不作为算法基准。

环境固定R4.4.1/APL1.9.1/CAdir0.0.99等，作者锁中CAdir仍指私有本地路径；未声称完整恢复该环境。ggrepel0.9.8内嵌新ggplot文字图例键，与固定ggplot3.5.2不兼容，第一绘图尝试因此失败；仅关闭冗余文字标签图例，点图例保留，未改环境或上游函数。第二次自检错误来自未按sample ID对齐上游按簇重排的行，已修正。所有失败绘图日志保留；成功后的最终渲染仅读同一CA/CAdir。上游S1B/历史绘图的manual-size警告仍保留在真实终端日志；未改变点坐标、颜色身份或聚类。

独立复验随后发现S1D/E标准坐标面板较窄，方向文字被裁切。已保存原四份PNG/PDF及SHA256，仅从同一保存CA/CAdir重画两图，将方向名称换成外置彩色虚线图例，保留`coord_equal`、全部点和方向数值；没有重算CA、聚类、GOA或其他图。最小入口为`scripts/repair_s1_legend.R`，修复日志、原图与不变数据表SHA见`evidence/s1-legend-fix/`。修后图仍须独立展示复验，严格作者输入等价状态不变。

重放入口见[README](README.md)。[外置RDS索引](evidence/external_RDS_index.json)保留CA、未排序/排序/注释对象、RNG、完整历史、历史GOA和图数据；[外置全量索引](evidence/external_artifacts.json)还含细胞/基因主坐标、基因方差、原元数据、全量点云与逐节点成员。大RDS和原始输入均未入Git。完整源码与脚本哈希、有效参数、RNG、alpha、版本、运行日志随小型包提供，原冻结成果的保护结果见[evidence/preservation.json](evidence/preservation.json)。

## 可用于报告的段落

我们在Tabula Muris Limb Muscle的1882个真实细胞上，保留既有预处理logcounts并选取6000个高变基因，使用30维Correspondence Analysis和固定CAdir参数执行一次方向聚类。所得7个簇共分配1200个基因，基于原始cell_ontology_class的ARI为0.6695、NMI为0.7419。我们完成了七簇Association Plots及真实top5基因标签、免疫与内皮方向比较、完整split/merge历史图，以及方向角、方向投影、原参考Sankey和标准坐标对照。数值核对表明主坐标投影保留方向夹角，而标准坐标转换可改变夹角。自动注释与原参考分别保留，未注释簇及非典型历史预测均如实呈现。本结果限定于所提供的6000-HVG输入；作者绘图代码的额外marker清单、另名filtered对象和私有执行环境尚未取得，因此不声称作者特定制品严格等价，独立复验另行进行。
