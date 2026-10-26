# Nestorowa HSC：准备阶段，正式实验阻塞

本目录只有公开获取、原始结构审计和协议检查脚本。**真实counts/metadata未获得，未运行任何新数据聚类或ARI/NMI；版本、QC和唯一参考标签NOT_VERIFIED。** 已取得官方ExperimentHub目录，确认EH2694/EH2695、legacy路径`scRNAseq/nestorowa-hsc/2.0.0`；下载被官方存储host的网络策略403阻塞。

[准备与阻塞报告](../../planning/new-dataset/2026-10-26/数据准备与阻塞报告.md)、[预注册中文草案](../../planning/new-dataset/2026-10-26/pre-registration.md)、[JSON](../../planning/new-dataset/2026-10-26/pre-registration.json)、[最小网络建议](../../planning/new-dataset/2026-10-26/最小网络配置建议.md)。

解除官方host网络阻塞后，可用现存同哈希catalog解析明确资源并下载到新外部目录：

```bash
case_dir=/workspace/cadir-next-data-plan/cases/nestorowa_hsc
python "$case_dir/scripts/acquire_hub.py" \
  --catalog /workspace/cadir-newdata-20261026/acquisition/experimenthub.sqlite3 \
  --output-root /workspace/cadir-newdata-20261026/new-authorized-acquisition --download
bash "$case_dir/scripts/run-r.sh" "$case_dir/scripts/audit_inputs.R" \
  /workspace/cadir-newdata-20261026/new-authorized-acquisition/counts.rds \
  /workspace/cadir-newdata-20261026/new-authorized-acquisition/coldata.rds \
  /workspace/cadir-newdata-20261026/new-raw-audit
```

所有输出目录须新建，不复用旧尝试。每次下载记录官方URL/重定向、字节/SHA、错误及原始响应，保留继承代理/TLS，单文件上限128MiB。不改路由/代理、不在错误后换镜像。Hub的fetch ID取自SQLite `rdatapaths.id`，**不能直接把EH2694当/fetch/2694**；目录结构不符则停止。

结构审计只检查矩阵、ID、计数、嵌套metadata并导出ID对齐和原字段；不归一化、不做QC筛选、降维、聚类或评价。嵌套FACS矩阵不被当成一个唯一类别列。原始文件及大型对象均放Git之外；当前可核验的是访问阻塞和小型合成结构测试，不是实际HSC内容审计通过。

```bash
python "$case_dir/scripts/check_protocol.py" \
  /workspace/cadir-next-data-plan/planning/new-dataset/2026-10-26/pre-registration.json --require-ready
# 当前预期退出2：数据、标签与独立审查门槛未关闭。
```

这里没有正式run_experiment入口；未来接口和五种子/公平基线配置已写入草案，须先完成数据/来源/标签锁及独立设计复核，再实施和冻结正式代码。保留旧case不变，不把首阶段放行当作新数据实验放行。
