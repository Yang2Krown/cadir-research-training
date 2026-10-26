# Nestorowa HSC：输入准备，正式执行仍禁止

最新交付见 [A03 修复与真实输入审计](../../planning/new-dataset/2026-10-26/input-legality-a03/README.md)。
历史准备及收据在 `planning/new-dataset/2026-10-26/metadata-preparation/`。
已有真实文件，不再将原始下载失败记录当作当前状态。

`audit_inputs.R` 分为两个明确入口，旧的三参数调用已移除：

```text
Rscript --vanilla audit_inputs.R metadata-only COL_RDS MANIFEST NEW_OUT
Rscript --vanilla audit_inputs.R full COUNTS_RDS COL_RDS GEO_GZ MANIFEST NEW_OUT
```

metadata-only 不接受 count/GEO 路径。共享 `metadata_identity.R` 从嵌套
`cell.type` 提取显式主键，核验每个字段并按 ID 对齐；保留原始顶层
NULL、其 R 序列化表示及所有 NA，不复制 count 列名或按行数补 ID。
缺失、重复、空 ID 或集合冲突均拒绝，并保存可用的身份差分。

full 额外校验获取清单中的大小/SHA256、真实矩阵结构和唯一基因/细胞
ID、有限非负整数，并以完整 GEO 表逐 ID 核验方向、顺序及全部数值。
仅生成审计摘要和 ID/标签表；不筛选、归一化或生成处理后的表达矩阵。

使用当前已有离线容器的例子（metadata-only 只挂载 coldata 文件）：

```bash
python cases/nestorowa_hsc/scripts/run_input_audit.py metadata-only \
  --metadata /workspace/nestorowa-metadata-preparation/reacquired-20261026/coldata.rds \
  --manifest planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json \
  --output /workspace/new-hsc-metadata-audit

python cases/nestorowa_hsc/scripts/run_input_audit.py full \
  --counts /workspace/nestorowa-metadata-preparation/reacquired-20261026/counts.rds \
  --metadata /workspace/nestorowa-metadata-preparation/reacquired-20261026/coldata.rds \
  --geo /workspace/nestorowa-metadata-preparation/reacquired-20261026/GSE81682_HTSeq_counts.txt.gz \
  --manifest planning/new-dataset/2026-10-26/metadata-preparation/acquisition_manifest.json \
  --output /workspace/new-hsc-full-input-audit
```

输出目录及同名执行收据/日志必须不存在；失败尝试保留。容器禁网、输入与
R 库只读，使用现有镜像，不安装包。`test_metadata_identity.R` 只对真实
元数据的内存副本作身份验证器回归检查，不生成模拟表达矩阵或运行科研算法。
旧 `run-r.sh` 依赖当前不存在的环境路径；本次实际执行使用新离线容器包装器，
没有声称它可用，也没有改动历史冻结副本。

完整输入合法性通过不等于 QC、data-input-lock、环境锁、正式设计或执行批准。
`formal_execution_permitted=false`。未实现正式运行入口，不创建 PR 或组织审查。
