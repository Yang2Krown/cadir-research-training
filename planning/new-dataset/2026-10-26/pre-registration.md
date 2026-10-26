# 新数据实验预注册草案：Nestorowa HSC 与无真值簇数基线

日期：2026-10-26；当前配置 GPT-6.1 Sol / high。依据主控《下一阶段启动与验收规则》和限定范围的首阶段结论，在任何新数据聚类、ARI/NMI 或结果图生成前提交。机器可读完整参数见 [pre-registration.json](pre-registration.json)。**这次提交冻结的是可审查草案；原始数据、QC来源与唯一参考标签未实读，正式实验仍 BLOCKED，不是预注册审查通过。**

## 科学问题与输入门槛

研究 CAdir 在不同于原论文已列场景的小鼠造血干/祖细胞研究中的细胞分区与几何解释，与正常流程的 PCA+SNN/Louvain 作对照，不预设优势。只选 Nestorowa/GSE81682 继续准备，不因网络受限切换候选，不根据任何算法分数择数据。

拟用官方 scRNAseq legacy `nestorowa-hsc/2.0.0` 的 counts 与 coldata（EH2694/EH2695）；当前新版默认 gypsum `2024-04-18` 不作为静默替代。该选择是可追溯且可直接读取的旧官方资源路线，并非宣称已拿到特定细胞集。输入内容 SHA256/大小、真实 shape、1656/1920细胞 ID关系、原作者过滤/2017修正计数对应关系、sample/donor/condition 与标签覆盖均为 **NOT_VERIFIED**。

下载解除后，先固定 `data-input-lock.json`：官方字节大小/SHA、完整基因与细胞 ID、各来源 ID集合差分、样本/供者/条件字段、原处理历史、每条QC规则与排除原因、最终细胞/HVG清单及唯一参考标签映射。不得凑1656、1920或论文目标数。作者宽/窄FACS门类存在重叠；最终唯一标签层级、冲突与缺失处理须经实读和来源论证，另一个提交冻结，**在任何新数据聚类之前**独立复核通过。若只能获得多标签重叠、无法得到有出处的唯一层级，不硬压标签做ARI/NMI；正式外部评价继续阻塞。

原 CAdir 正文和固定67脚本/QMD覆盖支持新增候选，但官方 S1 PDF全文仍未读取，须补足或由独立审查明确裁定覆盖是否充分；不能把一次没有搜到名字视为绝对未用。

## 共同预处理与公平性

两方法、五种子使用同一 QC 后细胞集、同一 logcounts 和一次固定的6000HVG清单。计数必须为基因×细胞、有限非负整数；基因/细胞ID唯一且非空，metadata按ID显式对齐，不猜前缀或默用行位置。保留Ensembl等原始ID，不按符号去重或扩充marker。

拟定的、尚待原数据来源核实的QC规则如下。先分出 `^__` HTSeq统计行和 `^ERCC-[0-9]+` spike-in行；用endogenous读数及检测基因数、ERCC占endogenous+ERCC比例审计。zero-endogenous细胞以技术原因排除；其余细胞在池化层面按 log2总读数、log2检测基因数的下侧及未log的ERCC比例上侧，以中位数±3×标准化MAD（常数1.4826）作严格不等式异常判定。零MAD保留等于中位数者。ERCC缺失时停止并事先修订，不暗换规则。实际保留数/排除数还未知，不声称这就是原作者QC；不依标签、基因型、稀有类或后续表现删细胞，不新增doublet检测，也不假装已有稳定线粒体注释。

QC后保留至少3细胞检测到的endogenous基因。用endogenous库大小/均值作size factor，`scuttle::logNormCounts` 一次得到 log2(count/sizeFactor+1)，不另做Z-score、批次整合或标签平衡。若实读对象已有logcounts，先确认来源公式；停止审议后是否复用，不能再归一化一遍。HVG采用 `scran::modelGeneVar`、`getTopHVGs(n=6000,var.threshold=NULL)`，不按标签分块；精确方差并列保留原基因顺序。若不足6000基因、100细胞、30有效维度，或HVG矩阵出现zero行/列，停止并保留失败，不让某方法静默少用细胞或降低维度。

这一共同输入不等于强迫两方法使用同一种几何：CAdir照常CA，基线照常中心化PCA。预处理会影响表现，这是待检验设计，不能据此外推所有预处理或声称完整复现原作者。

## 参数与种子

固定种子为 **2358、101、202、303、404**；共同准备种子20261026；统一 R RNG 为 Mersenne-Twister/Inversion/Rejection。种子只是事先列定的五个重复，不来自标签或筛选分数。

