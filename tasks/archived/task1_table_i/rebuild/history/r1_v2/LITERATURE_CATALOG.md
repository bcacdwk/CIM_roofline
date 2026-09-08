# 文献目录（R1 正文复核版）

更新：2026-09-08。A/B 主文 **55/55 到齐**；现登记 60 条来源（59 个去重资料包），其中 56 条本地主文可读。
已对 56 条本地主文完成面向估算用途的正文筛选；新 C 候选中 4 篇仍待主文。证据确认只涉及下列用途，并不代表已经完成参数换算。

[下载清单 V2（沿用 V1 文件路径）](DOWNLOAD_REQUESTS_V1.md) · [逐篇正文判断](FULLTEXT_REVIEW_R1.md) · [到件与重命名](INTAKE_AUDIT_R1.md) · [覆盖矩阵](COVERAGE.md)

优先级：P1 核心／关键缺口；P2 条件补充；P3 版本或结构对照。核心并非按性能高低选取，simulation 只在明确条件下提供方法依据。

## 00 — 28 nm CMOS 外围参考资料

共同外围分别由实测 SAR、CIM 内输入/读出路径、SRAM 局部服务与数字宏支持。通用 DAC 产品简表和 RF DAC 只作补充；CMOS-07 新增实际 28 nm SRAM 服务，但其 eFlash 工艺条件须保留。

