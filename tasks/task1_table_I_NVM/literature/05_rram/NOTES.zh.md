# 05 — RRAM

CIM 宏、产业 raw/P&V 与正式产品资料覆盖读出、写验、脉冲/终止和操作层级。binary 与模拟目标、SET/RESET、FORMING 与日常更新分开。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="RRAM-01"></a>
## RRAM-01 — A compute-in-memory chip based on resistive random-access memory

**核心** · 2022 · Nature 608, 504–512 · [全文](RRAM-01_2022_NeuRRAM.pdf)

**身份与版本：** Weier Wan, Rajkumar Kubendran, Clemens Schaefer, Sukru Burc Eryilmaz, Wenqiang Zhang, Dabin Wu, Stephen Deiss, Priyanka Raina, He Qian, Bin Gao, Siddharth Joshi, Huaqiang Wu, H.-S. Philip Wong, Gert Cauwenberghs。Published article including Methods and Extended Data。

**用途与结构：** NeuRRAM 正文含完整 set-read/reset-read 闭环、导电目标容差、超时条件与 MVM 实测；读／写测试条件可以分开记录。

**正文定位：** p.10，Methods：编程／控制；p.27，Extended Data Fig.12。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；模拟多级、差分权重。

**使用限制：** 1–10 ns 控制脉冲能力不能替代 Methods 中实际微秒级 program/verify 配置；网络级效果与 local MVM 分开。主文含所需 Methods/Extended Data。

