# C04 实际访问记录

浏览工具：`mcp__codex_apps__search_service_web_run`。本轮访问约为 2026-10-26 12:40–12:48 UTC；工具没有在每个请求上暴露独立时间戳。记录只描述实际返回，不把搜索摘要冒充 PDF 下载。

| 时间窗 | 请求/来源 | 结果 | 证据定位 |
|---|---|---|---|
| 12:40–12:41 UTC | 打开 PLOS 官方正文 `https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1014418` | 可读 HTML，947 行；读取 Methods 数据清单、Table 2 说明、cluster-number recovery、支持信息目录 | `turn427101view0` 行 65–95、136、438–449、478–493；定位内容也在 `turn254400view0` |
| 12:41 UTC | 在同一 PLOS 正文 find `Nestorowa`、`GSE81682` | 两项在当前主文 HTML 中均无匹配 | `turn768652view1`、`turn768652view5`；这是正文检索阴性，非附件或代码之外的绝对证明 |
| 12:41 UTC | 浏览工具搜索结果中打开 PMC article `https://pmc.ncbi.nlm.nih.gov/articles/PMC13349309/` | reCAPTCHA interstitial，无全文 | `turn768652view0` |
| 12:42 UTC | 搜索索引命中 PMC CAdir article | 返回支持信息索引摘要，显示 S1 Appendix 标题、PDF 文件名和 140.6 KB；摘要开头提到 Tabula Muris Limb Muscle S1 Fig | `turn427101search0`；只作索引摘要记录，未拿到文件字节 |
| 12:42 UTC | 从 PLOS 正文点击 S1 DOI `https://doi.org/10.1371/journal.pcbi.1014418.s001` | HTTP 500，重定向到 `https://dx.plos.org/10.1371/journal.pcbi.1014418.s001`，工具标注目标不可访问 | `turn286240view1`；未重复请求此失败地址 |
| 12:42 UTC | 点击 PLOS Table 2 图像 | HTTP 500，重定向到签名 Google Storage 资产地址，工具标注目标不可访问 | `turn286240view0`；未保存图像 |
| 12:43 UTC | 打开 PMC OA utility 及 PMC BioC API | 两个 endpoint 均由浏览工具报告 URL 不可访问 | `turn207438view0`、`turn207438view1` |
| 12:43 UTC | 打开论文指向的 Zenodo 记录 `https://zenodo.org/records/14900874` | 浏览工具报告 URL 不可访问 | `turn244364view0` |
| 12:47 UTC | 打开 Europe PMC fullTextXML API `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13349309/fullTextXML` | 浏览工具报告 URL 不可访问；没有取得 OA package FTP 路径 | `turn751530view0`；元数据层补查失败，未访问 FTP 文件 |

既有来源审计的 S1 访问失败记录已在 `/workspace/hsc-fair-experiment/planning/new-dataset/2026-10-26/sources.json`（`paper_supplement_plos.attempted_urls`）和 `来源审计报告.md` 留档。精确的 PLOS direct file URL `https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1014418.s001&type=printable` 已在该记录列为实际尝试，连同 asset 路径均未能读取；先前来源报告记为浏览器访问失败，本轮据此不重复请求。PMC OA utility 本轮也已尝试一次（turn207438view0），没有重复。

本轮无 `curl`/HTTP shell 请求、无真实数据访问、无 PDF/表格图像下载。故无附件字节数实测值或附件 SHA-256；索引中显示的 140.6 KB 仅是页面所示元数据。
