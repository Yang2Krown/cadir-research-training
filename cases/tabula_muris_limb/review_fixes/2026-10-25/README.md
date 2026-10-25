# 首阶段审查修复与勘误（2026-10-25）

本记录针对冻结提交 `756c8d16ae22fe671f7b715a696c8272523e08ed` 的 R1—R6。实施环境为 GPT-6.1 Sol / high，工作分支 `fix/stage1-review-20261025`，隔离工作目录 `/workspace/cadir-stage1-fix`。主控 chat `01a17385-6fd3-71dd-ae1a-a9fa2b77203d`；因当前应用会话调度工具不可用，使用内部临时实施代理，不创建重复可见 chat。授权来自 `/workspace/cadir-handover/项目组织者交接Prompt.md`，独立审查原 chat 为 `01a17354-6169-70a8-810e-d49d4d605029`。

**这是实施修复及自测记录，待另一评审员对新提交独立复验；不签署阶段通过。R3 的旧独立评审特定排序差异仍待归因。** 本轮仅为 6000 HVG 的 Limb Muscle 单案例；无算法改进、调参追分、新数据或公平基线实验。

## R1：新检出与输出隔离

`check_environment.py`、`run_case.py` 在创建临时运行目录前递归创建输出根；新增共同 `--output-root`，默认案例 `runs/`。环境/案例状态指针和收集物均在该根内，收集到 `deliverables/results/` 与 `deliverables/figures/`，不再覆盖案例根目录的历史 latest、results 或原图。`rerun.sh` 转发数据、配置与输出根，`--audit-only` 完成审计即停止。

真实验证从冻结 SHA 创建全新 detached worktree `/workspace/cadir-stage1-fix-evidence/fresh-checkout`，应用修复差异及新增辅助模块；启动前确认案例 `runs/` 不存在。两次运行使用这份相同的新检出源码，分别从空 `fresh-run-1`、`fresh-run-2` 输出根启动，没有借用旧 runs、latest 状态或结果对象。输入为 43,383,527 字节，SHA256 `af643523ccdf49e4931b5a0f8c53e67ba7fb24fbabb2fed7edfecf3b55c51f8b`；保留 `/workspace/cadir-env`，未要求 Docker 或重新安装。

两次完整 `rerun.sh --data ... --output-root ...` 均退出 0，依次完成环境检查、合成烟雾、真实分析、加强验证器与新成果收集。日志见 [第一次](evidence/fresh-run-1.log)、[第二次](evidence/fresh-run-2.log)，状态与输入校验见对应 evidence 子目录。每次新运行目录均在状态文件记录。

## R2：逐项核验及错误状态

验证器用 `gene_id` 索引 `cadir@gene_clusters`，核对全部 6000 行 cluster 值与 NA；按簇重新计算细胞数与基因数；完整排名必须每个已分配基因恰好出现一次，逐项比较 gene、cluster、Score、Rank、Row_num 与 `cadir.rds`。Score 使用 `1e-10` 绝对容差。验证开始写 RUNNING，任何捕获错误写 FAIL 并退出 1，旧 PASS 不会留存为本次状态。

[错误注入脚本](scripts/run_mutations.py) 仅修改独立副本；每项事先复制真实 PASS，检验失败后确实变为 FAIL。结果见 [JSON](evidence/verifier_mutations.json) 和 `evidence/verifier-*.log`。

| 样例 | 退出码 | 状态 |
| --- | ---: | --- |
| 正常新运行 | 0 | PASS |
| 交换两个不同簇基因标签，保持 ID 与簇计数 | 1 | FAIL |
| 交换一个已分配与一个 NA 基因，保持分配总数 | 1 | FAIL |
| 改动一个 Score +0.5 | 1 | FAIL |
| 交换两个 Rank | 1 | FAIL |
| 改动两簇基因数 +1/-1，保持总数 | 1 | FAIL |

PASS 在此只说明导出表与该次保存对象自洽，不是独立审查结论。

## R3：当前可重现，旧评审差异未归因

[两次新鲜运行比较](evidence/fresh_comparison.json)：两次 alpha 均为 `1.07506446203775`，alpha 差为 0，全部 1200 个 gene/cluster 相同，Score 最大绝对差 0（要求 ≤1e-10），Rank 变化 0，CA 行列 principal 坐标最大差均为 0。排序调用仍是原 `CAdir::rank_genes`，未修改阈值、CA 轴符号或排名规则。上游以 Score 降序，精确并列保留 CA 行顺序（R 稳定排序）；本轮不添加另一套排序法。

[当前运行对冻结表](evidence/ranking_diagnosis.json) 的全部 1200 Score 最大差为 0、Rank 变化 0。更强的补证是：两次新生成的 `ca.rds`、`cadir_unranked.rds`、`cadir.rds`、`cadir_annotated.rds` 的大小和 SHA256 **全部匹配冻结 publication/external_resources.json 中原 case-ppkaow9s 的索引**。详见 [逐对象哈希比较](evidence/historical_object_hash_comparison.json)。例如 CA 为 `e769376f42f5fc0eada10cc194c4b00101816bd80b7e6d23a01d0d44a472992f`，未排序对象为 `a65d07a24970dd2cbd7c47539cfea119ba438a9f8c04c91192260ec574d79b1d`。本轮是生成对象并与已提交索引比较，没有读取旧会话对象本体。

