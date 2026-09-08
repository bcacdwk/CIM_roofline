# 人工下载清单 V3 — SRAM DCIM 补充

2026-09-08。继续使用用户指定路径 `DOWNLOAD_REQUESTS_V1.md`，**内容已更新为 V3**；[V2 备份](history/r1_v2/DOWNLOAD_REQUESTS_V1.md)。

**V2 五包全部到齐并验收，旧请求缺件为 0。本次只请下载下列 2 篇 SRAM DCIM 主文。** 全部论文下载由用户负责；本轮代理没有下载 PDF。

本地已有 60 条主文记录、69 份 PDF；SRAM DCIM 现在有 5 条候选，其中 3 篇已有、2 篇待下载。完整目录与文件身份见 [LITERATURE_CATALOG.md](LITERATURE_CATALOG.md)，本轮正文判断见 [V2_INTAKE_AND_DCIM_REVIEW.md](V2_INTAKE_AND_DCIM_REVIEW.md)。

## 请下载

- [ ] **SDCIM-04 — A 28 nm 16-kb Sign-Extension-Less Digital-Compute-in-Memory Macro With Extension-Friendly Compute Units and Accuracy-Adjustable Adder-Tree**；2024；IEEE Transactions on Very Large Scale Integration (VLSI) Systems
  - DOI：[https://doi.org/10.1109/tvlsi.2024.3418888](https://doi.org/10.1109/tvlsi.2024.3418888)。
  - 官方/合法入口：[入口 1](https://ieeexplore.ieee.org/document/10582884/)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-04_2024_SignExtensionLess_DigitalCIM.pdf`
  - 为何需要：现有 D6CIM/动态逻辑主要解释逐位展开；这篇补有符号整数乘法、符号扩展处理和 accuracy-adjustable adder 的完整服务，核查精度模式而非只对比能效。
  - 下载内容：完整期刊主文 2164-2168；若出版社确有技术 SI，一并获取。
  - 日期/版本：IEEE 首发 2024-07-03；TVLSI 32(11), 2164–2168，卷期 2024-11。
  - 当前情况：仅题录与官方摘要已核验，尚未读取全文；完整精度、周期、阵列/写口边界仍待检查。
  - 核查重点：signed INT8 的完整 MAC 服务；精度可调模式下的输出/时序差异；不要先视为所有配置都 lossless。

- [ ] **SDCIM-05 — A 28-nm Digital Transpose SRAM Compute-in-Memory Macro With Accurate/Approximate Dual Mode for Floating-Point Edge Training and Inference**；2026；IEEE Journal of Solid-State Circuits
  - DOI：[https://doi.org/10.1109/jssc.2026.3679560](https://doi.org/10.1109/jssc.2026.3679560)。
  - 官方/合法入口：[入口 1](https://ieeexplore.ieee.org/document/11475654/)；[入口 2](https://sscs.ieee.org/category/ieee-journal-of-solid-state-circuits/ieee-journal-of-solid-state-circuits-early-access/page/16/)；[入口 3](https://sasasatori.github.io/)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-05_2026_DigitalTranspose_AccurateApprox.pdf`
  - 为何需要：补数字 SRAM 矩阵转置、FF/BP 的局部访问方向与 MAC 电路复用，以及精确/近似和整数/浮点控制。写入路径仍须正文确认，不能由题名“training”推断写周期。
  - 下载内容：完整期刊主文 5098-5110；若出版社确有技术 SI，一并获取。
  - 日期/版本：Crossref 当前卷期为 JSSC 61(9), 5098–5110（2026-09）。SSCS 2026-04-08 已刊 Early Access 介绍，证明此前已公开；不把该介绍日或 DOI 创建日充作论文精确首发日，待 PDF 确认。
  - 当前情况：仅题录与官方摘要已核验，尚未读取全文；完整精度、周期、阵列/写口边界仍待检查。
  - 避免重复：只要 2026 JSSC 期刊版（13 页，5098–5110；完整 Early Access 版也可），**不用再下同主题 ISSCC 2025 14.5**。转置/反向传播不自动证明普通权重写周期更快。

## 已关闭的 V2 请求

| 包 | 状态 |
|---|---|
| SACIM-05 | 5 页主文已核验，四组 2-bit DAC/GBL combining 有用 |
| RRAM-06 | 2 页主文已核验，保留写入方法；时间归一化，不当绝对 page 延时 |
| PCM-06 | 8 页主文已核验，逐行闭环及 FPGA 控制明确 |
| MRAM-06 | 24 页主文/Extended Data 与 15 页 SI 均齐 |
| PCM-04-SI | 18 页方法与 Figs.S1–S11 已齐 |

其他技术缺口暂没有经核实、明确需要用户再取的文件；不再列泛泛候补。原因见本轮报告。收到这两篇后先核对正文，不自动进入正式参数计算。
