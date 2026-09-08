# 09 — Gain-cell eDRAM

2T1C/4T/3T1C 结构、硅/oxide 通道、模拟/数字求值分别处理。保持分布、刷新占用与 storage/stationary 更新关系共同约束服务。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="GC-01"></a>
## GC-01 — Gain-Cell CIM: Leakage and Bitline Swing Aware 2T1C Gain-Cell eDRAM Compute in Memory Design with Bitline Precharge DACs and Compact Schmitt Trigger ADCs

**核心** · 2022 · VLSI Symposium, 112–113 · [全文](GC-01_2022_GainCell_CIM.pdf)

**身份与版本：** Shanshan Xie, Can Ni, Pulkit Jain, Fatih Hamzaoglu, Jaydeep P. Kulkarni。Published paper。

**用途与结构：** 65 nm 2T1C gain-cell CIM 的读写端口分离、BL 输入预充、泄漏夹位和 ST-ADC 有明确电路与测试证据。

**正文定位：** p.1，三步 MAV／Measurement Results；p.2，Figs.2–7。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；65 nm CMOS 2T1C gain-cell；数字权重。

**使用限制：** 2-bit 输入顺序展开及 complementary weight 不等于单次完整 8-bit 运算；不能取普通 1T1C DRAM 代替。

**出版标识：** [DOI](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338)。

<a id="GC-02"></a>
## GC-02 — An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications

**核心** · 2018 · IEEE Journal of Solid-State Circuits · [全文](GC-02_2018_MixedVT_4T_GainCell.pdf)

**身份与版本：** Robert Giterman, Alexander Fish, Narkis Geuli, Elad Mentovich, Andreas Burg, Adam Teman。完整正式论文/技术资料。

**用途与结构：** 28 nm 4T IFGC 实测 128×32 macro，WWL 升压与时序、SA、读写频率和保持分布；直接支撑刷新占用与局部边界。

**正文定位：** pp.4–8，Figs.4–11；pp.9–10，retention/availability。

**工艺/模式：** 直接的 28 nm 证据（gain-cell 存储）；28 nm bulk mixed-VT 4T gain-cell。

**使用限制：** 5 µs 刷新对应文中约 99% bit 可靠性条件，不是全 bit 无误保证；平均保持不能代替最差 cell。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2018.2820145)。

<a id="GC-03"></a>
## GC-03 — Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform

**核心** · 2024 · IEEE Transactions on Electron Devices 71(5), 3329–3335 · [全文](GC-03_2024_OxideGainCell.pdf)

**身份与版本：** Shuhan Liu, Koustav Jana, Kasidit Toprasertpong, Jian Chen, Zheng Liang, Qi Jiang, Sumaiya Wahid, Shengjun Qin, Wei-Chen Chen, Eric Pop, H.-S. Philip Wong。本地正式 PDF（已核验身份）。

**用途与结构：** 以 28 nm macro 模型将保持、读取电流和刷新阻塞联系起来，能支持从 oxide 器件到 local service 的透明换算。

**正文定位：** pp.2–4，top-down macro/refresh；pp.4–6，器件规格。

**工艺/模式：** 直接的 28 nm 模型条件／其他工艺器件依据（须逐项区分）；OS–OS／hybrid gain-cell，保留不同通道结构。

**使用限制：** GEMTOO/Timeloop 是设计评估，非实测完整 oxide CIM 芯片。

**出版标识：** [DOI](https://doi.org/10.1109/TED.2024.3372938)。

<a id="GC-04"></a>
## GC-04 — A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM

**核心** · 2024 · IEEE Journal of Solid-State Circuits · [全文](GC-04_2024_DynamicCascoded_MLC.pdf)

**身份与版本：** Jiahao Song, Xiyuan Tang, Haoyang Luo, Haoyi Zhang, Xin Qiao, Zixuan Sun, Xiangxing Yang, Zihan Wu, Yuan Wang, Runsheng Wang, Ru Huang。完整正式论文/技术资料。

**用途与结构：** 65 nm 3T1C MLC gain-cell，电流写入自校正，先电压粗写再电流精写；完整 CIM 含 precharge、DTC 求值和 SAR。

**正文定位：** pp.4–7，Figs.4–11；p.8，Fig.12／measurement。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；3T1C current-programmed dynamic-cascode MLC。

**使用限制：** 5 ns 仅粗写；60 ns 建立结论在 Fig.12 仿真中，不能称实测完整更新；180 ns compute 与保持漂移精度相关。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2023.3339887)。

<a id="GC-05"></a>
## GC-05 — An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips

**核心** · 2025 · IEEE Journal of Solid-State Circuits · [全文](GC-05_2025_DualMode_GainCell.pdf)

**身份与版本：** Ping-Chun Wu, Win-San Khwa, Jui-Jen Wu, Jian-Wei Su, Chuan-Jia Jhang, Ho-Yu Chen, Zhao-En Ke, Ting-Chien Chiu, Jun-Ming Hsu, Chiao-Yen Cheng, Yu-Chen Chen, Chung-Chuan Lo, Ren-Shuo Liu, Chih-Cheng Hsieh, Kea-Tiong Tang, Meng-Fan Chang。完整正式论文/技术资料。

**用途与结构：** 16 nm 4T gain-cell 存储配 7T stationary unit 的数字 CIM，明确 storage update、stationary update、self-refresh 和计算重叠模式。

**正文定位：** pp.2–3，4T GC+STU 架构；pp.6–8，Figs.13–20。

**工艺/模式：** 其他工艺的量级交叉参考（16 nm）；16 nm 4T gain-cell 存储 + 7T stationary unit；数字 INT/FP，分模式。

**使用限制：** 计算使用 stationary 数据；更新 storage 不代表同一权重立即参加计算。INT/FP 服务不同，也不是 3T1C 电荷域方案。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2024.3470215)。

