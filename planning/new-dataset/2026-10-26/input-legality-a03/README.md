# A03 修复与真实输入合法性审计

日期：2026-10-26（Asia/Shanghai）。基于 `d853986e2e3a1cabc9f3f728f616e402432257ec` 的隔离分支 `fix/nestorowa-input-audit-a03-20261026`。**实施验证完成，待主控安排独立复验；正式执行许可仍为 false。**

## 已读取的管理依据及范围

管理分支 `control/stage1-quality-20261025` 本轮取得的提交为 `1d99adbae456ad2b6df4898519a64ca826d878a5`。已读取其中：

- `project-control/HSC扩展范围裁定-2026-10-26.md`
- `project-control/reviews/d853986/独立审查报告.md`

原文副本保存在 `control-inputs/`，来源提交、路径、大小/SHA256 见 `control_provenance.json`。本轮没有修改或代签管理裁定。

采纳管理范围：研究固定官方 legacy `nestorowa-hsc/2.0.0` 的 1920 个候选细胞，不宣称恢复原文 1656、网页校正版或原始 flow 表完整对应。仅用发布 broad 六类作为表型参考候选；Rep/donor 不用于生物学重复推断。该范围允许本轮输入合法性审计，但没有授权 QC、归一化、算法、指标或正式实验。

## A03 的修复

当前 `cases/nestorowa_hsc/scripts/audit_inputs.R` 明确分为：

1. `metadata-only COL_RDS MANIFEST NEW_OUT`：只接收元数据和清单，容器不挂载 count/GEO 数据文件，不读取 count 内容或其哈希。
2. `full COUNTS_RDS COL_RDS GEO_GZ MANIFEST NEW_OUT`：先运行同一元数据检查，再核验三份文件的真实字节、矩阵及 GEO 对应。

共享 `metadata_identity.R` 以嵌套 `cell.type` 的显式行名为主键；每个嵌套字段独立检查类型、非空/唯一 ID、行数、集合、原顺序，并用 `match` 生成按 ID 的视图及原行索引。不赋写原元数据行名，不用行数、位置、前缀或复制 count 列名补 ID。缺失/重复/冲突立即失败，并保存差分详情。既有 NA 保留，原对象序列化摘要前后相同。

真实 RDS 还有一个必须区分的细节：原类名为旧 `DataFrame`，当前 S4Vectors 的虚拟类声明没有列出旧的 `rownames/listData` slots。原始 rownames 属性存储为 R 的 S4 NULL 哨兵符号 `\u0001NULL\u0001`；`methods::slot` 和 `rownames()` 解析后均为 NULL。修复不依赖 `slotNames()` 猜测身份，也不把该符号当成 ID；同时记录原始编码类型/符号与语义 NULL。显式非 NULL 顶层 ID 仍必须验证并与嵌套主键匹配。该记录保留了原始 NULL，未补写或改变 RDS。

历史 `recovered-branch/` 副本、已有准备物和旧哈希保持不变。旧三参数调用已由带模式的新接口替代；新的离线容器包装器用于实际执行，未使用当前路径失效的旧 `run-r.sh`。

## 实际使用的输入和环境

使用现存 `/workspace/nestorowa-metadata-preparation/reacquired-20261026/` 中的三份真实数据，没有新下载或替换数据。完整审计在 R 中重新计算大小和 SHA256，之后 Python 再核验源文件未变：

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| counts.rds | 90044893 | `6bf8a84f4db185eb6021ceb53b7d6d33083410e02a6ee7a6df2191f0bbb90563` |
| coldata.rds | 182319 | `16d9e3ee62d27aac74591ccddd064eb2be9b86836591c8ec99d39e1af0bf35bc` |
| GSE81682_HTSeq_counts.txt.gz | 30236635 | `e12745e4087823ae868c6fe82a38510c15730e82ee74e1983def85ed3b7df68a` |

均与 `metadata-preparation/acquisition_manifest.json` 的官方重新获取收据一致；不将它们称为此前失踪原件。

使用已有镜像 `cadir-r-ver:4.4.1-bioc3.19`，R 4.4.1、Matrix 1.7.0、S4Vectors 0.42.1、jsonlite 2.0.0、digest 0.6.39。容器禁网、根文件系统只读，源数据、代码及现有 R 库只读挂载；2 CPU、4 GiB 审计上限。未安装包；没有加载 APL、CAdir 或 CAbiNet。镜像 ID、精确命令、开始时间、耗时、返回码及最终源码哈希见执行收据。这是审计环境记录，不是未来算法环境锁验收。

## 最终真实输入结果

权威本轮实施结果为 `evidence/metadata-only-03/`、`evidence/full-03/` 和 `evidence/metadata_identity_regression_03.json`。

