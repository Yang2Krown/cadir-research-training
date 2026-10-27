---
title: "CAdir单细胞联合聚类的复现与新数据对照实验"
subtitle: "科研基础训练实验报告"
date: "2026年10月27日"
lang: zh-CN
toc-title: "目录"
---

# 摘要

单细胞转录组聚类需要同时解释细胞分组及其关联基因。本文复现CAdir基于对应分析与方向聚类的计算流程，在Tabula Muris Limb Muscle（LM）数据上实现原论文Fig3 A–D和关联S1 A–E，并在Nestorowa造血干／祖细胞（HSC/HSPC）数据上开展新数据对照实验。LM输入包含13204个基因和1882个细胞，使用既有对数归一化表达，选择6000个高变基因，计算30维对应分析，以初始簇数8、方向角阈值55°和随机种子2358执行CAdir。结果得到7个细胞簇及1200个已分配基因，调整兰德指数为0.669519，最大熵归一化互信息为0.741885。细胞数、已分配基因数、最终簇数、全部逐簇汇总及可见拆分合并日志与作者公开运行记录一致，调整兰德指数在作者显示精度下一致。九项分析包括关联图、方向比较、拆分合并历史、方向角矩阵、参考标签流量及坐标转换。新数据实验采用统一质量控制、归一化和6000个高变基因，保留1656个细胞，在1641个具有参考标签的细胞上评价CAdir和主成分分析＋共享近邻图＋Louvain两种流程。两种方法各运行五个预定种子，全部成功。CAdir的调整兰德指数中位数为0.291506，基线为0.269345；归一化互信息中位数分别为0.343414和0.356464。结果表明，在本次HSC配置下，两种评价指标呈现不同的相对排序；CAdir还提供了细胞与基因的联合分组、基因排名和方向诊断。本文结合数学表达、实际代码、运行命令、真实图表和独立数值复核，对上述结果进行解释。

**关键词：** 单细胞转录组；对应分析；方向聚类；联合聚类；可重复计算；聚类评价

# Abstract

**Reproduction of CAdir Joint Clustering for Single-Cell Transcriptomics and a Comparative Experiment on a New Dataset**

Single-cell transcriptomic analysis requires both a partition of cells and an explanation of the genes associated with that partition. This report reproduces the correspondence-analysis and directional-clustering workflow of CAdir and evaluates its behavior on two mouse datasets. The original-paper case uses the Limb Muscle subset of Tabula Muris. The input contains 13,204 genes and 1,882 cells. Existing log-normalized expression values are retained, 6,000 highly variable genes are selected, and correspondence analysis provides a 30-dimensional representation. CAdir is initialized with eight directions, a cutoff angle of 55 degrees, and random seed 2358. The analysis returns seven cell clusters and 1,200 assigned genes. Against the original reference annotations, the adjusted Rand index is 0.669519 and normalized mutual information, calculated using the larger of the two entropies, is 0.741885.

The LM analysis implements the four panels of the published Figure 3 and five associated supplementary panels. These outputs include association plots, immune and endothelial direction comparisons, an actual split-and-merge graph, pairwise direction angles, a direction projection matrix, a reference-label Sankey diagram, and comparisons between principal and standard coordinates. The published author execution record agrees with the reproduced cell count, assigned-gene count, final cluster count, all reported cluster sizes and names, and the visible split-and-merge messages. The adjusted Rand index also agrees at the precision printed by the author. Independent checks cover saved coordinates, gene scores and rankings, clustering metrics, overrepresentation analysis, annotation assignment, and graph topology.

The extension experiment uses the Nestorowa hematopoietic stem and progenitor cell study. A common preprocessing procedure retains 1,656 cells and selects 6,000 highly variable genes. External evaluation uses the same fixed set of 1,641 cells carrying published broad immunophenotype labels. CAdir is compared with a principal-component-analysis, rank-based shared-nearest-neighbor graph, and weighted Louvain workflow. Both methods use 30-dimensional representations and the same five predefined seeds. All ten runs complete successfully. Median adjusted Rand indices are 0.291506 for CAdir and 0.269345 for the baseline. Median normalized mutual information values are 0.343414 and 0.356464, respectively. The metric ordering therefore depends on the criterion used. CAdir produces nine to eleven clusters, whereas the baseline produces seven in each run. This difference provides a concrete basis for examining how cluster granularity affects agreement with the reference partition.

The report connects these results to mathematical definitions and executable source code. It explains correspondence-analysis coordinates, directional assignment, total-least-squares direction updates, gene selection and ranking, and reference-based evaluation. The execution procedure records exact input identifiers, configuration, source revisions, random-number states, saved analysis objects, and resource measurements. Figures are generated from the saved objects, linking each displayed result to the corresponding numerical tables. Together, the original-paper case and the new-data comparison demonstrate an interpretable analysis workflow in which clustering, associated genes, geometric diagnostics, and quantitative evaluation can be inspected as connected parts of one experiment.

**Key words:** single-cell transcriptomics; correspondence analysis; directional clustering; joint clustering; reproducible computation; clustering evaluation

# 1 引言

## 1.1 研究背景与问题

单细胞RNA测序以“基因×细胞”的表达矩阵记录细胞之间的转录差异。聚类的直接输出是细胞分组，而生物学解释还需要回答：哪些基因支持这些分组，组内细胞是否沿同一变化方向分布，不同簇的表达特征是否相近，初始簇数如何影响最终结果。CAdir将这些问题放在同一个几何框架中处理[1]。

常用分析流程先对表达矩阵归一化和选择高变基因，再做主成分分析（Principal Component Analysis，PCA），在低维空间构建近邻图并进行社区划分。CAdir使用对应分析（Correspondence Analysis，CA），将细胞和基因映射到关联的低维坐标中，通过寻找从原点出发的稠密方向进行聚类，同时给出与细胞簇相关的基因。关联图把点沿方向的投影和偏离方向的距离直接显示出来，使聚类机制与结果解释相互衔接。

## 1.2 实验目标

本文完成两组相互关联的实验。第一组以原论文LM案例为对象，重建输入检查、特征选择、CA、CAdir、基因分配、自动注释、指标计算及九项图表，分析原论文核心案例的结果。第二组以Nestorowa HSC/HSPC研究为新数据，采用共享输入比较CAdir与PCA＋SNN＋Louvain流程，观察方法迁移后的评价表现和聚类粒度。

报告围绕三个问题展开：CAdir怎样利用方向同时联系细胞与基因；LM结果怎样与作者公开运行结果对应；在新的HSC数据上，方向聚类与图聚类呈现怎样的指标和结构差异。

# 2 相关工作与数据来源

## 2.1 单细胞分析流程

Tabula Muris构建了小鼠多个组织的单细胞转录组资源[2]，其中Limb Muscle子集包含组织细胞及免疫细胞，适合观察不同细胞群之间的表达关联。本文以该组织子集作为原论文案例。

Nestorowa等研究了小鼠造血干／祖细胞分化的单细胞表达[3]。本文采用该研究的公开数据及已发布免疫表型元数据，构建新数据对照实验。研究涉及的六类broad标签包括LTHSC、LMPP、MPP、CMP、MEP和GMP，评价标签通过明确细胞ID与发布的成员列对应。

