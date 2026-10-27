# LM Fig3/S1 独立复验（2026-10-27）

数值基线：`a33e815971f8bb89e8136ed65ee41b99a2f3a2e9`；显示修复：`8c1ff1c08cbc177402bc0148ca7bb4f3133fa0e3`；最终交付tip：`ab68da7ef154f133ec436275fcf11396f37f884a`。本报告由未参与实施的独立评审完成；工作树为 `/workspace/cadir-lm-fig3-independent-review-20261027`，分支 `review/lm-fig3-20261027`。未改实施源码、数据或结果，未重跑CA、聚类、R3或原入口的smoke；只读实际R对象，另写独立核验代码和证据。

**最终结论：在所提供的6000-HVG输入及已披露环境边界内，发表方法范围的九项完整分析实现与图表交付PASS；S1D/E文字裁切已修复并独立复验。作者特定制品严格等价继续BLOCKED。** 本次不将旧HVG-only单例升级成严格论文复现PASS。

| 项目 | 独立状态 | 实际核对与结论边界 |
|---|---|---|
| Fig3A | PASS | 七簇名称保留未注释cluster_1及Schwalie文献名；全部1200分数、排名和35个top5标签按显式gene ID重算；7×(1882细胞+6000基因)点坐标核对。cluster_1的top5分数均为负，图注已说明排名不代表显著。 |
| Fig3B | PASS | 原输入B/T/macrophage参考最大重叠唯一选择cluster_3/4/5；1882点、方向及主坐标夹角复验。B簇113细胞中仅63原参考B cell、49为lymphocyte。 |
| Fig3C | PASS（预测层面） | GOA真实选择cluster_7与cluster_2；点、方向、夹角通过。原参考只有一个endothelial cell类别，不能证明vascular独立亚型真值。 |
| Fig3D | PASS | 从实际log逐阶段成员重建22节点23边；21节点的全1882成员、方向及APL坐标核对；历史GOA与原源码成本口径保留。 |
| S1A | PASS | 独立余弦角核对7×7矩阵，热图身份正确；对角的约1.21×10⁻⁶°是浮点acos自角噪声。 |
| S1B | PASS | 全49方向投影独立核对，逐张查看矩阵及对角APL；面板缩放不能替代数值角度。 |
| S1C | PASS | 逐cell ID对照原输入`cell_ontology_class`；7簇/8参考类/1882细胞流量逐项及两端守恒；手算ARI/NMImax。 |
| S1D | PASS（修后） | 数值、direction/D变换、全部点及方向通过；修后PNG/PDF底部T cell/Macrophage图例完整可读。 |
| S1E | PASS（修后） | 数值及标准坐标变换通过；修后PNG/PDF底部Vascular endothelial cell图例完整可读。 |
| 来源/参数/保护 | PASS（本地可核范围） | 四类实际R对象、基线138项外置索引核对、115项前后保护文件及源码索引通过；a33的105个新增路径均在fig3_completion。修复及封装增量另核；同一CA/alpha/运行对象，renderer不重算CA/聚类/排名。 |
| 对论文对应与结论 | PARTIAL | 正式Fig3对应作者figure2.qmd，S1 A–E方法与图表路径已对应；缺作者几何对象，不计算对作者的数值误差或要求像素相同。 |
| 作者特定输入/环境严格等价 | BLOCKED | marker CSV、另名filtered RDS及私有CAdir执行身份/完整锁等价未取得。已有有界来源检查不证明这些制品不存在，本轮不重复下载、不降低门槛。 |

独立重算结果为1882细胞、6000HVG、7簇、1200 assigned genes（4800未分配），保存alpha=1.0750644620377505。ARI=0.66951870448635153；以max熵归一化的NMI=0.74188542311548167，均只对原参考。B→T为63.998437696131582°，B→Macrophage为72.695619378409063°，Endothelial→Vascular为66.110065881868181°。独立点积与正交残差得到主坐标投影最大角误差1.5030×10⁻¹⁴°；标准坐标最大角变化27.535933804140633°。分数最大误差1.69×10⁻¹⁴，Fig3A坐标最大误差5.15×10⁻¹⁴；历史坐标最大误差5.56×10⁻¹⁵。

