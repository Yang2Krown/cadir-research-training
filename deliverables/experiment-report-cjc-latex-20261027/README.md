# 《计算机学报》LaTeX实验报告

主文档：[main.tex](main.tex)。阅读版：[main.pdf](main.pdf)。

首页保留《计算机学报》／CHINESE JOURNAL OF COMPUTERS刊名，去掉卷期，日期为2026年10月／October 2026。中英文署名已按用户提供的信息填写孙良坤、李思言、ChatGPT 6.1 Sol；南京农业大学对应前两位作者。

本版已按用户PDF反馈修正图表与命令排版：Fig3B/C及S1D/E分别并排；移去外侧白边，将四张窄图的重复标题整合进中文图注，保留数据、轴、图例及等比例坐标。13份原始PDF保存在项目仓库`figures/`，排版用文件位于`layout/figures/`。

命令清单采用小五大小的等宽字，取消额外细框，固定段前段后间距。安装命令写为先进入环境目录再执行脚本。正文中的命令空格和文件名数字组保留，路径及长标识可在窄栏中换行。

浮动页中的图表间距固定，余白集中在页底；参考文献接续正文排版。

图4使用已有逐节点坐标、成员和边表，改为完整拓扑加三个关键关联图；初始、合并、拆分阶段的全部21个关联图分组放入附录D。各阶段的历史注释和细胞数保持原值。LM跨栏图与对应解读衔接排版，避免解释文字提前流走后只剩图页。

方向角热图按已有7×7数值表重新设置打印字号，以C1—C7标识簇号，并显示一位小数；原始完整精度表保存在`evidence/S1A_pairwise_direction_angles_degrees.tsv`。热图与投影矩阵同页，两种HSC参考组成图同页。图文区使用跨栏图与双栏解读块，其他正文沿用双栏。

参考文献共15篇英文文献，其中9篇发表于2024—2026年。新增相关工作涉及CAbiNet、双聚类综述、iVAE、scICE、CHOIR、聚类基准、归一化及数据集相关流程评价，均已在正文引用；元数据核对记录见`evidence/reference-verification.json`。

采用用户指定的[计算机学报LaTeX模板](https://github.com/strive-yang/CHINESE-JOURNAL-OF-COMPUTERS--Latex-Template)，固定版本`69e5409cd9ad26c92348896494dd3a18b78a0fbe`。报告包含中英文题目、摘要与关键词、目录、双栏正文、16个编号图、公式、代码分析、GB/T 7714文献、附录和工作记录。原13份科学图保留，图4调整显示方式，另增3个历史阶段放大图。

## 编辑与编译

1. 在`metadata.tex`编辑标题、成员署名和单位。
2. 直接编译可在`sections/`编辑各部分，在`bib/ref.bib`维护文献。完整仓库通过`report-content.md`重新生成章节时，会覆盖`sections/`内的直接编辑；请选一种方式维护。
3. 使用XeLaTeX编译主文档`main.tex`。

本地TeX Live／MiKTeX环境：

```bash
bash build.sh
```

等价命令：

```bash
xelatex -halt-on-error -interaction=nonstopmode main.tex
bibtex main
xelatex -halt-on-error -interaction=nonstopmode main.tex
xelatex -halt-on-error -interaction=nonstopmode main.tex
```

Overleaf：上传源码ZIP，设置主文档为`main.tex`，编译器选择**XeLaTeX**，点击Recompile。源码包将`main.tex`放在压缩包根目录。

更新已有Overleaf项目时，用本次源码包完整替换，连同`layout/`、`sections/`和`main.tex`一起更新。便携包包含编译所需的排版图；原始PDF仍可从固定项目仓库取得。

中文依赖使用CTeX、xeCJK和Fandol字体。拉丁字体优先选择Times New Roman，其次TeX Gyre Termes，再使用Liberation Serif。本次云端编译使用Fandol和Liberation Serif。正文、页宽、栏间距及字号层级由模板文档类控制。

## 模板适配

- 沿用`CjC.cls`的页面、字号、章节及双面设置。
- 将文档类内部的旧`\zihao`命名为`\CjCzihao`，解决与现代CTeX同名定义的冲突，保持原字号映射。
- 使用标准`ctex`包入口，兼容Linux大小写规则及标准TeX Live依赖。
- 页眉沿用双面学报式布局，按用户要求填写刊名、日期和作者；正文双栏，较宽图表跨栏，附录单栏。
- 用正确的粗体希腊字母命令、可换行代码路径和窄栏公式排版处理数学及代码。
- 使用模板的GB/T 7714 BibTeX样式；正文引用、图表编号和目录页码由LaTeX生成。

精确模板差异见`evidence/template-compatibility.patch`，来源与图表哈希见`evidence/`。

## 内容来源

正文承接项目提交`b7d968ad8d30f366383c2b3afc97a5c2e5b2bfa5`中的完整实验报告。LM和HSC科学数据、数值及结果沿用固定成果。13幅图从固定提交的PDF原件提取，保留图表内容。

`scripts/prepare_report.py`供完整项目仓库从本目录`report-content.md`重新生成章节及提取固定PDF；源码包已经包含生成后的章节和图，直接编译即可。`evidence/build-check.json`记录实际编译与文档检查结果。

完整仓库重新生成排版图时执行`python scripts/prepare_figure_layout.py`。在完整仓库运行`python scripts/check_latex.py`检查原图与排版；便携包可运行`python scripts/check_latex.py --display-only`检查排版图和编译结果。

图4及附录D使用`python scripts/render_history_readable.py`从`evidence/history-data/`重绘显示图。需要Python的NumPy、pandas、Matplotlib；正常LaTeX编译不依赖Python或R。该脚本检查原表哈希、21节点的逐ID对齐和成员数量、22节点23边拓扑，生成记录`evidence/history-readable.json`。

方向角热图的显示脚本为`python scripts/render_angle_readable.py`，只读取固定角度表，不重新计算方向角；记录见`evidence/angle-readable.json`。