Bioconductor提供了表达数据容器、方差建模、降维及近邻图构建等基础设施[4]。低层单细胞分析通常包括质量控制、归一化、特征选择与降维[5]。本文用SingleCellExperiment组织表达矩阵和元数据，用scran、scuttle和scater完成相应步骤。

## 2.2 对照方法与评价

新数据对照采用PCA表示、共享近邻（Shared Nearest Neighbor，SNN）图和Louvain社区发现。Louvain通过局部节点移动与图聚合优化社区结构[6]，本文固定分辨率和邻居数执行。

调整兰德指数（Adjusted Rand Index，ARI）从细胞对的一致分组出发，并校正随机一致性[7]。归一化互信息（Normalized Mutual Information，NMI）衡量两个分区共享的信息。本文同时报告ARI和最大熵归一化NMI，以呈现两种评价角度。

## 2.3 数据规模与实验入口

| 项目 | LM原论文案例 | HSC新数据实验 |
|---|---|---|
| 数据研究 | Tabula Muris Limb Muscle | Nestorowa HSC/HSPC |
| 公共数据入口 | GEO GSE109774、TabulaMurisData | GEO GSE81682、scRNAseq legacy资源 |
| 起始对象 | 13204基因×1882细胞 | 46175行×1920细胞 |
| 实际聚类细胞 | 1882 | 1656 |
| 实际评价细胞 | 1882 | 1641 |
| CA／PCA输入特征 | 6000个高变基因 | 两方法共享6000个高变基因 |
| 参考信息 | cell_ontology_class，8类 | 发布的六类broad免疫表型 |

LM使用`tabula_muris_limb_preproc.rds`，对象为SingleCellExperiment，文件大小43383527字节。输入SHA256为`af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b`。本次分析读取其既有`logcounts`，保留1882个细胞及原始细胞ID。6000个高变基因构成本次实际CA特征集合，特征ID随运行记录导出。

HSC使用scRNAseq legacy `nestorowa-hsc/2.0.0`路径提供的表达与元数据资源（EH2694、EH2695），并保留GEO来源核对记录。细胞ID作为数据、元数据、分区与评价的共同连接键。

## 2.4 近年的联合聚类与可解释表示

CAbiNet通过对应分析构建细胞与基因的联合表示，并在网络上实施双聚类，为CAdir的技术背景提供了直接参照[8]。Castanho等对双聚类的数据建模、算法与分析流程进行了系统梳理，强调局部模式及行列联合关系的解释价值[9]。本文围绕同一细胞簇关联的基因、方向及富集注释组织结果，使细胞分组能够追溯到相应表达特征。

可解释性也出现在近期单细胞表示学习研究中。iVAE通过变分自编码器的潜在表示和解释模块研究聚类表现[10]。与潜变量表示的研究视角相联系，本文通过CA主坐标、方向夹角和关联图逐项展示几何结构，并使用明确的基因得分解释簇内排名。

## 2.5 聚类稳定性、粒度与流程评价

scICE以多次聚类标签的一致性评价随机过程的影响[11]；CHOIR则利用显著性驱动的层次分析识别细胞类型与状态[12]。这些研究分别从稳定性和分组层次解释聚类结果。本文在HSC中预先固定五个随机种子，并同时呈现全部运行、最终簇数与参考组成，使计算初始化和聚类粒度具有明确的观察依据。

Yin等的对比基准同时考察聚类指标、内存、时间及细胞类别粒度，展示了评价维度和数据模态之间的联系[13]。Ge等比较单细胞归一化方法，指出技术处理与下游聚类表现之间存在联系[14]。Fang等进一步将数据集特点和分析流程组合纳入评价，研究数据集相关的流程表现[15]。因此，本文通过固定共同输入、特征和评价细胞来比较两种HSC流程，并把ARI、NMI、簇数及实际运行资源分开报告。

# 3 方法原理

## 3.1 高变基因与输入表示

设表达矩阵为$\mathbf{X}\in\mathbb{R}_{\geq0}^{G\times N}$，行对应基因，列对应细胞。高变基因选择通过`scran::modelGeneVar`估计基因表达的均值、总方差及生物学变异成分，再按生物学变异选取6000个基因。实际调用使用`var.threshold=NULL`和固定数量，生成具有明确顺序的特征列表。

LM直接使用输入的`logcounts`。HSC先进行共同质量控制，以保留细胞的内源性文库大小$L_j$计算大小因子$s_j=L_j/\overline{L}$，再执行

$$x_{ij}=\log_2\left(\frac{c_{ij}}{s_j}+1\right),$$

其中$c_{ij}$是原始计数。HSC的大小因子使用低表达过滤前的全部内源性基因计算，随后选择在至少3个保留细胞中检出的基因并建立高变基因输入。两方法读取同一份归一化、高变基因对象。

## 3.2 对应分析

记矩阵元素总和为$T=\sum_i\sum_jx_{ij}$，比例矩阵为$\mathbf{P}=\mathbf{X}/T$，行质量为$r_i=\sum_jp_{ij}$，列质量为$c_j=\sum_ip_{ij}$。基因与细胞独立时的期望比例为$r_ic_j$，Pearson标准化残差矩阵为

$$\mathbf{S}=\mathbf{D}_r^{-1/2}(\mathbf{P}-\mathbf{r}\mathbf{c}^{\mathsf T})\mathbf{D}_c^{-1/2},$$

其中$\mathbf{D}_r=\operatorname{diag}(\mathbf{r})$，$\mathbf{D}_c=\operatorname{diag}(\mathbf{c})$。这一步突出相对于独立期望的关联结构。

对残差矩阵进行截断奇异值分解：

$$\mathbf{S}\approx\mathbf{U}_{d}\mathbf{D}\mathbf{V}_{d}^{\mathsf T},\qquad d=30.$$

基因、细胞的标准坐标分别为$\mathbf{\Phi}=\mathbf{D}_r^{-1/2}\mathbf{U}_{d}$和$\mathbf{\Gamma}=\mathbf{D}_c^{-1/2}\mathbf{V}_{d}$；主坐标为

$$\mathbf{F}=\mathbf{\Phi}\mathbf{D},\qquad \mathbf{G}=\mathbf{\Gamma}\mathbf{D}.$$

CAdir用细胞主坐标寻找聚类方向。APL调用中`princ_coords=3`选择同时计算行、列主坐标，`dims=30`设置保留维数。本文LM使用的APL版本在该截断维数下通过`irlba`计算部分奇异值分解。

## 3.3 方向分配与更新

令细胞主坐标为$\mathbf{z}_j$，第$k$个单位方向为$\mathbf{u}_k$。点到方向所在直线的正交距离为

$$d_{jk}=\sqrt{\max\{0,\|\mathbf{z}_j\|^2-(\mathbf{z}_j^{\mathsf T}\mathbf{u}_k)^2\}}.$$

实际方向分配采用正向投影约束：$\mathbf{z}_j^{\mathsf T}\mathbf{u}_k<0$时，该候选距离置为无穷。随后将细胞分配到距离最小的方向。

