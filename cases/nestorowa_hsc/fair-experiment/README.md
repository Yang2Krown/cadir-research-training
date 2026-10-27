当前新增：正式两方法×五种子及全部诊断已执行完成，结果待全新独立复验。见 [实际结果报告](results/6cc7b3d-20261027-attempt-01/实际结果报告.md) 与 [逐图说明](results/6cc7b3d-20261027-attempt-01/presentation/逐图说明.md)。以下为阶段一冻结说明，历史边界保留。

# Nestorowa HSC：评价前共同准备与公平比较

本目录是输入阶段独立通过后的新阶段。旧输入复验da802216、首案例结论沿用。科学配置见design/scientific-config.json；冻结与实际接口修订依据见design/冻结说明.md。共同准备完成不等于正式执行获准。本实现者没有签署独立准入；正式CA/PCA/CAdir/聚类/ARI/NMI没有在阶段一运行。

## 实际数据与证据

原件只读：`/workspace/nestorowa-metadata-preparation/reacquired-20261026/`；外部产物：`/workspace/hsc-fair-experiment-data-20261026/stage1/`。三份原件SHA、QC/标签/evaluation完整ID、共同HVG表达输入和全部输出保护条目见locks/data-input-lock.json。Git保存小型表与锁，大表达/运行对象不入Git。外部目录与Git副本均不能冒充已完成用户本机备份。

首次共同准备成功产生QC、归一化、HVG、标签及RDS，末尾汇总序列化失败，原失败和全部文件保留。随后只读收尾脚本验证原文件SHA、完整ID对应、共同归一化公式、保存矩阵、既定QC谓词与HVG排序，独立目录写汇总和最终状态；没有再次运行归一化或方差建模，没有把旧FAILED改写PASS。具体状态以实际收尾成功收据为准。

evidence/environment-probe-01至03为静态函数/派发/版本探测，未执行算法。实际APL1.2.0与igraph2.3.4和草案版本不同，已明确修订。PCA必须ntop=Inf且全部共同HVG行，避免scater默认二次选500基因。C04资料包保留正文/代码覆盖与S1缺失边界，须由独立评审裁定课程新数据范围是否充分；不把搜索阴性写为绝未使用。

## 正式runner与独立准入

`design/admission-template.json`是不可执行模板，必须由未参与实现的Sol High评审者签署限定PASS并绑定精确source commit、source manifest/data lock/config/environment SHA以及C04裁定；实现者不得自签。Python入口与R正式/诊断入口均在算法前检查准入及源码/数据/环境。Python还核对被准入commit的精确Git源文件，实际镜像按sha256 ID固定。

获准后唯一入口：

```sh
python3 cases/nestorowa_hsc/fair-experiment/scripts/run_experiment.py \
  --admission /workspace/PATH/independent-admission.json \
  --output-root /workspace/hsc-fair-experiment-data-20261026/formal/NEW_RUN
```

正式调用只在未存在的新输出根下顺序运行两方法×五种子。每次为独立R进程，读取相同shared-hvg-sce.rds。容器网络关闭、2CPU/8GiB、代码/库/原件/历史目录只读，唯一新尝试目录可写；宿主UID运行。每次保存实际CA/PCA/图/分区、核心资源、RNG和失败日志。600秒核心超时由外部父进程监视核心标记执行，载入/导出另有600秒余量；失败保留且主比较分母为5。核心时间含CA+splitmerge或PCA+SNN+Louvain及轻量检查，输出序列化与排名另计；50ms RSS样本与含启动载入的VmHWM分别报告。

CAdir排名在另一个R进程只读本次**实际保存的CA对象和未排名对象**，不重新算CA；保存RNG、alpha、完整upstream assigned-gene排名、未分配基因及独立几何得分核对、PNG/PDF。只对固定CA基底解释排名，不宣称同seed足以保证任意CA基底不变性。排名/绘图失败单独记，不隐去诊断失败或把排名时间混入核心。

外部标签仅为六类已发布免疫表型参考。缺失标签的QC合格细胞参与聚类；两方法五种子仅在同一冻结evaluation交集计算ARI及NMImax。未知donor/Rep、不宣称原文1656队列、五种子非生物学重复等限制保持。

## 执行角色和当前边界

核心实现者编写/固定脚本、独立读取与解释输出；因其权限工具历史阻塞，由父协调者核SHA后原样转接Docker命令，协调者保留实际console与执行前后源码SHA收据。该角色分离不冒充实现者直接取得Docker权限，更不替代后续独立科学评审。没有伪造历史截图/录屏；真实命令输出与时间日志可用于当前操作展示，录屏需实际录制。
