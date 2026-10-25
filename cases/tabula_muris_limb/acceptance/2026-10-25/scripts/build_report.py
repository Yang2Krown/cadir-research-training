#!/usr/bin/env python3
"""Build a Chinese acceptance report and a traceable Figure 2 comparison."""
from pathlib import Path
import json
import subprocess
import pandas as pd

review=Path(__file__).resolve().parents[1]
case=review.parents[1]
rows=[
 ('输入数据','Figure 2: data/real/discussed/preprocessed/tabula_muris_preprocessed_filtered.rds；论文页描述1882细胞',
  '附件tabula_muris_limb_preproc.rds，SHA256已核对；13204基因×1882细胞，Limb_Muscle、method=facs',
  'source_check/figure2.qmd:L56-L65；基线results/data_audit.json；freeze/baseline_manifest.json',
  '细胞数与组织相符，但缺少作者filtered对象的哈希和逐细胞对应，尚不能证明输入完全等价'),
 ('预处理','Figure 2直接读预处理RDS并使用logcounts；通用脚本另含QC、scran归一化、PCA/UMAP、scDblFinder评分',
  '复用已有logcounts/sizeFactor，未再次QC/归一化；55个标记doublet按原输入保留',
  'source_check/data_preprocessing.R；基线results/data_audit.json；基线scripts/pipeline.R:audit_object',
  '对象证据支持已归一化，但不能从通用脚本反推两份数据经过完全相同过滤'),
 ('HVG','modelGeneVar(logcounts)；getTopHVGs(n=6000,var.threshold=NULL)',
  '相同方法，实际6000 HVG，保留1882细胞',
  'source_check/figure2.qmd:L67-L74；基线results/selection.json；最终运行hvg_genes.tsv',
  'HVG选择调用一致，但依赖原输入；不能仅由数量一致推出基因清单一致'),
 ('额外marker','读取tabula_muris_marker_genes.csv，合并其中已表达基因，与HVG去重，最终数可能超过6000',
  '缺失该CSV，明确不扩充；不是用CellMarker注释表替代',
  'source_check/figure2.qmd:L58-L73；source_check/marker_search.json',
  '可能改变CA几何、分配、共聚类基因及注释；影响方向/幅度尚未测量'),
 ('CA后端与输入','logcounts；Pearson residuals；princ_coords=3；python=TRUE',
  'logcounts；Pearson residuals；princ_coords=3；python=FALSE，CPU R',
  'source_check/figure2.qmd:L76-L83；基线results/config.json',
  '后端数值路径及随机/线性代数差异尚未做等价性比较，不能假定完全相同'),
 ('CA维度','dims=30；top=nrow(sce_sub)',
  'dims=30；top=6000',
  'source_check/figure2.qmd:L78-L81；基线results/config.json',
  '维度一致；作者若加入额外marker，top及输入基因会不同'),
 ('聚类显式参数','k=8；cutoff=55；method=random；apl_quant=.99；counts=NULL；min_cells=20；reps=NULL；make_plots=TRUE；qcutoff=.8；convergence_thr=.001',
  '这些显式参数一致，最终7簇；未把参考8类当作目标簇数',
  'source_check/figure2.qmd:L92-L105；基线results/config.json、console.log',
  'k是初始化参数，split/merge可改变簇数；不因7≠8而改参数'),
 ('公共实现默认值','Figure 2未全部显式指定；当前公开实现默认epochs=NULL、max_iter=50、init=kmeanspp、keep_log=TRUE、apl_cutoff_reps=100',
  '显式固定上述默认值；未修改上游算法',
  'CAdir de74a008:R/splitmerge.R:L335-L352；基线results/config.json',
  '与当前公开实现一致，但作者锁指向本地CAdir，无法证明作者执行的是同一提交'),
 ('随机性','Figure 2在CAdir前set.seed(2358)；该CA代码段之前未见显式seed',
  'seed=2358；Mersenne-Twister/Inversion/Rejection；CA、CAdir和排序前分别重置',
  'source_check/figure2.qmd:L92；基线scripts/pipeline.R；基线results/config.json',
  '两次同种子分配相同仅证明本环境可复跑；未验证多种子稳健性'),
 ('注释资源/方法','CellMarker 2.0；GOA；org=mm；universe=入选基因；cost=logpval；filter_literature=FALSE',
  '相同资源家族及调用；固定公开CAdir内置Mouse数据35197条；默认alpha=.05、size 10..500',
  'source_check/figure2.qmd:L111-L119；source_check/resource_documentation.R；annotation/review_status.json',
  '资源原始版本在作者私有本地代码中是否逐条相同未知；保留文献标签，不强制改标准细胞名'),
 ('注释分配机制','公开实现：每簇前nclusters候选参与Hungarian全局一对一匹配，再按alpha门控',
  '重建7候选/簇的匹配，与保存的预测逐项一致',
  'source_check/celltype_anno.R:run_hungarian、annotate_by_gse；annotation/hungarian_assignments.tsv',
  '最终标签可不是该簇独立最强候选；不能据不同标签即推断新的真实生物亚型'),
 ('软件版本/来源','作者锁R4.4.1/Bioc3.19；APL1.9.1、aricode1.0.3；scater1.32.0；CAdir为本地目录，无公开SHA',
  'R4.4.1/Bioc3.19；APL1.9.1、aricode1.0.3匹配；scater1.32.1；CAdir公开de74a008；其余见完整清单',
  'freeze/upstream-renv.lock、sources.json、upstream_observed.json；基线evidence/author-lock-version-comparison.tsv',
  '不是完整作者环境；214锁定包缺失、197版本不同、85匹配，不对未执行的基准路径作运行声明'),
 ('评价/绘图','aricode::clustComp(cadir,cell_ontology_class)；Association Plot与UMAP展示',
  '相同原始标签做ARI/NMI；已输出Association Plot与CA图；本轮新增两种归一化混淆矩阵',
  'source_check/figure2.qmd:L126-L145；基线results/metrics.json；tables/counts_7x8.tsv',
  '参考标签只作事后评价；未完整重绘作者所有UMAP/论文子图；标签一致不是独立生物学验证')
]
comparison=pd.DataFrame(rows,columns=['项目','作者配置','当前配置','证据位置','可能影响与边界'])
comparison.to_csv(review/'tables/figure2_comparison.tsv',sep='\t',index=False)