每个簇通过过原点的总最小二乘更新方向。对簇内坐标组成的矩阵$\mathbf{Z}_k$，其第一右奇异向量给出最大投影能量方向，即求解

$$\max_{\|\mathbf{u}\|=1}\|\mathbf{Z}_k\mathbf{u}\|^2.$$

实现通过奇异向量求解，并将符号朝向簇内多数点。重复分配和方向更新，直到方向变化满足收敛阈值或达到最大迭代次数。初始化采用上游`kmeanspp`方式。本次LM初始方向数为8，收敛阈值为0.001°，最大迭代次数为50。

## 3.4 拆分、合并与簇数变化

两个方向的夹角为

$$\theta_{ab}=\arccos\left(\frac{\mathbf{u}_a^{\mathsf T}\mathbf{u}_b}{\|\mathbf{u}_a\|\|\mathbf{u}_b\|}\right).$$

方向聚类的外层过程根据方向接近程度、簇内候选子方向的分离程度及最小细胞数条件实施合并和拆分。本文显式设置角阈值55°、最小簇细胞数20。算法随迭代调整方向数，因此初始8个方向最终得到7簇。完整历史记录每次迭代的成员和方向，用于绘制实际拆分合并图。

## 3.5 基因分配与关联图

基因分配先根据基因主坐标向量长度筛选候选。`qcutoff=0.8`保留长度达到80%分位点的基因，再在基因标准坐标下比较到细胞方向的距离并分配。本次6000个高变基因中有1200个获得簇分配；完整导出表对其余4800个基因保留NA。

对一个给定方向$\mathbf{u}$，关联图将点$\mathbf{z}$转换为沿方向的投影和正交距离：

$$a(\mathbf{z})=\frac{\mathbf{z}^{\mathsf T}\mathbf{u}}{\|\mathbf{u}\|},\qquad b(\mathbf{z})=\sqrt{\max\{0,\|\mathbf{z}\|^2-a(\mathbf{z})^2\}}.$$

横坐标$a$越大表示沿该方向的投影越强，纵坐标$b$越小表示点越接近该方向。图中细胞的长条状分布反映方向集中程度，其他簇的投影可用于观察方向之间的几何关系。

主坐标与标准坐标通过各轴奇异值相联系。展示标准坐标细胞时，方向按$\mathbf{u}_{\mathrm{std}}=\mathbf{u}/\mathbf{D}$逐轴转换。该缩放改变不同维度的相对权重，因此标准坐标图与主坐标图呈现不同的方向夹角。

## 3.6 基因排名与自动注释

上游`rank_genes`使用主坐标关联图计算基因得分：

$$S_{\alpha}(i,k)=a_{ik}-\alpha b_{ik}.$$

得分同时奖励沿方向的关联强度，并惩罚离开方向的距离。实际保存对象的`alpha_genes`为1.07506446203775，完整1200个分数与排名随表导出。每簇top5按得分降序选取，图中标签展示真实前五名。

自动注释采用CellMarker小鼠基因集进行基因过度代表分析（Gene Overrepresentation Analysis，GOA）。基因集与本次特征背景求交；背景采用上游实现构造的基因集覆盖并集。设该背景大小为$M$，某候选基因集大小为$K$，簇内参与富集的基因数为$n$，交集大小为$q$，超几何上尾概率为

$$p=\sum_{t=q}^{\min(K,n)}\frac{\binom{K}{t}\binom{M-K}{n-t}}{\binom{M}{n}}.$$

上游对参与比较的候选集进行Benjamini–Hochberg校正，再通过Hungarian分配确定簇与候选名称的对应。最终注释调用使用`cost="logpval"`，历史图使用`cost="pval"`；代码中的这两个目标分别来自校正概率的对数及校正概率。报告以“自动预测名称”和“原参考标签”分别描述两种信息。

## 3.7 评价指标

设预测簇与参考类别构成列联表$n_{ij}$，行和为$a_i$，列和为$b_j$，评价细胞数为$N$，则

$$\mathrm{ARI}=\frac{\sum_{ij}\binom{n_{ij}}2-\frac{\sum_i\binom{a_i}2\sum_j\binom{b_j}2}{\binom N2}}{\frac12\left[\sum_i\binom{a_i}2+\sum_j\binom{b_j}2\right]-\frac{\sum_i\binom{a_i}2\sum_j\binom{b_j}2}{\binom N2}}.$$

令$p_{ij}=n_{ij}/N$、$p_i=a_i/N$、$p_j=b_j/N$，互信息与本文NMI定义为

$$I(C;Y)=\sum_{ij:p_{ij}>0}p_{ij}\log\frac{p_{ij}}{p_ip_j},\qquad\mathrm{NMI}_{\max}=\frac{I(C;Y)}{\max\{H(C),H(Y)\}}.$$

评价代码按明确细胞ID连接预测与参考。LM在1882个细胞上计算指标；HSC固定使用具有唯一broad参考标签的1641个细胞，另外15个QC合格细胞参与聚类。

# 4 实验环境与完整操作流程

## 4.1 软件与资源

| 软件或配置 | LM实际运行 | HSC正式运行 |
|---|---|---|
| R | 4.4.1 | 4.4.1 |
| Bioconductor | 3.19 | 3.19 |
| CAdir | 0.0.99 | 0.0.99 |
| APL | 1.9.1 | 1.2.0 |
| SingleCellExperiment | 1.26.0 | 1.26.0 |
| scran | 1.32.0 | 1.32.0 |
| scater | 1.32.1 | 1.32.1 |
| scuttle | 1.14.0 | 1.14.0 |
| ggplot2 | 3.5.2 | 4.0.3 |
| 核心运行资源 | 2 CPU、8 GiB内存配额 | 2 CPU、8 GiB内存配额 |

LM环境采用独立Conda前缀及R用户库，激活入口为`/workspace/cadir-env/activate.sh`。CAdir公开源码固定于`de74a008dfcd0d4fa4f7f93c57aa346892a8d935`，APL固定于`d4d1f40d9ea9f1d9a95b224d45de843334cd617d`。环境同时保存源码、Conda显式制品清单、实际包版本表和`sessionInfo`。HSC通过其固定容器环境顺序执行两方法，两个案例的实际版本分别记录。

## 4.2 环境建立与调试过程

已执行的LM环境建立包括：配置Conda的R 4.4.1及基础运行库；安装Bioconductor 3.19依赖；按固定提交安装APL、CAbiNet和CAdir；配置统一R用户库和CPU线程数；运行包加载、RDS读写、CA、CAdir及绘图的工程检查。

安装中，R下载使用系统CA信任文件`/etc/ssl/certs/ca-certificates.crt`；Cairo依赖通过匹配的zlib、expat和X11开发元数据补齐；fgsea编译通过专用Makevars采用GNU C++17。环境安装与重复执行日志保存在`/workspace/cadir-env/logs/`，固定制品清单为`conda-explicit-linux-64.txt`。以下为已建立环境的安装／刷新入口与激活命令。

```bash
bash /workspace/cadir-env/complete-setup.sh
source /workspace/cadir-env/activate.sh
Rscript --version
```

