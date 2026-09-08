# R0 核验与访问说明

核验日期：2026-09-08。此记录只用于来源身份、文件完整性和适用性初筛，不包含正式参数采集或吞吐分析。

## 起点与范围

开始时只读记录的 HEAD、Git 状态和理论检查点见 [baseline.json](baseline.json)。实际工作起点为 `5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c`，初始状态干净。新写入均位于 `tasks/task1_table_i/rebuild/`。

阅读入口为根 README、`docs/MODEL_CONVENTIONS.md`、`CIM_Roofline_Paper/cim_roofline.tex` 的定义与计量约定、归档旧稿的“硬件与 workload 的定量标定”，以及前轮 Task 1 manifest、SUPPORT.zh.md、AUDIT.md 与相关原文。保留逻辑 payload、完整服务间隔、完整更新和同一局部边界约定；旧表数字与“缺同篇实测配对就不能估算”的限制未继承。

## 身份核验的可追溯材料

- [source_manifest.json](../source_manifest.json) 每项保存题名、作者、日期、DOI／官方文档链接、优先级、用途、证据层级、状态、主路径、附件和版本关系。
- 本目录的 `ID_crossref.json` 是出版机构提交 Crossref 的原始 DOI 元数据，包含题名、作者及实际卷期／会议日期；manifest 的 `metadata_file` 指向对应文件。查询结果仅选身份精确匹配项，不将搜索结果本身作为 DOI。
- `PCM-03_crossref_query.json` 取第 0 项；`GC-02_crossref_query.json` 取第 0 项；`GC-04`、`GC-05` 查询各取第 1 项作为期刊主文，第 0 项为会议版本线索。下标从 0 开始。`GC-06_crossref.json` 是未纳入精选的结构待确认线索，不计目录数量。
- 前轮已核验来源复用原 manifest 身份，并重新核对现存 PDF 题名。NOR-05 没有可靠 DOI，保留作者主页原稿；厂商资料用产品／文档编号和实际修订号识别。
- 下载尝试见 [download_attempts.json](download_attempts.json)。它不是成功清单；成功与否以 manifest 中通过 PDF 检查的 `main_file`／附件记录为准。

## 文件检查

共归档 31 个有效 PDF：12 份仓库主文复制、14 份新取得主文、3 份 Supplementary Information、2 份相关会议前作／作者报告。所有文件检查 `%PDF-` 文件头、页数、页面尺寸、前两页可提取文字与 SHA-256，并用 PDFium 渲染首页。六张首页拼图已逐张目视检查，未发现登录页、空白伪 PDF 或题名错配。对带出版封面的文件，额外读后续实际论文首页。

结构化检查结果见 [archive_validation.json](archive_validation.json)；预览文件位于局部忽略的 `tmp/preview/`。这些检查只确认文件可打开及身份匹配，没有通读全部技术条件，也未做批量 OCR。

Zhou 2025／2026 直接从仓库根文件复制至本轮 `10_fenor_3d/`；与原文件以及前轮副本逐字节一致。原路径、前轮路径和哈希在 manifest 的 `copy_provenance` 中，原文件保留不动。

## 初筛发现及处理