def markdown_table(df):
    def val(x):return str(x).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(val,df.columns))+' |','| '+' | '.join(['---']*len(df.columns))+' |']+
                     ['| '+' | '.join(map(val,row))+' |' for row in df.itertuples(index=False,name=None)])

counts=pd.read_csv(review/'tables/counts_7x8.tsv',sep='\t')
clusters=pd.read_csv(review/'tables/cluster_composition.tsv',sep='\t')
refs=pd.read_csv(review/'tables/reference_distribution.tsv',sep='\t')
decisions=pd.read_csv(review/'annotation/annotation_decisions.tsv',sep='\t')
metrics=json.loads((case/'results/metrics.json').read_text())
freeze=json.loads((review/'freeze/baseline_manifest.json').read_text())
keycols=decisions[['cluster','original_prediction','best_gene_set','best_padj','hungarian_padj','annotation_accepted']].copy()
for c in ['best_padj','hungarian_padj']:keycols[c]=keycols[c].map(lambda x:f'{x:.4g}')
summary=clusters[['cluster','cells','dominant_reference','dominant_count','dominant_fraction']].copy()
summary['dominant_fraction']=summary.dominant_fraction.map(lambda x:f'{x:.2%}')
refsummary=refs[['reference','cells','observed_clusters','allocation']]
report=f'''# Tabula Muris Limb Muscle 结果验收与论文流程对照

日期：2026-10-25（Asia/Shanghai）。本轮只读取现有数据、分配和RDS，并在固定分配上重建GOA证据；没有重跑HVG/CA/CAdir，没有调参、改名或新增数据集。

## 验收结论与证据等级

**当前基线是成功且可复跑的单案例；尚未达到严格Figure 2复现，也没有多种子稳健性或独立生物学验证的证据。** 基线ARI={metrics['ARI']:.15f}、NMI={metrics['NMI']:.15f}维持原值，没有通过重分组提高指标。

已直接证实：1882个细胞的7×8计数及两种归一化分布；两大簇的构成；公开注释算法在保存分配上的显著性、支持基因和匹配结果；已核查范围内额外marker文件缺失。尚未证实：原始参考标签绝对正确、每个预测名称对应真实亚型、7簇是否在不同随机种子下稳定、附件与作者filtered数据等价、不同CA后端等价、完整论文结果一致。

## 1. 冻结与可复跑边界

当前分支 `{freeze['git_branch']}`；研究仓库HEAD为 `{freeze['git_HEAD']}`。工作区代码未提交，**不能用该HEAD冒充当前分析代码版本**：当前代码、配置、两个成功运行、历史失败和输入通过 [逐文件SHA256冻结清单](../freeze/baseline_manifest.json) 标识；[代码快照](../freeze/scripts/) 与配置另存。输入43,383,527字节，SHA256为 `af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b`。

最终运行：`{freeze['final_run']}`；首次成功：`{freeze['first_successful_run']}`。主流程31.32秒、R峰值RSS约2.17GiB是单次工程诊断，不是算法性能基准。本轮没有覆盖 `results/`、`figures/`、脚本、配置、latest状态或任何既有运行文件；最终保全检查单独输出。

基线种子2358，RNG为Mersenne-Twister/Inversion/Rejection；HVG=6000、CA维度30、初始k=8、55°、qcutoff=.8、min_cells=20，其余参数见冻结配置。R4.4.1、Bioconductor3.19，APL1.9.1、CAbiNet0.99.2、CAdir0.0.99、SingleCellExperiment1.26.0、scran1.32.0、scater1.32.1、scuttle1.14.0、aricode1.0.3。作者及当前来源详见 [对照表](../tables/figure2_comparison.tsv) 与 `freeze/`；当前CAdir公开提交de74a008dfcd0d4fa4f7f93c57aa346892a8d935，作者锁仅给本地目录。

两次相同种子、相同数据与环境的细胞/基因分配逐项一致，说明**重复执行一致性**；不是独立随机重复，没有估计种子间方差，不能写成“多种子稳健”“稳定性已充分验证”或“方法优越”。

## 2. 7簇与8类参考标签

[宽格式计数TSV](../tables/counts_7x8.tsv)。列是原始cell_ontology_class，行是冻结CAdir簇；不做标签匹配或重命名。

{markdown_table(counts)}

![按簇归一化](../figures/confusion_within_cluster.png)

第一张每行和为100%，表示P(参考类别/簇)，回答“该簇里有什么”。例如cluster_3只有55.75%为B cell，却收纳了全部B cell；不能把簇内占比和参考类召回混为一谈。

![按参考类别归一化](../figures/confusion_within_reference.png)

第二张每列和为100%，表示P(簇/参考类别)，回答“该参考类去了哪里”。两图均固定0..1色标，格内同时保留原始计数。它们是事后描述，不修改分配。PDF版本与绘图输入也随包保留。

### 两个大簇

**cluster_1：940细胞。** 526个skeletal muscle satellite cell（55.96%）与414个skeletal muscle satellite stem cell（44.04%），没有第三类。它分别收纳两类的98.50%和98.81%；两类参考在该簇基本合并，而不是产生一个“纯940细胞的单一参考类型”。不能因此把簇强行拆成两类或把940个细胞统一改名。

**cluster_6：490细胞。** 488个mesenchymal stem cell（99.59%）和2个satellite cell（0.41%），收纳全部495个mesenchymal stem cell中的98.59%。这是参考标签对照所得构成；它与后文的“Schwalie…”注释证据是两条不同记录，不能以488个参考标签直接把预测改成mesenchymal stem cell。

### 小簇和其余簇

- cluster_2（28）：19 endothelial（67.86%）、4 mesenchymal（14.29%）、3 satellite stem（10.71%）、2 satellite（7.14%）。小且混合，不能仅凭预测Vascular_endothelial_cell就认定是已验证的内皮亚型。
- cluster_3（113）：63 B cell（55.75%）、49 lymphocyte（43.36%）、1 satellite（0.88%）；全部B cell在此，但簇并不等于“113个已验证B细胞”。
- cluster_4（48）：33 T cell（68.75%）、9 lymphocyte（18.75%）、3 mesenchymal（6.25%）、2 satellite stem（4.17%）、1 satellite（2.08%）。全部T cell在此，仍含多类标签。
- cluster_5（76）：73 macrophage（96.05%）、2 satellite（2.63%）、1 lymphocyte（1.32%）；全部macrophage在此。
- cluster_7（187）：均为endothelial，收纳206个内皮参考细胞的90.78%；另19个在cluster_2（9.22%）。

各簇主类与占比：

{markdown_table(summary)}

逐参考类的完整分配：

{markdown_table(refsummary)}

因此，“8类变7簇”包含**两个satellite参考类在大簇合并、endothelial被分为两簇、lymphocyte主要进入B/T相关簇**及少量跨簇分配，不能归结为仅缺失一个类。lymphocyte可能存在标签粒度差异，但仅凭本表不能确认其真实亚型。少量分散也不能直接命名为污染、双细胞或新亚型。初始k=8不是要求最终8簇；本轮没有强行匹配簇数。

## 3. 自动注释审查：与参考标签对照分开

本节只使用保存的共聚类基因、固定CellMarker2.0和入选6000基因背景，**没有把cell_ontology_class输入GOA**。在固定分配上重新计算富集和Hungarian匹配，重现保存的全部预测，见 [annotation/review_status.json](../annotation/review_status.json)。此重建不是重跑聚类，也不是另一项独立生物学实验。

关键决策表（完整原始p、BH校正p、支持基因和所有候选均另存）：

{markdown_table(keycols)}

### 未注释的cluster_1

该簇只有45个被CAdir分配的共聚类基因，其中27个出现在与6000基因背景相交后的Mouse资源中；另外18个没有参与资源内的富集证据。20个有重叠的合格候选中，**0个BH校正值≤0.05**。最强候选是原名Type_IB_spiral_ganglion_neuron，仅由Col19a1、Ryr3两基因支持，原始p=0.0107721，BH校正p=0.215442；Hungarian后仍未达门限，所以保留cluster_1。

这说明本次集合和门控下没有获得显著资源标签，**不说明这940个细胞没有细胞类型，也不构成神经元注释**。45/27的基因覆盖可能限制注释，但不能在未实验的情况下断言缺少marker是唯一原因。全45基因及资源覆盖见 [cluster_1_gene_coverage.tsv](../annotation/cluster_1_gene_coverage.tsv)，全部显著性见 [goa_all.tsv](../annotation/goa_all.tsv)。

### Schwalie_et_al.Nature.P1

这是CellMarker资源中的**文献/群体命名基因集**，原始记录来自Mouse、Adipose tissue，PMID 29925944，2018年Nature论文“A stromal cell population that inhibits adipogenesis in mammalian fat depots.”，并非本案例新发现的标准本体标签。原始资源有187个marker；其中93个在当前6000基因背景中。cluster_6的106个共聚类基因中83个映射到资源背景，12个与该集合重叠：

`1700019D03Rik, Adamts16, Aldh1a3, Crispld1, Dpp4, Duoxa1, Efhd1, Ildr2, Pcdh20, Pla1a, Rab38, Sema3c`。

富集GeneRatio=12/83，BgRatio=93/3366，原始p=1.86613e-6，BH校正p=9.33064e-5，经过全局匹配后保留该名称。[原始资源记录](../annotation/schwalie_resource_records.tsv) 与 [逐支持基因](../annotation/support_genes_long.tsv) 可核查。这是共享基因集的富集证据，**不证明Limb Muscle样本变成脂肪组织细胞、也不能直接把它改为mesenchymal stem cell**；后者仅是前节488个参考标签的对照结果。

### 全局匹配与显著性定义

公开实现先按簇保留前7个候选，做跨簇一对一Hungarian分配，再用alpha=.05门控。因此cluster_2的独立最强候选Endothelial_cell（BH=8.94e-8）没有成为最终名称，而得到Vascular_endothelial_cell（BH=.00176770）；cluster_7获得Endothelial_cell（BH=7.18e-39）。这个算法竞争机制不构成两个内皮亚型已经被独立证实的依据。

保留上游的统计定义：超几何检验背景是6000入选基因与**全部资源集合的并集**相交所得3366基因；集合大小10..500；只对有正重叠的合格集合按簇BH校正；匹配矩阵缺失条目cost=0；本次所有实际分配候选都有真实检验行。没有改统计算法或将零重叠候选补成伪显著结果。富集是算法内部支持；参考标签一致是外部标签对照；二者均不能替代独立样本、实验或人工生物学验证。

## 4. 作者Figure 2逐项对照

作者文本以CAdir_results提交c15b49578bde38b42fd5db2c9830c10dd441ee4c的figure2.qmd为准，行号和文件哈希随 [来源快照](../source_check/author_reference_manifest.json) 保留。通用预处理脚本只说明可能步骤，不作为附件完整历史的证明。

{markdown_table(comparison)}

### 缺失marker CSV：本轮有范围核查

核查两个固定作者提交的完整文件名树、已提供材料与云端数据目录；另外只发出2次GitHub元数据请求：当前main提交和最多20条release列表，每次上限2MiB、无重试、不下载数据归档。两请求均HTTP200；main仍是固定c15b495提交，release列表为空。检查范围内未找到tabula_muris_marker_genes.csv，见 [完整核查记录](../source_check/marker_search.json)。

结论只限这些来源，不能证明文件从未存在或作者私下没有该文件。已有CellMarker注释资源不是这份额外marker CSV；不从参考标签反推，不自行编造替代列表。本轮没有获取到新增marker，基线继续明确称为HVG-only案例。

## 5. 下一步只优先补齐一项

**优先取得作者Figure 2额外marker CSV及其来源/哈希，或作者明确说明该文件生成方法。** 它直接定义HVG之外的输入基因集合，是目前可明确定位、但尚未量化的上游配置缺口；在输入基因清单不等价时，继续追逐指标或强迫8簇会掩盖差异。取得后应另建对照输出、保留当前基线，不承诺必然提高ARI/NMI。本轮仅提出这一步，没有联系作者或运行新的变体。

## 6. 交付与复核

完整结果、主要图、复跑入口、来源/软件与关键历史日志随成果包提供。原始输入、两个成功运行的大型RDS仍在原处，路径、大小及SHA256见冻结清单与外部制品索引。成果包不包含原始表达数据、R运行库、缓存或大型中间RDS，大小检查强制≤24MiB。

本轮验收脚本复跑见 [交付README](../README.md)；它只重新生成验收表、图和固定分配GOA证据，不调用全量实验。基线完整实验入口保留在原case/scripts/rerun.sh，包中明确标记其会重跑完整案例。
'''
(review/'report/结果解读报告.md').write_text(report)
subprocess.run(['/workspace/cadir-env/skeleton_runtime/bin/pandoc',
  str(review/'report/结果解读报告.md'),'--from=gfm','--to=html5','--standalone',
  '--embed-resources','--toc','--metadata','title=Tabula Muris Limb Muscle 结果验收',
  '--css',str(review/'report/review.css'),'-o',str(review/'report/结果解读报告.html')],
  cwd=review/'report',check=True)
print('Chinese report and Figure 2 comparison written')
