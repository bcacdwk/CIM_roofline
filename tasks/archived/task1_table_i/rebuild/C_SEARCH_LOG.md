# 定向检索取舍（V3 更新）

2026-09-08。本次只浏览题录/摘要、作者/机构页面和 Crossref 元数据，未下载全文。原 C/V2 五包的检索记录保存在 [V2 快照](history/r1_v2/C_SEARCH_LOG.md)，请求已经全部关闭；本地内容的复核见 [本轮报告](V2_INTAKE_AND_DCIM_REVIEW.md)。

## 新增两篇 SRAM DCIM

| ID | 身份核验 | 补充作用 | 版本/限制 |
|---|---|---|---|
| SDCIM-04 | [IEEE 官方记录](https://ieeexplore.ieee.org/document/10582884/)、[DOI](https://doi.org/10.1109/TVLSI.2024.3418888)，Xin Si 等；TVLSI 32(11), 2164–2168，2024 | signed MAC、符号扩展与可调精度 adder；官方摘要明确 28 nm 流片 | 2024-07-03 首发、11 月卷期；主文未读，不能预设所有配置无损 |
| SDCIM-05 | [IEEE 记录](https://ieeexplore.ieee.org/document/11475654/)、[DOI](https://doi.org/10.1109/JSSC.2026.3679560)、[SSCS 官方 Early Access 介绍](https://sscs.ieee.org/category/ieee-journal-of-solid-state-circuits/ieee-journal-of-solid-state-circuits-early-access/page/16/)、[作者主页](https://sasasatori.github.io/)；Yiyang Yuan 等 | 28 nm 数字 transpose SRAM，精确/近似、FF/BP 方向和计算复用；补局部服务条件 | Crossref 卷期 2026-09；SSCS 2026-04-08 已介绍，确为已公开来源，但精确首发日留待正文确认；不重复取同主题 2025 ISSCC 14.5 |

两条 Crossref 原始登记已保存到 metadata/SDCIM-04_crossref.json 与 metadata/SDCIM-05_crossref.json。没有用搜索摘要的“几个月前”推算发表日期。当前清单只请求这两个期刊包。

## 筛过但不增加任务

- [ISSCC 2025 14.5 6T-SRAM transpose 前作](https://ieeexplore.ieee.org/document/10904659/)：与新 JSSC 同主题/团队，按一个演进工作包处理。先读期刊，不同时要求两版。
- [28 nm 两周期 Winograd DCIM processor，JSSC 2025](https://ieeexplore.ieee.org/document/10562243/)：可补 radix-16/两周期执行，但系统 sparsity/Winograd 的收益需要分离；当前优先两篇更直接的局部 signed/transpose 资料，不再追加第三篇。
- [CICC 2024 analog-digital hybrid SRAM](https://doi.org/10.1109/CICC60959.2024.10529098)：搜索中出现的混合域/ADC 路线不应按“数字输出”归入 DCIM。此项仅为检索方向排除，未据此索取或登记核心来源。
- [28 nm 输入稀疏 DTC macro，TCAS-II 2024](https://doi.org/10.1109/TCSII.2024.3360284)：时间编码/量化路线，不因含数字控制或 SRAM 就补入纯数字类别。
- [早期 column-MAC/bit-serial 系列的 ESSCIRC 2019 记录](https://doi.org/10.1109/ESSCIRC.2019.8902824)：该系列有多种 cell/near-memory 演进，与现有 SDCIM-02 作者有重叠；本次先补更近、明确 28 nm 的两篇，避免再拓展旧系列。

## V2 正文暴露的边界

SACIM-05 提供真实 28 nm 局部写路径及四组 2-bit DAC/ADC 共享；RRAM-06 的时间为归一化，只补步骤和控制，不能兑现绝对 page 时序的原先期待；PCM-06 明确调谐环使用 FPGA；MRAM-06 明确位串行多位输入；PCM-04-SI 明确仪器、结构和实验间隔。五包都提供有效依据，没有因此新增整篇删除项。

3D NAND SLC 完整操作手册、RRAM 绝对 page 服务与通用 compiler 库仍作为技术缺口记录。没有核实到必须立刻再取的具体文件，故不把它们变成泛泛人工任务。
