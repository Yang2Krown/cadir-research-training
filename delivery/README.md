# 真实输入独立复验小型证据包

结论 PASS，仅 A01 输入合法性与 A03 真实对象复验；formal_execution_permitted=false。被审 b7ee2335dc25ffab3a60d1feab44272d6d5a45cb。报告与逐项索引在 project-control/reviews/b7ee233-real-input-20261026。

ZIP 只含本次独立脚本、元数据/ID派生表、完整日志、环境、哈希、差异表及报告；不含原始 RDS/count、库或 ZIP 本身。evidence_sha256.tsv 不索引自身，ZIP 校验和在旁置 .sha256，避免循环。提交精确 SHA 请使用 GitHub 当前文件对应提交，或克隆后 git rev-parse HEAD；最终交付消息同时提供精确 SHA。

执行角色：独立评审者 GPT-6.1 Sol / High 编写与解释；协调者仅转接 Docker 权限命令与推送。保留全部真实失败及后续修复，不把旧实施自验作本次独立证据。