| 方法 | 冻结的拟定配置 | 无真值簇数说明 |
| --- | --- | --- |
| CAdir | 6000HVG logcounts；APL 30维、principal行列坐标、Pearson残差、python=FALSE（本路径R/irlba）、clip=FALSE/cutoff=NULL等固定版本默认；splitmerge初始k8、55°、min_cells20、qcutoff0.8、max_iter50、init=kmeanspp、epochs/reps=NULL、convergence_thr0.001，其余参数逐项列于JSON；核心阶段make_plots=FALSE | 完整转移首案例的k8/55°/30维/6000HVG，不看HSC标签数；k仅初始化，允许正常split/merge，承认该迁移可能表现差，不调参追分 |
| PCA+SNN/Louvain | 同一logcounts/HVG；30个中心化、不按基因方差缩放的PCA分量，BiocSingular IrlbaParam；SNN k15、rank权重、精确Kmknn、单进程；已PCA矩阵以transposed=TRUE、d=NA入图，避免重复降维；igraph Louvain resolution1，保留小簇和单细胞簇 | 正常邻域图社区工作流自行给簇数；不输入真值K、不扫resolution、不用UMAP/t-SNE坐标聚类 |

基线API参数已对本环境实际函数签名检查；尚未运行PCA、建图或Louvain。核心版本为 R4.4.1、Bioconductor3.19、APL1.9.1、CAdir0.0.99、scran1.32.0、scater1.32.1、scuttle1.14.0、igraph2.3.3、BiocNeighbors1.22.0、BiocSingular1.20.0。每项函数的参数/函数体摘要与实际版本仍须在正式run记录，包版本号不是全部二进制等价的证明。

## 评价及失败处理

唯一参考标签只能来自经审查固定的作者实验/index-sort/FACS元数据。宽窄门类可以重叠，不是现成独立功能谱系真值；不以表达聚类、CellMarker或SingleR预测补成真值。缺失/冲突标签的QC合格细胞继续参与聚类，仅按事先映射从外部指标中排除，固定n_total/n_evaluated/n_excluded和原因；两方法评价同一细胞集。n_evaluated<2或不足两个参考类别时标SKIPPED，不造标签或改QC。

ARI用列联计数组合数公式；NMI为 **MI/max(H_cluster,H_reference)**，自然对数。一个预测簇配多类参考时NMI=0；退化ARI分母处理在JSON明列，不用不同归一化NMI混比。报告全部五种子的逐项ARI/NMI、簇数/规模、成功数/5、成功样本的中位数/IQR/min/max；不只挑最优种子、不把成功者均值当无失败结果，不用五个随机seed给出泛化显著性结论。

CAdir基因分配、完整分数/排名和Association Plot为几何解释输出，基线未提供同等双聚类真值，不编造基因准确率或生物学验证。自动注释不进入本次主要实验。

全部尝试独立目录，失败、超时、OOM与不利结果保留。技术性重试须同配置/seed并保留原失败；参数或来源变更须说明原因、新commit并在评价前重审。不能从结果中挑参数、删除失败种子或申请已未授权的付费资源。

## R3与资源测量

每次实际CA对象、轴顺序/符号、RNG前后状态、alpha、实际安装函数/来源、完整分数与排名均保存。上游符号/正正交限随机采样不改，排名只在固定CA基底或实际验证过的对齐范围内比较；同seed不能宣称任意基底排名等价。若需方法变体，另立协议，不混入本实验。

预算2核/8GiB，每个方法/seed顺序运行，核心超时600秒，不并发争抢资源。共同QC/归一化/HVG单独计时，下载/安装不算算法耗时。每个核心R进程加载共同输入后，分别计CA+splitmerge（含内置基因分配）与PCA+SNN+Louvain；明确记录方法步骤差异。每50ms采样核心阶段RSS，并在核心结束时记录含启动/读入的VmHWM；两种口径不混用。CAdir额外排名/绘图放另一个诊断进程并单列资源，避免额外功能暗中进入核心比较或被完全隐去。不因一次诊断给出普遍性能优势。

## 放行和命令

当前可执行获取/结构审计命令见 [新case说明](../../../cases/nestorowa_hsc/README.md)。协议结构检查通过；`check_protocol.py --require-ready` 当前必须退出2，明确阻止把草案当可运行方案。正式runner尚未实现，也没有运行任何新数据CAdir/基线或ARI/NMI。

预计正式入口接口为 `run_experiment.R --protocol PRE_REG_JSON --input-lock DATA_INPUT_LOCK --method {cadir,pca_snn_louvain} --seed FIXED_SEED --output-root NEW_DIR`。这是审查后才实施的接口说明，不是当前存在或可执行的脚本。正式运行前必须先完成来源/数据/唯一标签/QC锁、独立Sol High设计审查、再提交实现和冻结输入/代码哈希；当前任务止于可审核准备物。