| 来源 | 已核验事实及处理 |
| --- | --- |
| CMOS-01 | 官方两页 `IGADACT01C_Product_Brief_v002` 明确 28 nm HPM；未署发行日期，因此用 `undated`，不将 URL 的 2025 上传日期当出版年。已得具体 IP 简表，不再请求粗粒度 2022Q3 总览。 |
| CMOS-02 | 正文第 4 节 Measurement Results，有 die photo 和实测；另有 PVT 后仿真，二者区分。 |
| CMOS-06 | 第 4 节为 Simulation results，比较表标注 post-layout；按 28 nm 后仿真模型登记，未写成实测 ADC。 |
| CMOS-05 | DOI 元数据题名缺少 `GS/` 后的 s，保留登记形式并标注待 PDF 核对。另发现同团队 ESSERC 2025 的 32-GS/s 相关设计官方 PDF 线索，但两次下载均 SSL 连接失败；未把它当成本地全文或同一实测设计。 |
| SACIM-03 | 已取得 2022 会议前作，第 III 节明确仿真且已有 input-sparsity 方案；2023 期刊版放入暂缓，不宣称一定新增某项机制。首批转而补 Intel 独立实际 macro 的 SACIM-04。 |
| NOR-01 | 当前官方链接实际是 **002-18741 Rev. *E，2024-09-04，Military**，106 页；不是最初检索混入的 GL-T 文号 002-00247。已纠正身份，军规温度／寿命／时序不能当作普通商规条件。 |
| NOR-02／03 | Winbond 文件是 Rev. G，2019-04-08；Microchip 第 67 页确认 Rev. K 为 March 2022。未用门户新版本或下载日期覆盖本地实际修订。 |
| NAND-01 | Micron 官方索引的页脚为 ©2016／02/16，表中 MLC 2b/c 与 TLC 3b/c 分列；是技术简表，不是最新产品 datasheet。 |
| NAND-02／03 | 两篇为 KIOXIA 2026 与 SK hynix 2025 的不同 QLC 芯片；厂商和 4b/c 状态模式按正式出版记录登记。 |
| RRAM-03／04 | Weebit 文件前附作者转载声明，后为 28 nm 原始论文；Fujitsu datasheet 从 MikroE 开发板厂商文档站取得，原厂文号 DS501-00045-1v0-E，2016.12。 |
| FERAM-06 | 正文同时包含 Si:HfO₂ FeCAP 和 memristor 支路；本组只将 FeCAP 的存储／更新依据作为 FeRAM 支撑。 |
| GC-03 | 作者正式 PDF 首页 DOI 为 10.1109/TED.2024.3372938；28 nm macro 性能是基于实测 OS 器件的模型／仿真，不是实测 28 nm gain-cell 芯片。 |
| FENOR-01／02 | 两篇指定原稿均 3 页。2026 DOI 已由出版方 Crossref 元数据与题名／作者对应确认；`>` 在元数据中错成 `¾`，题名按原 PDF 规范为 `>10^12`。正文 2026 明确 AND-type，未改写为 NOR。 |
| FENOR-03／04 | 同团队直接相关 2024 会议／2025 期刊系列，保守合一个资料包。优先期刊，具体实验复用程度待全文；公开接受稿下载返回 HTTP 418。 |
| FENOR-05 | 摘要明确 **3D FeNAND**。保留垂直 FeFET 编程、集成和 VMM 结构的条件性交叉用途；串联 NAND 读路径不能直接代表 NOR 的局部服务。 |

## 访问失败与附件边界

GUC 旧总览链接、Micron 简表曾返回 HTML，Infineon 下载为空，Everspin 直接地址返回 404。无效载荷仅保留在忽略的 `tmp/`，没有放入有效 PDF 清单。当前环境的 IEEE 链接通常返回验证页面或拒绝下载，未绕过权限；出版身份与可点击 DOI 仍保留供用户正常访问。

CMOS-03 作者旧地址返回 404、CiteSeerX 超时；正式出版入口可用作人工获取路径。FENOR-04 接受稿链接虽已发现，但未因 URL 形似 PDF 就标为已获得。上述失败并不表示用户浏览器或机构权限也不能获取。

FERAM-05、FERAM-06、FENOR-05 的独立补充材料已从出版社链接取得并匹配题名／DOI。NeuRRAM、Jung MRAM、PCM-02 的主文带 Methods／Extended Data；独立附件完整性尚未全部核查，R1 若依赖其中内容再定向补，不重复索取主文。其他论文未识别必需 supplement 不等于确认不存在。

## 结束边界

第一批 18 个资料包，暂缓 10 个；另有 FENOR-03 同包线索而无重复任务。已取得文件不再作为主文人工任务。来源目录、manifest 和下载路径做一致性检查；原始 PDF／ZIP 与临时文件只由本任务 `.gitignore` 排除。

未修改 Table II、主论文、共享 docs 或根 README；未计算最终 ρ、τ、RI*，未制作新版 Table I，未执行 Git 提交类命令。状态为“R0 文献准备完成，等待用户补充第一批全文”。

最终只读 Git 检查：HEAD 未变；除本轮未跟踪的 rebuild 文件外，观察到根 `.DS_Store` 和 `tasks/.DS_Store` 两项变化。未判断其产生来源，也未直接写入、恢复或清理；其余已跟踪研究文件无差异。
