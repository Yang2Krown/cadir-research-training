# 《计算机学报》LaTeX实验报告

主文档：[main.tex](main.tex)。阅读版：[main.pdf](main.pdf)。

采用用户指定的[计算机学报LaTeX模板](https://github.com/strive-yang/CHINESE-JOURNAL-OF-COMPUTERS--Latex-Template)，固定版本`69e5409cd9ad26c92348896494dd3a18b78a0fbe`。报告包含中英文题目、摘要与关键词、目录、双栏正文、13幅PDF结果图、公式、代码分析、GB/T 7714文献、附录和工作记录。

## 编辑与编译

1. 在`metadata.tex`编辑标题、成员署名和单位。
2. 在`sections/`编辑报告各部分，在`bib/ref.bib`维护文献。
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

中文依赖使用CTeX、xeCJK和Fandol字体。拉丁字体优先选择Times New Roman，其次TeX Gyre Termes，再使用Liberation Serif。本次云端编译使用Fandol和Liberation Serif。正文、页宽、栏间距及字号层级由模板文档类控制。

## 模板适配

- 沿用`CjC.cls`的页面、字号、章节及双面设置。
- 将文档类内部的旧`\zihao`命名为`\CjCzihao`，解决与现代CTeX同名定义的冲突，保持原字号映射。
- 使用标准`ctex`包入口，兼容Linux大小写规则及标准TeX Live依赖。
- 页眉沿用双面学报式布局，填写课程报告信息；正文双栏，较宽图表跨栏，附录单栏。
- 用正确的粗体希腊字母命令、可换行代码路径和窄栏公式排版处理数学及代码。
- 使用模板的GB/T 7714 BibTeX样式；正文引用、图表编号和目录页码由LaTeX生成。

精确模板差异见`evidence/template-compatibility.patch`，来源与图表哈希见`evidence/`。

## 内容来源

正文承接项目提交`b7d968ad8d30f366383c2b3afc97a5c2e5b2bfa5`中的完整实验报告。LM和HSC科学数据、数值及结果沿用固定成果。13幅图从固定提交的PDF原件提取，保留图表内容。

`scripts/prepare_report.py`供完整项目仓库从报告Markdown重新生成章节及提取固定PDF；源码包已经包含生成后的章节和图，直接编译即可。`evidence/build-check.json`记录实际编译与文档检查结果。
