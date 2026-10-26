# 新实例网络验证与数据准备执行记录

日期：2026-10-26，Asia/Shanghai；原始收据保留 UTC。工作目录 `/workspace/cadir-validation-20261026/repo`；原件及失败尝试在 Git 外的 `/workspace/cadir-validation-20261026/data`。独立 clone 恢复远端小型成果，没有依赖旧会话工作目录或修改已有工作树。

**实施结论：本实例仍未取得三个研究数据文件，实际请求均为代理 CONNECT 403。真实数据审计和正式实验继续 BLOCKED。本记录待不同评审员复核，不自报阶段 PASS。** 首阶段限定通过与 R3 已关闭的结论保持；未索要旧 RDS，未重跑首阶段。

## 环境、配置与实际访问

已读取并遵循 [cloud-environment-runtime 技能](skill://plugin_connector_1p_c5b7d5df5d7081918f2c4be5a633ed5d/cloud-environment-runtime/SKILL.md)及 networking 引用。保留继承的代理、CA 信任及 TLS 验证；没有改路由、代理或策略，也未安装包。

| 项目 | 本实例实际观测 |
| --- | --- |
| environment_id | `ccarenv_b64_Y2NhcmVudl8zNjk0OGI5NWM1ZWM4MTkxYWJkZjJjMTIzOGQyNjk1OA` |
| source_config_id | `ae71c8d4-6392-40b0-901b-38e81b54b433~cecfg_6add8dca76c0819cae32b18fd4b1c220` |
| source_config_version_id | `ae71c8d4-6392-40b0-901b-38e81b54b433~cecfgver_6adda21e15fc819c857dd9cc03d2aff7` |
| spec_revision / observed_spec_revision | `2` / `2` |
| observations_current / phase | `true` / `running` |
| network_policy mode / state | `restricted` / `unknown`（不能宣称 enforced） |
| 自定义 allowed_hosts | `*.bioconductor.org`, `api.github.com`, `bioconductor.org`, `cloud.r-project.org`, `cran.r-project.org`, `micro.mamba.pm` |
| 实际返回的 effective_allowed_hosts | 完整列表在 [environment-status.json](evidence/network/environment-status.json)；两个目标 host 均不在其中 |
| `/etc/codex/network-policy.json` | version=1；VPN=false；HTTP proxy=`http://proxy:8080`；egress_rules 同样不含两个目标 host；[原字节副本](evidence/network/network-policy.json) |

两次 environment_status 返回相同配置版本和 unknown 状态，见 [复查快照](evidence/network/environment-status-recheck.json)。`observations_current=true` 仅表示观测是当前的，不会把 unknown 转成 enforced。effective 列表也是该绑定配置的返回列表，不是对所有目的地址已放行的证明。

用户已明确表示两个 host 已添加并发布，本次不要求重复添加。当前实例返回的绑定配置与本机策略均不含它们，**未证明本实例采用了用户所述的新配置**；没有新发布版本 ID，因此不能断言平台未发布、准确比较两个版本，或确定其未绑定的后台原因。工具只有环境状态读取能力，不能在此重绑配置。技术解除条件是受支持的运行实例绑定/配置刷新流程使此实例采用含两个 host 的已发布版本，再取得 current/enforced 状态并实测成功；不是再次填写相同域名，也不要求用户传矩阵。

正式带执行器网络权限的请求均保留代理/TLS。首轮未授予该执行器权限时 curl exit=7（无法连接 proxy），归档为本地执行权限层失败，不能据此判断目的域名策略；后续 `*-network-enabled.*` 才是本次域名访问证据。

| GET 目标 | 时间（UTC） | curl / CONNECT / 源站 HTTP | 实际数据字节 / SHA256 |
| --- | --- | --- | --- |
| [counts.rds](https://mghp.osn.xsede.org/bir190004-bucket01/ExperimentHub/scRNAseq/nestorowa-hsc/2.0.0/counts.rds) | 02:41:41 起，详见原收据 | 56 / 403 / 0 | 0 / 未取得文件，null |
| [coldata.rds](https://mghp.osn.xsede.org/bir190004-bucket01/ExperimentHub/scRNAseq/nestorowa-hsc/2.0.0/coldata.rds) | 同次批量探测 | 56 / 403 / 0 | 0 / 未取得文件，null |
| [GEO counts.txt.gz](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE81nnn/GSE81682/suppl/GSE81682_HTSeq_counts.txt.gz) | 同次批量探测 | 56 / 403 / 0 | 0 / 未取得文件，null |

精确错误为 `curl: (56) CONNECT tunnel failed, response 403`；代理响应 `HTTP/1.1 403 Forbidden`、server=envoy。没有建立源站 TLS 连接，不能将 ssl_verify_result=0 解释为已完成源站证书验证。三个 [request JSON、headers 和 stderr](evidence/network/)保存 URL、开始/结束时间、重定向数量、字节数及命令。重定向数量为0，因为直接目标的 CONNECT 已失败。没有把空文件或错误页哈希当研究数据 SHA。

## 从远端恢复与目录重核

实际 GitHub clone 成功，三个远端提交与用户给定值逐项相符：[remote-refs.json](evidence/remote-refs.json)。完整读取管理分支 README、2026-10-26 首阶段/新准备阶段结论、下一阶段规则和 AI 使用与调度台账；读取新数据 case README、来源审计、数据准备阻塞报告、预注册 Markdown、最小网络建议、独立准备清单及旧独立复核报告。管理材料以 `git show origin/control/stage1-quality-20261025:...` 读取，未将它们假称为新数据分支自带文件。

复用已有 `fetch_public.py` 新取官方 [ExperimentHub SQLite](https://experimenthub.bioconductor.org/metadata/experimenthub.sqlite3)，02:42:34 UTC 开始，HTTP200，**10,378,240 字节**，SHA256 **`1c0786502f29cf67b892d7452dc03d29af6c1dda82ddd89118a4d79d10a83c4e`**。最终 URL 与原 URL 相同，大小/哈希匹配旧记录，但字节为本次新获取；[下载收据](evidence/acquisition/catalog-receipt.json)。SQLite 原件保留 Git 外，不是 counts/metadata。

复用 `acquire_hub.py` 对新目录进行只读 SQLite 解析，[获取计划](evidence/acquisition/acquisition_plan.json)重新确认：

| 逻辑资源 | rdatapaths.id / 正确 fetch | 目录声明 class |
| --- | --- | --- |
| EH2694 / `scRNAseq/nestorowa-hsc/2.0.0/counts.rds` | 2710 / `/fetch/2710` | dgCMatrix |
| EH2695 / `scRNAseq/nestorowa-hsc/2.0.0/coldata.rds` | 2711 / `/fetch/2711` | DataFrame |

分别对两个正确 fetch 发送不跟随 HEAD，均实际返回302，Location精确指向上述官方 counts/coldata 存储地址，原始响应在 [network/](evidence/network/)。本次没有请求错误的 `/fetch/2694` 或 `/fetch/2695`。目录 class 尚不代表 readRDS 验证。

`acquire_hub.py --download` 取 counts 经正确 fetch 路线再次报 `Tunnel connection failed: 403 Forbidden`，退出1后按原脚本停止；未假称它继续下载了 coldata。coldata/GEO 另用既有 `fetch_public.py` 请求，各退出1并保留 [独立收据](evidence/acquisition/)。128MiB 上限未改。

## 数据审计状态与执行门槛

复用结构审计脚本指向本轮未取得的真实输入，退出2并写 [BLOCKED_INPUTS_NOT_ACQUIRED](evidence/acquisition/audit_status.json)。协议 `--require-ready` 退出2，`formal_execution_permitted=false`；离线映射退出0。[命令和退出码](evidence/checks/executions.json)及 stdout/stderr 已保存。

| 真实数据门槛 | 当前状态 |
| --- | --- |
| 矩阵维度、方向、稀疏结构、全部值为有限非负整数 | NOT_VERIFIED：未取得 counts |
| 基因/细胞 ID 唯一性、顺序、metadata 对应 | NOT_VERIFIED：未取得两个 RDS |
| GEO 与 Hub 版本、1656/1920 来源、全部 ID 差分和历史修正 | NOT_VERIFIED：无真实原件可比较 |
| 批次/个体字段、嵌套 FACS 门、重叠/缺失及唯一标签层级 | NOT_VERIFIED / NOT_FROZEN |
| S1 Appendix 覆盖、新数据新增性最终裁定 | 原阻塞保持；本轮没有新增补充全文证据 |
| 真实 QC/标签/输入锁、正式实现及独立设计评审 | BLOCKED；本轮不签署放行 |

没有用 argmax 将 FACS 重叠门压成唯一真值，没有用表达或预测注释补标签，未运行 QC 筛选、HVG、CA/PCA、聚类或 ARI/NMI。本轮仅重新验证网络、官方目录和已有阻塞入口；不把目录下载成功当作新数据审计通过。

## 固定、复核与回传台账

工作分支 `audit/new-env-network-20261026` 基于 `122fdbf2986f3791917197385f8d07ba0a75fce6`，只新增本目录；既有算法/准备脚本、草案开关、R3/旧结果和 main 均不改。先固定实施提交，随后交不同 Sol High 实际参数的内部子任务独立审查；修复与复验记录另附，最终阶段结论由复核后追加，不把本实施结论当独立结论。

本轮工具发现支持 read/list/wait chat，但没有 `send_message_to_thread`、`handoff_thread` 或 `create_thread`，不能直接向原主控发消息；没有尝试用其他消息接口代传。授权范围内将轻量收据、评审和阶段结论 push 到独立分支及草稿 PR，供原主控直接读取。此次调用的工具范围不支持后台自动等待配置更新后续跑。

原始 SQLite 和外部记录的实际大小/SHA在 [external-artifacts.json](evidence/external-artifacts.json)。本目录轻量证据索引见 [evidence_index.json](evidence_index.json)。后续成功取得原件后仍须先冻结标签层级、冲突/缺失与评价 ID，再经独立数据/设计审查；首阶段通过边界和正式实验门槛不变。

首次 diff 空白检查提示 HTTP 原始 headers 中 CRLF/末尾空行。保留收据原字节，以本目录 `.gitattributes` 将这些 wire headers 标为不作文本转换/文本 diff，再检查；没有清洗或改写响应证据。
