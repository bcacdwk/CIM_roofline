# 02 — SRAM DCIM

五篇全文覆盖位串行、两位/四位输入展开、动态逻辑、可调加法器及转置访问。把 clock、完整精度服务、memory 模式写入和精确/近似结果分别记录。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

共同/共享依据：[CMOS-03](../00_cmos_periphery/NOTES.zh.md#CMOS-03)、[CMOS-07](../00_cmos_periphery/NOTES.zh.md#CMOS-07)。

<a id="SDCIM-01"></a>
## SDCIM-01 — D6CIM: 60.4-TOPS/W, 1.46-TOPS/mm2, 1005-Kb/mm2 Digital 6T-SRAM-Based Compute-in-Memory Macro Supporting 1-to-8b Fixed-Point Arithmetic in 28-nm CMOS

**核心** · 2023 · ESSCIRC, 413–416 · [全文](SDCIM-01_2023_D6CIM.pdf)

**身份与版本：** Jonghyun Oh, Chuan-Tung Lin, Mingoo Seok。Published paper。

**用途与结构：** 28 nm 数字 6T macro；128-bit 普通写入端口与 CIM 控制分开；8-bit 128×16 VMM 需要 64 个时钟，提供完整精度服务粒度。

**正文定位：** p.1，Fig.1、完整 VMM 步骤；pp.2–4，架构／测量。

**工艺/模式：** 直接的 28 nm 证据；精度按正文条件限定。

**使用限制：** 一个 clock 不是一次完整 8-bit VMM；写端口宽度不等于已量测独立写入周期。

**出版标识：** [DOI](https://doi.org/10.1109/ESSCIRC59616.2023.10268725)。

<a id="SDCIM-02"></a>
## SDCIM-02 — A Digital Bit-Reconfigurable Versatile Compute-In-Memory Macro for Machine Learning Acceleration

**补充** · 2023 · IEEE Transactions on Circuits and Systems II: Express Briefs · [全文](SDCIM-02_2023_BitReconfigurable_CIM.pdf)

**身份与版本：** Xin Zhang, Yuncheng Lu, Bo Wang, Tony Tae-Hyoung Kim。完整正式论文/技术资料。

**用途与结构：** 65 nm 数字 macro 给出重构运算、n-bit 加法、位串行乘法和 carry 写回的逐周期关系。

**正文定位：** pp.2–4，Figs.3–8；p.5，测量比较。

**工艺/模式：** 其他工艺的量级交叉参考（65 nm）；精度按正文条件限定。

**使用限制：** 精度与运算类型改变所需周期；不能把 65 nm headline TOPS/W 直接映射为共同 28 nm 服务。

**出版标识：** [DOI](https://doi.org/10.1109/tcsii.2023.3257058)。

<a id="SDCIM-03"></a>
## SDCIM-03 — A 1.041-Mb/mm^2 27.38-TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-less SRAM Compute-in-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications

**核心** · 2022 · 2022 IEEE International Solid- State Circuits Conference (ISSCC) · [全文](SDCIM-03_2022_DynamicLogic_INT8.pdf)

**身份与版本：** Bonan Yan, Jeng-Long Hsu, Pang-Cheng Yu, Chia-Chi Lee, Yaojun Zhang, Wenshuo Yue, Guoqiang Mei, Yuchao Yang, Yue Yang, Hai Li, Yiran Chen, Ru Huang。完整正式论文/技术资料。

**用途与结构：** 28 nm 动态逻辑数字 macro；先存权重再计算，8-bit 输入按八拍展开，并有可选 post-sum 维度。

**正文定位：** p.1，memory/CIM 模式、8-clock 展开；p.2，Figs.11.7.2–6。

**工艺/模式：** 直接的 28 nm 证据；精度按正文条件限定。

**使用限制：** 引言的普通 SRAM 小于 1 ns 是背景陈述；测得 clock 与完整精度输出须区分。memory 权重装载与 CIM 求值不自动重叠。

**出版标识：** [DOI](https://doi.org/10.1109/isscc42614.2022.9731545)。

<a id="SDCIM-04"></a>
## SDCIM-04 — A 28 nm 16-kb Sign-Extension-Less Digital-Compute-in-Memory Macro With Extension-Friendly Compute Units and Accuracy-Adjustable Adder-Tree

**补充** · 2024 · IEEE Transactions on Very Large Scale Integration (VLSI) Systems · [全文](SDCIM-04_2024_SignExtensionLess_DigitalCIM.pdf)

**身份与版本：** Xin Si, Fangyuan Dong, Shengnan He, Yuhui Shi, Anran Yin, Hui Gao, Xiang Li。完整正式论文/技术资料。

**用途与结构：** 28 nm 16-kb compact-6T 数字 MAC：128×128-bit SRAM 分为一个 signed-weight bank 与七个 unsigned-weight banks，128×2-bit 输入 buffer；8-bit 输入分四拍完成 signed INT8 MAC。ALC=0 是完整精度，其余配置控制近似加法器。memory 与 compute 模式分开。

**正文定位：** pp.1–3，II-A/III-A、Figs.1–6；p.4，Figs.7/10、Table I。

**工艺/模式：** 28 nm 设计/作者报告；无歧义证据为结构、模式和四拍展开；signed INT8，2-bit 输入/拍；完整/近似 adder 分模式。

**使用限制：** Fig.7 分列完整精度 6.4 ns 与近似 5.6 ns；不能把 5.6 ns 记为无损模式。摘要/正文及 Fig.10 内使用 fabricated/measured，但 IV-C 标题和 Fig.10 图注又标 simulation：性能来源标签不一致，保留作者报告，不能作为无歧义的独立硅测定值。普通写入绝对周期未给出。

**出版标识：** [DOI](https://doi.org/10.1109/tvlsi.2024.3418888)。

<a id="SDCIM-05"></a>
## SDCIM-05 — A 28-nm Digital Transpose SRAM Compute-in-Memory Macro With Accurate/Approximate Dual Mode for Floating-Point Edge Training and Inference

**核心** · 2026 · IEEE Journal of Solid-State Circuits · [全文](SDCIM-05_2026_DigitalTranspose_AccurateApprox.pdf)

**身份与版本：** Yiyang Yuan, Bingxin Zhang, Yiming Yang, Yishan Luo, Qirui Chen, Haitao Wang, Qihao Liu, Zhiming Chen, Hao Wu, Jinshan Yue, Shidong Lv, Xinghua Wang, Pui-In Mak, Xiaoran Li, Feng Zhang。完整正式论文/技术资料。

**用途与结构：** 实际 28 nm 数字 transpose SRAM；上下两组 cyclic-weight-mapping SRAM 与 bit-parallel MAC，共用 FF/BP 数据通路。普通读写为 32-bit 端口，计算时提供 256-bit 驻留向量；INT4/FP8 一 MAC 拍，INT8/BF16 将输入分段用两 MAC 拍。有 die photo、测试平台与按模式区分的结果。

**正文定位：** pp.3–5，III、Figs.4–7；pp.9–11，VI、Figs.19–23、Table III。

**工艺/模式：** 直接 28 nm 实测证据；配置/单位须服从明确的局部结构；INT4/8、FP8、BF16；FF/BP；accurate/approximate 分模式。

**使用限制：** Fig.6 省略 write 电路，32-bit 端口不直接给完整写周期。正文多处写 32 kB，但 Table III 写 32 Kb，后者与图示两组 64×64 个 4-bit cell 的局部结构一致；边界/容量换算须显式说明此差异。p.10 文字与 Table III 对 FP8 的 2.5/2.7 ns 精确/近似归属相反，不拼接模式指标。AHB/APB 外部服务与本地 MAC 分开。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2026.3679560)。

