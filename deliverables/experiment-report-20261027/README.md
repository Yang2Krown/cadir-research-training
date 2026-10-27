# 实验报告阅读与编辑入口

最新课程排版采用用户指定的《计算机学报》LaTeX模板，见[LaTeX源码与PDF](../experiment-report-cjc-latex-20261027/README.md)。本目录保留正文源文件、前一版Word／PDF及材料索引。

- [实验报告.docx](实验报告.docx)：可编辑Word，包含目录、公式、13幅真实结果图、表格、参考文献及工作记录表。
- [实验报告.pdf](实验报告.pdf)：排版阅读版，目录显示实际页码。
- [实验报告.md](实验报告.md)：正文源文件。
- `assets/`：报告使用的LM九图与HSC四图，按固定Git对象原样提取。
- `evidence/`：数值表、环境／配置记录、固定代码、文件SHA256与报告一致性检查。

正文按研究背景、原理、环境与操作、代码分析、LM结果、HSC对照、讨论和结论组织。报告复用既有实验及独立验收。本轮完成文稿、图表嵌入、Word／PDF排版及文档一致性检查。

构建命令（在已保存本目录材料的环境中执行）：

```bash
python scripts/build_report.py
python scripts/check_report.py
```

依赖：Python及python-docx、PyMuPDF，Pandoc和LibreOffice。`scripts/reference.docx`由构建脚本生成，用于设置A4、字体层级、页眉页脚和公式／图表排版。目录通过PDF实际书签页码写入Word，并重新导出核对。

从项目Git对象重新收集图表和源码：

```bash
python scripts/build_report.py --source-repo /path/to/cadir-research-training
```

源仓库需保留本目录索引中的LM与HSC固定提交。正文编辑后执行构建命令即可更新Word、PDF和目录页码。
