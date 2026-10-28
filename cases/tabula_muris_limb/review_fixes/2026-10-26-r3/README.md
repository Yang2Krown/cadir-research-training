# R3：收到两端实际对象后的排序差异因果诊断

日期：2026-10-26。实施配置沿用 GPT-6.1 Sol / high；主控 chat `01a17385-6fd3-71dd-ae1a-a9fa2b77203d`，原独立评审 chat `01a17354-6169-70a8-810e-d49d4d605029`。诊断基于当前修复分支的 `0acd73d23b46f7bf84ab2571dc9722b3d2f10d0b`，以新提交保存；未 push、合并 main 或改写冻结历史。

**R3 中两次具体运行的 alpha/完整排名差异，现已用两端实际 CA 与未排序 CAdir 对象因果复现。** 差异来自八个 CA 轴的符号选择，作用于上游只在正正交限采样随机方向的阈值估计。细胞/基因分配与用于评分的几何保持一致。此为实施诊断，仍须不同评审员独立复验，不自行签署阶段通过；未修改 CA、CAdir 算法、参数、历史阈值、分数或排名。

## 收到的原始证据与保全

本次收到旧独立评审的 `ca.rds`、`cadir_unranked.rds`、小文本证据 ZIP 及导出清单；没有用当前生成对象冒充旧对象。虽然 unranked 在首批中未到，随后已实际上传并验收，最终 [接收记录](evidence/received_intake.json) 中 34 项 manifest 文件全部匹配。另由诊断脚本独立实算确认；[39 个输入前后保全](evidence/input_preservation_before.json) / [after](evidence/input_preservation_after.json) 均保持原字节。

| 对象 | 旧独立评审实际收到的 SHA256 | 基线按冻结索引核实的 SHA256 |
| --- | --- | --- |
| CA | `1e6348adc31fc1ae3d8971605953f1524116399ea2e299817aa89c75d9d2e661` | `e769376f42f5fc0eada10cc194c4b00101816bd80b7e6d23a01d0d44a472992f` |
| 未排序 CAdir | `df428b523f8b4027209ea81673ccb25665b1e490cd9dab58ef797f22807b2d96` | `a65d07a24970dd2cbd7c47539cfea119ba438a9f8c04c91192260ec574d79b1d` |

基线对象读取自 `/workspace/cadir-stage1-fix-evidence/fresh-run-1/case-wq48i9bp/`，已在前轮与冻结 `publication/external_resources.json` 做逐字节哈希验证。旧评审对象读取自 `/workspace/cadir-r3-evidence-20261026/`。原始数据主流程没有复跑，也没有从 CA 重新生成 CAdir；四项排名重放全部从两端已存在的对象开始。

[配置与环境比较](evidence/config_environment_comparison.json) 显示：配置仅 `data_path` 的位置不同，输入 SHA256、seed=2358、30 维及全部科学参数相同；两份原 `sessionInfo.txt` 字节完全相同。[22 份 APL/CAdir R 源码哈希](evidence/source_hash_comparison.json) 全部匹配旧评审保存记录。旧评审保存的安装函数比较结果及前轮当前安装函数比较均支持与这些固定源码一致；没有补造旧运行瞬间的 RNG 或函数体快照。

## CA 数值比较：符号差异，无实质旋转

[逐轴比较脚本](scripts/compare_ca.R) 按基因/细胞 ID 比较实际坐标，先确认 6000 个基因、1882 个细胞的 ID 和顺序均相同，再推导每轴符号及最优正交映射。不是仅比较文件哈希。

- 第 **7、10、11、15、17、18、21、22** 轴符号相反，其余轴同向。
- 奇异值最大绝对差 `6.66e-16`。
- 按上述八轴对齐后，细胞 principal 坐标最大误差 `9.05e-13`，基因 principal 坐标最大误差 `2.91e-12`。
- 最优正交映射偏离该对角符号矩阵的最大条目为 `6.22e-13`，没有需要另行旋转才能解释的数值差异。
- 两个未排序对象的细胞/基因 factor 分配（含命名与 levels）逐项相同；方向按同样符号对齐后最大误差 `2.02e-13`。用于评分的基因投影最大差 `7.33e-14`、正交距离最大差 `9.28e-14`。

见 [CA 汇总](evidence/ca_comparison.json)、[30 轴明细](evidence/per_axis_comparison.tsv) 和 [未排序对象/评分几何检查](evidence/ranking_replays.json)。对象中的 plots、log、distances 等并非逐字节相同，本报告只对实际检查的分配、方向、坐标、阈值和排名给出数值结论。

## 实际重放与双向反事实

[重放脚本](scripts/replay_rankings.R) 每项均重新设置 `RNGkind("Mersenne-Twister", "Inversion", "Rejection")` 与 `set.seed(2358)`，调用未改的 `CAdir::rank_genes`。反事实只在内存诊断副本中，同时反射 CA 的 U/V、standard/principal 坐标及簇方向；不更改基因、细胞、分配、参数、seed 或算法。该同时反射保持点积与距离。

每项逐基因核对全部 1200 个 gene/cluster、Score 和 Rank，以 `1e-10` 绝对容差判断分数等价，并独立按投影/正交距离重算 `Score = x − alpha_genes × y`。四项独立几何评分与上游的最大误差均不超过 `5.33e-15`。