**出版标识：** [DOI](https://doi.org/10.1038/s41586-022-04992-8)。

<a id="RRAM-02"></a>
## RRAM-02 — A 28 nm 576K RRAM-based computing-in-memory macro featuring hybrid programming with area efficiency of 2.82 TOPS/mm2

**核心** · 2025 · Journal of Semiconductors 46(6), 062304 · [全文](RRAM-02_2025_HybridProgramming.pdf)

**身份与版本：** Siqi Liu, Songtao Wei, Peng Yao, Dong Wu, Lu Jie, Sining Pan, Jianshi Tang, Bin Gao, He Qian, Huaqiang Wu。Publisher PDF; June 5, 2025。

**用途与结构：** 28 nm 实测 macro，分段 WL、单 cell verify、八步 ADC 与 1T1R/2T2R 混合闭环相互对应；提供程序步骤与容差。

**正文定位：** pp.3–6，Figs.2–8；后续芯片测试。

**工艺/模式：** 直接的 28 nm 证据（专用 RRAM 外围）；多级／2T2R 差分。

**使用限制：** 速度改善主要按平均脉冲数比较，不能从倍数独立得到绝对完整写周期。

**出版标识：** [DOI](https://doi.org/10.1088/1674-4926/24100017)。

<a id="RRAM-03"></a>
## RRAM-03 — High temperature stability embedded ReRAM for 2x nm node and beyond

**补充** · 2022 · 2022 IEEE International Memory Workshop (IMW) · [全文](RRAM-03_2022_Weebit_28nm.pdf)

**身份与版本：** G. Molas, G. Piccolboni, A. Bricalli, A. Verdy, I. Naot, Y. Cohen, A. Regev, I. Naveh, D. Deleruyelle, Q. Rafhay, N. Castellani, L. Reganaz, A. Persico, R. Segaud, J. F. Nodin, V. Meli, S. Martin, F. Andrieu, L. Grenouillet。Weebit 厂商托管作者接受稿，前附 IEEE 作者转载声明。

**用途与结构：** Weebit/CEA-Leti 实际阵列对照 raw 与 P&V 的分布，说明固定脉冲、温度、可靠性终点改变可用写策略。

**正文定位：** pp.2–5，raw reliability、读扰与 Program and verify。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；数字存储；多级适用性未主张。

**使用限制：** 重点是可靠性；读扰应力脉冲不是完整 array access。不能提供独立的完整 CIM 求值周期。

**出版标识：** [DOI](https://doi.org/10.1109/imw52921.2022.9779293)。

<a id="RRAM-04"></a>
## RRAM-04 — MB85AS4MT — Memory ReRAM 4M (512 K × 8) Bit SPI

**补充** · 2016 · 厂商 datasheet，DS501-00045-1v0-E · [全文](RRAM-04_2016_MB85AS4MT.pdf)

**身份与版本：** Fujitsu Semiconductor。本地正式 PDF（已核验身份）。

**用途与结构：** 正式 ReRAM 产品资料区分写 buffer、串行数据接收与非易失提交；tWC 表按数据翻转比例给出内部完整写周期。

**正文定位：** pp.7–13，WRITE/WIP；p.17，AC：tWC；pp.19–21，接口图。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；普通数字存储。

**使用限制：** 内部 tWC 为毫秒量级，不能用 5 MHz SPI 或单 cell ns 切换替换，也不能强行推广到其他 RRAM。

**文档编号：** DS501-00045-1v0-E，2016.12。

<a id="RRAM-05"></a>
## RRAM-05 — A 28-nm RRAM Computing-in-Memory Macro Using Weighted Hybrid 2T1R Cell Array and Reference Subtracting Sense Amplifier for AI Edge Inference

**核心** · 2023 · IEEE Journal of Solid-State Circuits · [全文](RRAM-05_2023_WeightedHybrid_2T1R.pdf)

**身份与版本：** Wang Ye, Linfang Wang, Zhidao Zhou, Junjie An, Weizeng Li, Hanghang Gao, Zhi Li, Jinshan Yue, Hongyang Hu, Xiaoxin Xu, Jianguo Yang, Jing Liu, Dashan Shang, Feng Zhang, Jinghui Tian, Chunmeng Dou, Qi Liu, Ming Liu。完整正式论文/技术资料。

**用途与结构：** 28 nm 2T1R 混合阵列，binary HRS/LRS 与不同晶体管尺寸构造空间权重；完整读流程含 PH0 稳定和 PH1–4 参考扣除。

**正文定位：** p.3，Fig.4；pp.5–7，Figs.10、18；测量环境。

**工艺/模式：** 直接的 28 nm 证据（专用 RRAM 外围）；binary HRS/LRS；2T1R 晶体管尺寸与多 subarray 的空间权重映射。

**使用限制：** Fig.18 实测 66 ns 与估计优化 13 ns 必须分列；测试板外部 DAC 供偏置；缺完整写入/verify 周期。

**出版标识：** [DOI](https://doi.org/10.1109/jssc.2023.3280357)。

<a id="RRAM-06"></a>
## RRAM-06 — A 40nm 2Mb ReRAM Macro with 85% Reduction in FORMING Time and 99% Reduction in Page-Write Time Using Auto-FORMING and Auto-Write Schemes

**核心** · 2019 · 2019 Symposium on VLSI Technology · [全文](RRAM-06_2019_AutoForming_AutoWrite.pdf)

**身份与版本：** Yen-Cheng Chiu, Han-Wen Hu, Li-Ya Lai, Tsung-Yuan Huang, Hui-Yao Kao, Kuang-Tang Chang, Mon-Shu Ho, Chung-Cheng Chou, Yu-Der Chih, Tsung-Yung Chang, Meng-Fan Chang。完整正式论文/技术资料。

**用途与结构：** 实际 40 nm 2 Mb bipolar ReRAM；两组 IO/column 控制、等待组内完成、地址跳过、timeout 和 FORMING/SET/RESET 终止机制清楚。HRPW 把 page RESET 放在 idle，再对所需 cell SET，支持显式更新步骤/资源占用建模。

**正文定位：** p.1 AF/ARST/ASET 与测量小节；p.2 Figs.3–10。

**工艺/模式：** 40 nm 专用外围；其他工艺交叉参考；精度按正文条件限定。

**使用限制：** Fig.9 使用 normalized time unit，Fig.10 也是归一化时间/相对改善；全文没有因此补出绝对 page 延时。99% 改善包含 hidden-RESET，不能解释为省掉 RESET，FORMING 也不能算作每次更新。

**出版标识：** [DOI](https://doi.org/10.23919/vlsit.2019.8776540)。