共享：[SACIM-03](LITERATURE_CATALOG.md#SACIM-03)、[SDCIM-01](LITERATURE_CATALOG.md#SDCIM-01)、[SDCIM-03](LITERATURE_CATALOG.md#SDCIM-03)、[SACIM-05](LITERATURE_CATALOG.md#SACIM-05)。不复制主文件，也不重复计数。

<a id="CMOS-01"></a>
### CMOS-01 — IGADACT01C — 28nm HPM 1.8V/0.9V 10bit 300MHz Current Steering DAC [3ch]

- 身份：未署日期；官方 Product Brief，v002（未署发行日期）；Global Unichip Corporation (GUC)。
- 链接：[官方页面](https://www.guc-asic.com/en/solutions/IPPortfolio/MixedSignalFront-EndIP)。
- 判断：**补充 / P2**；层级：外围电路／IP 产品规格。
- 用途标签：28 nm 外围服务；输入驱动；DAC 转换服务。
- 工艺／状态：直接的 28 nm 证据（官方 IP 明确 HPM 工艺）；精度／模式按正文限定。
- 已确认／预判：官方明确 28 nm HPM、DAC 类型及输出电流／compliance 条件，适合作为输入服务的 IP 可实现性参考。
- 限制：没有指定 CIM 容性负载的建立时间；300 MHz 不能直接当作阵列输入稳定服务。文件未署出版日期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf`。
- 正文定位：pp.1–2，Features／Specifications（本地 PDF 页序）。
- 版本核验：两页原文未署发行日期；URL 的 2025-07-01 是上传路径，不能作为发表年。文件名用 undated。另有 2022Q3 产品总览索引作为版本线索，不再请求内容较粗的总览。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-02"></a>
### CMOS-02 — A 28 nm CMOS 10 bit 100 MS/s Asynchronous SAR ADC with Low-Power Switching Procedure and Timing-Protection Scheme

- 身份：2021；Electronics；Fang Tang、Qiyun Ma、Zhou Shu 等。
- 链接：[DOI](https://doi.org/10.3390/electronics10222856) · [官方页面](https://doi.org/10.3390/electronics10222856)。
- 判断：**核心 / P1**；层级：外围电路（实测 ADC）。
- 用途标签：28 nm 外围服务；ADC 转换；输入建立。
- 工艺／状态：直接的 28 nm 证据；精度／模式按正文限定。
- 已确认／预判：28 nm 实测差分 SAR；正文区分采样、逐次比较、CDAC 建立和时序保护。测试含输入 buffer 与参考电路，实测频谱随输入频率变化。
- 限制：PVT 表是后仿真；有效精度低于名义 10 bit。正文与 Fig.10 的 SNDR 数字不一致，后续不可混抄；CIM 共模与负载适配仍须建模。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf`。
- 正文定位：pp.2–6，Figs.1–7；pp.7–8，Figs.8–12（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-03"></a>
### CMOS-03 — SRAM Assist Techniques for Operation in a Wide Voltage Range in 28-nm CMOS

- 身份：2012；IEEE Transactions on Circuits and Systems II: Express Briefs；Brian Zimmer、Seng Oon Toh、Huy Vo 等。
- 链接：[DOI](https://doi.org/10.1109/tcsii.2012.2231015) · [官方页面](https://doi.org/10.1109/tcsii.2012.2231015)。
- 判断：**核心 / P1**；层级：器件／SRAM 局部电路（建模与仿真）。
- 用途标签：28 nm 外围服务；读写时序；负载与驱动条件。
- 工艺／状态：直接的 28 nm 证据（模型条件）；精度／模式按正文限定。
- 已确认／预判：给出读写成功终点、back-to-back 服务、WL 脉宽与 BL 电容的显式参考条件；适合通用 SRAM 写入换算方法。
- 限制：28 nm、50 FO4 时钟及 128-cell 负载属于作者模型假设，不能写成量产 compiler 或流片保证。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf`。
- 正文定位：pp.1–3，动态读写定义、IV-A／IV-C；pp.4–5，assist 比较（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-04"></a>
### CMOS-04 — A 28 nm Dual-Port SRAM Macro With Screening Circuitry Against Write-Read Disturb Failure Issues

- 身份：2011；IEEE Journal of Solid-State Circuits；Yuichiro Ishii、Hidehiro Fujiwara、Shinji Tanaka 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2011.2164021) · [官方页面](https://doi.org/10.1109/jssc.2011.2164021)。
- 判断：**补充 / P2**；层级：阵列／局部 macro。
- 用途标签：28 nm 外围服务；局部读写；操作粒度与冲突。
- 工艺／状态：直接的 28 nm 证据；精度／模式按正文限定。
- 已确认／预判：实测 28 nm 双端口 SRAM；局部 32 kb macro、64-bit word、双端口同址冲突与筛选方法清楚。
- 限制：shmoo 横轴是两端口 clock skew，不是读／写周期；Table I 没有独立的普通写入服务时间。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf`。
- 正文定位：pp.2–6，Figs.6–14；pp.7–9，Table I、Figs.15–20（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-05"></a>
### CMOS-05 — A 28-nm 8-Bit 16-GS/ DAC With >60 dBc/>40 dBc SFDR Up To 2.3 GHz/5.4 GHz Using 4-Channel NRZ-Output-Overlapped Time-Interleaving

- 身份：2025；IEEE Transactions on Circuits and Systems II: Express Briefs；Sihao Chen、Chengyu Huang、Limeng Sun 等。
- 链接：[DOI](https://doi.org/10.1109/tcsii.2024.3518084) · [官方页面](https://doi.org/10.1109/tcsii.2024.3518084)。
- 判断：**补充 / P2**；层级：外围电路（实测 DAC，非 CIM 负载）。
- 用途标签：28 nm 外围服务；DAC／驱动；采样与建立的区别。
- 工艺／状态：直接的 28 nm 证据（CIM 负载适配未确认）；精度／模式按正文限定。
- 已确认／预判：28 nm 实测 8-bit 四通道交织电流舵 DAC，交织、相位校正和输出负载条件明确。
- 限制：16 GS/s 是四路交织输出；单 sub-DAC、100 Ω 差分负载、片外编码条件与 CIM 字线负载不同。未报告 CIM 输入建立保证。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf`。
- 正文定位：pp.3–4，III-A／III-B；pp.4–5，测量（本地 PDF 页序）。
- 年份/日期：期刊卷期为 2025-02；DOI 字符串含 2024，不将其当作最终卷期年份。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-06"></a>
### CMOS-06 — A high-speed single channel reconfigurable 1-GS/s to 1.5-GS/s, 8-bit to 6-bit SAR ADC in 28 nm CMOS

- 身份：2025；IEICE Electronics Express；Qing Su、Xuan Guo、Hanbo Jia 等。
- 链接：[DOI](https://doi.org/10.1587/elex.22.20250220) · [官方页面](https://doi.org/10.1587/elex.22.20250220)。
- 判断：**条件保留 / P2**；层级：外围电路（28 nm 后仿真，非实测）。
- 用途标签：28 nm 外围服务；ADC 精度与节拍；独立模型交叉核查。
- 工艺／状态：直接的 28 nm 模型／后仿真条件，不是实测芯片；精度／模式按正文限定。
- 已确认／预判：28 nm SAR 的完整转换序列、两种精度模式、参考 buffer 开销及输入范围有明确设计依据。
- 限制：性能为仿真，且本地为 advance/accepted PDF；不提供独立流片验证。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-06_2025_ReconfigurableSAR.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-06_2025_ReconfigurableSAR.pdf`。
- 正文定位：pp.3–6，Fig.1、冗余转换、性能小节（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="CMOS-07"></a>
### CMOS-07 — Disturbance Aware Dynamic Power Reduction in Synchronous 2RW Dual-Port 8T SRAM by Self-Adjusting Wordline Pulse Timing

- 身份：2023；IEEE Journal of Solid-State Circuits；Yoshisato Yokoyama、Koji Nii、Yuichiro Ishii 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2022.3229828) · [官方页面](https://doi.org/10.1109/jssc.2022.3229828)。
- 判断：**核心 / P1**；层级：局部 SRAM macro／外围实测。
- 用途标签：28 nm 外围服务；读写周期与端口条件。
- 工艺／状态：直接 28 nm eFlash CMOS 平台证据；特殊高阈值条件保留；精度／模式按正文限定。
- 已确认／预判：C 轮找到的公开作者稿：实际 28 nm eFlash CMOS 平台上的同步 2RW 8T SRAM，区分 clock、WL 脉冲、read access 与端口操作；Table II 有 macro 配置和频率。
- 限制：28 nm 为 eFlash 优化的高阈值工艺；不能等同一般 logic SRAM compiler。本文与 CMOS-04 有作者重叠。公开 R2 稿含排版占位，不宣称正式版；当前内容足够用途判断，无需重复请求。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf`。
- 正文定位：作者修订稿 pp.1–2，Figs.1–2；pp.4–6，WL tracking；pp.8–9，Table II（本地 PDF 页序）。
- 版本核验：实际作者稿题名为 Dualport，正式登记 Dual-Port；作者五人一致。年份采用 JSSC 58(7), 2098–2108 (2023)，不采用稿内占位日期。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：与 CMOS-04 部分作者重叠；新的工艺/宏验证，非完全独立团队。

## 01 — SRAM ACIM

用不同团队的电荷域／电容阵列 macro 核查完整多位求值、ADC 使用方式和局部边界。共享 CMOS-03／04 补普通 SRAM 读写基础；不同工艺的 macro 只作结构与量级交叉参考，不能直接冠以统一 28 nm 的性能。

共享：[CMOS-03](LITERATURE_CATALOG.md#CMOS-03)、[CMOS-04](LITERATURE_CATALOG.md#CMOS-04)、[CMOS-07](LITERATURE_CATALOG.md#CMOS-07)。不复制主文件，也不重复计数。

<a id="SACIM-01"></a>
### SACIM-01 — Scalable and Programmable Neural Network Inference Accelerator Based on In-Memory Computing

- 身份：2022；IEEE JSSC 57(1), 198–211；Hongyang Jia、Murat Ozatay、Yinqi Tang 等。
- 链接：[DOI](https://doi.org/10.1109/JSSC.2021.3119018) · [官方页面](https://doi.org/10.1109/JSSC.2021.3119018)。
- 判断：**核心 / P1**；层级：阵列／局部 macro 及整芯片。
- 用途标签：完整多位求值；操作粒度与局部并行度；CIM 求值桥接。
- 工艺／状态：其他工艺的量级交叉参考（65 nm）；精度／模式按正文限定。
- 已确认／预判：可区分本地 CIMA、SIMD、片上网络及权重装载网络；完整精度需位平面与数字累加配合。实测数字时钟与 ADC 输出服务率分列。
- 限制：目标 500 MHz 与受封装供电限制的实测频率不同；28 MB 权重 buffer 未集成在原型中；整芯片吞吐不能直接作为 local macro 服务。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf`。
- 正文定位：pp.4–7，CIMU／CIMA 与 BPBS；p.9，V-A／Table III（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/jia2022.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/jia2022.pdf', 'previous_source_id': 't1_jia2022', 'sha256': '26bd395f41879bec0d555e2db0f05d98f266fe6e6d3c76a0e95d358fe46a0128', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SACIM-02"></a>
### SACIM-02 — PICO-RAM: A PVT-Insensitive Analog Compute-In-Memory SRAM Macro With In Situ Multi-Bit Charge Computing and 6T Thin-Cell-Compatible Layout

- 身份：2025；IEEE Journal of Solid-State Circuits；Zhiyu Chen、Ziyuan Wen、Weier Wan 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2024.3422826) · [官方页面](https://doi.org/10.1109/jssc.2024.3422826)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：CIM 求值桥接；输入 DAC／ADC 共享；完整多位求值。
- 工艺／状态：其他工艺的量级交叉参考（65 nm）；精度／模式按正文限定。
- 已确认／预判：实测 65 nm 电荷域 macro；同一组电容依次用于两阶段 DAC、MAC、移位累加与 ADC，说明外围开销可重用，不能简单串加独立转换器延时。
- 限制：本地为作者稿，2024 预印本与 2025 期刊记录关联；65 nm 不是共同 28 nm 的直接速度证据。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf`。
- 正文定位：pp.4–7，Figs.4–14；pp.8–10，测量与 PVT（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SACIM-03"></a>
### SACIM-03 — A 28nm 32Kb SRAM Computing-in-Memory Macro With Hierarchical Capacity Attenuator and Input Sparsity-Optimized ADC for 4b Mac Operation

- 身份：2023；IEEE Transactions on Circuits and Systems II: Express Briefs；Kanglin Xiao、Xiaoxin Cui、Xin Qiao 等。
- 链接：[DOI](https://doi.org/10.1109/tcsii.2023.3234620) · [官方页面](https://doi.org/10.1109/tcsii.2023.3234620)。
- 判断：**核心 / P1**；层级：28 nm 实测局部 macro；2022 会议前作仿真。
- 用途标签：28 nm 外围服务；CIM 求值桥接；ADC 与局部读出。
- 工艺／状态：直接的 28 nm 实测证据（期刊扩展版）；精度／模式按正文限定。
- 已确认／预判：2023 期刊明确新增流片测量；28 nm 128×256 9T1C 阵列、128 路 4-bit 输入 DAC、64 路 4-bit ADC，给出 reset/evaluation/readout 关系与 die photo。
- 限制：2022 会议稿为相同工作前作，不能另算独立实测证据；4-bit ADC 输出不等于完整无损 MAC 精度；普通权重写入周期仍未闭合。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf`。
- 正文定位：p.2，扩展版说明、Figs.1–3；p.3，Fig.5／III；p.4，Figs.6–8（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 相关版本：[A Computing-in-Memory SRAM Macro Based on Fully-Capacitive-Coupling With Hierarchical Capacity Attenuator for 4-b MAC Operation](literature/01_sram_acim/versions/SACIM-03_2022_Hierarchical_Attenuator_ISCAS.pdf)；2023 期刊 p.2 明确扩展本会议稿并新增流片测量；会议仿真与期刊测量不是两个独立芯片。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SACIM-04"></a>
### SACIM-04 — A Charge Domain SRAM Compute-in-Memory Macro With C-2C Ladder-Based 8-Bit MAC Unit in 22-nm FinFET Process for Edge Inference

- 身份：2023；IEEE Journal of Solid-State Circuits；Hechen Wang、Renzhi Liu、Richard Dorrance 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2022.3232601) · [官方页面](https://doi.org/10.1109/jssc.2022.3232601)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：CIM 求值桥接；完整多位求值；独立结构交叉核查。
- 工艺／状态：其他工艺的量级交叉参考（22 nm FinFET）；精度／模式按正文限定。
- 已确认／预判：实际 22 nm 电荷域 macro；DAC/MAC 建立可重叠，SAR 内部八步放在另一半周期；R2R 驱动选型明确考虑 C2C 无法驱动的扇出负载。
- 限制：完整周期与内部 SAR 步骤不能混用；工艺不是 28 nm。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf`。
- 正文定位：p.5，Fig.10；pp.7–9，Figs.16–20；pp.10–11，测量（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SACIM-05"></a>
### SACIM-05 — 8-Bit Precision 6T SRAM Compute-in-Memory Macro Using Global Bitline-Combining Scheme for Edge AI Chips

- 身份：2024；IEEE Transactions on Circuits and Systems II: Express Briefs；Jian-Wei Su、Pei-Jung Lu、Ping-Chun Wu 等。
- 链接：[DOI](https://doi.org/10.1109/tcsii.2023.3331375) · [官方页面](https://doi.org/10.1109/tcsii.2023.3331375)。
- 判断：**C 候选，主文待审 / P1**；层级：局部 macro（流片属性由官方摘要确认）。
- 用途标签：28 nm 外围服务；完整精度求值；ADC 共享。
- 工艺／状态：直接 28 nm 候选，具体服务待正文；精度／模式按正文限定。
- 已确认／预判：身份与摘要已核验；预期用途尚未由主文确认。
- 限制：主文尚未到件；摘要和 SI 不替代完整时序、负载与操作条件审阅。
- 状态：身份已核验；主文未到，尚不能确认完整时序；拟下载主文。
- 保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf`。
- 年份/日期：IEEE 页面首次发表 2023-11-09；期刊卷期为 2024-04，文件名使用卷期年。
- 附件情况：请主文与出版社列出的技术 SI 一并获取；已归档的 SI 无需重复。
- 独立性：NTHU/ITRI 系列，与 SRAM-DCIM、PCM 部分候选团队有关；收到全文后核对其与已有 384-kb 前作的版本关系，不重复请求前作。

## 02 — SRAM DCIM

数字求值需区分单个时钟、位串行步骤和完整精度输出。D6CIM、动态逻辑 macro 与可重构数字 macro 提供互补实现，共享 CMOS-03／04 解释普通写入与读写冲突；未要求单篇同时闭合两路吞吐。

共享：[CMOS-03](LITERATURE_CATALOG.md#CMOS-03)、[CMOS-04](LITERATURE_CATALOG.md#CMOS-04)、[CMOS-07](LITERATURE_CATALOG.md#CMOS-07)。不复制主文件，也不重复计数。

<a id="SDCIM-01"></a>
### SDCIM-01 — D6CIM: 60.4-TOPS/W, 1.46-TOPS/mm2, 1005-Kb/mm2 Digital 6T-SRAM-Based Compute-in-Memory Macro Supporting 1-to-8b Fixed-Point Arithmetic in 28-nm CMOS

- 身份：2023；ESSCIRC, 413–416；Jonghyun Oh、Chuan-Tung Lin、Mingoo Seok。
- 链接：[DOI](https://doi.org/10.1109/ESSCIRC59616.2023.10268725) · [官方页面](https://doi.org/10.1109/ESSCIRC59616.2023.10268725)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：28 nm 外围服务；数字累加／位串行；普通写入粒度。
- 工艺／状态：直接的 28 nm 证据；精度／模式按正文限定。
- 已确认／预判：28 nm 数字 6T macro；128-bit 普通写入端口与 CIM 控制分开；8-bit 128×16 VMM 需要 64 个时钟，提供完整精度服务粒度。
- 限制：一个 clock 不是一次完整 8-bit VMM；写端口宽度不等于已量测独立写入周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf`。
- 正文定位：p.1，Fig.1、完整 VMM 步骤；pp.2–4，架构／测量（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/d6cim2023.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/d6cim2023.pdf', 'previous_source_id': 't1_d6cim2023', 'sha256': 'bbb72fb65095bfeee511c7ef5ca4f12c8a427a6718347695c0a462f1f4358e9e', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SDCIM-02"></a>
### SDCIM-02 — A Digital Bit-Reconfigurable Versatile Compute-In-Memory Macro for Machine Learning Acceleration

- 身份：2023；IEEE Transactions on Circuits and Systems II: Express Briefs；Xin Zhang、Yuncheng Lu、Bo Wang 等。
- 链接：[DOI](https://doi.org/10.1109/tcsii.2023.3257058) · [官方页面](https://doi.org/10.1109/tcsii.2023.3257058)。
- 判断：**补充 / P2**；层级：阵列／局部 macro。
- 用途标签：数字求值与控制；操作粒度；独立量级交叉核查。
- 工艺／状态：其他工艺的量级交叉参考（65 nm）；精度／模式按正文限定。
- 已确认／预判：65 nm 数字 macro 给出重构运算、n-bit 加法、位串行乘法和 carry 写回的逐周期关系。
- 限制：精度与运算类型改变所需周期；不能把 65 nm headline TOPS/W 直接映射为共同 28 nm 服务。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf`。
- 正文定位：pp.2–4，Figs.3–8；p.5，测量比较（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="SDCIM-03"></a>
### SDCIM-03 — A 1.041-Mb/mm^2 27.38-TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-less SRAM Compute-in-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications

- 身份：2022；2022 IEEE International Solid- State Circuits Conference (ISSCC)；Bonan Yan、Jeng-Long Hsu、Pang-Cheng Yu 等。
- 链接：[DOI](https://doi.org/10.1109/isscc42614.2022.9731545) · [官方页面](https://doi.org/10.1109/isscc42614.2022.9731545)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：28 nm 外围服务；数字求值与控制；完整精度输出。
- 工艺／状态：直接的 28 nm 证据；精度／模式按正文限定。
- 已确认／预判：28 nm 动态逻辑数字 macro；先存权重再计算，8-bit 输入按八拍展开，并有可选 post-sum 维度。
- 限制：文中引言的普通 SRAM 小于 1 ns 属背景陈述；测得 clock 与完整精度输出须区分。35 页作者 slides 是同源解释资料。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf`。
- 正文定位：p.1，memory/CIM 模式、8-clock 展开；p.2，Figs.11.7.2–6（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 相关版本：[A 1.041Mb/mm2 27.38TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-Less SRAM Compute-In-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications](literature/02_sram_dcim/versions/SDCIM-03_2022_DynamicLogic_INT8_AuthorSlides.pdf)；正式主文已经到件；35 页作者报告保留用于读图和解释，属于同一来源。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

## 03 — 2D NOR Flash

三家厂商的存储资料提供编程、擦除、busy 和操作粒度定义，两篇早期原始 NOR 模拟计算论文连接普通存储与精细电导调谐。普通存储时序可以支撑更新依据，但 SPI／并行封装输出速度和模拟 CIM 求值不是同一边界。

<a id="NOR-01"></a>
### NOR-01 — S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military

- 身份：2024；厂商 datasheet，002-18741 Rev. *E；Infineon Technologies。
- 链接：[官方页面](https://www.infineon.com/dgdl/Infineon-S29GL01GS_S29GL512S_S29GL256S_S29GL128S_128_Mb_256_Mb_512_Mb_1_Gb_GL-S_MIRRORBIT_Flash_Parallel_3-DataSheet-v06_00-EN.pdf?fileId=8ac78c8c7d0d8da4017d0ee99af9726b)。
- 判断：**核心 / P1**；层级：整芯片存储规格，含局部操作定义。
- 用途标签：读侧时间尺度；编程／擦除周期；字／buffer／sector 粒度。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；数字 NOR／MirrorBit，军规产品条件；非模拟精度声明。
- 已确认／预判：完整厂商 datasheet 明确 512-byte 写 buffer、32-byte ECC page、128 KB erase sector；内置擦除含 pre-program，typ/max 和负载／温度脚注可追溯。
- 限制：这是 65 nm GL-S 军规器件；effective per-word 数字是整 buffer 摊销值；读接口时序不是 CIM 模拟求值时间。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf`。
- 正文定位：pp.7、22–32；p.45，Table 16；AC timing 小节（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NOR-02"></a>
### NOR-02 — W25Q128JV — 3V 128M-BIT Serial Flash Memory with Dual/Quad SPI

- 身份：2019；厂商 datasheet，Revision G；Winbond Electronics。
- 链接：[官方页面](https://www.winbond.com/hq/support/documentation/?__locale=en&pno=W25Q128JV)。
- 判断：**核心 / P1**；层级：整芯片存储规格。
- 用途标签：编程／擦除周期；操作粒度；接口与内部 busy 区分。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；普通数字 NOR（未作多级模拟精度假设）。
- 已确认／预判：Winbond Rev.G 给出 1–256-byte page program、4/32/64 KB 擦除、BUSY 完成定义及 typ/max；正文指出 Quad 输入加速可能被内部编程时间淹没。
- 限制：SPI 传输率不能替代编程完成或 cell 读出；只支持普通 binary 存储模式的更新时间尺度。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf`。
- 正文定位：p.14，BUSY；pp.37–43，program／erase；pp.65–66，AC 表（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NOR-03"></a>
### NOR-03 — SST26VF064B/SST26VF064BA — 2.5V/3.0V 64-Mbit Serial Quad I/O (SQI) Flash Memory

- 身份：2022；厂商 datasheet，DS20005119K；Microchip Technology。
- 链接：[官方页面](https://www.microchip.com/en-us/product/SST26VF064B)。
- 判断：**补充 / P2**；层级：整芯片存储规格。
- 用途标签：编程／擦除周期；操作粒度；独立量级交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；普通数字 SuperFlash NOR。
- 已确认／预判：Microchip 独立产品系列补 page、erase、suspend/resume 与 self-timed BUSY；正式时序表和 SFDP 超时定义可交叉核查。
- 限制：SFDP 最大 timeout 不应冒充 typ；与 NOR-04/05 同为 SST 相关生态，不将其全部视为独立器件团队。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf`。
- 正文定位：pp.10–14，状态／命令；pp.25–31，编程／挂起；pp.45–49，AC；p.82，SFDP（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NOR-04"></a>
### NOR-04 — Fast, Energy-Efficient, Robust, and Reproducible Mixed-Signal Neuromorphic Classifier Based on Embedded NOR Flash Memory Technology

- 身份：2017；IEDM, 6.5.1–6.5.4；Xinjie Guo、Farnood Merrikh Bayat、Mohammad Bavandpour 等。
- 链接：[DOI](https://doi.org/10.1109/IEDM.2017.8268341) · [官方页面](https://doi.org/10.1109/IEDM.2017.8268341)。
- 判断：**核心 / P1**；层级：阵列与两层网络实验。
- 用途标签：CIM 求值桥接；输入驱动与输出边界；阵列结构。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；模拟调谐浮栅权重。
- 已确认／预判：实际嵌入式 NOR 模拟分类器，区分输入串行装载与网络内部传播；权重细调、half-select disturb 和神经元外围均影响整体服务。
- 限制：实测原型与更先进 ESF3 工艺预测分开；细调设定精度并非最精确单 cell 示范值；同 NOR-05 的研究关系不独立。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf`。
- 正文定位：pp.1–2，II–IV；pp.3–4，Figs.4–16（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/nor2017.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/nor2017.pdf', 'previous_source_id': 't1_nor2017', 'sha256': '987806007d2283dc8b8acc8282a15ccbdd1e7e48a73d0729dcfa3cd17fec03b6', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：ucsb_esf1；同族条目不自动视作独立交叉验证。

<a id="NOR-05"></a>
### NOR-05 — Model-Based High-Precision Tuning of NOR Flash Memory Cells for Analog Computing Applications

- 身份：2016；Device Research Conference；Farnood Merrikh Bayat、Xinjie Guo、Michael Klachko 等。
- 链接：[官方页面](https://web.ece.ucsb.edu/~strukov/papers/2016/DRCflash2016.pdf)。
- 判断：**核心 / P1**；层级：器件／小阵列。
- 用途标签：写入／编程周期；擦除与更新方式；精度与 verify。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；模拟多级调谐。
- 已确认／预判：100-cell 实验提供 write-verify 算法、脉冲数与目标调谐精度的关系，是普通 Flash 到模拟权重更新的重要桥接。
- 限制：固定脉冲数不是完整更新时间；不是大规模并行 array 写入保证；与 NOR-04 同团队。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf`。
- 正文定位：pp.1–2，模型与 Fig.1 调谐流程（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/nor_tuning2016.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/nor_tuning2016.pdf', 'previous_source_id': 't1_nor_tuning2016', 'sha256': '87ea1a0bcb77e62d01e4b357384dc5972af4c3c2cef86d529512d987db9bab5f', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：ucsb_esf1；同族条目不自动视作独立交叉验证。

## 04 — 3D NAND Flash

现有正文已覆盖 Micron MLC/TLC、两家新 QLC 芯片以及实际 SLC SGVC 器件。SLC 专用完整 program/erase 服务和 plane 命令约束仍有缺口；不是完全没有 SLC 证据。模型/RC 结果与制造商实测明确分开。

<a id="NAND-01"></a>
### NAND-01 — Micron 3D NAND Flash Memory Technology

- 身份：2016；厂商技术产品简表，02/16；Micron Technology。
- 链接：[官方页面](https://www.micron.com/products/storage/nand-flash/3d-nand/part-catalog)。
- 判断：**核心 / P1**；层级：厂商器件／die 规格简表。
- 用途标签：读侧时间尺度；编程／擦除周期；页／块／plane 粒度。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；MLC 2b/c；TLC 3b/c（分列）。
- 已确认／预判：Micron 官方资料虽为两页 flyer，正文实际有 MLC/TLC 分列的 read/program/erase typ/max、页／块尺寸和具体料号，值得保留。
- 限制：不是完整部件 datasheet，部分并行命令／busy 约束仍缺；2016 年而非近期下载年。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf`。
- 正文定位：p.2，产品／时序表（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NAND-02"></a>
### NAND-02 — A 2Tb 4b/Cell 6-Plane 3D-Flash Memory with 37.6Gb/mm^2 Bit Density and >85MB/s Write Throughput

- 身份：2026；2026 IEEE International Solid-State Circuits Conference (ISSCC)；Jayanth M. Thimmaiah、Ryuji Yamashita、In-Soo Yoon 等。
- 链接：[DOI](https://doi.org/10.1109/isscc49663.2026.11409136) · [官方页面](https://doi.org/10.1109/isscc49663.2026.11409136)。
- 判断：**核心 / P1**；层级：阵列／die 与整芯片。
- 用途标签：编程周期；plane 并行条件；独立产品交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；QLC 4b/c，6-plane；另含 SLC burst 操作模式，分别使用。
- 已确认／预判：Sandisk/KIOXIA 2026 原始 QLC 芯片；六 plane、物理/逻辑 page 区别、verify 与读搜索明确，还含 QLC 芯片的 SLC burst 模式。
- 限制：die program throughput 包含内部并行；SLC burst 不是独立 SLC 产品；完整 erase 条件仍不足。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf`。
- 正文定位：p.1，架构与模式；pp.2–3，Figs.15.1.1–7（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NAND-03"></a>
### NAND-03 — A 321-Layer 2Tb 4b/cell 3D-NAND-Flash Memory with a 75MB/s Program Throughput

- 身份：2025；2025 IEEE International Solid-State Circuits Conference (ISSCC)；Wanik Cho、Chanhui Jeong、Jongwoo Kim 等。
- 链接：[DOI](https://doi.org/10.1109/isscc49661.2025.10904748) · [官方页面](https://doi.org/10.1109/isscc49661.2025.10904748)。
- 判断：**核心 / P1**；层级：阵列／die 与整芯片。
- 用途标签：编程周期；操作粒度与局部并行度；独立量级交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；QLC 4b/c（不是 TLC）。
- 已确认／预判：SK hynix 321-layer QLC 实际芯片，给出 page-program 时间、六 plane 与 page 大小；HV 供电、WL 电阻与干扰条件可支持特殊驱动分析。
- 限制：75 MB/s 是 die 并行 program 结果；不能当作单 page latency 或外部 I/O 速度。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf`。
- 正文定位：p.1，programming／HV 配置；p.2，Fig.30.5.6（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NAND-04"></a>
### NAND-04 — System-Technology Codesign of 3-D NAND Flash-Based Compute-in-Memory Inference Engine

- 身份：2021；IEEE JXCDC 7(1), 61–69；Wonbo Shim、Shimeng Yu。
- 链接：[DOI](https://doi.org/10.1109/jxcdc.2021.3093772) · [官方页面](https://doi.org/10.1109/JXCDC.2021.3093772)。
- 判断：**核心 / P1**；层级：阵列／外围与系统仿真。
- 用途标签：CIM 求值桥接；字线／位线与重构；局部阵列边界。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；CIM 选定阈值态／权重编码，不能自动等同商品 TLC 页模式。
- 已确认／预判：给出 NAND 串读、映射、64-block subarray 边界和 RC／HSPICE 求值方法，可复用估算思路。
- 限制：Table 1 是作者估计；外围为 32 nm 并另用高压器件，不能称统一 28 nm 实测。器件数据与 NAND-05 有来源关联。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf`。
- 正文定位：pp.2–4，II、Table 1、Fig.3；后续建模小节（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="NAND-05"></a>
### NAND-05 — Optimal Design Methods to Transform 3D NAND Flash into a High-Density, High-Bandwidth and Low-Power Nonvolatile Computing in Memory (nvCIM) Accelerator for Deep-Learning Neural Networks (DNN)

- 身份：2019；IEDM, 38.1.1–38.1.4；Hang-Ting Lue、Po-Kai Hsu、Ming-Liang Wei 等。
- 链接：[DOI](https://doi.org/10.1109/iedm19573.2019.8993652) · [官方页面](https://doi.org/10.1109/IEDM19573.2019.8993652)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：CIM 求值桥接；局部并行组织；NAND 结构依据。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；实际 16-layer 64 Gb SLC SGVC 器件，multi-bit 用 SLC 复制/选择编码。
- 已确认／预判：实际 16-layer 64 Gb SLC SGVC 器件与电流分布，用 SSL／BL／SL 解释多位输入及 SLC 复制编码；补直接 SLC 结构证据。
- 限制：多位感测及 accelerator 指标含设计预估，不是完整已流片 CIM 性能；缺完整 SLC program/erase 服务。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf`。
- 正文定位：pp.1–2，器件与映射；pp.3–4，Figs.1–16（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

## 05 — RRAM

厂商 ReRAM datasheet 和 Weebit／CEA-Leti 原始测量补普通写入与器件条件；三种 CIM 实现补差分编码、读出和编程策略。比较时必须保留 binary／multi-level、单脉冲／闭环完成的区别，不能把厂家 SPI 时钟当作 cell 切换时间。

<a id="RRAM-01"></a>
### RRAM-01 — A compute-in-memory chip based on resistive random-access memory

- 身份：2022；Nature 608, 504–512；Weier Wan、Rajkumar Kubendran、Clemens Schaefer 等。
- 链接：[DOI](https://doi.org/10.1038/s41586-022-04992-8) · [官方页面](https://doi.org/10.1038/s41586-022-04992-8)。
- 判断：**核心 / P1**；层级：阵列／局部 macro 及整芯片。
- 用途标签：CIM 求值桥接；闭环编程；状态精度与验证。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；模拟多级、差分权重。
- 已确认／预判：NeuRRAM 正文含完整 set-read/reset-read 闭环、导电目标容差、超时条件与 MVM 实测；读／写测试条件可以分开记录。
- 限制：1–10 ns 控制脉冲能力不能替代实际微秒级 program/verify 配置；全网效果与 local MVM 分开。出版页未列独立技术 SI PDF，不再笼统请求附件。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/05_rram/RRAM-01_2022_NeuRRAM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-01_2022_NeuRRAM.pdf`。
- 正文定位：p.10，Methods：编程／控制；p.27，Extended Data Fig.12（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/neurram2022.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/neurram2022.pdf', 'previous_source_id': 't1_neurram2022', 'sha256': '4e75d89025e0e3bc7c04bf00f50bf0f618935c3e405612fd23c95856bf209a5b', 'byte_identical': True}`。
- 附件情况：2026-09-08 官方出版页未列独立技术 SI PDF；本地包含 Methods/Extended Data，V2 不请求不存在于页面的通用附件。

<a id="RRAM-02"></a>
### RRAM-02 — A 28 nm 576K RRAM-based computing-in-memory macro featuring hybrid programming with area efficiency of 2.82 TOPS/mm2

- 身份：2025；Journal of Semiconductors 46(6), 062304；Siqi Liu、Songtao Wei、Peng Yao 等。
- 链接：[DOI](https://doi.org/10.1088/1674-4926/24100017) · [官方页面](https://doi.org/10.1088/1674-4926/24100017)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：28 nm 读出；写入／编程方式；操作粒度。
- 工艺／状态：直接的 28 nm 证据（专用 RRAM 外围）；多级／2T2R 差分。
- 已确认／预判：28 nm 实测 macro，分段 WL、单 cell verify、八步 ADC 与 1T1R/2T2R 混合闭环相互对应；提供程序步骤与容差。
- 限制：速度改善主要按平均脉冲数比较，不能从倍数独立得到绝对完整写周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/05_rram/RRAM-02_2025_HybridProgramming.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-02_2025_HybridProgramming.pdf`。
- 正文定位：pp.3–6，Figs.2–8；后续芯片测试（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/liu2025.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/liu2025.pdf', 'previous_source_id': 't1_liu2025', 'sha256': 'd55cb5abda2d3374d86ea094c82396c86d5c408489816a0fb1d4abd8e4f55752', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="RRAM-03"></a>
### RRAM-03 — High temperature stability embedded ReRAM for 2x nm node and beyond

- 身份：2022；2022 IEEE International Memory Workshop (IMW)；G. Molas、G. Piccolboni、A. Bricalli 等。
- 链接：[DOI](https://doi.org/10.1109/imw52921.2022.9779293) · [官方页面](https://doi.org/10.1109/imw52921.2022.9779293)。
- 判断：**补充 / P2**；层级：器件／测试阵列。
- 用途标签：器件编程条件；binary 存储；独立产业交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；数字存储；多级适用性未主张。
- 已确认／预判：Weebit/CEA-Leti 实际阵列对照 raw 与 P&V 的分布，说明固定脉冲、温度、可靠性终点改变可用写策略。
- 限制：重点是可靠性；读扰应力脉冲不是完整 array access。不能提供独立的完整 CIM 求值周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf`。
- 正文定位：pp.2–5，raw reliability、读扰与 Program and verify（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="RRAM-04"></a>
### RRAM-04 — MB85AS4MT — Memory ReRAM 4M (512 K × 8) Bit SPI

- 身份：2016；厂商 datasheet，DS501-00045-1v0-E；Fujitsu Semiconductor。
- 链接：[官方页面](https://www.fujitsu.com/global/documents/products/devices/semiconductor/memory/reram/MB85AS4MT-DS501-00045-1v0-E.pdf)。
- 判断：**补充 / P2**；层级：整芯片存储规格。
- 用途标签：普通写入完成；操作粒度；存储时序定义。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；普通数字存储。
- 已确认／预判：正式 ReRAM 产品资料区分写 buffer、串行数据接收与非易失提交；tWC 表按数据翻转比例给出内部完整写周期。
- 限制：内部 tWC 为毫秒量级，不能用 5 MHz SPI 或单 cell ns 切换替换，也不能强行推广到其他 RRAM。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf`。
- 正文定位：pp.7–13，WRITE/WIP；p.17，AC：tWC；pp.19–21，接口图（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="RRAM-05"></a>
### RRAM-05 — A 28-nm RRAM Computing-in-Memory Macro Using Weighted Hybrid 2T1R Cell Array and Reference Subtracting Sense Amplifier for AI Edge Inference

- 身份：2023；IEEE Journal of Solid-State Circuits；Wang Ye、Linfang Wang、Zhidao Zhou 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2023.3280357) · [官方页面](https://doi.org/10.1109/jssc.2023.3280357)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：28 nm 专用感测；CIM 求值桥接；局部并行组织。
- 工艺／状态：直接的 28 nm 证据（专用 RRAM 外围）；binary HRS/LRS；2T1R 晶体管尺寸与多 subarray 的空间权重映射。
- 已确认／预判：28 nm 2T1R 混合阵列，binary HRS/LRS 与不同晶体管尺寸构造空间权重；完整读流程含 PH0 稳定和 PH1–4 参考扣除。
- 限制：Fig.18 实测 66 ns 与估计优化 13 ns 必须分列；测试板外部 DAC 供偏置；缺完整写入/verify 周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf`。
- 正文定位：p.3，Fig.4；pp.5–7，Figs.10、18；测量环境（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="RRAM-06"></a>
### RRAM-06 — A 40nm 2Mb ReRAM Macro with 85% Reduction in FORMING Time and 99% Reduction in Page-Write Time Using Auto-FORMING and Auto-Write Schemes

- 身份：2019；2019 Symposium on VLSI Technology；Yen-Cheng Chiu、Han-Wen Hu、Li-Ya Lai 等。
- 链接：[DOI](https://doi.org/10.23919/vlsit.2019.8776540) · [官方页面](https://doi.org/10.23919/vlsit.2019.8776540)。
- 判断：**C 候选，主文待审 / P1**；层级：实际存储 macro（官方摘要确认）。
- 用途标签：完整写入周期；局部并行；RESET/SET 控制。
- 工艺／状态：40 nm 专用外围；其他工艺交叉参考；精度／模式按正文限定。
- 已确认／预判：身份与摘要已核验；预期用途尚未由主文确认。
- 限制：主文尚未到件；摘要和 SI 不替代完整时序、负载与操作条件审阅。
- 状态：身份已核验；主文未到，尚不能确认完整时序；拟下载主文。
- 保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-06_2019_AutoForming_AutoWrite.pdf`。
- 附件情况：请主文与出版社列出的技术 SI 一并获取；已归档的 SI 无需重复。
- 独立性：产业/NTHU 同技术生态，作步骤补充；99% 改善不能先写成绝对周期，也不能遗漏被移入 standby 的 RESET。

## 06 — MRAM

Jung 的电阻求和与 Chiu 的 near-memory 数字引擎是不同机制，不能拼为一个实现。存储 macro 补读写步骤，新增 MRAM-06 用于核查 bitcell 内数字计算；互补 MTJ、PUF 与普通数据路径分别记录。

<a id="MRAM-01"></a>
### MRAM-01 — A crossbar array of magnetoresistive memory devices for in-memory computing

- 身份：2022；Nature 601, 211–216；Seungchul Jung、Hyungwoo Lee、Sungmeen Myung 等。
- 链接：[DOI](https://doi.org/10.1038/s41586-021-04196-6) · [官方页面](https://doi.org/10.1038/s41586-021-04196-6)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：读写服务；CIM 求值桥接；互补单元与局部并行度。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；二值互补 MTJ；电阻求和／TDC。
- 已确认／预判：28 nm 电阻串联求和、TDC 读出及互补 MTJ 权重；Methods 明确一行左侧、右侧分两次并行编程，每次一个写时钟。
- 限制：两写步骤、read resistance sum 和 ordinary STT RAM 感测不是同一机制；正文 scaling 是分析。出版附件为视频，不缺另一份技术 SI PDF。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf`。
- 正文定位：pp.6–8，Methods：MTJ write/read、weight update、operating frequency（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/jung2022.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/jung2022.pdf', 'previous_source_id': 't1_jung2022', 'sha256': '8ae3c42c9e811194bc3ae2af456144e7fa475c798040bec1bdeb3a6986fd38a5', 'byte_identical': True}`。
- 附件情况：官方页面附件为演示视频，未列另一份技术 SI PDF；关键 Methods/Extended Data 已有。视频不影响本轮用途判断，不请求。

<a id="MRAM-02"></a>
### MRAM-02 — A CMOS-integrated spintronic compute-in-memory macro for secure AI edge devices

- 身份：2023；Nature Electronics 6, 534–543；Y.-C. Chiu、W.-S. Khwa、C.-S. Yang 等。
- 链接：[DOI](https://doi.org/10.1038/s41928-023-00994-0) · [官方页面](https://doi.org/10.1038/s41928-023-00994-0)。
- 判断：**补充 / P2**；层级：存储 array／近存数字计算 macro；不是模拟 crossbar 累加。
- 用途标签：CIM 求值桥接；局部并行度；独立 macro 交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；22 nm STT-MRAM；sense 后 near-memory 数字计算；PUF 与数据模式分开。
- 已确认／预判：22 nm STT macro 的正文明确 near-memory 数字 dot-product：sense 输出送数字引擎；SI 提供 PUF 写回、普通感测和访问时间测量边界。
- 限制：PUF 双 cell 写回不能替代一般权重更新；稀疏/ ReLU early termination 不等于固定全精度服务；非 Jung 电阻求和路径。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf`。
- 正文定位：pp.2–4、p.7 Fig.4、Methods；SI pp.3–10，Notes 1–4（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件：[Supplementary Information](literature/06_mram/MRAM-02_2023_SecureSpintronicCIM_Supplement.pdf)（13 页）。
- 附件情况：SI 已补齐并核验；无需用户重复下载。

<a id="MRAM-03"></a>
### MRAM-03 — A 1-Mb 28-nm 1T1MTJ STT-MRAM With Single-Cap Offset-Cancelled Sense Amplifier and In Situ Self-Write-Termination

- 身份：2019；IEEE Journal of Solid-State Circuits；Qing Dong、Zhehong Wang、Jongyup Lim 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2018.2872584) · [官方页面](https://doi.org/10.1109/jssc.2018.2872584)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：写入完成与终止；感测服务；28 nm 专用外围。
- 工艺／状态：直接的 28 nm 证据（专用 MRAM 外围）；binary 1T1MTJ STT-MRAM。
- 已确认／预判：28 nm 1T1MTJ 实测 macro，local subarray/SA、预充与 offset cancel、写稳定与自终止信号明确；读写成功率随时间/温度改变。
- 限制：读写指标附 BER 条件；自终止的节能收益不自动证明缩短固定外部写周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf`。
- 正文定位：pp.3–7，Figs.7–21，read timing／write termination（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="MRAM-04"></a>
### MRAM-04 — A 28nm 32Kb embedded 2T2MTJ STT-MRAM macro with 1.3ns read-access time for fast and reliable read applications

- 身份：2018；2018 IEEE International Solid - State Circuits Conference - (ISSCC)；Tzu-Hsien Yang、Kai-Xiang Li、Yen-Ning Chiang 等。
- 链接：[DOI](https://doi.org/10.1109/isscc.2018.8310394) · [官方页面](https://doi.org/10.1109/isscc.2018.8310394)。
- 判断：**补充 / P2**；层级：阵列／局部 macro。
- 用途标签：读侧时间尺度；感测与操作粒度；结构交叉核查。
- 工艺／状态：直接的 28 nm 证据（专用 MRAM 外围）；binary 2T2MTJ STT-MRAM。
- 已确认／预判：28 nm 2T2MTJ 实测快速读，包含预充、发展与感测三阶段，可独立核查读侧电路量级。
- 限制：互补物理单元与逻辑 bit 数不同；读 access 不能替代写时间或 CIM 多位求值。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf`。
- 正文定位：p.1，CREVSA；p.2，Figs.30.3.2–6（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="MRAM-05"></a>
### MRAM-05 — EMxxxLX/B/HR — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory

- 身份：2026；Everspin datasheet, EMxxxLX/B/HR v3.7；Everspin Technologies。
- 链接：[官方页面](https://www.everspin.com/design-support)。
- 判断：**补充 / P2**；层级：整芯片／封装接口。
- 用途标签：直接更新语义；字节粒度；普通存储交叉核查。
- 工艺／状态：功能与时序定义参考（该文件不证明 28 nm）；binary STT-MRAM；NOR erase 指令可模拟。
- 已确认／预判：用户下载的是 2026-07-23 v3.7，已替代原请求 v3.4；支持 back-to-back 写且无页跨越限制，给出读写命令与恢复条件。
- 限制：封装 xSPI 不是局部 cell 服务；ERASE 是产品兼容命令，不能据命令名称断言 STT 介质须先物理擦除。旧 brief 信息由 v3.7 覆盖。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf`。
- 正文定位：pp.15、41–48，WRITE/ERASE；pp.69–71，AC；pp.81–82，修订史（本地 PDF 页序）。
- 版本核验：修订史 pp.81–82 确认 v3.7 日期；部分内页沿用 ©2025 页脚，以版本史为准。不得将 v3.4 下载入口当作 v3.7 身份证据。
- 相关版本：[EMxxLX Product Brief](literature/06_mram/versions/MRAM-05_2023_EMxxLX_ProductBrief_v2p1.pdf)；冗余产品简表；仅留用户来件记录，不作为技术证据。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="MRAM-06"></a>
### MRAM-06 — A lossless and fully parallel spintronic compute-in-memory macro for artificial intelligence chips

- 身份：2025；Nature Electronics；Humiao Li、Zheng Chai、Weirong Dong 等。
- 链接：[DOI](https://doi.org/10.1038/s41928-025-01479-y) · [官方页面](https://doi.org/10.1038/s41928-025-01479-y)。
- 判断：**C 候选，主文待审 / P1**；层级：局部 64-kb macro（摘要）及实有补充材料。
- 用途标签：CIM 求值桥接；互补权重写入步骤；独立团队核查。
- 工艺／状态：40 nm STT-MRAM；其他工艺条件保留；精度／模式按正文限定。
- 已确认／预判：主文未到。官方摘要确认 40 nm、数字 bitcell 乘法；本地 SI p.4 Fig.2 已确认先两 MTJ 写 0 再目标写 1 的流程，绝对完整周期待主文。
- 限制：主文尚未到件；摘要和 SI 不替代完整时序、负载与操作条件审阅。
- 状态：身份已核验；主文未到，尚不能确认完整时序；拟下载主文。
- 保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM.pdf`。
- 附件：[Supplementary Information](literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM_Supplement.pdf)（15 页）。
- 附件情况：SI 已补齐并核验；无需用户重复下载。
- 独立性：Li/Chai 等团队不同于 Jung/Samsung 和 Chiu/TSMC，提供机制互补，不能将其 headline 与前两者平均。

## 07 — PCM

两种 IBM 多核／多 tile 实验和 TSMC 的 SLC／MLC macro 用于局部求值与并行写入，ST 合作器件测量及 Sc-Sb-Te 原始论文补材料与写入终点差异。SET、RESET、模拟精度与完整编程过程分别核查；两个 IBM 芯片是不同实验，但不是完全独立的工艺团队交叉证据。

<a id="PCM-01"></a>
### PCM-01 — A 64-core mixed-signal in-memory compute chip based on phase-change memory for deep neural network inference

- 身份：2023；Nature Electronics 6, 680–693；Manuel Le Gallo、Riduan Khaddam-Aljameh、Milos Stanisavljevic 等。
- 链接：[DOI](https://doi.org/10.1038/s41928-023-01010-1) · [官方页面](https://doi.org/10.1038/s41928-023-01010-1)。
- 判断：**核心 / P1**；层级：阵列／局部 macro 及整芯片。
- 用途标签：CIM 求值桥接；并行 writehead；多级编程与校验。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；模拟多级 PCM、差分映射。
- 已确认／预判：64-core 芯片的 diagonal selection 一次选不同 row/column 的器件，局部 write DAC、SET/RESET 形状与读 ADC 边界清楚。
- 限制：论文的部分 latency 由 RTL 得到，不能全部称直接测量；14 nm、四 PCM/cell 与其他芯片不同。附加视频不是必需时序文献。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/07_pcm/PCM-01_2023_PCM64_Core.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-01_2023_PCM64_Core.pdf`。
- 正文定位：pp.2–3，diagonal programming/ADC；Methods 与 p.10，Power measurements（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/pcm64.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/pcm64.pdf', 'previous_source_id': 't1_pcm64', 'sha256': '81c512921e635d20769b9a0752d958f6820158f8459728e9333cb320d39b1278', 'byte_identical': True}`。
- 附件情况：官方页面附件为演示视频，未列另一份技术 SI PDF；关键 Methods/Extended Data 已有。视频不影响本轮用途判断，不请求。
- 独立性：相关实验／团队族：ibm_pcm_platform；同族条目不自动视作独立交叉验证。

<a id="PCM-02"></a>
### PCM-02 — An analog-AI chip for energy-efficient speech recognition and transcription

- 身份：2023；Nature；S. Ambrogio、P. Narayanan、A. Okazaki 等。
- 链接：[DOI](https://doi.org/10.1038/s41586-023-06337-5) · [官方页面](https://doi.org/10.1038/s41586-023-06337-5)。
- 判断：**核心 / P1**；层级：阵列／tile、芯片与系统。
- 用途标签：CIM 求值桥接；行并行编程；局部与系统边界。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；模拟多级、2/4 PCM-per-weight。
- 已确认／预判：14 nm 芯片支持 row-wise 同时调谐 512 个权重，但一次选每权重的一个 PCM；闭环、校正与 tile 控制在正文交代。
- 限制：约 1 GHz controller clock 不是一次完整 MVM 或写入；写算法细节转引 ref.4，值得获取原始 2021 TED。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf`。
- 正文定位：p.3，Fig.1f；pp.9–10，Methods：weight programming、controller、calibration（本地 PDF 页序）。
- 附件情况：2026-09-08 官方出版页未列独立技术 SI PDF；本地包含 Methods/Extended Data，V2 不请求不存在于页面的通用附件。
- 独立性：相关实验／团队族：ibm_pcm_platform；同族条目不自动视作独立交叉验证。

<a id="PCM-03"></a>
### PCM-03 — A 40-nm, 2M-Cell, 8b-Precision, Hybrid SLC-MLC PCM Computing-in-Memory Macro with 20.5 - 65.0TOPS/W for Tiny-AI Edge Devices

- 身份：2022；2022 IEEE International Solid- State Circuits Conference (ISSCC)；Win-San Khwa、Yen-Cheng Chiu、Chuan-Jia Jhang 等。
- 链接：[DOI](https://doi.org/10.1109/isscc42614.2022.9731670) · [官方页面](https://doi.org/10.1109/isscc42614.2022.9731670)。
- 判断：**核心 / P1**；层级：阵列／局部 macro。
- 用途标签：CIM 求值桥接；binary／multi-level；操作粒度。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；hybrid SLC／MLC（分模式）。
- 已确认／预判：40 nm 实测 PCM CIM，8-bit weight 以 2 SLC+3 MLC 编码，8-bit input 默认八拍；VSA 四阶段与 sparsity 重排解释求值粒度。
- 限制：低功耗全 MLC 与混合模式不同；input-reordering 的跳过拍数依赖数据；没有完整 SET/RESET 更新周期。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf`。
- 正文定位：p.1，Figs.11.3.2–6 的说明；pp.2–3，图与 summary（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="PCM-04"></a>
### PCM-04 — Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing

- 身份：2017；Science；Feng Rao、Keyuan Ding、Yuxing Zhou 等。
- 链接：[DOI](https://doi.org/10.1126/science.aao3212) · [官方页面](https://doi.org/10.1126/science.aao3212)。
- 判断：**条件保留 / P2**；层级：器件／材料。
- 用途标签：器件写入时间尺度；材料差异；独立量级交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；Sc-Sb-Te 晶化／相变条件；非默认多级 PCM 写入。
- 已确认／预判：Sc-Sb-Te 器件原始写入／材料结果可核查快速结晶，与 GST 系芯片构成材料条件对照。
- 限制：Materials and Methods、RESET 补充图 S6、测量装置及脉冲条件在缺失 SI；亚纳秒不能代替整阵列闭环写入。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf`。
- 正文定位：pp.2–4，Figs.2–4；p.4，Supplementary Materials 声明（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：缺 Materials and Methods、Figs.S1–S11；已列 V2，主文不用重复。

<a id="PCM-05"></a>
### PCM-05 — Phase Change Memory Drift Compensation in Spiking Neural Networks Using a Non-Linear Current Scaling Strategy

- 身份：2024；Journal of Low Power Electronics and Applications；Joao Henrique Quintino Palhares、Nikhil Garg、Yann Beilliard 等。
- 链接：[DOI](https://doi.org/10.3390/jlpea14040050) · [官方页面](https://doi.org/10.3390/jlpea14040050)。
- 判断：**补充 / P2**；层级：器件测量与电路／网络仿真。
- 用途标签：SET／RESET 与多级编程；测试条件；独立量级交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；Ge-rich GST 多级 PCM；SET／RESET 分开。
- 已确认／预判：28 nm FD-SOI 相关 PCM 原始器件测试明确 75 ns SET/RESET、幅值／compliance 和多次序列；用读后等待跟踪漂移。
- 限制：75 ns 是实验单脉冲；1000 次测试序列不是每次逻辑写入的必需脉冲数；SNN 补偿结果不能直接转为 local CIM 服务。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/07_pcm/PCM-05_2024_PCM_Drift.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-05_2024_PCM_Drift.pdf`。
- 正文定位：p.3，§2.1–2.2；后续漂移补偿验证（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="PCM-06"></a>
### PCM-06 — Fully On-Chip MAC at 14 nm Enabled by Accurate Row-Wise Programming of PCM-Based Weights and Parallel Vector-Transport in Duration-Format

- 身份：2021；IEEE Transactions on Electron Devices；P. Narayanan、S. Ambrogio、A. Okazaki 等。
- 链接：[DOI](https://doi.org/10.1109/ted.2021.3115993) · [官方页面](https://doi.org/10.1109/ted.2021.3115993)。
- 判断：**C 候选，主文待审 / P1**；层级：局部 tile／实际芯片（官方摘要确认）。
- 用途标签：写入闭环；并行粒度；编程控制与读验。
- 工艺／状态：14 nm PCM 专用外围，非共同 28 nm；精度／模式按正文限定。
- 已确认／预判：身份与摘要已核验；预期用途尚未由主文确认。
- 限制：主文尚未到件；摘要和 SI 不替代完整时序、负载与操作条件审阅。
- 状态：身份已核验；主文未到，尚不能确认完整时序；拟下载主文。
- 保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-06_2021_RowWise_ClosedLoopProgramming.pdf`。
- 附件情况：请主文与出版社列出的技术 SI 一并获取；已归档的 SI 无需重复。
- 独立性：与 PCM-02 同一 IBM 技术线，提供方法细节，不新增独立工艺交叉证据。

## 08 — FeRAM（HfO₂-based）

SK hynix、Sony 与 Micron 正文确认 HfO₂ 系 1T1C 阵列及读后恢复；Micron NVDRAM 并非仅有 LPDDR5 总线数据。C2FeRAM 给非破坏读桥接但大阵列为模型；混合 FeCAP/memristor 只保留 FeCAP 本身的证据。

<a id="FERAM-01"></a>
### FERAM-01 — A 2-Transistor-2-Capacitor Ferroelectric Edge Compute-in-Memory Scheme with Disturb-Free Inference and High Endurance

- 身份：2023；IEEE Electron Device Letters 44(7), 1088–1091；Xiaoyang Ma、Shan Deng、Juejian Wu 等。
- 链接：[DOI](https://doi.org/10.1109/LED.2023.3274362) · [官方页面](https://doi.org/10.1109/LED.2023.3274362)。
- 判断：**核心 / P1**；层级：HfO₂ 系 FeCAP 器件实验与电路仿真。
- 用途标签：CIM 求值桥接；读／恢复机制；写入步骤。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；HfO₂ 系 FeCAP；2T2C。
- 已确认／预判：C2FeRAM 的 2T2C 路径解释非破坏读与电流求和；行写入明确先 write-0 再 write-1，MLC 需 verify；离散 FeCAP/MOS 实验支持器件机制。
- 限制：大阵列／网络 latency 为模型，3D 集成为提议；不能当作完整已流片 28 nm FeRAM CIM。非破坏性读也不消除浮置节点漏电恢复。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf`。
- 正文定位：pp.2–3，Figs.3–6、II–III（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/c2feram2023.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/c2feram2023.pdf', 'previous_source_id': 't1_c2feram2023', 'sha256': '1e878eb85396e3c7ca67c4ae0006bd6344d1acd668eed06eaa18267c1d51b88a', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="FERAM-02"></a>
### FERAM-02 — Low Voltage and High Speed 1Xnm 1T1C FE-RAM with Ultra-Thin 5nm HZO

- 身份：2021；2021 IEEE International Electron Devices Meeting (IEDM)；Minchul Sung、Kwangmyoung Rho、Jayong Kim 等。
- 链接：[DOI](https://doi.org/10.1109/iedm19574.2021.9720545) · [官方页面](https://doi.org/10.1109/iedm19574.2021.9720545)。
- 判断：**核心 / P1**；层级：器件／存储阵列。
- 用途标签：读写时间尺度；1T1C 阵列操作；低压条件。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；5 nm HZO；1T1C FeRAM。
- 已确认／预判：SK hynix 8 Gb 1T1C、5 nm HZO 真正阵列；SAWAR 读后明确重写；write-recovery 扫描显示极化随写时间继续增加。
- 限制：20 ns 对应部分极化响应，不是全部 cell/完整周期通用终点；5 nm 薄膜厚度不是 CMOS 工艺节点。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf`。
- 正文定位：pp.1–2，II-B／III-B；pp.3–4，Figs.3、8–10（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="FERAM-03"></a>
### FERAM-03 — SoC Compatible 1T1C FeRAM Memory Array Based on Ferroelectric Hf0.5Zr0.5O2

- 身份：2020；2020 IEEE Symposium on VLSI Technology；Jun Okuno、Takafumi Kunihiro、Kenta Konishi 等。
- 链接：[DOI](https://doi.org/10.1109/vlsitechnology18217.2020.9265063) · [官方页面](https://doi.org/10.1109/vlsitechnology18217.2020.9265063)。
- 判断：**核心 / P1**；层级：器件／1T1C 阵列及外围。
- 用途标签：阵列读写；局部操作粒度；独立交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；Hf0.5Zr0.5O2；1T1C。
- 已确认／预判：Sony/NaMLab 的 64 kbit HZO 1T1C 实测读写 shmoo；Fig.9 明确读状态翻转和 data writeback 阶段。
- 限制：8 ns sense 与 14 ns write 是分别测量，不把单独 sense 当成含恢复的读周期；不是 28 nm 外围流片。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf`。
- 正文定位：p.1，64 kbit array demonstration；p.2，Figs.8–11（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="FERAM-04"></a>
### FERAM-04 — NVDRAM: A 32Gb Dual Layer 3D Stacked Non-volatile Ferroelectric Memory with Near-DRAM Performance for Demanding AI Workloads

- 身份：2023；2023 International Electron Devices Meeting (IEDM)；N. Ramaswamy、A. Calderoni、J. Zahurak 等。
- 链接：[DOI](https://doi.org/10.1109/iedm45741.2023.10413848) · [官方页面](https://doi.org/10.1109/iedm45741.2023.10413848)。
- 判断：**核心 / P1**；层级：阵列／die 与整芯片。
- 用途标签：完整读写服务；操作粒度；大阵列交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；HZO 1T1C 铁电存储；不归为普通 DRAM。
- 已确认／预判：正文明确 5.7 nm 掺杂 HfZrOx 电容、双层 1T1C；Fig.13 同时给 sensing、writeback、precharge 和完整 tRC，确属本轮 HfO₂ FeRAM。
- 限制：短 tWR 将部分恢复代价转到 tRP；不能摘取 10 ns 宣称完整写入结束。LPDDR5 兼容不等于 DRAM 相同阵列时序。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf`。
- 正文定位：p.2，Memory Cell／Component Performance；p.4，Fig.13（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="FERAM-05"></a>
### FERAM-05 — Enhanced polarization switching characteristics of HfO2 ultrathin films via acceptor-donor co-doping

- 身份：2024；Nature Communications；Chao Zhou、Liyang Ma、Yanpeng Feng 等。
- 链接：[DOI](https://doi.org/10.1038/s41467-024-47194-8) · [官方页面](https://doi.org/10.1038/s41467-024-47194-8)。
- 判断：**补充 / P2**；层级：器件／铁电电容。
- 用途标签：器件切换时间尺度；测试偏置与终点；独立交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；共掺杂 HfO₂ 铁电电容。
- 已确认／预判：La/Ta 共掺 hafnia 原始材料测量提供厚度、偏置、成核/畴壁与极化终点，适合解释同类器件时间差异。
- 限制：外延薄膜/电极/测量层级不同于集成 1T1C array；高速切换不是 macro 服务。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf`。
- 正文定位：pp.4–7，switching kinetics／Methods；已归档 SI（本地 PDF 页序）。
- 附件：[Supplementary Information](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia_Supplement.pdf)（34 页）。
- 附件情况：已归档技术 Supplementary Information；见附件链接。

<a id="FERAM-06"></a>
### FERAM-06 — A ferroelectric–memristor memory for both training and inference

- 身份：2025；Nature Electronics；Michele Martemucci、François Rummens、Yannick Malot 等。
- 链接：[DOI](https://doi.org/10.1038/s41928-025-01454-7) · [官方页面](https://doi.org/10.1038/s41928-025-01454-7)。
- 判断：**补充 / P2**；层级：FeCAP／memristor 阵列与计算实验。
- 用途标签：FeCAP 阵列写入；并行粒度；训练／推理桥接。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；Si:HfO₂ FeCAP 为本组主体；memristor 支路另区分。
- 已确认／预判：真实共集成 FeCAP 与 memristor 及权重转移实验，给 FeCAP 电压/时间扫描、读写节点与外部脉冲测量条件。
- 限制：推理主路径是 memristor；全突触含多 FeCAP 和两个 memristor，不能把混合推理性能归为纯 FeRAM CIM；网络部分为仿真。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf`。
- 正文定位：pp.3–5，FeCAP/混合阵列；p.9，Methods；已归档 SI（本地 PDF 页序）。
- 附件：[Supplementary Information](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor_Supplement.pdf)（18 页）。
- 附件情况：已归档技术 Supplementary Information；见附件链接。

## 09 — Gain-cell eDRAM

现有全文形成 2T1C 模拟、4T 普通存储、3T1C 多级电流写入与 4T+stationary 数字 CIM 的互补来源。保持分布、刷新占用、粗写/精写以及 storage 更新与计算权重更新的区别必须保留。

<a id="GC-01"></a>
### GC-01 — Gain-Cell CIM: Leakage and Bitline Swing Aware 2T1C Gain-Cell eDRAM Compute in Memory Design with Bitline Precharge DACs and Compact Schmitt Trigger ADCs

- 身份：2022；VLSI Symposium, 112–113；Shanshan Xie、Can Ni、Pulkit Jain 等。
- 链接：[DOI](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338) · [官方页面](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338)。
- 判断：**核心 / P1**；层级：2T1C gain-cell 局部 macro。
- 用途标签：完整求值；读写端口；保持与泄漏。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；65 nm CMOS 2T1C gain-cell；数字权重。
- 已确认／预判：65 nm 2T1C gain-cell CIM 的读写端口分离、BL 输入预充、泄漏夹位和 ST-ADC 有明确电路与测试证据。
- 限制：2-bit 输入顺序展开及 complementary weight 不等于单次完整 8-bit 运算；不能取普通 1T1C DRAM 代替。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf`。
- 正文定位：p.1，三步 MAV／Measurement Results；p.2，Figs.2–7（本地 PDF 页序）。
- 复制关系：`{'original_path': 'tasks/task1_table_i/sources/local-only/gaincell2022.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/gaincell2022.pdf', 'previous_source_id': 't1_gaincell2022', 'sha256': 'c5e1c9c42668751b94220d9457f894a7ab43d6d26211605678dfe3a100921542', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="GC-02"></a>
### GC-02 — An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications

- 身份：2018；IEEE Journal of Solid-State Circuits；Robert Giterman、Alexander Fish、Narkis Geuli 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2018.2820145) · [官方页面](https://doi.org/10.1109/jssc.2018.2820145)。
- 判断：**核心 / P1**；层级：实测 gain-cell 局部 macro。
- 用途标签：28 nm 读写服务；保持／刷新；普通 gain-cell 粒度。
- 工艺／状态：直接的 28 nm 证据（gain-cell 存储）；28 nm bulk mixed-VT 4T gain-cell。
- 已确认／预判：28 nm 4T IFGC 实测 128×32 macro，WWL 升压与时序、SA、读写频率和保持分布；直接支撑刷新占用与局部边界。
- 限制：5 µs 刷新对应文中约 99% bit 可靠性条件，不是全 bit 无误保证；平均保持不能代替最差 cell。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf`。
- 正文定位：pp.4–8，Figs.4–11；pp.9–10，retention/availability（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="GC-03"></a>
### GC-03 — Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform

- 身份：2024；IEEE Transactions on Electron Devices 71(5), 3329–3335；Shuhan Liu、Koustav Jana、Kasidit Toprasertpong 等。
- 链接：[DOI](https://doi.org/10.1109/TED.2024.3372938) · [官方页面](https://poplab.stanford.edu/pdfs/Liu-DesignOSFETgainCell-ted24.pdf)。
- 判断：**核心 / P1**；层级：器件依据与局部 macro 仿真／建模。
- 用途标签：读写设计方法；保持与刷新；28 nm 映射桥接。
- 工艺／状态：直接的 28 nm 模型条件／其他工艺器件依据（须逐项区分）；OS–OS／hybrid gain-cell，保留不同通道结构。
- 已确认／预判：以 28 nm macro 模型将保持、读取电流和刷新阻塞联系起来，能支持从 oxide 器件到 local service 的透明换算。
- 限制：GEMTOO/Timeloop 是设计评估，非实测完整 oxide CIM 芯片。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf`。
- 正文定位：pp.2–4，top-down macro/refresh；pp.4–6，器件规格（本地 PDF 页序）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="GC-04"></a>
### GC-04 — A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM

- 身份：2024；IEEE Journal of Solid-State Circuits；Jiahao Song、Xiyuan Tang、Haoyang Luo 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2023.3339887) · [官方页面](https://doi.org/10.1109/jssc.2023.3339887)。
- 判断：**核心 / P1**；层级：3T1C gain-cell 型局部 macro。
- 用途标签：写入建立；多级状态；CIM 求值与保持。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；3T1C current-programmed dynamic-cascode MLC。
- 已确认／预判：65 nm 3T1C MLC gain-cell，电流写入自校正，先电压粗写再电流精写；完整 CIM 含 precharge、DTC 求值和 SAR。
- 限制：5 ns 仅粗写；60 ns 建立结论在 Fig.12 仿真中，不能称实测完整更新；180 ns compute 与保持漂移精度相关。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf`。
- 正文定位：pp.4–7，Figs.4–11；p.8，Fig.12／measurement（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

<a id="GC-05"></a>
### GC-05 — An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips

- 身份：2025；IEEE Journal of Solid-State Circuits；Ping-Chun Wu、Win-San Khwa、Jui-Jen Wu 等。
- 链接：[DOI](https://doi.org/10.1109/jssc.2024.3470215) · [官方页面](https://doi.org/10.1109/jssc.2024.3470215)。
- 判断：**核心 / P1**；层级：gain-cell 局部 macro。
- 用途标签：完整精度求值；局部并行度；近期产业交叉核查。
- 工艺／状态：其他工艺的量级交叉参考（16 nm）；16 nm 4T gain-cell 存储 + 7T stationary unit；数字 INT/FP，分模式。
- 已确认／预判：16 nm 4T gain-cell 存储配 7T stationary unit 的数字 CIM，明确 storage update、stationary update、self-refresh 和计算重叠模式。
- 限制：计算使用 stationary 数据；更新 storage 不代表同一权重立即参加计算。INT/FP 服务不同，也不是 3T1C 电荷域方案。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf`。
- 正文定位：pp.2–3，4T GC+STU 架构；pp.6–8，Figs.13–20（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。

## 10 — 3D FeNOR／vertical FeFET

Zhou 2025 NOR-type 与 2026 AND-type 原文件均已核验，根目录不动。Feng 会议/期刊合为一个证据包；POSTECH FeNAND 退出 FeNOR 核心并移入 comparisons，仅作为直接拓扑对照。

<a id="FENOR-01"></a>
### FENOR-01 — 3D NOR-type FeFETs with Record Endurance of 10^11, Fast Erase of 50 ns, and Immediate Read-After-Write for In-Memory Learning

- 身份：2025；Symposium on VLSI Technology and Circuits；Yuejia Zhou、Runteng Zhu、Wenpu Luo 等。
- 链接：[DOI](https://doi.org/10.23919/vlsitechnologyandcir65189.2025.11074820) · [官方页面](https://doi.org/10.23919/VLSITechnologyandCir65189.2025.11074820)。
- 判断：**核心 / P1**；层级：器件／三层小阵列与 CIM 仿真。
- 用途标签：器件读写时间尺度；更新步骤；局部阵列结构。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；IGO／HZO；NOR-type；器件偏置分条件。
- 已确认／预判：指定 Zhou 2025 文件确认 8×8×3 IGO/HZO NOR-type；PGM/ERS、read-after-write、层间差异及 cell 逻辑有实际测量。
- 限制：NN benchmark 与大阵列延时为模拟；单 cell/小阵列测试不等于全精度 macro 周期。根目录原稿保持不动。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf`。
- 正文定位：p.1，Fabrication/Speed/Simulation；pp.2–3，Figs.2–12（本地 PDF 页序）。
- 复制关系：`{'original_path': '2025--Yuejia Zhou--3D NOR-Type FeFETs with Record Endurance of 1011 , Fast Erase of 50 Ns, and Immediate Read-After-Write for In-Memory Learning.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/zhou2025.pdf', 'previous_source_id': 't1_zhou2025', 'sha256': '1fbb27c7d95d0239b1e179323a980d16a49c352c0bd1206e36e666d64d2e0289', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。

<a id="FENOR-02"></a>
### FENOR-02 — 3D Vertical FeFET Array with Record Endurance (>10^12), Fast Writing (±2V, 20 ns), Disturb Immunity, and Kb-scale Verification for High Density 1T RAM

- 身份：2026；Symposium on VLSI Technology and Circuits T11.1；Yuejia Zhou、Yuancheng Yang、Liang Chen 等。
- 链接：[DOI](https://doi.org/10.1109/vlsitechnologyandcir65830.2026.11577291) · [官方页面](https://vlsi26.mapyourshow.com/8_0/sessions/session-details.cfm?ScheduleID=251)。
- 判断：**核心 / P1**；层级：器件／四层阵列与 TCAD／SPICE。
- 用途标签：器件读写；写扰与并行选择条件；局部阵列验证。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；IGO／HZO；AND-type vertical FeFET；SL/SS 与 O-rich/O-poor 分条件。
- 已确认／预判：指定 Zhou 2026 文件实际为 3D-AND FeFET；32×32×4 制造结构与 16×16×4 验证范围分开，写入/半选/相邻扰动方案有直接依据。
- 限制：20 ns 为偏置和结构限定的 switching；TCAD/SPICE read 与密度预测不当作实测宏；不因简称 FeNOR 忽略 AND 结构。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf`。
- 正文定位：p.1，array/disturb/benchmark；pp.2–3，Figs.7–11（本地 PDF 页序）。
- 复制关系：`{'original_path': '2026--Yuejia Zhou--3D Vertical Fefet Array with Record Endurance (¾1012 ), Fast Writing (± 2 V, 20 Ns), Disturb Immunity, and Kb-Scale Verification for High Density 1T Ram.pdf', 'previous_task_path': 'tasks/task1_table_i/sources/local-only/zhou2026.pdf', 'previous_source_id': 't1_zhou2026', 'sha256': '322482d834c279a278d0aaa007a0cfeb26dee49253fe50661d0483975d9b19d5', 'byte_identical': True}`。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。

<a id="FENOR-03"></a>
### FENOR-03 — First Demonstration of BEOL-Compatible 3D Vertical FeNOR

- 身份：2024；2024 IEEE Symposium on VLSI Technology and Circuits (VLSI Technology and Circuits)；Yang Feng、Dong Zhang、Chen Sun 等。
- 链接：[DOI](https://doi.org/10.1109/vlsitechnologyandcir46783.2024.10631352) · [官方页面](https://doi.org/10.1109/vlsitechnologyandcir46783.2024.10631352)。
- 判断：**版本归并 / P3**；层级：器件／BEOL 三维阵列。
- 用途标签：阵列结构；写扰与更新方式；独立团队交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；ZnO／MFMIS BEOL vertical FeNOR。
- 已确认／预判：2024 会议稿记录首个 BEOL vertical FeNOR、脉冲窗口和阵列逻辑；2025 TED 正文明确扩展此稿。保留以追踪测试条件和版本差异。
- 限制：不再独立占一个核心交叉来源；同一数据不能双重计数；正文文本层乱码，图像已核验。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/versions/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/versions/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf`。
- 正文定位：pp.1–2，Figs.1–14；对照 FENOR-04 p.2（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 本轮原归档路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf`（已按上述路径整理）。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：feng_beol_fenor_2024_2025；同族条目不自动视作独立交叉验证。

<a id="FENOR-04"></a>
### FENOR-04 — Efficient Large Scale Neural Network Acceleration With 3-D FeNOR-Based Computing-in-Memory Design

- 身份：2025；IEEE Transactions on Electron Devices；Yang Feng、Dong Zhang、Chen Sun 等。
- 链接：[DOI](https://doi.org/10.1109/ted.2025.3554164) · [官方页面](https://doi.org/10.1109/ted.2025.3554164)。
- 判断：**核心 / P1**；层级：器件／阵列及计算建模。
- 用途标签：CIM 求值桥接；局部读出／并行条件；独立团队交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；ZnO/MFMIS 3D FeNOR；小阵列测量 + 大阵列网络模拟。
- 已确认／预判：ZnO/MFMIS 3D FeNOR 器件、阵列电流逻辑实测，与 4096×4096 网络/外围仿真分开；扩展版补写入偏置与变异条件。
- 限制：大阵列 4096×4096 不是流片尺寸；高电压时 charge injection 影响 MW；system energy 不作为实测统一外围。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf`。
- 正文定位：p.2，版本声明；pp.4–6，Figs.7–14、III–IV（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：feng_beol_fenor_2024_2025；同族条目不自动视作独立交叉验证。

<a id="FENOR-05"></a>
### FENOR-05 — Highly-scaled and fully-integrated 3-dimensional ferroelectric transistor array for hardware implementation of neural networks

- 身份：2023；Nature Communications；Ik-Jyae Kim、Min-Kyu Kim、Jang-Sik Lee。
- 链接：[DOI](https://doi.org/10.1038/s41467-023-36270-0) · [官方页面](https://doi.org/10.1038/s41467-023-36270-0)。
- 判断：**结构对照 / P3**；层级：器件／三维 FeFET 阵列与计算实验。
- 用途标签：器件编程；三维阵列读出；独立结构交叉核查。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；HfZrOx 三维 FeNAND；串联选择、multiple layers／VMM 实验。
- 已确认／预判：实际垂直 HfZrOx/InZnOx FeNAND，支持串联选择、pass bias、层间编程等对照，有助解释 NOR/AND 与 NAND 拓扑差异。
- 限制：不是 FeNOR，不能占 FeNOR 核心速度来源或直接迁移 NOR 并行度。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND.pdf`。
- 正文定位：pp.2–5，Results／FeNAND；Methods 与已归档 SI（本地 PDF 页序）。
- 本轮原归档路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-05_2023_Integrated3D_FeFET.pdf`（已按上述路径整理）。
- 附件：[Supplementary Information](literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND_Supplement.pdf)（14 页）。
- 附件情况：已归档技术 Supplementary Information；见附件链接。

<a id="FENOR-06"></a>
### FENOR-06 — Gate Stack Engineering of 3D Oxide Channel FeNOR Memory with High-Speed and Reliabilitity

- 身份：2026；2026 10th IEEE Electron Devices Technology & Manufacturing Conference (EDTM)；Yuejia Zhou、Ru Huang、Kechao Tang。
- 链接：[DOI](https://doi.org/10.1109/edtm65772.2026.11498024) · [官方页面](https://doi.org/10.1109/edtm65772.2026.11498024)。
- 判断：**核心 / P1**；层级：器件／三维 FeNOR。
- 用途标签：器件读写与偏置；栅堆栈差异；更新约束。
- 工艺／状态：介质专用器件／阵列条件，不自行认定 28 nm；3D oxide-channel FeNOR；不同栅堆栈分条件。
- 已确认／预判：2026 EDTM 对照 MFS/MFIS/MIFS/MIFIS，写速度随栅堆栈与偏置改变，可解释 Zhou 系列与其他 FeNOR 差异。
- 限制：与 Zhou 同团队，不能当独立外部验证；耐久与写速测试偏置不同，不能拼接最优点。
- 状态：本地主文已核验，正文用途已复核；[本地 PDF](literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf)。
- 保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf`。
- 正文定位：pp.1–2，B/C；p.3，Figs.5–10（本地 PDF 页序）。
- 版本核验：R1 实际 PDF 身份与 R0 题录匹配；原始来件路径见 intake_path／rename_log_r1.json。
- 附件情况：R1 未从正文识别额外必需技术附件；不将通用出版社尾注自动视为缺件。
- 独立性：相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。