`complete-setup.sh`顺序执行基础制品核对、定向R包安装和工程smoke。案例运行通过`run-r.sh`调用`Rscript --vanilla`，使用该环境中的包和解释器。实际RNG类型为Mersenne-Twister／Inversion／Rejection，CA、CAdir及排名各阶段保存随机数状态。OpenMP、OpenBLAS和MKL线程数设置为2。

## 4.3 LM操作步骤

步骤一，读取固定成果代码及配置。案例代码位于`cases/tabula_muris_limb/scripts/`，九图脚本位于`cases/tabula_muris_limb/fig3_completion/scripts/`，本报告采用的固定成果提交为`ab68da7ef154f133ec436275fcf11396f37f884a`。

步骤二，计算输入文件大小与SHA256，与配置记录比较。R层读取SingleCellExperiment后导出assay、基因ID、细胞ID和元数据，检查表达为有限非负值及标识唯一性。

步骤三，对`logcounts`进行方差建模，按顺序选取6000个高变基因，导出`hvg_genes.tsv`和`selected_genes.tsv`。

步骤四，设置种子2358，运行30维CA，保存`ca.rds`及实际随机数状态。随后重置该阶段种子，按固定参数调用`dirclust_splitmerge`，保存`cadir_unranked.rds`。

步骤五，调用`rank_genes`，保存`cadir.rds`、alpha、全体已分配基因排名及基因／细胞分区。对原参考标签计算ARI和NMI，导出列联表。GOA注释保存为`cadir_annotated.rds`。

步骤六，从该次保存对象生成九项图表及数值表。S1D/E使用相同对象和数值，只调整图例展示；图例修复已复验。

下列命令表达实际采用的入口。每次重算使用独立输出目录。

```bash
case_dir=/workspace/cadir-lm-fig3-completion-20261027/cases/tabula_muris_limb
input_rds=/workspace/cadir-handover/input/tabula_muris_limb_preproc.rds
out_root=/workspace/lm-report-replay/run-01

bash "$case_dir/scripts/rerun.sh" \
  --data "$input_rds" --output-root "$out_root"

run_dir=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' \
  "$out_root/latest-case.json")

bash "$case_dir/scripts/run-r.sh" \
  "$case_dir/fig3_completion/scripts/render_fig3.R" \
  "$run_dir" /workspace/lm-report-replay/plots-01

bash "$case_dir/scripts/run-r.sh" \
  "$case_dir/fig3_completion/scripts/verify_fig3.R" \
  "$run_dir" /workspace/lm-report-replay/plots-01
```

`rerun.sh`先进行版本检查及独立工程smoke，再调用真实案例；`latest-case.json`定位本次真实案例目录。最终发布的S1D/E使用`repair_s1_legend.R`，其三个参数依次为真实运行目录、原绘图目录和独立修复输出目录。

## 4.4 HSC共同准备与对照操作

首先按ID读取1920个候选细胞的计数和元数据，将`__`开头的统计行、ERCC spike-in和内源性基因分别识别。共同QC对内源性总计数、检出基因数和ERCC比例建立预定阈值：前两项在log2尺度使用中位数减3倍标准化MAD作为下限，ERCC比例使用中位数加3倍MAD作为上限。保留1656个细胞，过滤264个细胞。

随后进行一次共同归一化和高变基因选择，得到40721个合格基因及6000个HVG。参考标签根据六个broad二元成员列逐ID生成；具有唯一成员的细胞进入评价集合，形成1641个评价细胞。共享表达对象和评价ID集合固定后供两方法读取。

CAdir采用30维CA、初始k=8、55°、最小簇20细胞及`qcutoff=0.8`。基线对全部共同HVG计算30维PCA，使用`ntop=Inf`明确保留全部已选特征；构建`k=15`、`type="rank"`的SNN图；以边权和`resolution=1`执行Louvain。两方法均使用2358、101、202、303、404五个种子。正式执行入口为：

```bash
python3 cases/nestorowa_hsc/fair-experiment/scripts/run_experiment.py \
  --admission cases/nestorowa_hsc/fair-experiment/results/6cc7b3d-20261027-attempt-01/design-admission/admission.json \
  --output-root /workspace/hsc-replay/formal-run-01
```

其中`--admission`指向固定代码、配置、输入和环境对应的独立准入记录。执行器逐次建立新目录，保存CA／PCA、图结构、分区、RNG、指标、日志及资源记录。HSC的代码与结果分别固定于实现提交`6cc7b3da67c193da11a67c45a75167d6521438b0`和结果提交`091a8a4585cabc59a5504380398892bac49044f4`。

# 5 代码结构与关键实现分析

## 5.1 入口、配置与数据检查

LM的`run_case.py`负责读取JSON配置、验证输入、创建独立运行目录并启动R。`pipeline.R`承担数据检查、特征选择、模型运行和导出；`verify_results.R`执行结果检查；`render_fig3.R`读取已保存对象并生成九图；`repair_s1_legend.R`完成标准坐标图的图例布局。固定源码与本节各段的对应见附录B代码索引。

`run_case.py`中用`tempfile.mkdtemp`创建每次独立的`case-`目录，写入有效配置和运行状态。数据检查位于R的`audit_object`，包括：对象类、各assay维数与取值、基因／细胞ID唯一性、元数据列和参考标签数量。结果导出前通过`identical`核对CA细胞顺序、表达列顺序和聚类成员名称。

## 5.2 特征选择

以下两行来自实际执行的`pipeline.R`。第一行对指定assay估计方差，第二行选择固定数量的高变基因。

```r
gv <- timed("modelGeneVar", scran::modelGeneVar(sce, assay.type = cfg$assay))
chosen <- scran::getTopHVGs(gv, n = cfg$hvg_n, var.threshold = NULL)
```

`cfg$assay`为`logcounts`，`cfg$hvg_n`为6000。导出完整方差表与高变基因列表后，使用`sce[chosen, ]`建立子对象，使后续CA、基因分配和图表共享同一特征顺序。

## 5.3 CA与方向聚类

CA调用将输入矩阵和配置中的维数、残差类型及坐标选项传给APL：

```r
ca <- timed("CA", do.call(APL::cacomp,
  c(list(obj = assay(sce_sub, cfg$assay), top = nrow(sce_sub)), cfg$ca)))
```

`top=nrow(sce_sub)`将已经选定的所有6000个特征交给CA。返回对象中，`prin_coords_cols`为细胞主坐标，`prin_coords_rows`为基因主坐标，`std_coords_cols`与`std_coords_rows`为标准坐标，`D`保存奇异值。脚本检查细胞数、维数和有限值后保存对象。

CAdir通过`dirclust_splitmerge`接收该对象。配置中的`k`、`cutoff`、`min_cells`、`qcutoff`、`max_iter`和`keep_log`分别控制初始方向数、拆分合并角度、最小簇规模、基因候选范围、迭代上限和历史保存。上游`dirclust.R`中的`dist_to_line`实现第3.3节距离公式；`total_least_squares`使用`irlba`提取方向；`splitmerge.R`组织外层拆分合并。

## 5.4 完整基因导出与排名

实际导出先按全部CA基因ID建立结果表，再通过名称索引填入上游分配：

