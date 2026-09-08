# 03 — 2D NOR Flash

正式厂商资料提供字/页/sector 与内部 program/erase/BUSY，原始模拟 NOR 研究补细调与 CIM 联系。存储接口与阵列模拟读出是不同层级。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="NOR-01"></a>
## NOR-01 — S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military

**核心** · 2024 · 厂商 datasheet，002-18741 Rev. *E · [全文](NOR-01_2024_GL_S_MIRRORBIT_Military.pdf)

**身份与版本：** Infineon Technologies。完整正式论文/技术资料。

**用途与结构：** 完整厂商 datasheet 明确 512-byte 写 buffer、32-byte ECC page、128 KB erase sector；内置擦除含 pre-program，typ/max 和负载／温度脚注可追溯。

**正文定位：** pp.7、22–32；p.45，Table 16；AC timing 小节。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；数字 NOR／MirrorBit，军规产品条件；非模拟精度声明。

**使用限制：** 这是 65 nm GL-S 军规器件；effective per-word 数字是整 buffer 摊销值；读接口时序不是 CIM 模拟求值时间。

**文档编号：** 002-18741 Rev. *E，2024-09-04；官方 URL v06_00-EN。

<a id="NOR-02"></a>
## NOR-02 — W25Q128JV — 3V 128M-BIT Serial Flash Memory with Dual/Quad SPI

**核心** · 2019 · 厂商 datasheet，Revision G · [全文](NOR-02_2019_W25Q128JV_RevG.pdf)

**身份与版本：** Winbond Electronics。本地正式 PDF（已核验身份）。

**用途与结构：** Winbond Rev.G 给出 1–256-byte page program、4/32/64 KB 擦除、BUSY 完成定义及 typ/max；正文指出 Quad 输入加速可能被内部编程时间淹没。

**正文定位：** p.14，BUSY；pp.37–43，program／erase；pp.65–66，AC 表。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；普通数字 NOR（未作多级模拟精度假设）。

**使用限制：** SPI 传输率不能替代编程完成或 cell 读出；只支持普通 binary 存储模式的更新时间尺度。

**文档编号：** W25Q128JV Rev. G，2019-04-08。

<a id="NOR-03"></a>
## NOR-03 — SST26VF064B/SST26VF064BA — 2.5V/3.0V 64-Mbit Serial Quad I/O (SQI) Flash Memory

**补充** · 2022 · 厂商 datasheet，DS20005119K · [全文](NOR-03_2022_SST26VF064B_RevK.pdf)

**身份与版本：** Microchip Technology。本地正式 PDF（已核验身份）。

**用途与结构：** Microchip 独立产品系列补 page、erase、suspend/resume 与 self-timed BUSY；正式时序表和 SFDP 超时定义可交叉核查。

**正文定位：** pp.10–14，状态／命令；pp.25–31，编程／挂起；pp.45–49，AC；p.82，SFDP。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；普通数字 SuperFlash NOR。

**使用限制：** SFDP 最大 timeout 不应冒充 typ；与 NOR-04/05 同为 SST 相关生态，不将其全部视为独立器件团队。

**文档编号：** DS20005119K，March 2022。

<a id="NOR-04"></a>
## NOR-04 — Fast, Energy-Efficient, Robust, and Reproducible Mixed-Signal Neuromorphic Classifier Based on Embedded NOR Flash Memory Technology

**核心** · 2017 · IEDM, 6.5.1–6.5.4 · [全文](NOR-04_2017_EmbeddedNOR_Classifier.pdf)

**身份与版本：** Xinjie Guo, Farnood Merrikh Bayat, Mohammad Bavandpour, Michael Klachko, Mohammad Reza Mahmoodi, Mirko Prezioso, Konstantin K. Likharev, Dmitri B. Strukov。Author-hosted original manuscript。

**用途与结构：** 实际嵌入式 NOR 模拟分类器，区分输入串行装载与网络内部传播；权重细调、half-select disturb 和神经元外围均影响整体服务。

**正文定位：** pp.1–2，II–IV；pp.3–4，Figs.4–16。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；模拟调谐浮栅权重。

**使用限制：** 实测原型与更先进 ESF3 工艺预测分开；细调设定精度并非最精确单 cell 示范值；同 NOR-05 的研究关系不独立。

**证据关系：** 与 NOR-05 同团队/技术线；两篇分别补系统求值与细调方法。

**出版标识：** [DOI](https://doi.org/10.1109/IEDM.2017.8268341)。

<a id="NOR-05"></a>
## NOR-05 — Model-Based High-Precision Tuning of NOR Flash Memory Cells for Analog Computing Applications

**核心** · 2016 · Device Research Conference · [全文](NOR-05_2016_NOR_ModelBased_Tuning.pdf)

**身份与版本：** Farnood Merrikh Bayat, Xinjie Guo, Michael Klachko, N. Do, Konstantin K. Likharev, Dmitri B. Strukov。Author-hosted original manuscript。

**用途与结构：** 100-cell 实验提供 write-verify 算法、脉冲数与目标调谐精度的关系，是普通 Flash 到模拟权重更新的重要桥接。

**正文定位：** pp.1–2，模型与 Fig.1 调谐流程。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；模拟多级调谐。

**使用限制：** 固定脉冲数不是完整更新时间；不是大规模并行 array 写入保证；与 NOR-04 同团队。

**证据关系：** 与 NOR-04 同技术线；不重复计为独立器件交叉证据。

