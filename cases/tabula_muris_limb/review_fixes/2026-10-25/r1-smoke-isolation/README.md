# R1 后续：合成烟雾输出隔离

独立复验对提交 `8561914bc67c511ec76374996fb12d713f23f171` 发现，`check_environment.py` 仍调用共享 runtime 的 `run-smoke.py`。该启动器硬编码写入 `/workspace/cadir-env/runs` 和 `latest-smoke.json`，环境检查再读取共享 latest；即使案例使用独立 output-root，这部分仍存在并发竞态。首版修复并未做到完整输出隔离，原证据保留，本记录明确修正这一边界。

本后续修改仅涉及环境检查编排：先阅读 `smoke.R`，确认其所有测试产物以命令行传入目录为根；再通过现有 `run-r.sh` 直接执行原 `smoke.R`，目标为本次 `environment-*/synthetic-smoke/`。不调用、读取或更新共享 smoke 启动器状态。`run-smoke.py` 仍作为来源文件留存哈希，未被修改或执行；runtime 启动器、算法源码、冻结成果与旧证据均不改。

保留与历史启动器相同的六个必需非空文件检查（status、sessionInfo、installed packages、两个 RDS、PNG），要求 status 以 PASS 开头，保存控制台、PNG SHA256、耗时、退出码和资源 JSON。RSS 通过 Linux `os.wait4` 获取这一次 R 子进程的 usage，排除先前版本检查的累计子进程峰值；仅作工程诊断。

## 实际验证

按主控要求，只运行一次完整入口，覆盖环境烟雾、真实单案例、结果验证及收集，不额外重复两次真实案例。[验证脚本](verify_smoke_isolation.py) 在执行前确认输出目录不存在，并记录共享 runtime 的 latest-smoke、runs 子目录/全部文件哈希及文件 mtime；完整入口退出后立即记录同样快照。

- 完整入口退出码 0，环境状态 PASS，案例状态 `SINGLE_CASE_COMPLETE_WITH_DOCUMENTED_DIFFERENCES`，加强结果验证 PASS，新 deliverables 收集成功。
- 烟雾目录确在本次环境检查目录下；全部八个烟雾产物（六个必需文件及 console/resources）非空，PASS 文本与 PNG SHA256 正确。
- 烟雾耗时约 14.32 秒，child 峰值 RSS 1,186,432 KiB；不据此作算法性能比较。
- 共享 latest-smoke 与 runs 下共 49 个文件的大小、SHA256、mtime 及子目录列表前后相同；六份 runtime 来源文件 SHA256 全部不变。
- Python py_compile 和 `git diff --check` 通过。

详见 [验证汇总](evidence/summary.json)、[共享状态 before](evidence/shared_before.json) / [after](evidence/shared_after.json)、[环境状态](evidence/environment-status.json)、[原样完整入口日志的轻量副本](evidence/full-entry.log)、[烟雾资源](evidence/smoke-resources.json) 和 [结果验证](evidence/case-verification.json)。没有启动额外并发烟雾压力测试；此处隔离依据为直接传参路径及运行前后保全，而非声称验证所有并发场景。

大对象、PNG、全量结果和原始日志在 `/workspace/cadir-stage1-fix-evidence/r1-smoke-isolation-20261025/`，逐文件哈希见 [外部索引](evidence/external_artifacts_sha256.json)。Git 文本副本只规范行末空白及末尾多余空行，转换见 [记录](evidence/log_copy_normalization.json)，外部原字节保留。旧 `8561914` 的证据与此前失败记录未覆盖。

这仍是实施自测，待独立复验新提交。R3 旧独立评审排序差异的归因保持未解决，不引入算法或阈值修改，不宣称阶段通过。