```r
gene_cl <- setNames(as.character(cadir@gene_clusters), names(cadir@gene_clusters))
gene_results <- data.frame(gene_id = rownames(ca@prin_coords_rows),
  cluster = unname(gene_cl[rownames(ca@prin_coords_rows)]))
```

因此6000个输入基因均保存在导出表中，1200个有簇号，4800个为NA。排名由`CAdir::rank_genes(cadir=cadir, caobj=ca)`执行。上游核心得分语句为：

```r
score <- gene_coords[, 1] - (gene_coords[, 2] * alpha)
ranking <- ranking[order(ranking$Score, decreasing = TRUE), ]
ranking$Rank <- seq_len(nrow(ranking))
```

这里两列`gene_coords`依次是关联图投影和正交距离。保存实际CA对象、alpha及排名阶段RNG，将每个得分绑定到本次运行的几何坐标。

## 5.5 自动注释与参考评价

注释调用指定`method="goa"`、`set="CellMarker"`、`org="mm"`及`cost="logpval"`，保存自动预测与原簇号的对应。评价使用输入原参考列`cell_ontology_class`。`export_results`先建立含`cell_id`、`cluster`和`reference`的表，再调用`aricode::clustComp`计算指标，并导出列联表。自动预测名称单独存放在`predicted_annotations.tsv`。

## 5.6 HSC基线与共同输入

HSC的`prepare_common.R`执行共同QC、归一化、HVG及标签固定，输出`shared-hvg-sce.rds`。正式入口`formal_run.R`根据方法名执行CA方向聚类或PCA图聚类，所有种子读取相同表达对象。基线的关键参数如下，变量名与正式配置一致：

```r
# PCA：全部共同HVG，30维，按特征中心化且不做方差缩放
sce <- scater::runPCA(sce, assay.type="logcounts", ncomponents=30,
  ntop=Inf, subset_row=seq_len(nrow(sce)), scale=FALSE,
  BSPARAM=BiocSingular::IrlbaParam(deferred=FALSE, fold=Inf,
    extra.work=7, tol=1e-5, maxit=1000),
  BPPARAM=BiocParallel::SerialParam())

# PCA结果按细胞×维度输入rank-SNN，然后用边权执行Louvain
graph <- scran::buildSNNGraph(pca, d=NA, transposed=TRUE,
  k=15, type="rank", BNPARAM=BiocNeighbors::KmknnParam(),
  BPPARAM=BiocParallel::SerialParam())
community <- igraph::cluster_louvain(graph,
  weights=igraph::E(graph)$weight, resolution=1)
```

本段将配置值展开便于阅读，完整调用顺序和变量连接保存在附录B所列的固定原脚本。`ntop=Inf`使PCA使用共同准备的6000个特征；`d=NA`表示直接使用输入的PCA表示；`transposed=TRUE`对应细胞位于矩阵行的方向。

# 6 LM实验结果与分析

## 6.1 总体结果及作者公开输出对照

LM得到7簇、1200个已分配基因。相对8类原参考，ARI为0.66951870448635153，NMImax为0.74188542311548167。各簇规模和自动名称如表1，与作者固定HTML公开打印的逐簇汇总一致。

**表1　LM逐簇结果（细胞数与基因数均与作者公开汇总一致）**

| 自动预测名称 | 细胞数 | 已分配基因数 |
|---|---:|---:|
| cluster_1 | 940 | 45 |
| Vascular_endothelial_cell | 28 | 184 |
| B_cell | 113 | 200 |
| T_cell | 48 | 192 |
| Macrophage | 76 | 203 |
| Schwalie_et_al.Nature.P1 | 490 | 106 |
| Endothelial_cell | 187 | 270 |
| 合计 | 1882 | 1200 |

作者HTML显示ARI为0.6695187，本次结果按相同显示精度一致。可见运行日志中，第一轮出现两次合并，随后第二轮发生拆分并进入第三轮，记录与本次对应。作者仓库的`results/figure2.qmd/html`对应正式论文Fig3。表1与本文ARI共同构成公开结果对照依据。

## 6.2 Fig3A：细胞与基因联合显示

如图1所示，七个关联图分别展示一个方向，簇内细胞为黄绿色、关联基因为橙色，其他细胞和基因为深绿色及灰色。每簇标出真实排名前五的基因。T细胞方向呈现沿横轴集中的结构；其他簇的纵向离散程度和背景点重叠展示了不同的分离状况。

![图1　LM七簇关联图与真实top5基因（对应原论文Fig3A）。](assets/Fig3A_association_top5.png){width=95%}

基因得分将投影强度和偏离距离结合。`cluster_1`前五名为Cadm2、Syt12、Ntn5、Pax3、Gdnf，其得分依次为−0.230963、−0.258898、−0.288689、−0.347069、−0.382294。这组负分数说明：在该簇的当前alpha下，正交距离惩罚大于投影收益；图中top5表示簇内排序最高的五个基因。完整分数表支持逐个基因解释。

## 6.3 Fig3B/C：免疫与内皮方向

图2展示B细胞预测簇及T细胞、巨噬细胞方向，图3展示两个内皮预测方向。B与T方向夹角为63.9984377°，B与巨噬细胞为72.6956194°；两个内皮方向夹角为66.1100659°。等比例坐标轴便于观察投影几何。

![图2　B细胞簇及T细胞、巨噬细胞的主坐标方向比较（对应Fig3B）。](assets/Fig3B_Bcell_principal.png){width=85%}

![图3　两个内皮预测方向的主坐标比较（对应Fig3C）。](assets/Fig3C_endothelial_principal.png){width=85%}

预测与参考的对应进一步解释了图形。B预测簇含113个细胞，其中63个原参考为B cell、49个为lymphocyte。Macrophage预测簇76个细胞中73个参考为macrophage。Endothelial预测簇187个细胞均为endothelial cell参考，Vascular endothelial预测簇28个细胞中19个为该参考。两个内皮方向的细分来自GOA预测；原参考对它们使用同一个endothelial类别。

## 6.4 Fig3D：实际拆分合并过程

图4根据保存的真实节点、边、坐标和成员表重新组织：上半部给出22节点、23条边的完整拓扑，节点直接标明阶段簇号与细胞数；下半部放大合并簇C2及其拆分后的C2、C7三个关联图。21个非根节点的完整关联图按初始、合并、拆分三个阶段分组放在附录D，每个面板保留该阶段成员、坐标、自动注释和细胞数。

![图4　LM真实拆分合并历史（对应Fig3D）。](assets/Fig3D_actual_split_merge_history.png){width=95%}

历史图使用`keep_end=FALSE`展示到最后一次拆分，最终成员表则来自随后的细化。因此一个末层25细胞分支与最终28细胞簇分别代表不同计算时点。历史注释保留Immune cell、Bergmann glial cell等上游预测名称，反映当时的基因富集结果。该图把初始8方向到最终7簇的调整过程与细胞几何联系起来。

## 6.5 S1A/B：全部方向的定量关系

图5给出7×7两两方向角矩阵，图6将七个基准关联图及其他方向投影组织成49个面板。前者适合读出明确角度，后者便于比较同一基准下其他簇的投影位置。

![图5　全部簇方向的两两夹角，单位为度（对应S1A）。](assets/S1A_direction_angle_heatmap.png){width=85%}

