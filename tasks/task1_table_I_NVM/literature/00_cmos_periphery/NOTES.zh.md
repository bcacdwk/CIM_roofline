# 00 — 28 nm CMOS 外围参考

用实测 SAR、普通 SRAM 局部服务和实际 CIM 宏共同建立外围参考。此组保留 3 份主文件，并复用 5 份 CIM 主文，形成 8 份共同依据；转换率、输入建立和完整求值周期不互相替代。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

共同/共享依据：[SACIM-03](../01_sram_acim/NOTES.zh.md#SACIM-03)、[SACIM-05](../01_sram_acim/NOTES.zh.md#SACIM-05)、[SDCIM-01](../02_sram_dcim/NOTES.zh.md#SDCIM-01)、[SDCIM-03](../02_sram_dcim/NOTES.zh.md#SDCIM-03)、[SDCIM-05](../02_sram_dcim/NOTES.zh.md#SDCIM-05)。

<a id="CMOS-02"></a>
## CMOS-02 — A 28 nm CMOS 10 bit 100 MS/s Asynchronous SAR ADC with Low-Power Switching Procedure and Timing-Protection Scheme

**核心** · 2021 · Electronics · [全文](CMOS-02_2021_AsynchronousSAR.pdf)

**身份与版本：** Fang Tang, Qiyun Ma, Zhou Shu, Yuanjin Zheng, Amine Bermak。本地正式 PDF（已核验身份）。

**用途与结构：** 28 nm 实测差分 SAR；正文区分采样、逐次比较、CDAC 建立和时序保护。测试含输入 buffer 与参考电路，实测频谱随输入频率变化。

**正文定位：** pp.2–6，Figs.1–7；pp.7–8，Figs.8–12。

**工艺/模式：** 直接的 28 nm 证据；精度按正文条件限定。

**使用限制：** PVT 表是后仿真；有效精度低于名义 10 bit。正文与 Fig.10 的 SNDR 数字不一致，后续不可混抄；CIM 共模与负载适配仍须建模。

**出版标识：** [DOI](https://doi.org/10.3390/electronics10222856)。

<a id="CMOS-03"></a>
## CMOS-03 — SRAM Assist Techniques for Operation in a Wide Voltage Range in 28-nm CMOS

**核心** · 2012 · IEEE Transactions on Circuits and Systems II: Express Briefs · [全文](CMOS-03_2012_SRAM_Assist.pdf)

**身份与版本：** Brian Zimmer, Seng Oon Toh, Huy Vo, Yunsup Lee, Olivier Thomas, Krste Asanovic, Borivoje Nikolic。完整正式论文/技术资料。

**用途与结构：** 给出读写成功终点、back-to-back 服务、WL 脉宽与 BL 电容的显式参考条件；适合通用 SRAM 写入换算方法。

**正文定位：** pp.1–3，动态读写定义、IV-A／IV-C；pp.4–5，assist 比较。

**工艺/模式：** 直接的 28 nm 证据（模型条件）；精度按正文条件限定。

**使用限制：** 28 nm、50 FO4 时钟及 128-cell 负载属于作者模型假设，不能写成量产 compiler 或流片保证。

**出版标识：** [DOI](https://doi.org/10.1109/tcsii.2012.2231015)。

<a id="CMOS-07"></a>
## CMOS-07 — Disturbance Aware Dynamic Power Reduction in Synchronous 2RW Dual-Port 8T SRAM by Self-Adjusting Wordline Pulse Timing

**核心** · 2023 · IEEE Journal of Solid-State Circuits · [全文](CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf)

**身份与版本：** Yoshisato Yokoyama, Koji Nii, Yuichiro Ishii, Shinji Tanaka, Kazutoshi Kobayashi。作者机构公开修订稿；当前唯一采用版本，内容足以支撑所列用途。

**用途与结构：** 实际 28 nm eFlash CMOS 平台上的同步 2RW 8T SRAM，区分 clock、WL 脉冲、read access 与端口操作；Table II 有 macro 配置、频率和读写测试条件。

**正文定位：** 作者修订稿 pp.1–2，Figs.1–2；pp.4–6，WL tracking；pp.8–9，Table II。

**工艺/模式：** 直接 28 nm eFlash CMOS 平台证据；特殊高阈值条件保留；精度按正文条件限定。

**使用限制：** 该工艺针对 eFlash 优化、core/SRAM 阈值较高，不能等同所有 28 nm logic compiler。当前采用机构公开作者修订稿，内容完整但有排版占位；仅用明确的 28 nm 条件。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2022.3229828)。

