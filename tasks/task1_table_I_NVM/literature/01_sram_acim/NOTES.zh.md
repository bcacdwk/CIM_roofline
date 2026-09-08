# 01 — SRAM ACIM

电荷域 macro 补输入方式、转换共享、复位/建立和规定输出。不同工艺仅用作结构与条件交叉；普通 SRAM 写服务由共同组支持。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

共同/共享依据：[CMOS-03](../00_cmos_periphery/NOTES.zh.md#CMOS-03)、[CMOS-07](../00_cmos_periphery/NOTES.zh.md#CMOS-07)。

<a id="SACIM-01"></a>
## SACIM-01 — Scalable and Programmable Neural Network Inference Accelerator Based on In-Memory Computing

**核心** · 2022 · IEEE JSSC 57(1), 198–211 · [全文](SACIM-01_2022_Scalable_IMC.pdf)

**身份与版本：** Hongyang Jia, Murat Ozatay, Yinqi Tang, Hossein Valavi, Rakshit Pathak, Jinseok Lee, Naveen Verma。Published paper。

**用途与结构：** 可区分本地 CIMA、SIMD、片上网络及权重装载网络；完整精度需位平面与数字累加配合。实测数字时钟与 ADC 输出服务率分列。

**正文定位：** pp.4–7，CIMU／CIMA 与 BPBS；p.9，V-A／Table III。

**工艺/模式：** 其他工艺的量级交叉参考（65 nm）；精度按正文条件限定。

**使用限制：** 目标 500 MHz 与受封装供电限制的实测频率不同；28 MB 权重 buffer 未集成在原型中；整芯片吞吐不能直接作为 local macro 服务。

**出版标识：** [DOI](https://doi.org/10.1109/JSSC.2021.3119018)。

<a id="SACIM-02"></a>
## SACIM-02 — PICO-RAM: A PVT-Insensitive Analog Compute-In-Memory SRAM Macro With In Situ Multi-Bit Charge Computing and 6T Thin-Cell-Compatible Layout

**核心** · 2025 · IEEE Journal of Solid-State Circuits · [全文](SACIM-02_2025_PICO_RAM.pdf)

**身份与版本：** Zhiyu Chen, Ziyuan Wen, Weier Wan, Akhil Reddy Pakala, Yiwei Zou, Wei-Chen Wei, Zengyi Li, Yubei Chen, Kaiyuan Yang。与 2025 期刊对应的 2024 作者稿；正文有实际芯片测量，引用正式期刊 DOI。

**用途与结构：** 实测 65 nm 电荷域 macro；同一组电容依次用于两阶段 DAC、MAC、移位累加与 ADC，说明外围开销可重用，不能简单串加独立转换器延时。

**正文定位：** pp.4–7，Figs.4–14；pp.8–10，测量与 PVT。

**工艺/模式：** 其他工艺的量级交叉参考（65 nm）；精度按正文条件限定。

**使用限制：** 本地为作者稿，2024 预印本与 2025 期刊记录关联；65 nm 不是共同 28 nm 的直接速度证据。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2024.3422826)。

<a id="SACIM-03"></a>
## SACIM-03 — A 28nm 32Kb SRAM Computing-in-Memory Macro With Hierarchical Capacity Attenuator and Input Sparsity-Optimized ADC for 4b Mac Operation

**核心** · 2023 · IEEE Transactions on Circuits and Systems II: Express Briefs · [全文](SACIM-03_2023_Hierarchical_Attenuator.pdf)

**身份与版本：** Kanglin Xiao, Xiaoxin Cui, Xin Qiao, Jiahao Song, Haoyang Luo, Xin’an Wang, Yuan Wang。完整正式论文/技术资料。

**用途与结构：** 2023 期刊明确新增流片测量；28 nm 128×256 9T1C 阵列、128 路 4-bit 输入 DAC、64 路 4-bit ADC，给出 reset/evaluation/readout 关系与 die photo。

**正文定位：** p.2，扩展版说明、Figs.1–3；p.3，Fig.5／III；p.4，Figs.6–8。

**工艺/模式：** 直接的 28 nm 实测证据（期刊扩展版）；精度按正文条件限定。

**使用限制：** 4-bit ADC 输出不等于完整无损 MAC 精度；普通权重写入绝对周期仍未闭合。电荷复位、建立、稀疏判读与 MAC 读出必须按 Fig.5 区分。

**出版标识：** [DOI](https://doi.org/10.1109/tcsii.2023.3234620)。

<a id="SACIM-04"></a>
## SACIM-04 — A Charge Domain SRAM Compute-in-Memory Macro With C-2C Ladder-Based 8-Bit MAC Unit in 22-nm FinFET Process for Edge Inference

**核心** · 2023 · IEEE Journal of Solid-State Circuits · [全文](SACIM-04_2023_C2C_ChargeDomain.pdf)

**身份与版本：** Hechen Wang, Renzhi Liu, Richard Dorrance, Deepak Dasalukunte, Dan Lake, Brent Carlton。完整正式论文/技术资料。

**用途与结构：** 实际 22 nm 电荷域 macro；DAC/MAC 建立可重叠，SAR 内部八步放在另一半周期；R2R 驱动选型明确考虑 C2C 无法驱动的扇出负载。

**正文定位：** p.5，Fig.10；pp.7–9，Figs.16–20；pp.10–11，测量。

**工艺/模式：** 其他工艺的量级交叉参考（22 nm FinFET）；精度按正文条件限定。

**使用限制：** 完整周期与内部 SAR 步骤不能混用；工艺不是 28 nm。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2022.3232601)。

<a id="SACIM-05"></a>
## SACIM-05 — 8-Bit Precision 6T SRAM Compute-in-Memory Macro Using Global Bitline-Combining Scheme for Edge AI Chips

**核心** · 2024 · IEEE Transactions on Circuits and Systems II: Express Briefs · [全文](SACIM-05_2024_GlobalBitlineCombining_8bit.pdf)

**身份与版本：** Jian-Wei Su, Pei-Jung Lu, Ping-Chun Wu, Yen-Chi Chou, Ta-Wei Liu, Yen-Lin Chung, Li-Yang Hung, Jin-Sheng Ren, Wei-Hsing Huang, Chih-Han Chien, Peng-I Mei, Sih-Han Li, Shyh-Shyuan Sheu, Wei-Chung Lo, Shih-Chieh Chang, Hao-Chiao Hong, Chung-Chuan Lo, Ren-Shuo Liu, Chih-Cheng Hsieh, Kea-Tiong Tang, Meng-Fan Chang。完整正式论文/技术资料。

**用途与结构：** 28 nm 实测 6T SRAM macro；32 个 cell 共享 HIPCC，本地/全局 BL 与普通读写路径明确。8-bit 输入分成四组 2-bit DAC 电压并行输入；GBL-comb 将同位权部分和合并，SAR 数量由 96 减到 69，并以数字移位累加形成输出。

**正文定位：** p.2 III-A/B、Fig.4；pp.3–4 III-C/D、IV、Figs.5–10；p.5 Fig.11。

**工艺/模式：** 直接的 28 nm 实测证据；普通写入绝对周期仍未闭合；精度按正文条件限定。

**使用限制：** 不是一个独立 8-bit DAC 直接驱动全部字线。voltage-stacking 有初始化、采样、叠加三阶段；输出数字位数不代表模拟无误精度；仍未明确普通写入的绝对完整服务周期。

**出版标识：** [DOI](https://doi.org/10.1109/tcsii.2023.3331375)。