![图6　七个基准方向的关联图与方向投影矩阵（对应S1B）。](assets/S1B_direction_projection_matrix.png){width=95%}

方向接近表示表达关联几何相近；结合原参考、自动注释和基因排名，可讨论哪些簇具有相似表达成分。方向角表保存了完整精度，补充了图中面板缩放后的视觉信息。

## 6.6 S1C：预测分区与参考标签

图7保留1882个细胞在七个预测簇与八类原参考之间的全部流量。流量表、列联表和指标使用相同细胞ID，因此可以从总体ARI进一步定位到具体类别。

![图7　LM七簇与八类原参考的细胞流量（对应S1C）。](assets/S1C_reference_sankey.png){width=95%}

参考重叠显示，`cluster_1`以skeletal muscle satellite cell为最大类别（526／940），Schwalie命名簇以mesenchymal stem cell为最大类别（488／490）。各簇的组成有不同纯度，解释了总体指标与局部结构之间的关系。自动预测提供基因集层面的注释，参考流量提供已发布标签层面的对应。

## 6.7 S1D/E：标准坐标与主坐标

图8和图9将对应的免疫、内皮展示转换为标准坐标，并叠加相同簇的方向。方向按奇异值逐轴转换，细胞与方向坐标由实际对象计算。

![图8　免疫方向的标准坐标关联图（对应S1D）。](assets/S1D_Bcell_standard.png){width=85%}

![图9　内皮方向的标准坐标关联图（对应S1E）。](assets/S1E_endothelial_standard.png){width=85%}

本次两组比较中的最大角度变化为27.5359338°。这一结果展示了各轴缩放如何改变方向关系。主坐标图用于解释原聚类方向角，标准坐标图用于观察与联合显示基因相联系的坐标表达。修复后的底部图例完整显示比较方向。

## 6.8 资源记录与数值检查

LM本次真实案例进程耗时36.3743秒，R进程峰值RSS为2278652 KiB，约2.173 GiB。阶段记录中，CA为6.535秒，CAdir为3.770秒；进程总耗时还包括读取、检查、排名、注释及导出。

独立检查从保存对象重算CA与关联图坐标、1200个基因分数及排名、ARI／NMI、GOA超几何与校正概率、Hungarian目标以及历史拓扑。最终图例修复经复验，九图和科学表采用固定提交。通过这些记录，数值、图形和运行对象形成可追溯对应。

# 7 HSC新数据对照结果

## 7.1 共同队列与比较设计

共同QC由1920个候选细胞保留1656个，得到40721个合格基因和6000个共享高变基因。两种方法使用相同表达矩阵及1641细胞评价集合，各运行五个种子。图10展示质量控制与最终队列组成。

![图10　HSC共同QC与聚类／评价队列组成。](assets/HSC_04-common-cohort.png){width=90%}

比较保持了输入、特征、降维维数、参考集合及预定种子的一致；CAdir的方向更新、拆分合并与PCA-SNN-Louvain的社区划分分别按各自配置执行。

## 7.2 全部种子的指标

**表2　HSC两方法五种子完整结果**

| 方法 | 种子 | ARI | NMImax | 簇数 |
|---|---:|---:|---:|---:|
| CAdir | 2358 | 0.288542 | 0.335759 | 11 |
| CAdir | 101 | 0.293858 | 0.346271 | 9 |
| CAdir | 202 | 0.291506 | 0.343414 | 10 |
| CAdir | 303 | 0.289742 | 0.342399 | 10 |
| CAdir | 404 | 0.294305 | 0.345318 | 9 |
| PCA＋SNN＋Louvain | 2358 | 0.266975 | 0.356258 | 7 |
| PCA＋SNN＋Louvain | 101 | 0.269439 | 0.356192 | 7 |
| PCA＋SNN＋Louvain | 202 | 0.269345 | 0.356464 | 7 |
| PCA＋SNN＋Louvain | 303 | 0.268724 | 0.358623 | 7 |
| PCA＋SNN＋Louvain | 404 | 0.269799 | 0.359383 | 7 |

图11展示全部十次运行。两方法成功次数均为5／5。CAdir的ARI范围为0.288542—0.294305，基线为0.266975—0.269799；CAdir的NMImax范围为0.335759—0.346271，基线为0.356192—0.359383。

![图11　HSC两方法五种子ARI与NMImax。](assets/HSC_01-all-seed-ARI-NMI.png){width=95%}

**表3　HSC结果的中位数汇总**

| 指标 | CAdir | PCA＋SNN＋Louvain |
|---|---:|---:|
| ARI | 0.291506398370853 | 0.269345381294258 |
| NMImax | 0.343414049181671 | 0.356463934525198 |
| 核心耗时／秒 | 13.321 | 5.331 |
| 最终簇数 | 9—11 | 7 |
| 成功运行 | 5／5 | 5／5 |

核心耗时分别记录CA＋方向聚类和PCA＋rank-SNN＋Louvain，输出序列化与额外基因排名在各自记录中单独计时。

## 7.3 结果解释

CAdir的ARI中位数比基线高0.022161，NMImax中位数低0.013050。ARI从细胞对是否共同分组衡量一致性，并校正随机期望；NMImax以共享信息相对于较大分区熵归一化。CAdir产生9—11簇，基线产生7簇，聚类粒度与参考类别分布共同影响这两种度量，因而呈现不同排序。

以预定种子2358为展示例，图12、13分别给出每一参考类别在预测簇之间的分布，每列归一化到100%。完整列联表同时保留细胞计数，可进一步检查各簇的参考组成。五个种子提供计算初始化变化下的描述，所有种子均进入汇总。

![图12　HSC CAdir种子2358：各参考类别在预测簇间的分布。](assets/HSC_02-cadir-seed2358-reference-share.png){width=95%}

![图13　HSC基线种子2358：各参考类别在预测簇间的分布。](assets/HSC_02-pca_snn_louvain-seed2358-reference-share.png){width=95%}

HSC结果的独立检查重新计算了十次指标，并检查保存对象、输入ID、输出完整性及主要图表。最大数值差异处于浮点舍入量级。

# 8 综合讨论与实验体会

## 8.1 原论文案例与新数据之间的联系

LM以组织类型相对明确的参考标签展示CAdir的联合输出：细胞簇、关联基因、自动名称及方向关系。HSC以造血干／祖细胞免疫表型标签开展方法比较，呈现出更细的预测分区和较低的参考一致性指标。两组实验分别回答“原案例怎样实现并解释”和“共享新输入下方法表现怎样”的问题。

LM的ARI为0.669519、HSC的CAdir中位ARI为0.291506。这些数值对应各自数据、标签和实际运行环境。LM的参考包含肌肉、间充质及免疫细胞，HSC的参考围绕造血干／祖细胞分化。比较结果时，应结合各自标签粒度、分区规模及几何展示解释。HSC同队列两方法对照提供了评价算法相对表现的直接依据。

## 8.2 联合聚类的解释价值

CAdir的价值体现在输出之间的连接。一个细胞方向对应一个分组，该分组关联一组基因，基因可按$S_\alpha$排序并参与富集，关联图显示聚类与基因的几何关系。LM的九图从单簇、簇间、历史和参考对应四个角度解释同一批对象，使读者可以逐层追踪结论。