- `counts.rds` 为有效 `dgCMatrix`，46175 行×1920 列，方向为基因×细胞。46175 个基因/特征 ID 与1920个细胞 ID 均显式、非空、唯一。行中含46078个 Ensembl基因ID、92个ERCC、5个HTSeq统计项；本轮仅分类计数，没有删行。
- 全部22595902个稀疏存储值均有限、非负且严格为整数；非有限、负值、非整数均为0。其余隐式零满足相同合法性。没有使用容差接纳小数，也没有计算每细胞 QC 或筛选。
- counts 细胞与三个封装元数据矩阵 ID 集合及原顺序一致，完整按 ID 索引表为 `count_metadata_alignment.tsv` 和 `metadata_alignment.tsv`。基因 ID 全表为 `gene_ids.tsv`。
- GEO 表全量流式读取，以显式基因和细胞 ID 对齐。基因/细胞集合及原顺序均与 RDS 一致，全部 **88656000** 个数值逐项比较，差异 **0**。对应证据为 `geo_correspondence.json`；没有把“同维度”当作内容对应证明。
- 元数据顶层语义 NULL 保留；`cell.type` 为1920×23的 `lgCMatrix`，全部0/1无缺失。diffusion保留1263个NA（421行全缺失），FACS保留4300个NA（430行全缺失）。broad候选1784个分配、136个未分配、0冲突，没有填第七类或删细胞。
- 与原提交逐 ID 对照，44160个成员标记、1920条候选标签、全部缺失/Projected标记均一致；metadata-only和full的元数据结果相同。实现方证据回读共25项通过，见 `implementation_readback.json`，明确不是独立审查。

## 验证器回归及失败保留

9项最终回归检查全部通过：真实NULL/NA不变；旧顶层身份契约会拒绝此真实输入；逆序FACS可按ID精确恢复；拒绝重复ID、缺少嵌套ID、缺细胞、集合冲突、隐式序号顶层ID和legacy原始属性冲突。检查仅修改真实元数据的内存副本，没有生成合成表达矩阵或运行科研流程。

所有失败与早期成功尝试均保留。首轮真实输入审计成功，但回归检查在修改旧对象副本时遇到类slot不兼容；第二轮直接将原始NULL哨兵当ID而失败，均在读取counts前停止。最终实现分别保留原始编码并经R slot解析NULL，第三轮元数据、全量输入及回归全部成功。早期源码副本在 `executed-sources/attempt-01/02/`；它们是运行后、修改前保存的源码快照，不是历史Git提交。首轮回归收据的时间字段曾在运行后组装，具体更正说明见 `attempt_notes.json`，没有覆盖原记录。

最终执行收据在运行前固定源码SHA；`implementation_readback.json` 确认最终源码仍相同、三份源数据字节不变，以及 metadata-only 没有 count/GEO 挂载。原准备包的61项索引另行复核，未修改历史证据。

## 本轮后仍未关闭的事项

- A03 已修复且真实输入与拒绝逻辑已由实施方验证，**待主控独立复验**。A01中的字节、矩阵/基因/细胞身份和数值合法性部分已取得真实证据；不扩写成完整科学输入准入通过。
- 本轮没有做QC或决定最终队列/HVG/评价ID，没有生成正式 `data-input-lock.json`；broad标签仍为DRAFT。共同QC及标签交集必须在授权后、看聚类指标前冻结。
- 管理分支已采纳官方1920候选范围，不再无限追索网页28个ID；网页修订适用于当前GEO/Hub与否仍未知，不声称已验证网页校正或复现原文1656。
- 不证明原始flow表match命中或NA来源；不使用FACS/DC强度、重门控或以其补标签。Rep/donor关系仍未知，不合并Rep或作生物学重复/供者推断。
- C04官方CAdir S1覆盖/逐来源新增性裁定仍待补齐。正式实现、配置/环境/输入锁、独立正式设计及C05准入均未完成。

机器状态见 `preparation_status.json`。`formal_execution_permitted=false`，未做QC筛选、归一化、聚类、ARI/NMI、模拟或smoke，未创建PR或自行组织审查。本次只交付修复和实际输入合法性证据，交主控安排独立复验。

`evidence_index.json` / `evidence_sha256.tsv` 按仓库相对路径索引本目录的
全部交付物及本轮修改/新增的案例脚本和README；两个索引自身不纳入以免循环。
原始表达文件不入Git。最终源码运行前哈希另在执行收据中，可与此索引交叉核对。
控制台日志原样保留，包括R打印的尾空格及空行；本目录属性禁止换行转换，
仅对原始日志关闭空白风格检查，不改写失败或诊断记录。
