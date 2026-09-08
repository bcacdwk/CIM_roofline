# C 轮定向检索与取舍

检索/复核日期：2026-09-08。C 是 A/B 全文到件后的缺口补充，不是再收集一套 50–80 篇目录。用户要求停止下载后，本轮仅继续本地审阅与清单整理；后续全文获取全部由用户完成。

## 进入本轮目录的 5 条新来源

| ID | 正文暴露的缺口 | 新来源与身份依据 | 处理 |
|---|---|---|---|
| CMOS-07 | CMOS-04 的 clock-skew shmoo 不能给出普通 macro 服务周期 | [Yokoyama 等，JSSC 2023](https://doi.org/10.1109/JSSC.2022.3229828)；[作者机构 R2 稿](https://www-vlsi.es.kit.ac.jp/thesis/papers/pdfs/JSSC-22-0279.R2.pdf)，题名/作者与出版登记匹配 | 停止下载指令前已归档。实际 28 nm SRAM 的配置、频率和 read/write 控制有用；eFlash 工艺及作者稿版本明确保留，不再请求正式版 |
| SACIM-05 | SACIM-03 新增实测但仅 4-bit 路径；RF DAC 不能直接代替 CIM 输入 | [Su 等，TCAS-II 2024](https://doi.org/10.1109/TCSII.2023.3331375)；[IEEE 记录](https://ieeexplore.ieee.org/document/10314139/) | 请求主文；官方摘要确认实际 28 nm 8-bit 输入/权重及 ADC combining。在线首发 2023-11-09，卷期 2024-04；精度服务与负载细节待全文 |
| RRAM-06 | RRAM-02 主要比较脉冲次数，RRAM-05 完整测量偏读侧 | [Chiu 等，VLSI 2019](https://doi.org/10.23919/VLSIT.2019.8776540)；[TSMC 官方技术记录](https://research.tsmc.com/page/rram/1.html) | 请求主文；有 auto-RESET、auto-SET、hidden-RESET 和 page-write 的直接产业线索，值得保留较早来源。需要核实被隐藏/移出前台的 RESET 代价 |
| PCM-06 | PCM-02 Methods 将逐行闭环写入转引 ref.4 | [Narayanan 等，TED 2021](https://doi.org/10.1109/TED.2021.3115993)；[IBM 原始记录](https://research.ibm.com/publications/fully-on-chip-mac-at-14-nm-enabled-by-accurate-row-wise-programming-of-pcm-based-weights-and-parallel-vector-transport-in-duration-format) | 请求期刊主文，补闭环/512 权重并行操作；不重复要同题 VLSI 会议版，也不算与 PCM-02 独立工艺证据 |
| MRAM-06 | MRAM-02 正文是 sense 后 near-memory 数字计算，不是 bitcell 内乘法 | [Li 等，Nature Electronics 2025](https://doi.org/10.1038/s41928-025-01479-y)；[出版社页面](https://www.nature.com/articles/s41928-025-01479-y) | 请求主文；SI 已在停止指令前归档。SI Fig.2 确认互补 MTJ 两阶段写入，主文的完整周期/数字路径仍待审。发表 2025-10-16，不用网页抓取相对日期推算年份 |

四篇尚缺主文的新候选只属于“出版身份+摘要/部分 SI 已核验”，不属于已完成主文分析。新增 CMOS-07 已读关键正文。各文件目标路径统一见 [下载清单 V2](DOWNLOAD_REQUESTS_V1.md) 和 [目录](LITERATURE_CATALOG.md)。

## 对已有包的附件检查

- **PCM-04**：主文明确把 Materials and Methods、Figs.S1–S11 放在附件，确有技术缺件；V2 只请求 SI。
- **MRAM-02**：[官方 13 页 SI](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41928-023-00994-0/MediaObjects/41928_2023_994_MOESM1_ESM.pdf)已归档。实际含普通感测、PUF 生成/写回、访问延时测量边界，不再由用户下载。
- **MRAM-06**：[官方 15 页 SI](https://media.springernature.com/original/springer-static/esm/art:10.1038%2Fs41928-025-01479-y/MediaObjects/41928_2025_1479_MOESM1_ESM.pdf)已归档。主文仍缺，SI 不能代替。
- [NeuRRAM](https://www.nature.com/articles/s41586-022-04992-8)、[IBM 2023 speech PCM](https://www.nature.com/articles/s41586-023-06337-5)出版页本次未列独立技术 SI PDF；本地已有 Methods/Extended Data，不再根据通用结尾语无差别索取附件。
- [Jung MRAM](https://www.nature.com/articles/s41586-021-04196-6)和[IBM 64-core PCM](https://www.nature.com/articles/s41928-023-01010-1)页面的额外附件为演示视频；当前方法依据已在主文，不请求视频。

## 检索到但未增加下载任务

| 线索 | 判断与处理 |
|---|---|
| [28-nm 9T SRAM CIM、redundant array-assisted ADC，Integration 2024](https://www.sciencedirect.com/science/article/pii/S1879239124001012) | 公开摘要为仿真；现有 SACIM-03 已有流片，CMOS-06 已提供设计仿真。本轮不再补功能相近但缺独立实测的资料 |
| [6-bit pitch-matched SAR for SRAM CIM，Integration 2025](https://www.sciencedirect.com/science/article/abs/pii/S1879239125001341) | 对 pitch/并行读有潜在价值，但尚未确认完整流片/服务证据；先审新增 SACIM-05 的实际 ADC 共享路径，不列立即待办 |
| [ISSCC 2022 paper 11.6 simultaneous MAC/write，官方 press kit](https://static1.squarespace.com/static/6130ef779c7a2574bd4b8888/t/626325a757094e52110f7db0/1650664892028/ISSCC2022PressKit.pdf) | 实际为 5 nm、12T latch 结构，不能仅凭关键词当成共同 28 nm 6T SRAM 写入基线。已有 GC-05 可支持一种明确的并行更新机制，暂不追加 |
| [28-nm FD-SOI 8T SRAM，TCAS-I 2019 的机构全文](https://da.lib.kobe-u.ac.jp/da/kernel/90008144/90008144.pdf) | 低电压、FD-SOI 的实际连续写参考有用，但本轮 CMOS-07 已补普通 SRAM 服务；暂不扩展另一种工艺/工作点 |
| [SRAM Write- and Performance-Assist Cells，JSSC 2022](https://doi.org/10.1109/JSSC.2021.3138785) | 28 nm 测试芯片加电阻模拟更先进节点互连；若直接当 28 nm 普通 BL 条件会误用。暂不补下载 |
| [Macronix SLC NAND 正式目录](https://www.mxic.com.tw/en-us/support/technical-documentation/Pages/SLC-NAND-Flash.aspx) | 目录有 SLC 产品，但没有据此核实目标料号为 3D 结构。不能把普通 SLC 产品自动归为 3D NAND；不要求用户盲选文件 |
| [Micron 2016 3D NAND flyer（已有 NAND-01）](LITERATURE_CATALOG.md#NAND-01) | 确有 MLC/TLC 的时间与粒度表，不因只有两页便剔除；未找到匹配料号的公开完整时序手册，完整 plane/SLC 约束仍列缺口 |
| 第三方镜像的 TSMC 28 nm SRAM databook | 未核实官方公开发布身份，不进入候选或下载清单；用原始 SRAM 电路论文补透明条件 |

访问尝试的 HTTP 状态记录保留在 [c_access_attempts.json](metadata/c_access_attempts.json)；这些均发生于停止下载指令之前。HTML 或限制页没有以 `.pdf` 归档。后续不再执行文献下载。