图中名称按其生成方式解读：CellMarker提供GOA自动预测，原参考提供标签对应。内皮方向展示了自动注释在原参考粗类别内部给出的细分；B簇的混合参考组成展示了基因预测名与细胞标签之间的实际关系。保留这些结果有助于理解方法在不同信息来源下的表现。

## 8.3 指标与可视化的互补

ARI和NMI给出总体一致性，而关联图、方向角、流量和列联表定位具体差异。HSC中指标的不同排序说明，同时呈现两项评价能够提供更完整的描述。LM中巨噬细胞簇参考重叠较高，而B预测簇含有较多lymphocyte参考，进一步说明总体分数由不同局部结构共同构成。

## 8.4 可重复计算与调试经验

本次实验将输入文件哈希、明确ID、有效配置、实际CA对象、RNG、alpha与完整排名共同保存。基底符号问题的排查通过实际CA轴及排名变化得到解释，形成了固定／对齐基底下的排名重放方法。图表从保存对象生成，使数值计算、图形展示和版式修复各有明确输入。

实践中，脚本入口的Python层管理文件和状态，R层负责科学计算，JSON及TSV连接配置、指标和图表。按层保存对象及日志，使环境调试、数值检查和结果解释能够对应到具体阶段。独立数值复核则为图形和汇总指标提供了计算证据。

# 9 结论

本文完成了CAdir的LM原论文案例分析和HSC新数据对照实验。LM使用1882个细胞和6000个高变基因，得到7个细胞簇、1200个已分配基因，ARI为0.669519、NMImax为0.741885，完成原论文Fig3及关联S1的九项分析，核心汇总与作者公开运行记录对应。HSC采用共同QC、归一化、特征与评价集合，完成两方法各五种子实验，CAdir表现为ARI较高、NMImax较低及较细的预测分区。

方法分析与代码分析说明，CA提供细胞与基因的关联表示，方向分配与总最小二乘更新产生细胞分组，拆分合并调整簇数，基因排名与GOA连接分组和解释。实际对象、完整表格、九图、对照结果与独立检查记录共同构成了本报告的实验依据。

# 参考文献