GOA从实际资源、HVG universe及实际阶段基因归属独立重算交集、hypergeometric p值和BH校正，通过final及三历史阶段全部行。另一套SciPy Hungarian精确重现最终`logpval`七名称。源码`cost='pval'`实际使用BH **padj**，`logpval`最小化`log10(padj)`；历史三阶段的实际Immune_cell与SciPy选择的Macrophage，在双精度目标上并列（0.09614756421054912、0.03236403431079518、0.14962368067305934）。约束实际名称后仍达到相同最优目标，且满足alpha。故历史名称忠实于保存的Rcpp实现，但不能签为跨求解器唯一名称；没有改成预期论文标签。Bergmann/Immune/Schwalie也不作组织生物学真值。

历史保留的层为iter_0、merge_iter_1、split_iter_2。边按原源码取各事件前一细化状态的成员交集，再连接到上一保留层；这是split/merge拓扑，不是完整逐细胞迁移图。`keep_end=FALSE`省略后续无split/merge细化，因此末层25细胞分支不等于最终28细胞簇。图中中间节点的方向及成员均取其自身阶段。

九张PNG和九张PDF均已实际逐张查看；PDF用pdftoppm另存预览并读取pdfinfo/文本，原件不变。Fig3A的35标签、Sankey预测/原参考两侧、Fig3D异常自动名均可辨识。S1D/E原版方向名称裁切已由原实施方修复；四份新PNG/PDF再次逐张查看，底部彩色虚线图例完整可读。标准面板仍因等比例轴而窄、局部基因标签较密，完整top5身份与数值另表可查，不影响方向名修复验收。

修复差异仅涉及显示代码、四图与解释/收据。独立从固定修复源码构造实际ggplot对象并拦截ggsave（不重画文件），逐项检查每图全部7882点、比较簇成员点、top5 ID、方向斜率、图例身份和coord_equal=1，均通过。原16表、9对象RDS索引、全部原外置记录SHA保持；新图与固定Git blob完全相同，保留原四图也与a33 blob相同。ab68对8c仅external_artifacts、preservation、review_packet三个JSON变化，最新外置索引全部记录及小包SHA/大小已核对，未因封装重跑科学数值。[修复数据核验](repair/plot_result.json)、[修复与封装文件核验](repair/file_result.json)、[新PDF预览](repair/)保存独立结果。历史成本和并列最优的解释也已补入实施报告/图注。

资源实限为2CPU/8GiB。原运行日志记录36.37秒、峰值2278652KiB，最终原绘图33.29秒、峰值1376168KiB；本review只核日志与cgroup，不把它们当作独立性能基准。源码10个保存函数与当前安装源码MD5相同；HVG ID与保存variance的top6000一致，renderer种子与2358一致，未重新推断alpha。ggrepel兼容修正只关闭冗余文字图例；原失败日志均保留。作者源码Git逐字来源核对使用主控已提供证据，本轮只读固定代码确认对应，不重做全量项目/来源审查。

复验入口（现有Conda环境）：

```bash
bash /workspace/cadir-stage1-fix/cases/tabula_muris_limb/scripts/run-r.sh reviews/lm-fig3-20261027/independent_numeric.R
python reviews/lm-fig3-20261027/independent_annotation.py
bash /workspace/cadir-stage1-fix/cases/tabula_muris_limb/scripts/run-r.sh reviews/lm-fig3-20261027/independent_provenance.R
python reviews/lm-fig3-20261027/audit_files.py
python reviews/lm-fig3-20261027/repair_audit.py
bash /workspace/cadir-stage1-fix/cases/tabula_muris_limb/scripts/run-r.sh reviews/lm-fig3-20261027/repair_plot_audit.R
```

主要证据：[数值结果](numeric_result.json)、[逐检查误差](numeric_errors.tsv)、[独立GOA](independent_GOA.tsv)、[注释复验](annotation_result.json)、[历史边成员](independent_history_edge_members.tsv)、[来源/RNG](provenance_result.json)、[文件核对](file_audit_result.json)、[源码/资源](source_resource_result.json)、[前哈希](hashes_before.json)、[后哈希](hashes_after.json)、[PDF预览](pdf_preview/)。脚本自身的早期维度处理、正向射线处理、named alpha属性断言修正日志亦保留，未用实施verify的PASS替代独立结论。

review分支只本地提交。子线程推送曾被自动审批拒绝，理由为缺本子线程可核实的远程目标/研究制品载荷授权；随后主控用完整对话确认原始用户既有授权，并要求本评审不重试，由主控处理发布。原拒绝记录见[push_status.json](push_status.json)，不影响科学结论。
