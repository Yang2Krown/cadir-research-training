# CAdir 科研基础训练

CAdir论文复现、Nestorowa HSC新数据对照实验及课程材料。`main`集中保存实验实现、固定结果、独立评审和当前LaTeX报告，原分支及提交历史保留。

## 直接查看

| 内容 | 入口 |
| --- | --- |
| 当前实验报告 | [《计算机学报》格式PDF](deliverables/experiment-report-cjc-latex-20261027/main.pdf) · [LaTeX源码与编译](deliverables/experiment-report-cjc-latex-20261027/README.md) |
| LM首案例 | [案例与复跑](cases/tabula_muris_limb/README.md) · [Fig3/S1九项图表](cases/tabula_muris_limb/fig3_completion/README.md) |
| HSC新数据对照 | [案例入口](cases/nestorowa_hsc/README.md) · [实验实现](cases/nestorowa_hsc/fair-experiment/README.md) · [实际结果](cases/nestorowa_hsc/fair-experiment/results/6cc7b3d-20261027-attempt-01/实际结果报告.md) |
| HSC结果及证据包 | [ZIP、说明与哈希](deliverables/hsc-course-20261027/README.md) |
| 独立验收 | [评审索引](reviews/README.md) |
| 项目进度与课程材料 | [主控台账](project-control/README.md) · [交付物索引](deliverables/README.md) |

## 已完成的实验与材料

- **LM**：1882个细胞、6000个高变基因，得到7簇、1200个已分配基因；ARI为0.66951870448635153，NMImax为0.74188542311548167。完成原论文Fig3 A–D及关联S1 A–E，九项图表与数值检查已独立通过。[阶段结论](project-control/LM首案例图表补齐阶段结论-2026-10-27.md) · [作者公开输出对照](project-control/LM作者公开输出对照结论-2026-10-27.md)。
- **HSC新数据扩展**：共同QC保留1656个细胞，在1641个有参考标签的细胞上比较CAdir与PCA＋SNN＋Louvain，两方法各运行5个预定种子，已完成独立设计准入和结果复验。[阶段结论](project-control/HSC公平实验阶段结论-2026-10-27.md)。
- **LaTeX报告**：中英文题名、作者与单位、数学及代码分析、图表和附录；15篇英文参考文献，其中9篇为2024—2026年。当前入口为上表所列LaTeX版本，旧Word稿保留为历史材料。

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `cases/` | 两个案例的代码、配置、结果表、图表及运行证据 |
| `reviews/` | 独立评审原件、重算表及执行证据 |
| `deliverables/` | 当前LaTeX报告、HSC交付包和历史报告 |
| `project-control/` | 阶段结论、课程进度、看板增量、交接和评审归档 |
| `planning/` | 数据来源核查、输入准备和早期方案 |
| `delivery/` | 早期输入审核交付索引 |

运行命令见各案例README。报告主文档为`deliverables/experiment-report-cjc-latex-20261027/main.tex`，使用XeLaTeX。原始表达数据、大型RDS与运行库按外置对象清单管理；Git保存相应路径、大小与SHA256。

2026年10月28日按用户授权汇总分支并整理入口，见[仓库整理记录](project-control/repository-integration-20261028/README.md)。