| 诊断条件 | alpha_genes（约） | 对照目标 | 全部 Score 最大差 | Rank 变化 |
| --- | ---: | --- | ---: | ---: |
| 基线实际 CA + 实际未排序对象 | 1.07506446203775 | 冻结基线表 | 5.33e-15 | 0 |
| 旧评审实际 CA + 实际未排序对象 | 1.10141280187352 | 旧评审表 | 5.11e-15 | 0 |
| 基线对象仅反射已测八轴 | 1.10141280187356 | 旧评审表 | 5.72e-13 | 0 |
| 旧评审对象仅反射回基线八轴 | 1.07506446203776 | 冻结基线表 | 1.21e-13 | 0 |

两端实际重放彼此相较，重现全部 **541 个名次变化**、最大 Score 差约 **0.346546986154591**，与原独立评审报告一致。双向符号干预既产生旧评审的全部名次，也消除其相对基线的全部名次变化；这里的证据强于前轮任意反射某个轴的敏感性展示。

完整 [重放结果](evidence/ranking_replays.json)、[诊断 RNG 前后状态](evidence/diagnostic_rng_states.json) 及四份 `evidence/*_ranks.tsv` 均保留。R 脚本对两项真实重放、两项反事实的 gene/cluster、全部 Score 与完整排名均执行断言，退出码为 0。[四项诊断 RNG 比较](evidence/diagnostic_rng_equality.json)确认调用前状态彼此相同、调用后状态也彼此相同。旧运行瞬间 RNG 快照没有收到；本次状态明确标为诊断重置后的新快照，没有冒称历史原始状态。其缺失不妨碍用收到对象和原 seed 精确复现已经保存的旧表。

## 机制、剩余边界与处置建议

固定 [CAdir apl.R](https://github.com/VingronLab/CAdir/blob/de74a008dfcd0d4fa4f7f93c57aa346892a8d935/R/apl.R#L74-L122) 的 `random_direction_cutoff` 为每一维调用 `runif(0, q99)`，随机方向只落在当前坐标基底的正正交限。轴反射之后，使用相同随机数也不代表同一批几何方向；cotangent 分布及其 0.99 分位数改变，经 `atan(1/cutoff_cotan)` 得到不同 alpha。固定 [genes.R](https://github.com/VingronLab/CAdir/blob/de74a008dfcd0d4fa4f7f93c57aa346892a8d935/R/genes.R#L69-L129) 将该 alpha 用作评分系数；点的评分投影/距离基本相同，但系数改变，造成全量分数与部分排序变化。

SVD 轴的符号本就不唯一。两端存储对象确实选择了上述不同符号；本轮未观测产生旧 SVD 符号的底层具体事件，不能进一步断言是哪次 BLAS 归约、硬件或内部调用导致。已闭环的是 **已发生的 CA 符号差异→随机阈值变化→已保存分数与541名次变化**，而不是证明任意机器从原矩阵重算 CA 都会选择相同符号。

建议保持上游算法和冻结结果，按现有来源记录保存 CA 对象/基底、RNG、alpha 与完整排名。将复跑主张限定为固定 CA 基底或明确验证过的对齐条件；同 seed 本身不保证跨任意 CA 基底的全排名一致。若未来确需基底无关的排名，须事先固定规则、另建研究变体并独立评审：如确定 CA 符号约定，或改变随机方向采样方法。二者都可能改变上游数值输出，本轮均未实施，不将其夹带为复现修补。

本提交唯一运行脚本修改是 N2 的元数据文案：`pipeline.R` 不再硬编码“历史对象不可用/未建立等价”，改为 `ranking_scope` 描述本次运行使用的 CA 基底、RNG、alpha 和安装函数；历史诊断状态放在本报告。[逐字比较](evidence/metadata_only_diff.json)确认该文件仅这一项元数据替换，不涉及调用、随机数、阈值、排序或参数，可静态核对，无需完整输入复跑。[提交前保全](evidence/pre_r3_commit_preservation.json)核对其余既有文件字节不变。

## 验证与复验入口

原输出与脚本保存在 `/workspace/cadir-r3-diagnosis-20261026/`，文件哈希见 [外部索引](evidence/external_artifacts_sha256.json)。接收原件 `/workspace/cadir-r3-evidence-20261026/` 保持只读；RDS、输入数据、ZIP、运行库及完整上游源码不入 Git。Git 日志副本仅规范尾空白，转换见 [记录](evidence/log_copy_normalization.json)。旧报告、R1/R2 证据、原图及 `results/acceptance` 都不覆盖。

```bash
case_dir=/workspace/cadir-stage1-fix/cases/tabula_muris_limb
out=/workspace/independent-r3-diagnosis
mkdir -p "$out"
bash "$case_dir/scripts/run-r.sh" "$case_dir/review_fixes/2026-10-26-r3/scripts/compare_ca.R" \
  BASELINE_RUN/ca.rds RECEIVED_REVIEW/ca.rds "$out/ca_comparison.json" "$out/per_axis_comparison.tsv"
bash "$case_dir/scripts/run-r.sh" "$case_dir/review_fixes/2026-10-26-r3/scripts/replay_rankings.R" \
  BASELINE_RUN RECEIVED_REVIEW "$out"
```

两份 R 诊断脚本实际执行成功；修改后的 pipeline 及诊断脚本静态解析、`git diff --check` 通过。当前结论限于这一 HVG-only 案例和已有两次具体运行；不外推严格论文复现、多种子稳健、生物学验证或普遍算法优势。R3 补证已准备完整，是否解除阶段门槛交独立复验及主控判断，不再要求用户重复上传已齐备对象。