[1] Kohl C, Vingron M. CAdir: Joint clustering of cells and genes for single-cell transcriptomics with visualization-driven cluster quality assessment. PLOS Computational Biology, 2026, 22(6): e1014418. DOI: [10.1371/journal.pcbi.1014418](https://doi.org/10.1371/journal.pcbi.1014418).

[2] The Tabula Muris Consortium. Single-cell transcriptomics of 20 mouse organs creates a Tabula Muris. Nature, 2018, 562: 367–372. DOI: [10.1038/s41586-018-0590-4](https://doi.org/10.1038/s41586-018-0590-4).

[3] Nestorowa S, Hamey F K, Pijuan Sala B, et al. A single-cell resolution map of mouse hematopoietic stem and progenitor cell differentiation. Blood, 2016, 128(8): e20–e31. DOI: [10.1182/blood-2016-05-716480](https://doi.org/10.1182/blood-2016-05-716480).

[4] Huber W, Carey V J, Gentleman R, et al. Orchestrating high-throughput genomic analysis with Bioconductor. Nature Methods, 2015, 12: 115–121. DOI: [10.1038/nmeth.3252](https://doi.org/10.1038/nmeth.3252).

[5] Lun A T L, McCarthy D J, Marioni J C. A step-by-step workflow for low-level analysis of single-cell RNA-seq data with Bioconductor. F1000Research, 2016, 5: 2122. [PubMed记录](https://pubmed.ncbi.nlm.nih.gov/27909575/).

[6] Blondel V D, Guillaume J L, Lambiotte R, Lefebvre E. Fast unfolding of communities in large networks. Journal of Statistical Mechanics: Theory and Experiment, 2008, 2008(10): P10008. DOI: [10.1088/1742-5468/2008/10/P10008](https://doi.org/10.1088/1742-5468/2008/10/P10008).

[7] Hubert L, Arabie P. Comparing partitions. Journal of Classification, 1985, 2: 193–218. DOI: [10.1007/BF01908075](https://doi.org/10.1007/BF01908075).

[8] Zhao Y, Kohl C, Rosebrock D, et al. CAbiNet: joint clustering and visualization of cells and genes for single-cell transcriptomics. Nucleic Acids Research, 2024, 52(13): e57. DOI: [10.1093/nar/gkae480](https://doi.org/10.1093/nar/gkae480).

[9] Castanho E N, Aidos H, Madeira S C. Biclustering data analysis: a comprehensive survey. Briefings in Bioinformatics, 2024, 25(4): bbae342. DOI: [10.1093/bib/bbae342](https://doi.org/10.1093/bib/bbae342).

[10] Fu Z, Chen C, Wang S, et al. iVAE: an interpretable representation learning framework enhances clustering performance for single-cell data. BMC Biology, 2025, 23: 213. DOI: [10.1186/s12915-025-02315-7](https://doi.org/10.1186/s12915-025-02315-7).

[11] Kim H, Park I, Park J E, et al. scICE: enhancing clustering reliability and efficiency of scRNA-seq data with multi-cluster label consistency evaluation. Nature Communications, 2025, 16: 6031. DOI: [10.1038/s41467-025-60702-8](https://doi.org/10.1038/s41467-025-60702-8).

[12] Sant C, Mucke L, Corces M R. CHOIR improves significance-based detection of cell types and states from single-cell data. Nature Genetics, 2025, 57: 1309–1319. DOI: [10.1038/s41588-025-02148-8](https://doi.org/10.1038/s41588-025-02148-8).

[13] Yin Y H, Wang F, Li W, et al. Comparative benchmarking of single-cell clustering algorithms for transcriptomic and proteomic data. Genome Biology, 2025, 26: 265. DOI: [10.1186/s13059-025-03719-y](https://doi.org/10.1186/s13059-025-03719-y).

[14] Ge Q, Sheng Y, Lu J, et al. Single-cell RNA-seq data normalization: A benchmarking study. PLOS One, 2025, 20(12): e0335102. DOI: [10.1371/journal.pone.0335102](https://doi.org/10.1371/journal.pone.0335102).

[15] Fang C, Selega A, Campbell K R. Beyond benchmarking and towards predictive models of dataset-specific single-cell RNA-seq pipeline performance. Genome Biology, 2024, 25: 159. DOI: [10.1186/s13059-024-03304-9](https://doi.org/10.1186/s13059-024-03304-9).

# 附录A 源码、数据与固定成果

## A.1 源码地址

- 项目源码：[Yang2Krown/cadir-research-training](https://github.com/Yang2Krown/cadir-research-training)。
- 作者分析代码：[VingronLab/CAdir_results](https://github.com/VingronLab/CAdir_results/tree/c15b49578bde38b42fd5db2c9830c10dd441ee4c)。
- CAdir计算包：[VingronLab/CAdir](https://github.com/VingronLab/CAdir/tree/de74a008dfcd0d4fa4f7f93c57aa346892a8d935)。
- APL计算包：[VingronLab/APL](https://github.com/VingronLab/APL/tree/d4d1f40d9ea9f1d9a95b224d45de843334cd617d)。

## A.2 数据地址

- Tabula Muris研究：[GEO GSE109774](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE109774)。LM实际输入、SHA256与特征规模见第2.3节。
- Nestorowa研究：[GEO GSE81682](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE81682)。实验读取scRNAseq legacy资源路径，保留原始表达、元数据及共同准备索引。

## A.3 固定成果与独立检查

| 内容 | 固定提交 |
|---|---|
| LM九项分析与图表 | ab68da7ef154f133ec436275fcf11396f37f884a |
| LM独立最终检查 | 060e32beb41a65c0ef13553cd9827b2aa95ba12f |
| HSC正式实现 | 6cc7b3da67c193da11a67c45a75167d6521438b0 |
| HSC正式结果 | 091a8a4585cabc59a5504380398892bac49044f4 |
| HSC独立结果检查 | b48066cba0bf4cd308f2f75b1134c12f85c576ef |
| HSC结果交付 | 4277589d24bedc2ae85dfc75296426c56e7679fa |

LM独立报告保存在`project-control/reviews/lm-fig3-20261027/report.md`。HSC独立结论及交付入口保存在`project-control/HSC公平实验阶段结论-2026-10-27.md`。本报告图像和原始科学表的文件名、固定提交、大小与SHA256见随附`evidence/材料来源索引.json`。

# 附录B 代码与输出索引

| 模块 | 实际源文件 | 输入与输出 |
|---|---|---|
| LM运行管理 | scripts/run_case.py | 配置与RDS→独立目录、状态及R控制台 |
| LM科学计算 | scripts/pipeline.R | SCE→HVG、CA、CAdir、排名、注释和指标 |
| LM结果检查 | scripts/verify_results.R | 实际对象与表→数值检查记录 |
| 九图生成 | fig3_completion/scripts/render_fig3.R | 保存对象→九图及科学表 |
| 图例布局 | fig3_completion/scripts/repair_s1_legend.R | 相同对象→S1D/E布局修复 |
| HSC共同准备 | fair-experiment/scripts/prepare_common.R | 计数和元数据→QC、共享表达与评价ID |
| HSC正式运行 | fair-experiment/scripts/formal_run.R | 共享表达与种子→CA／PCA、分区和资源 |
| HSC运行管理 | fair-experiment/scripts/run_experiment.py | 准入与配置→两方法五种子执行 |
| HSC排名诊断 | fair-experiment/scripts/rank_diagnostics.R | 实际CA与CAdir→基因得分及图 |

前五行均相对于`cases/tabula_muris_limb/`，后四行相对于`cases/nestorowa_hsc/`。本报告的构建脚本还生成按固定源码定位的行号索引，保存为`evidence/代码段索引.tsv`。LM导出包括完整细胞分配、完整6000基因分配、1200基因排名、方向向量、角矩阵、参考流量及历史节点／边；HSC导出包括十次分区、指标及共同队列ID。

# 附录C 工作记录表

| 已完成工作 | 对应交付 |
|---|---|
| 环境建立与调试 | 固定包版本、环境脚本、加载及工程检查日志 |
| LM分析实现 | 保存对象、九图、16项科学表 |
| LM独立数值检查与图例复验 | 独立报告、重算表及图形检查 |
| 作者公开输出对照 | 固定HTML、逐簇汇总及日志对照 |
| HSC共同准备与方法对照 | 固定QC、评价集合、两方法五种子结果 |
| HSC独立检查 | 指标重算、对象检查及图表复核 |
| 报告写作与排版 | 本报告、代码分析、图表与来源索引 |

| 成员姓名 | 实际承担工作 | 实际工时／小时 | 组内排序 |
|---|---|---:|---:|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

# 附录D 历史节点的放大关联图

三个阶段共21个面板使用已有逐节点坐标与逐细胞成员表绘制。每个面板展示1882个细胞，亮绿色表示该节点的成员，深绿色表示其余细胞；标题列出该阶段簇号、细胞数与历史自动注释。各阶段的细胞总数均为1882。

```{=latex}
\begin{figure}[p]
\centering
\includegraphics[width=0.98\textwidth,height=0.91\textheight,keepaspectratio]{layout/figures/history_initial_panels.pdf}
\caption{初始阶段的8个节点关联图，按两列四行放大显示。}\label{fig:history-initial}
\end{figure}
\begin{figure}[p]
\centering
\includegraphics[width=0.98\textwidth,height=0.83\textheight,keepaspectratio]{layout/figures/history_merge_panels.pdf}
\caption{合并阶段的6个节点关联图，按两列三行放大显示。}\label{fig:history-merge}
\end{figure}
\begin{figure}[p]
\centering
\includegraphics[width=0.98\textwidth,height=0.91\textheight,keepaspectratio]{layout/figures/history_split_panels.pdf}
\caption{拆分阶段的7个节点关联图，按两列四行放大显示。}\label{fig:history-split}
\end{figure}
```

# Background

Single-cell transcriptomics studies variation among individual cells by measuring expression for thousands of genes. A central computational task is to organize cells into groups and connect those groups to interpretable molecular features. Conventional workflows commonly normalize counts, select variable genes, calculate principal components, and identify communities in a neighbor graph. Such workflows provide useful cell partitions, while interpretation draws on gene expression patterns and published cell annotations. CAdir approaches this task through correspondence analysis and directional clustering. Its geometry links cells and genes, allowing cluster assignment, associated-gene ranking, and visualization to be interpreted within a common representation.

This research training project examines that connection through an original-paper case and a new-data comparison. The Limb Muscle subset of Tabula Muris serves as the original case. It contains a mixture of tissue and immune populations and is used to reconstruct association plots, comparisons among directions, split-and-merge history, reference-label flows, and coordinate transformations. The resulting seven clusters and 1,200 assigned genes agree with the core summaries printed in the author's public execution record. Examination of individual clusters connects the aggregate evaluation score to the actual distribution of reference labels. For example, the macrophage prediction shows a concentrated reference composition, while the B-cell prediction includes both B-cell and lymphocyte reference annotations.

The extension uses the Nestorowa mouse hematopoietic stem and progenitor cell study. A shared preparation procedure fixes quality control, normalization, highly variable genes, and evaluation identifiers before comparing methods. CAdir and a principal-component-analysis, shared-nearest-neighbor, and Louvain baseline are each evaluated with five predefined seeds. Their relative ordering differs between the adjusted Rand index and normalized mutual information. The number of predicted clusters also differs, providing a practical example of the relationship between partition granularity and reference agreement. This experiment joins quantitative evaluation with inspection of cluster composition.

The project emphasizes a traceable connection between computation and explanation. Input hashes identify the data objects, explicit identifiers connect matrices and annotations, and source revisions identify the executed implementation. Saved correspondence-analysis coordinates, random-number states, gene-ranking parameters, numerical tables, and figures make the results inspectable at multiple levels. Independent recalculation supports the reported metrics and geometric outputs. The educational contribution is an end-to-end account of how a published clustering method is implemented, evaluated, and explained using real single-cell data. The report combines the original method's mathematical ideas with the practical steps required to obtain interpretable, reproducible experimental evidence.
