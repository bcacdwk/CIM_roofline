# R1 / V3 归档核验

2026-09-08。当前结果见 [archive_validation_v3.json](archive_validation_v3.json)；本地核验脚本 `../scripts/verify_v3.py` 不联网、不修改 Git。

- 69 份 PDF 与 manifest 一一对应，文件签名、SHA-256、页数与各页尺寸通过；全部首尾页可渲染；没有未登记 PDF 或字节相同重复。
- V2 的 5 个用户文件身份核对且重命名前后哈希相同；原根目录 Zhou 两篇保持与副本一致。
- 当前 60 条本地主文完成用途筛选；SRAM DCIM 有 5 条候选、3 篇全文在本地，新增两篇仅核验官方题录/摘要。
- 本轮看过五份新文件封面及关键图表：RRAM-06 Figs.9/10、PCM-04-SI Fig.S6、SACIM-05 Fig.6/10；结合正文/Methods 判定用途。没有执行大规模 OCR。
- V2 缺件 0；V3 清单恰有 2 个待下载包，目标文件均未在本地。当前根目录 Markdown 与 11 个分类 README 的本地链接有效。
- PDF 不被 Git 忽略，保留用户设置。HEAD 不变；任务外仅原有 `.DS_Store` 两处修改。未暂存、提交或推送。
- 本轮代理下载 PDF 为 0；网络请求仅用于网页检索/题录和 Crossref 元数据。

先前的 archive_validation_r1.json 是 V2 发出前的 64 PDF 核验快照；当前以本文件所链的 V3 报告为准。
