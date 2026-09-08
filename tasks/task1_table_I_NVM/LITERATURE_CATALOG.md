# 文献目录

本地资料集已整理就绪：**55 份主文、4 份技术补充，共 59 份 PDF**。下表只列保留来源；全部主文已按估算用途审阅。点击 ID 查看正文要点，点击 PDF 直接阅读。

固定 ID 是引用标识，不要求连续；跳号不表示缺件。核心与补充表示支撑作用，均为有效资料；有参考价值不等于其所有数字都可直接用于统一设计。

## 00 — 28 nm CMOS 外围参考

用实测 SAR、普通 SRAM 局部服务和实际 CIM 宏共同建立外围参考。此组保留 3 份主文件，并复用 5 份 CIM 主文，形成 8 份共同依据；转换率、输入建立和完整求值周期不互相替代。

共享主文：[SACIM-03](literature/01_sram_acim/NOTES.zh.md#SACIM-03)、[SACIM-05](literature/01_sram_acim/NOTES.zh.md#SACIM-05)、[SDCIM-01](literature/02_sram_dcim/NOTES.zh.md#SDCIM-01)、[SDCIM-03](literature/02_sram_dcim/NOTES.zh.md#SDCIM-03)、[SDCIM-05](literature/02_sram_dcim/NOTES.zh.md#SDCIM-05)。这些 PDF 只保存一份。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [CMOS-02](literature/00_cmos_periphery/NOTES.zh.md#CMOS-02) | [A 28 nm CMOS 10 bit 100 MS/s Asynchronous SAR ADC with Low-Power Switching Procedure and Timing-Protection Scheme](https://doi.org/10.3390/electronics10222856)<br>2021 · Fang Tang, Qiyun Ma et al.<br>Electronics | 28 nm 外围服务、ADC 转换、输入建立 | 核心 | [PDF](literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf) |
| [CMOS-03](literature/00_cmos_periphery/NOTES.zh.md#CMOS-03) | [SRAM Assist Techniques for Operation in a Wide Voltage Range in 28-nm CMOS](https://doi.org/10.1109/tcsii.2012.2231015)<br>2012 · Brian Zimmer, Seng Oon Toh et al.<br>IEEE Transactions on Circuits and Systems II: Express Briefs | 28 nm 外围服务、读写时序、负载与驱动条件 | 核心 | [PDF](literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf) |
| [CMOS-07](literature/00_cmos_periphery/NOTES.zh.md#CMOS-07) | [Disturbance Aware Dynamic Power Reduction in Synchronous 2RW Dual-Port 8T SRAM by Self-Adjusting Wordline Pulse Timing](https://doi.org/10.1109/jssc.2022.3229828)<br>2023 · Yoshisato Yokoyama, Koji Nii et al.<br>IEEE Journal of Solid-State Circuits | 28 nm 外围服务、读写周期与端口条件 | 核心 | [PDF](literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf) |

## 01 — SRAM ACIM

电荷域 macro 补输入方式、转换共享、复位/建立和规定输出。不同工艺仅用作结构与条件交叉；普通 SRAM 写服务由共同组支持。

共享主文：[CMOS-03](literature/00_cmos_periphery/NOTES.zh.md#CMOS-03)、[CMOS-07](literature/00_cmos_periphery/NOTES.zh.md#CMOS-07)。这些 PDF 只保存一份。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [SACIM-01](literature/01_sram_acim/NOTES.zh.md#SACIM-01) | [Scalable and Programmable Neural Network Inference Accelerator Based on In-Memory Computing](https://doi.org/10.1109/JSSC.2021.3119018)<br>2022 · Hongyang Jia, Murat Ozatay et al.<br>IEEE JSSC 57(1), 198–211 | 完整多位求值、操作粒度与局部并行度、CIM 求值桥接 | 核心 | [PDF](literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf) |
| [SACIM-02](literature/01_sram_acim/NOTES.zh.md#SACIM-02) | [PICO-RAM: A PVT-Insensitive Analog Compute-In-Memory SRAM Macro With In Situ Multi-Bit Charge Computing and 6T Thin-Cell-Compatible Layout](https://doi.org/10.1109/jssc.2024.3422826)<br>2025 · Zhiyu Chen, Ziyuan Wen et al.<br>IEEE Journal of Solid-State Circuits | CIM 求值桥接、输入 DAC／ADC 共享、完整多位求值 | 核心 | [PDF](literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf) |
| [SACIM-03](literature/01_sram_acim/NOTES.zh.md#SACIM-03) | [A 28nm 32Kb SRAM Computing-in-Memory Macro With Hierarchical Capacity Attenuator and Input Sparsity-Optimized ADC for 4b Mac Operation](https://doi.org/10.1109/tcsii.2023.3234620)<br>2023 · Kanglin Xiao, Xiaoxin Cui et al.<br>IEEE Transactions on Circuits and Systems II: Express Briefs | 28 nm 外围服务、CIM 求值桥接、ADC 与局部读出 | 核心 | [PDF](literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf) |
| [SACIM-04](literature/01_sram_acim/NOTES.zh.md#SACIM-04) | [A Charge Domain SRAM Compute-in-Memory Macro With C-2C Ladder-Based 8-Bit MAC Unit in 22-nm FinFET Process for Edge Inference](https://doi.org/10.1109/jssc.2022.3232601)<br>2023 · Hechen Wang, Renzhi Liu et al.<br>IEEE Journal of Solid-State Circuits | CIM 求值桥接、完整多位求值、独立结构交叉核查 | 核心 | [PDF](literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf) |
| [SACIM-05](literature/01_sram_acim/NOTES.zh.md#SACIM-05) | [8-Bit Precision 6T SRAM Compute-in-Memory Macro Using Global Bitline-Combining Scheme for Edge AI Chips](https://doi.org/10.1109/tcsii.2023.3331375)<br>2024 · Jian-Wei Su, Pei-Jung Lu et al.<br>IEEE Transactions on Circuits and Systems II: Express Briefs | 28 nm 外围服务、完整精度求值、ADC 共享 | 核心 | [PDF](literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf) |

## 02 — SRAM DCIM

五篇全文覆盖位串行、两位/四位输入展开、动态逻辑、可调加法器及转置访问。把 clock、完整精度服务、memory 模式写入和精确/近似结果分别记录。

共享主文：[CMOS-03](literature/00_cmos_periphery/NOTES.zh.md#CMOS-03)、[CMOS-07](literature/00_cmos_periphery/NOTES.zh.md#CMOS-07)。这些 PDF 只保存一份。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [SDCIM-01](literature/02_sram_dcim/NOTES.zh.md#SDCIM-01) | [D6CIM: 60.4-TOPS/W, 1.46-TOPS/mm2, 1005-Kb/mm2 Digital 6T-SRAM-Based Compute-in-Memory Macro Supporting 1-to-8b Fixed-Point Arithmetic in 28-nm CMOS](https://doi.org/10.1109/ESSCIRC59616.2023.10268725)<br>2023 · Jonghyun Oh, Chuan-Tung Lin et al.<br>ESSCIRC, 413–416 | 28 nm 外围服务、数字累加／位串行、普通写入粒度 | 核心 | [PDF](literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf) |
| [SDCIM-02](literature/02_sram_dcim/NOTES.zh.md#SDCIM-02) | [A Digital Bit-Reconfigurable Versatile Compute-In-Memory Macro for Machine Learning Acceleration](https://doi.org/10.1109/tcsii.2023.3257058)<br>2023 · Xin Zhang, Yuncheng Lu et al.<br>IEEE Transactions on Circuits and Systems II: Express Briefs | 数字求值与控制、操作粒度、独立量级交叉核查 | 补充 | [PDF](literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf) |
| [SDCIM-03](literature/02_sram_dcim/NOTES.zh.md#SDCIM-03) | [A 1.041-Mb/mm^2 27.38-TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-less SRAM Compute-in-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications](https://doi.org/10.1109/isscc42614.2022.9731545)<br>2022 · Bonan Yan, Jeng-Long Hsu et al.<br>2022 IEEE International Solid- State Circuits Conference (ISSCC) | 28 nm 外围服务、数字求值与控制、完整精度输出 | 核心 | [PDF](literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf) |
| [SDCIM-04](literature/02_sram_dcim/NOTES.zh.md#SDCIM-04) | [A 28 nm 16-kb Sign-Extension-Less Digital-Compute-in-Memory Macro With Extension-Friendly Compute Units and Accuracy-Adjustable Adder-Tree](https://doi.org/10.1109/tvlsi.2024.3418888)<br>2024 · Xin Si, Fangyuan Dong et al.<br>IEEE Transactions on Very Large Scale Integration (VLSI) Systems | 数字求值与控制、精度与必要步骤、局部操作粒度、独立结构交叉核查 | 补充 | [PDF](literature/02_sram_dcim/SDCIM-04_2024_SignExtensionLess_DigitalCIM.pdf) |
| [SDCIM-05](literature/02_sram_dcim/NOTES.zh.md#SDCIM-05) | [A 28-nm Digital Transpose SRAM Compute-in-Memory Macro With Accurate/Approximate Dual Mode for Floating-Point Edge Training and Inference](https://doi.org/10.1109/jssc.2026.3679560)<br>2026 · Yiyang Yuan, Bingxin Zhang et al.<br>IEEE Journal of Solid-State Circuits | 数字求值与控制、精度与必要步骤、局部操作粒度、独立结构交叉核查 | 核心 | [PDF](literature/02_sram_dcim/SDCIM-05_2026_DigitalTranspose_AccurateApprox.pdf) |

## 03 — 2D NOR Flash

正式厂商资料提供字/页/sector 与内部 program/erase/BUSY，原始模拟 NOR 研究补细调与 CIM 联系。存储接口与阵列模拟读出是不同层级。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [NOR-01](literature/03_nor_2d/NOTES.zh.md#NOR-01) | [S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military](https://www.infineon.com/dgdl/Infineon-S29GL01GS_S29GL512S_S29GL256S_S29GL128S_128_Mb_256_Mb_512_Mb_1_Gb_GL-S_MIRRORBIT_Flash_Parallel_3-DataSheet-v06_00-EN.pdf?fileId=8ac78c8c7d0d8da4017d0ee99af9726b)<br>2024 · Infineon Technologies<br>厂商 datasheet，002-18741 Rev. *E | 读侧时间尺度、编程／擦除周期、字／buffer／sector 粒度 | 核心 | [PDF](literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf) |
| [NOR-02](literature/03_nor_2d/NOTES.zh.md#NOR-02) | [W25Q128JV — 3V 128M-BIT Serial Flash Memory with Dual/Quad SPI](https://www.winbond.com/hq/support/documentation/?__locale=en&pno=W25Q128JV)<br>2019 · Winbond Electronics<br>厂商 datasheet，Revision G | 编程／擦除周期、操作粒度、接口与内部 busy 区分 | 核心 | [PDF](literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf) |
| [NOR-03](literature/03_nor_2d/NOTES.zh.md#NOR-03) | [SST26VF064B/SST26VF064BA — 2.5V/3.0V 64-Mbit Serial Quad I/O (SQI) Flash Memory](https://www.microchip.com/en-us/product/SST26VF064B)<br>2022 · Microchip Technology<br>厂商 datasheet，DS20005119K | 编程／擦除周期、操作粒度、独立量级交叉核查 | 补充 | [PDF](literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf) |
| [NOR-04](literature/03_nor_2d/NOTES.zh.md#NOR-04) | [Fast, Energy-Efficient, Robust, and Reproducible Mixed-Signal Neuromorphic Classifier Based on Embedded NOR Flash Memory Technology](https://doi.org/10.1109/IEDM.2017.8268341)<br>2017 · Xinjie Guo, Farnood Merrikh Bayat et al.<br>IEDM, 6.5.1–6.5.4 | CIM 求值桥接、输入驱动与输出边界、阵列结构 | 核心 | [PDF](literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf) |
| [NOR-05](literature/03_nor_2d/NOTES.zh.md#NOR-05) | [Model-Based High-Precision Tuning of NOR Flash Memory Cells for Analog Computing Applications](https://web.ece.ucsb.edu/~strukov/papers/2016/DRCflash2016.pdf)<br>2016 · Farnood Merrikh Bayat, Xinjie Guo et al.<br>Device Research Conference | 写入／编程周期、擦除与更新方式、精度与 verify | 核心 | [PDF](literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf) |

## 04 — 3D NAND Flash

MLC/TLC、QLC 与 SLC 器件/模式分开。制造商芯片、实际 SLC 器件和 RC/外围模型互补；不使用 SSD 带宽代表 local NAND 服务。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [NAND-01](literature/04_nand_3d/NOTES.zh.md#NAND-01) | [Micron 3D NAND Flash Memory Technology](https://www.micron.com/products/storage/nand-flash/3d-nand/part-catalog)<br>2016 · Micron Technology<br>厂商技术产品简表，02/16 | 读侧时间尺度、编程／擦除周期、页／块／plane 粒度 | 核心 | [PDF](literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf) |
| [NAND-02](literature/04_nand_3d/NOTES.zh.md#NAND-02) | [A 2Tb 4b/Cell 6-Plane 3D-Flash Memory with 37.6Gb/mm^2 Bit Density and >85MB/s Write Throughput](https://doi.org/10.1109/isscc49663.2026.11409136)<br>2026 · Jayanth M. Thimmaiah, Ryuji Yamashita et al.<br>2026 IEEE International Solid-State Circuits Conference (ISSCC) | 编程周期、plane 并行条件、独立产品交叉核查 | 核心 | [PDF](literature/04_nand_3d/NAND-02_2026_Sandisk_KIOXIA_6Plane_QLC.pdf) |
| [NAND-03](literature/04_nand_3d/NOTES.zh.md#NAND-03) | [A 321-Layer 2Tb 4b/cell 3D-NAND-Flash Memory with a 75MB/s Program Throughput](https://doi.org/10.1109/isscc49661.2025.10904748)<br>2025 · Wanik Cho, Chanhui Jeong et al.<br>2025 IEEE International Solid-State Circuits Conference (ISSCC) | 编程周期、操作粒度与局部并行度、独立量级交叉核查 | 核心 | [PDF](literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf) |
| [NAND-04](literature/04_nand_3d/NOTES.zh.md#NAND-04) | [System-Technology Codesign of 3-D NAND Flash-Based Compute-in-Memory Inference Engine](https://doi.org/10.1109/jxcdc.2021.3093772)<br>2021 · Wonbo Shim, Shimeng Yu<br>IEEE JXCDC 7(1), 61–69 | CIM 求值桥接、字线／位线与重构、局部阵列边界 | 核心 | [PDF](literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf) |
| [NAND-05](literature/04_nand_3d/NOTES.zh.md#NAND-05) | [Optimal Design Methods to Transform 3D NAND Flash into a High-Density, High-Bandwidth and Low-Power Nonvolatile Computing in Memory (nvCIM) Accelerator for Deep-Learning Neural Networks (DNN)](https://doi.org/10.1109/iedm19573.2019.8993652)<br>2019 · Hang-Ting Lue, Po-Kai Hsu et al.<br>IEDM, 38.1.1–38.1.4 | CIM 求值桥接、局部并行组织、NAND 结构依据 | 核心 | [PDF](literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf) |

## 05 — RRAM

CIM 宏、产业 raw/P&V 与正式产品资料覆盖读出、写验、脉冲/终止和操作层级。binary 与模拟目标、SET/RESET、FORMING 与日常更新分开。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [RRAM-01](literature/05_rram/NOTES.zh.md#RRAM-01) | [A compute-in-memory chip based on resistive random-access memory](https://doi.org/10.1038/s41586-022-04992-8)<br>2022 · Weier Wan, Rajkumar Kubendran et al.<br>Nature 608, 504–512 | CIM 求值桥接、闭环编程、状态精度与验证 | 核心 | [PDF](literature/05_rram/RRAM-01_2022_NeuRRAM.pdf) |
| [RRAM-02](literature/05_rram/NOTES.zh.md#RRAM-02) | [A 28 nm 576K RRAM-based computing-in-memory macro featuring hybrid programming with area efficiency of 2.82 TOPS/mm2](https://doi.org/10.1088/1674-4926/24100017)<br>2025 · Siqi Liu, Songtao Wei et al.<br>Journal of Semiconductors 46(6), 062304 | 28 nm 读出、写入／编程方式、操作粒度 | 核心 | [PDF](literature/05_rram/RRAM-02_2025_HybridProgramming.pdf) |
| [RRAM-03](literature/05_rram/NOTES.zh.md#RRAM-03) | [High temperature stability embedded ReRAM for 2x nm node and beyond](https://doi.org/10.1109/imw52921.2022.9779293)<br>2022 · G. Molas, G. Piccolboni et al.<br>2022 IEEE International Memory Workshop (IMW) | 器件编程条件、binary 存储、独立产业交叉核查 | 补充 | [PDF](literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf) |
| [RRAM-04](literature/05_rram/NOTES.zh.md#RRAM-04) | [MB85AS4MT — Memory ReRAM 4M (512 K × 8) Bit SPI](https://www.fujitsu.com/global/documents/products/devices/semiconductor/memory/reram/MB85AS4MT-DS501-00045-1v0-E.pdf)<br>2016 · Fujitsu Semiconductor<br>厂商 datasheet，DS501-00045-1v0-E | 普通写入完成、操作粒度、存储时序定义 | 补充 | [PDF](literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf) |
| [RRAM-05](literature/05_rram/NOTES.zh.md#RRAM-05) | [A 28-nm RRAM Computing-in-Memory Macro Using Weighted Hybrid 2T1R Cell Array and Reference Subtracting Sense Amplifier for AI Edge Inference](https://doi.org/10.1109/jssc.2023.3280357)<br>2023 · Wang Ye, Linfang Wang et al.<br>IEEE Journal of Solid-State Circuits | 28 nm 专用感测、CIM 求值桥接、局部并行组织 | 核心 | [PDF](literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf) |
| [RRAM-06](literature/05_rram/NOTES.zh.md#RRAM-06) | [A 40nm 2Mb ReRAM Macro with 85% Reduction in FORMING Time and 99% Reduction in Page-Write Time Using Auto-FORMING and Auto-Write Schemes](https://doi.org/10.23919/vlsit.2019.8776540)<br>2019 · Yen-Cheng Chiu, Han-Wen Hu et al.<br>2019 Symposium on VLSI Technology | 完整写入周期、局部并行、RESET/SET 控制 | 核心 | [PDF](literature/05_rram/RRAM-06_2019_AutoForming_AutoWrite.pdf) |

## 06 — MRAM

电阻求和和 bitcell 数字 CIM 分成不同参考机制；普通存储宏和正式 datasheet 支持读写与更新语义。互补 MTJ、两步写入、读验与位串行不能略去。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [MRAM-01](literature/06_mram/NOTES.zh.md#MRAM-01) | [A crossbar array of magnetoresistive memory devices for in-memory computing](https://doi.org/10.1038/s41586-021-04196-6)<br>2022 · Seungchul Jung, Hyungwoo Lee et al.<br>Nature 601, 211–216 | 读写服务、CIM 求值桥接、互补单元与局部并行度 | 核心 | [PDF](literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf) |
| [MRAM-03](literature/06_mram/NOTES.zh.md#MRAM-03) | [A 1-Mb 28-nm 1T1MTJ STT-MRAM With Single-Cap Offset-Cancelled Sense Amplifier and In Situ Self-Write-Termination](https://doi.org/10.1109/jssc.2018.2872584)<br>2019 · Qing Dong, Zhehong Wang et al.<br>IEEE Journal of Solid-State Circuits | 写入完成与终止、感测服务、28 nm 专用外围 | 核心 | [PDF](literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf) |
| [MRAM-04](literature/06_mram/NOTES.zh.md#MRAM-04) | [A 28nm 32Kb embedded 2T2MTJ STT-MRAM macro with 1.3ns read-access time for fast and reliable read applications](https://doi.org/10.1109/isscc.2018.8310394)<br>2018 · Tzu-Hsien Yang, Kai-Xiang Li et al.<br>2018 IEEE International Solid - State Circuits Conference - (ISSCC) | 读侧时间尺度、感测与操作粒度、结构交叉核查 | 补充 | [PDF](literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf) |
| [MRAM-05](literature/06_mram/NOTES.zh.md#MRAM-05) | [EMxxxLX/B/HR — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory](https://www.everspin.com/design-support)<br>2026 · Everspin Technologies<br>Everspin datasheet, EMxxxLX/B/HR v3.7 | 直接更新语义、字节粒度、普通存储交叉核查 | 补充 | [PDF](literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf) |
| [MRAM-06](literature/06_mram/NOTES.zh.md#MRAM-06) | [A lossless and fully parallel spintronic compute-in-memory macro for artificial intelligence chips](https://doi.org/10.1038/s41928-025-01479-y)<br>2025 · Humiao Li, Zheng Chai et al.<br>Nature Electronics | CIM 求值桥接、互补权重写入步骤、独立团队核查 | 核心 | [PDF](literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM.pdf) · [SI](literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM_Supplement.pdf) |

## 07 — PCM

两类 IBM 芯片及逐行闭环、混合 SLC/MLC 宏和独立材料/器件测量互补。SET/RESET、连续模拟权重、离散状态及脉冲测试终点分别使用。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [PCM-01](literature/07_pcm/NOTES.zh.md#PCM-01) | [A 64-core mixed-signal in-memory compute chip based on phase-change memory for deep neural network inference](https://doi.org/10.1038/s41928-023-01010-1)<br>2023 · Manuel Le Gallo, Riduan Khaddam-Aljameh et al.<br>Nature Electronics 6, 680–693 | CIM 求值桥接、并行 writehead、多级编程与校验 | 核心 | [PDF](literature/07_pcm/PCM-01_2023_PCM64_Core.pdf) |
| [PCM-02](literature/07_pcm/NOTES.zh.md#PCM-02) | [An analog-AI chip for energy-efficient speech recognition and transcription](https://doi.org/10.1038/s41586-023-06337-5)<br>2023 · S. Ambrogio, P. Narayanan et al.<br>Nature | CIM 求值桥接、行并行编程、局部与系统边界 | 核心 | [PDF](literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf) |
| [PCM-03](literature/07_pcm/NOTES.zh.md#PCM-03) | [A 40-nm, 2M-Cell, 8b-Precision, Hybrid SLC-MLC PCM Computing-in-Memory Macro with 20.5 - 65.0TOPS/W for Tiny-AI Edge Devices](https://doi.org/10.1109/isscc42614.2022.9731670)<br>2022 · Win-San Khwa, Yen-Cheng Chiu et al.<br>2022 IEEE International Solid- State Circuits Conference (ISSCC) | CIM 求值桥接、binary／multi-level、操作粒度 | 核心 | [PDF](literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf) |
| [PCM-04](literature/07_pcm/NOTES.zh.md#PCM-04) | [Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing](https://doi.org/10.1126/science.aao3212)<br>2017 · Feng Rao, Keyuan Ding et al.<br>Science | 器件写入时间尺度、材料差异、独立量级交叉核查 | 补充 | [PDF](literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf) · [SI](literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf) |
| [PCM-05](literature/07_pcm/NOTES.zh.md#PCM-05) | [Phase Change Memory Drift Compensation in Spiking Neural Networks Using a Non-Linear Current Scaling Strategy](https://doi.org/10.3390/jlpea14040050)<br>2024 · Joao Henrique Quintino Palhares, Nikhil Garg et al.<br>Journal of Low Power Electronics and Applications | SET／RESET 与多级编程、测试条件、独立量级交叉核查 | 补充 | [PDF](literature/07_pcm/PCM-05_2024_PCM_Drift.pdf) |
| [PCM-06](literature/07_pcm/NOTES.zh.md#PCM-06) | [Fully On-Chip MAC at 14 nm Enabled by Accurate Row-Wise Programming of PCM-Based Weights and Parallel Vector-Transport in Duration-Format](https://doi.org/10.1109/ted.2021.3115993)<br>2021 · P. Narayanan, S. Ambrogio et al.<br>IEEE Transactions on Electron Devices | 写入闭环、并行粒度、编程控制与读验 | 核心 | [PDF](literature/07_pcm/PCM-06_2021_RowWise_ClosedLoopProgramming.pdf) |

## 08 — FeRAM（HfO₂-based）

主体为真实 HfO₂ 系 1T1C 电容阵列、C2FeRAM 机制与电容器件测量。破坏性读后恢复、两步行更新与混合 FeCAP/memristor 中的 FeCAP 证据分别标明。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [FERAM-01](literature/08_feram_hfo2/NOTES.zh.md#FERAM-01) | [A 2-Transistor-2-Capacitor Ferroelectric Edge Compute-in-Memory Scheme with Disturb-Free Inference and High Endurance](https://doi.org/10.1109/LED.2023.3274362)<br>2023 · Xiaoyang Ma, Shan Deng et al.<br>IEEE Electron Device Letters 44(7), 1088–1091 | CIM 求值桥接、读／恢复机制、写入步骤 | 核心 | [PDF](literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf) |
| [FERAM-02](literature/08_feram_hfo2/NOTES.zh.md#FERAM-02) | [Low Voltage and High Speed 1Xnm 1T1C FE-RAM with Ultra-Thin 5nm HZO](https://doi.org/10.1109/iedm19574.2021.9720545)<br>2021 · Minchul Sung, Kwangmyoung Rho et al.<br>2021 IEEE International Electron Devices Meeting (IEDM) | 读写时间尺度、1T1C 阵列操作、低压条件 | 核心 | [PDF](literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf) |
| [FERAM-03](literature/08_feram_hfo2/NOTES.zh.md#FERAM-03) | [SoC Compatible 1T1C FeRAM Memory Array Based on Ferroelectric Hf0.5Zr0.5O2](https://doi.org/10.1109/vlsitechnology18217.2020.9265063)<br>2020 · Jun Okuno, Takafumi Kunihiro et al.<br>2020 IEEE Symposium on VLSI Technology | 阵列读写、局部操作粒度、独立交叉核查 | 核心 | [PDF](literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf) |
| [FERAM-04](literature/08_feram_hfo2/NOTES.zh.md#FERAM-04) | [NVDRAM: A 32Gb Dual Layer 3D Stacked Non-volatile Ferroelectric Memory with Near-DRAM Performance for Demanding AI Workloads](https://doi.org/10.1109/iedm45741.2023.10413848)<br>2023 · N. Ramaswamy, A. Calderoni et al.<br>2023 International Electron Devices Meeting (IEDM) | 完整读写服务、操作粒度、大阵列交叉核查 | 核心 | [PDF](literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf) |
| [FERAM-05](literature/08_feram_hfo2/NOTES.zh.md#FERAM-05) | [Enhanced polarization switching characteristics of HfO2 ultrathin films via acceptor-donor co-doping](https://doi.org/10.1038/s41467-024-47194-8)<br>2024 · Chao Zhou, Liyang Ma et al.<br>Nature Communications | 器件切换时间尺度、测试偏置与终点、独立交叉核查 | 补充 | [PDF](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf) · [SI](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia_Supplement.pdf) |
| [FERAM-06](literature/08_feram_hfo2/NOTES.zh.md#FERAM-06) | [A ferroelectric–memristor memory for both training and inference](https://doi.org/10.1038/s41928-025-01454-7)<br>2025 · Michele Martemucci, François Rummens et al.<br>Nature Electronics | FeCAP 阵列写入、并行粒度、训练／推理桥接 | 补充 | [PDF](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf) · [SI](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor_Supplement.pdf) |

## 09 — Gain-cell eDRAM

2T1C/4T/3T1C 结构、硅/oxide 通道、模拟/数字求值分别处理。保持分布、刷新占用与 storage/stationary 更新关系共同约束服务。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [GC-01](literature/09_gain_cell_edram/NOTES.zh.md#GC-01) | [Gain-Cell CIM: Leakage and Bitline Swing Aware 2T1C Gain-Cell eDRAM Compute in Memory Design with Bitline Precharge DACs and Compact Schmitt Trigger ADCs](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338)<br>2022 · Shanshan Xie, Can Ni et al.<br>VLSI Symposium, 112–113 | 完整求值、读写端口、保持与泄漏 | 核心 | [PDF](literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf) |
| [GC-02](literature/09_gain_cell_edram/NOTES.zh.md#GC-02) | [An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications](https://doi.org/10.1109/jssc.2018.2820145)<br>2018 · Robert Giterman, Alexander Fish et al.<br>IEEE Journal of Solid-State Circuits | 28 nm 读写服务、保持／刷新、普通 gain-cell 粒度 | 核心 | [PDF](literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf) |
| [GC-03](literature/09_gain_cell_edram/NOTES.zh.md#GC-03) | [Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform](https://doi.org/10.1109/TED.2024.3372938)<br>2024 · Shuhan Liu, Koustav Jana et al.<br>IEEE Transactions on Electron Devices 71(5), 3329–3335 | 读写设计方法、保持与刷新、28 nm 映射桥接 | 核心 | [PDF](literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf) |
| [GC-04](literature/09_gain_cell_edram/NOTES.zh.md#GC-04) | [A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM](https://doi.org/10.1109/jssc.2023.3339887)<br>2024 · Jiahao Song, Xiyuan Tang et al.<br>IEEE Journal of Solid-State Circuits | 写入建立、多级状态、CIM 求值与保持 | 核心 | [PDF](literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf) |
| [GC-05](literature/09_gain_cell_edram/NOTES.zh.md#GC-05) | [An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips](https://doi.org/10.1109/jssc.2024.3470215)<br>2025 · Ping-Chun Wu, Win-San Khwa et al.<br>IEEE Journal of Solid-State Circuits | 完整精度求值、局部并行度、近期产业交叉核查 | 核心 | [PDF](literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf) |

## 10 — 3D FeNOR／vertical FeFET

保留四篇直接相关的器件/小阵列和栅堆栈研究，包括指定的 Zhou 2025/2026。NOR 与 AND 拓扑、半选/相邻扰动、器件脉冲与宏级模拟分开。

| ID / 正文笔记 | 文献 | 支撑作用 | 等级 | 文件 |
|---|---|---|---|---|
| [FENOR-01](literature/10_fenor_3d/NOTES.zh.md#FENOR-01) | [3D NOR-type FeFETs with Record Endurance of 10^11, Fast Erase of 50 ns, and Immediate Read-After-Write for In-Memory Learning](https://doi.org/10.23919/vlsitechnologyandcir65189.2025.11074820)<br>2025 · Yuejia Zhou, Runteng Zhu et al.<br>Symposium on VLSI Technology and Circuits | 器件读写时间尺度、更新步骤、局部阵列结构 | 核心 | [PDF](literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf) |
| [FENOR-02](literature/10_fenor_3d/NOTES.zh.md#FENOR-02) | [3D Vertical FeFET Array with Record Endurance (>10^12), Fast Writing (±2V, 20 ns), Disturb Immunity, and Kb-scale Verification for High Density 1T RAM](https://doi.org/10.1109/vlsitechnologyandcir65830.2026.11577291)<br>2026 · Yuejia Zhou, Yuancheng Yang et al.<br>Symposium on VLSI Technology and Circuits T11.1 | 器件读写、写扰与并行选择条件、局部阵列验证 | 核心 | [PDF](literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf) |
| [FENOR-04](literature/10_fenor_3d/NOTES.zh.md#FENOR-04) | [Efficient Large Scale Neural Network Acceleration With 3-D FeNOR-Based Computing-in-Memory Design](https://doi.org/10.1109/ted.2025.3554164)<br>2025 · Yang Feng, Dong Zhang et al.<br>IEEE Transactions on Electron Devices | CIM 求值桥接、局部读出／并行条件、独立团队交叉核查 | 核心 | [PDF](literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf) |
| [FENOR-06](literature/10_fenor_3d/NOTES.zh.md#FENOR-06) | [Gate Stack Engineering of 3D Oxide Channel FeNOR Memory with High-Speed and Reliabilitity](https://doi.org/10.1109/edtm65772.2026.11498024)<br>2026 · Yuejia Zhou, Ru Huang et al.<br>2026 10th IEEE Electron Devices Technology & Manufacturing Conference (EDTM) | 器件读写与偏置、栅堆栈差异、更新约束 | 核心 | [PDF](literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf) |