因此，**原实施基线在当前保留环境中可重现**，不能继续笼统称原基线不可复跑。另一方面，旧独立评审报告的 `alpha=1.101412801873519`、541 名次变化尚未解释；新证据不抹去那次不利结果。当前最小缺件是那次独立评审的 **CA、未排序 CAdir、实际配置与 RNG/软件来源记录**，不需再向用户重复索要已按哈希重建的原实施对象。

实际读取固定上游 [CAdir genes.R](https://github.com/VingronLab/CAdir/blob/de74a008dfcd0d4fa4f7f93c57aa346892a8d935/R/genes.R) 与 [apl.R](https://github.com/VingronLab/CAdir/blob/de74a008dfcd0d4fa4f7f93c57aa346892a8d935/R/apl.R)。4 个相关安装函数的参数与函数体逐项等于固定源码，见 [诊断](evidence/ranking_diagnosis.json)；源码 SHA、干净状态见 [来源](evidence/upstream_sources.json)。新增 `rng_stages.json` 保存 CA/CAdir/排名前后真实完整 RNG 状态，`ranking_provenance.json` 保存 alpha、函数摘要与 CA 轴符号。其运行时对历史等价性的保守提示早于本次索引比较，历史等价性证据以上述逐对象 SHA256 比较为准。

上游 `random_direction_cutoff` 在每个 CA 维度以 `runif(0,q99)` 采样正正交限方向，因此对 CA 轴反射不具不变性。[仅诊断的符号干预](scripts/diagnose_ranking.R) 同时反射行列坐标和簇方向，保留几何关系，并重置同一 RNG：首轴反射后 alpha 为 `1.10049740439402`、528 名次变化；全部轴反射后 alpha 为 `1.20205172532586`、938 名次变化。它说明一个实际实现敏感性，**不证明旧评审差异由 CA 符号引起**，也未被用于更改正式运行结果。

R3 处置：`UNRESOLVED / 待独立评审归因与判断`。不为凑放行预设 alpha、重写旧分数、改变上游随机采样或引入新算法。

## R4—R6：现行说明勘误

- R4：当前 6000×1882、30 维设置走固定 [APL CA.R:470–495](https://github.com/VingronLab/APL/blob/d4d1f40d9ea9f1d9a95b224d45de843334cd617d/R/CA.R#L470-L495) 的 `irlba::irlba` 分支；TRUE/FALSE 在本路径只构成参数值差异。旧审查已实际切换两值得到相同行列坐标/奇异值；本轮读取源码确认分支，不重复冒称另做了后端切换实验。新生成 `paper_differences.txt` 已修正。完整依赖、输入与作者私有 CAdir 等价性仍不成立。
- R5：作者固定 [figure2.qmd](https://github.com/VingronLab/CAdir_results/blob/c15b49578bde38b42fd5db2c9830c10dd441ee4c/results/figure2.qmd) 是仓库文件名，对应[正式论文](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014418) Fig 3 Limb Muscle 案例；正式 Fig 2 是方法概览。现行 README 与新生成说明已修正。
- R6：实际打开冻结 PNG，逐项对照固定绘图源码；增加[相邻完整图注](../../figures/association_plots.caption.md)，注明七个方向、投影/正交距离、细胞 standard / 基因 principal、四类颜色及排名解释。原 PNG/PDF 字节未变。

历史 `results/`、`acceptance/`、报告及已有图不重写，原文中的“Figure 2”“python 后端不同”和笼统完整复跑主张应结合本勘误阅读。[保全检查](evidence/preservation.json) 对 239 个原有且未列为当前修复修改的文件确认 SHA256 不变，包含历史脚本快照、结果及验收基线。ARI/NMI 保留单案例定义（NMI 为 MI/max(Hcluster,Hreference)）；自动注释仍为预测，未显著簇与文献资源名称均不人工改为真值。

## 复验入口与证据位置

完整大对象、坐标、真实输入和完整上游源码不入 Git；大输出位于 `/workspace/cadir-stage1-fix-evidence/`，逐文件大小及 SHA256 见 [外部清单](evidence/external_evidence_manifest.json)。Git 中仅保留轻量状态、RNG、日志、哈希与脚本。失败注入原日志全部保留在外部目录并记录哈希；Git 中的日志副本仅删除行末空白及文件末尾多余空行，以通过 diff 空白检查，正文不改。

```bash
case_dir=/workspace/cadir-stage1-fix/cases/tabula_muris_limb
bash "$case_dir/scripts/rerun.sh" \
  --data /workspace/cadir-handover/input/tabula_muris_limb_preproc.rds \
  --output-root /workspace/independent-new-run
# 取新 run_directory 后，以新输出核验错误注入或重复运行。
python "$case_dir/review_fixes/2026-10-25/scripts/run_mutations.py" \
  "$case_dir" NEW_RUN_DIR /workspace/independent-mutations
```

本轮静态检查：修改 Python 模块通过 py_compile，shell 通过 bash -n，两份核心 R 脚本可解析；`git diff --check` 无空白错误。真实验证及范围如上，不扩展到从零装环境、跨机器稳健性、生物学验证、普遍优势或严格论文复现。具体修复提交 SHA 以包含本记录的 Git 提交为准，主控统一推送，本实施代理不 push。
