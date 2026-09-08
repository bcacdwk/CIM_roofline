# 第一轮人工下载清单（V1）

已有并核验：**12 份主文**；本轮自动取得并核验：**14 份主文 + 3 份补充材料 + 2 份会议前作／作者报告**。这些文件均已归档，不需要重复下载。

第一批请协助取得 **18 个资料包**；其余 **10 个**先暂缓。FENOR-03 与 FENOR-04 合包，先取期刊版；已取得的接受稿不另外请求内容相同正式版。

请放入 `tasks/task1_table_i/rebuild/literature/` 下对应分类目录，具体文件名逐项给出。所有路径均从仓库根目录开始。补充材料按同名 `_Supplement.pdf` 保存；出版社若提供 ZIP 则用 `_Supplement.zip`。若已下载文件采用不同名字，可在回复中列 ID 与实际文件名，不必修改内容。

主文完整、题名和作者匹配的作者接受稿也可；无需绕过权限。若某项没有补充文件，只交主文即可。第一批到件后再由用户启动 R1；当前不进入正式参数提取。

优先顺序考虑证据缺口和互补性，不按每类平均分配。共同外围的 ADC 已有两篇全文、DAC IP 已取得；第一批补 DAC 负载机制、SRAM 普通读写及实际 CIM 读出连接，再补各介质关键阵列依据。

## A. 第一批优先下载

- [ ] **CMOS-03 — SRAM Assist Techniques for Operation in a Wide Voltage Range in 28-nm CMOS**；2012；IEEE Transactions on Circuits and Systems II: Express Briefs
  - DOI：[10.1109/tcsii.2012.2231015](https://doi.org/10.1109/tcsii.2012.2231015)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/6424019/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6424019)；[入口 2](https://citeseerx.ist.psu.edu/document?doi=8d786312b6f1a1727b8d26304236576dcc1f3f12&repid=rep1&type=pdf)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf`
  - 为何需要：读写 assist、WL 脉冲与 bitline 负载条件共同约束普通 SRAM 写入估计；可作为显式条件的参考设计依据，不能宣称其仿真假设是量产 compiler 保证值。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。DOI 登记与作者发表页一致；网页可读原文片段，作者 PDF 返回 404、CiteSeerX 连接超时。

- [ ] **CMOS-04 — A 28 nm Dual-Port SRAM Macro With Screening Circuitry Against Write-Read Disturb Failure Issues**；2011；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2011.2164021](https://doi.org/10.1109/jssc.2011.2164021)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/6008511/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6008511)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf`
  - 为何需要：独立核查双口 SRAM 的局部读写边界、感测与 write-read disturb 条件；补仅有 assist 仿真而无实际 macro 的不足。双口机制不能无条件代表单口 SRAM。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **CMOS-05 — A 28-nm 8-Bit 16-GS/ DAC With >60 dBc/>40 dBc SFDR Up To 2.3 GHz/5.4 GHz Using 4-Channel NRZ-Output-Overlapped Time-Interleaving**；2025；IEEE Transactions on Circuits and Systems II: Express Briefs
  - DOI：[10.1109/tcsii.2024.3518084](https://doi.org/10.1109/tcsii.2024.3518084)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10802956/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10802956)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf`
  - 为何需要：核查真实 28 nm 电流舵 DAC 的分辨率、输出方式、各子 DAC 节拍及负载条件，补 IP 简表缺少的电路机制。高带宽四路交织输出不是单个 CIM 字线驱动的直接替代；是否包含可用阶跃建立指标待全文判断。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。出版登记题名写作 16-GS/（缺 s）；此处保留登记形式，待正式 PDF 核对排印。

- [ ] **SACIM-04 — A Charge Domain SRAM Compute-in-Memory Macro With C-2C Ladder-Based 8-Bit MAC Unit in 22-nm FinFET Process for Edge Inference**；2023；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2022.3232601](https://doi.org/10.1109/jssc.2022.3232601)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10008405/)
  - 备用合法入口：[入口 1](https://rdorrance.com/publications/)；[入口 2](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10008405)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf`
  - 为何需要：Intel C-2C ladder 的完整 8-bit 电荷域 MAC 补独立团队证据，核查位并行输入、求值粒度与输出精度。22 nm 节拍不直接作为 28 nm 基线。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **MRAM-03 — A 1-Mb 28-nm 1T1MTJ STT-MRAM With Single-Cap Offset-Cancelled Sense Amplifier and In Situ Self-Write-Termination**；2019；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2018.2872584](https://doi.org/10.1109/jssc.2018.2872584)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/8493263/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8493263)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf`
  - 为何需要：1T1MTJ 存储 macro 的 self-write-termination 和 offset-cancelled sense amplifier 补完整写入终点及局部读出，避免将外部脉冲等同普通写周期。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **NAND-01 — Micron 3D NAND Flash Memory Technology**；2016；厂商技术产品简表，02/16
  - 官方页面：[出版／原厂入口](https://www.micron.com/products/storage/nand-flash/3d-nand/part-catalog)
  - 备用合法入口：[入口 1](https://assets.micron.com/adobe/assets/urn%3Aaaid%3Aaem%3A3e6db2c4-d096-425e-91f4-1355e5262cc3/renditions/original/as/3d-nand-flyer.pdf)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf`
  - 为何需要：官方表分别列 2b/c MLC 和 3b/c TLC 的 tR、tPROG、tBERS、页块与 plane 组织，可为完整普通存储操作提供粗粒度依据。是技术简表，详细约束仍需后续 datasheet 核查。
  - 下载内容：指定 3d-nand-flyer.pdf，02/16 PDF；若门户改版，请保留实际修订号。
  - 当前情况：官方 PDF 网页内容可读；本地文件未取得。官方 PDF 网页索引可读产品表，页脚 ©2016／02/16 已确认；本地 curl 返回 Request Rejected HTML。

- [ ] **NAND-02 — A 2Tb 4b/Cell 6-Plane 3D-Flash Memory with 37.6Gb/mm^2 Bit Density and >85MB/s Write Throughput**；2026；2026 IEEE International Solid-State Circuits Conference (ISSCC)
  - DOI：[10.1109/isscc49663.2026.11409136](https://doi.org/10.1109/isscc49663.2026.11409136)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/11409136/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=11409136)；[入口 2](https://www.kioxia.com/ja-jp/rd/technology/topics/topics-92.html)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf`
  - 为何需要：KIOXIA 第十代 QLC 原始芯片资料补 plane 并行与写入组织；题名 write throughput 仍需全文区分内部编程与 die 级数据路径。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **NAND-03 — A 321-Layer 2Tb 4b/cell 3D-NAND-Flash Memory with a 75MB/s Program Throughput**；2025；2025 IEEE International Solid-State Circuits Conference (ISSCC)
  - DOI：[10.1109/isscc49661.2025.10904748](https://doi.org/10.1109/isscc49661.2025.10904748)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10904748/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10904748)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf`
  - 为何需要：SK hynix 321 层 QLC 实际芯片补独立厂商依据，核对编程步骤、页／plane 组织及吞吐定义。其题名数值不能被旧稿误记为 KIOXIA 或 TLC。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **NAND-04 — System-Technology Codesign of 3-D NAND Flash-Based Compute-in-Memory Inference Engine**；2021；IEEE JXCDC 7(1), 61–69
  - DOI：[10.1109/jxcdc.2021.3093772](https://doi.org/10.1109/jxcdc.2021.3093772)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/9468674/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9468674)；[入口 2](https://www.researchgate.net/publication/352865690_System-Technology_Codesign_of_3-D_NAND_Flash-Based_Compute-in-Memory_Inference_Engine)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf`
  - 为何需要：解释 NAND 物理组织如何映射 CIM、外围共享与必要求值阶段；补商品页读与电流求和之间的估算桥梁。原始参数表图像必须补齐。
  - 下载内容：完整主文 PDF，特别是 Table 1 原图；如有补充材料一并获取。
  - 当前情况：题录／摘要可读，主文未取得。复用前轮原文网页线索；前轮 Table 1 原图未取得，本轮没有将它升级为已核实全文。

- [ ] **RRAM-05 — A 28-nm RRAM Computing-in-Memory Macro Using Weighted Hybrid 2T1R Cell Array and Reference Subtracting Sense Amplifier for AI Edge Inference**；2023；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2023.3280357](https://doi.org/10.1109/jssc.2023.3280357)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10145046/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10145046)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf`
  - 为何需要：foundry RRAM 的解耦存储／计算路径及 reference-subtracting sense amplifier 补另一类 28 nm 阵列读出结构，防止只依赖 NeuRRAM 单实现。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **MRAM-02 — A CMOS-integrated spintronic compute-in-memory macro for secure AI edge devices**；2023；Nature Electronics 6, 534–543
  - DOI：[10.1038/s41928-023-00994-0](https://doi.org/10.1038/s41928-023-00994-0)
  - 官方页面：[出版／原厂入口](https://doi.org/10.1038/s41928-023-00994-0)
  - 备用合法入口：[入口 1](https://www.nature.com/articles/s41928-023-00994-0)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf`
  - 为何需要：CMOS 集成 spintronic macro 补真实局部服务机制、精度和写入路径；与 Jung 的电阻求和实现分开核查。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **PCM-03 — A 40-nm, 2M-Cell, 8b-Precision, Hybrid SLC-MLC PCM Computing-in-Memory Macro with 20.5 - 65.0TOPS/W for Tiny-Al Edge Devices**；2022；2022 IEEE International Solid- State Circuits Conference (ISSCC)
  - DOI：[10.1109/isscc42614.2022.9731670](https://doi.org/10.1109/isscc42614.2022.9731670)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/9731670/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9731670)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf`
  - 为何需要：TSMC／NTHU PCM macro 补独立产业团队与 SLC/MLC 模式差异，核查写入、读出精度和求值服务，避免仅依 IBM 平台确定范围。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **FERAM-02 — Low Voltage and High Speed 1Xnm 1T1C FE-RAM with Ultra-Thin 5nm HZO**；2021；2021 IEEE International Electron Devices Meeting (IEDM)
  - DOI：[10.1109/iedm19574.2021.9720545](https://doi.org/10.1109/iedm19574.2021.9720545)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/9720545/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9720545)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf`
  - 为何需要：SK hynix 的超薄 HZO 1T1C FE-RAM 补实际低压读写与状态判读条件；需全文核对读取是否含恢复、操作粒度和偏置。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **FERAM-03 — SoC Compatible 1T1C FeRAM Memory Array Based on Ferroelectric Hf0.5Zr0.5O2**；2020；2020 IEEE Symposium on VLSI Technology
  - DOI：[10.1109/vlsitechnology18217.2020.9265063](https://doi.org/10.1109/vlsitechnology18217.2020.9265063)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/9265063/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9265063)；[入口 2](https://publica.fraunhofer.de/entities/publication/03fdad8b-f3a2-4201-9987-faacc3b81673)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf`
  - 为何需要：Sony／NaMLab／Fraunhofer 阵列集成研究补局部操作电路与 program/read 实验，避免只由电容切换脉冲估计 FeRAM 服务。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **FERAM-04 — NVDRAM: A 32Gb Dual Layer 3D Stacked Non-volatile Ferroelectric Memory with Near-DRAM Performance for Demanding AI Workloads**；2023；2023 International Electron Devices Meeting (IEDM)
  - DOI：[10.1109/iedm45741.2023.10413848](https://doi.org/10.1109/iedm45741.2023.10413848)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10413848/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10413848)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf`
  - 为何需要：Micron 的 HfO₂ 系非易失铁电存储补器件到三维阵列的实际读写与外围实现；需从整芯片中辨识可用于局部参考的边界，不能把标题 near-DRAM 当数值时序。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **GC-02 — An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications**；2018；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2018.2820145](https://doi.org/10.1109/jssc.2018.2820145)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/8356248/)
  - 备用合法入口：[入口 1](https://www.eng.biu.ac.il/temanad/publications/)；[入口 2](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8356248)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf`
  - 为何需要：28 nm bulk 4T gain-cell 存储原始实测补读写端口、retention 与刷新边界；approximate storage 的错误容忍条件不能忽略。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。Crossref 题名的内联 LaTeX 格式规范为 VT；未改变题意。

- [ ] **GC-04 — A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM**；2024；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2023.3339887](https://doi.org/10.1109/jssc.2023.3339887)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10360848/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10360848)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf`
  - 为何需要：电流编程动态 cascode 3T1C 多级 eDRAM 补不同于二值 2T1C 的写入／保持和求值步骤；保留其模拟状态接受条件。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **FENOR-04 — Efficient Large Scale Neural Network Acceleration With 3-D FeNOR-Based Computing-in-Memory Design**；2025；IEEE Transactions on Electron Devices
  - DOI：[10.1109/ted.2025.3554164](https://doi.org/10.1109/ted.2025.3554164)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10957835/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10957835)；[入口 2](https://ieeexplore.ieee.org/ielam/16/11004132/10957835-aam.pdf)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf`
  - 为何需要：优先较完整的期刊文；2024 会议版 FENOR-03 先不下载。公开接受稿 URL 已尝试，服务器返回 HTTP 418。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

## B. 暂缓候补（现在不必下载）

以下资料仍有价值，但先用已有全文和第一批内容判断具体缺口。这里列出可点击入口和最终路径，避免以后重新找题名。SDCIM-03 作者报告已取得，正式主文可暂缓；FENOR-03 仅为同包版本线索。

- [ ] **SACIM-03 — A 28nm 32Kb SRAM Computing-in-Memory Macro With Hierarchical Capacity Attenuator and Input Sparsity-Optimized ADC for 4b Mac Operation**；2023；IEEE Transactions on Circuits and Systems II: Express Briefs
  - DOI：[10.1109/tcsii.2023.3234620](https://doi.org/10.1109/tcsii.2023.3234620)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10008052/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10008052)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf`
  - 为何需要：2022 会议前作已自动取得，明确为仿真且已有 input-sparsity 方案，足够 R0 初筛。暂缓 2023 期刊文，R1 仅在前作不能覆盖所需条件时再补，核查扩展差异。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：相关 2022 会议前作已取得；2023 主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **SDCIM-02 — A Digital Bit-Reconfigurable Versatile Compute-In-Memory Macro for Machine Learning Acceleration**；2023；IEEE Transactions on Circuits and Systems II: Express Briefs
  - DOI：[10.1109/tcsii.2023.3257058](https://doi.org/10.1109/tcsii.2023.3257058)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10068798/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10068798)；[入口 2](https://repository.sutd.edu.sg/esploro/outputs/journalArticle/A-Digital-Bit-Reconfigurable-Versatile-Compute-In-Memory-Macro/9912748209846)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf`
  - 为何需要：可编程加法及位串行乘法提供独立实现，检查不同运算的完整服务粒度；65 nm 实测只支持结构和量级交叉核查。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **SDCIM-03 — A 1.041-Mb/mm^2 27.38-TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-less SRAM Compute-in-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications**；2022；2022 IEEE International Solid- State Circuits Conference (ISSCC)
  - DOI：[10.1109/isscc42614.2022.9731545](https://doi.org/10.1109/isscc42614.2022.9731545)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/9731545/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9731545)；[入口 2](https://scholars.duke.edu/publication/1519651)；[入口 3](https://www.icacworkshop.cn/2022/slides/ICAC_2022_14.3_Yan_Bonan.pdf)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf`
  - 为何需要：动态逻辑 ADC-less 28 nm macro 与 D6CIM 互补，核查预充／求值步骤、精度及数字控制节拍；不能把介绍段的通用 SRAM 速度当作本 macro 完整求值。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：同篇作者报告已取得；正式主文暂缺。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **NOR-01 — S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military**；2024；厂商 datasheet，002-18741 Rev. *E
  - 官方页面：[出版／原厂入口](https://www.infineon.com/dgdl/Infineon-S29GL01GS_S29GL512S_S29GL256S_S29GL128S_128_Mb_256_Mb_512_Mb_1_Gb_GL-S_MIRRORBIT_Flash_Parallel_3-DataSheet-v06_00-EN.pdf?fileId=8ac78c8c7d0d8da4017d0ee99af9726b)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf`
  - 为何需要：Infineon GL-S 并行 NOR 提供 random/page read、write-buffer、sector erase 和完成状态定义，补串行 NOR 之外的独立厂家依据。MirrorBit 的物理存储与模拟权重精度不混同。
  - 下载内容：指定 002-18741 Rev. *E，2024-09-04；官方 URL v06_00-EN PDF；若门户改版，请保留实际修订号。
  - 当前情况：官方 PDF 网页内容可读；本地文件未取得。官方 106 页 PDF 网页正文页 1 核验题名、文号、日期；直接下载为空。该链接实为军规版，不能当普通商规版本；保留其操作定义，温度／寿命／时序必须随产品条件。

- [ ] **NAND-05 — Optimal Design Methods to Transform 3D NAND Flash into a High-Density, High-Bandwidth and Low-Power Nonvolatile Computing in Memory (nvCIM) Accelerator for Deep-Learning Neural Networks (DNN)**；2019；IEDM, 38.1.1–38.1.4
  - DOI：[10.1109/iedm19573.2019.8993652](https://doi.org/10.1109/iedm19573.2019.8993652)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/8993652/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8993652)；[入口 2](https://ieee-iedm.org/wp-content/uploads/2026/05/2019-IEDM-Archive.pdf)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf`
  - 为何需要：产业团队原始 nvCIM 研究补 block／string 组织与输入读出映射，连接 NAND-04 所引用硬件；是否包含编程条件尚需全文。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **MRAM-04 — A 28nm 32Kb embedded 2T2MTJ STT-MRAM macro with 1.3ns read-access time for fast and reliable read applications**；2018；2018 IEEE International Solid - State Circuits Conference - (ISSCC)
  - DOI：[10.1109/isscc.2018.8310394](https://doi.org/10.1109/isscc.2018.8310394)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/8310394/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8310394)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf`
  - 为何需要：互补 2T2MTJ 局部读出补与 1T1MTJ 不同的面积／可靠性／感测组织；题名 read-access 指标仅是读入口，不能当完整多位 MVM。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **MRAM-05 — EMxxLX — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory**；2025；官方 datasheet，v3.4
  - 官方页面：[出版／原厂入口](https://www.everspin.com/design-support)
  - 备用合法入口：[入口 1](https://www.everspin.com/file/158451/download)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-05_2025_EMxxLX_v3p4.pdf`
  - 为何需要：商业 STT-MRAM 的字节读写、无需物理擦除及 NOR 兼容模拟命令用于更新方式核查。xSPI 速率仅是产品端口服务；工艺未由此 datasheet 证明为 28 nm。
  - 下载内容：指定 EMxxLX v3.4，©2025 PDF；若门户改版，请保留实际修订号。
  - 当前情况：官方 PDF 网页内容可读；本地文件未取得。网页工具可读 81 页官方 v3.4 PDF；直接下载返回 404，候补人工获取。

- [ ] **PCM-04 — Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing**；2017；Science
  - DOI：[10.1126/science.aao3212](https://doi.org/10.1126/science.aao3212)
  - 官方页面：[出版／原厂入口](https://www.science.org/doi/10.1126/science.aao3212)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf`
  - 为何需要：Sc-Sb-Te 原始研究用于解释材料／成核条件导致的极快写入报道。保留它作为条件性器件基线，不将单次晶化脉冲替代 GST 多级阵列完整写入。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **GC-05 — An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips**；2025；IEEE Journal of Solid-State Circuits
  - DOI：[10.1109/jssc.2024.3470215](https://doi.org/10.1109/jssc.2024.3470215)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/10716755/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10716755)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf`
  - 为何需要：16 nm 产业 gain-cell macro 的 integer／floating-point 两模式补现代控制及精度组织。对 28 nm 仅为结构与量级交叉参考，不直接移用速率。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

- [ ] **FENOR-06 — Gate Stack Engineering of 3D Oxide Channel FeNOR Memory with High-Speed and Reliabilitity**；2026；2026 10th IEEE Electron Devices Technology & Manufacturing Conference (EDTM)
  - DOI：[10.1109/edtm65772.2026.11498024](https://doi.org/10.1109/edtm65772.2026.11498024)
  - 官方页面：[出版／原厂入口](https://ieeexplore.ieee.org/document/11498024/)
  - 备用合法入口：[入口 1](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=11498024)
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf`
  - 为何需要：直接比较 3D oxide-channel FeNOR 的 MFS/MFIS/MIFS/MIFIS 栅堆栈，有助解释脉冲与状态窗口的差异。来自 Zhou 相关团队，只作为机制补充，不增加独立团队数量。
  - 下载内容：主文（完整图表）；同页 Supplementary Information／技术附录如有，也请一并保存。
  - 当前情况：题录／摘要可读，主文未取得。已核验出版身份；全文适用性和完整时序尚待审阅。

### 同包版本线索：先不发重复任务

- FENOR-03：[DOI: 10.1109/vlsitechnologyandcir46783.2024.10631352](https://doi.org/10.1109/vlsitechnologyandcir46783.2024.10631352) · [出版页面](https://ieeexplore.ieee.org/document/10631352/) · [机构／作者／原厂入口 1](https://scholar.nycu.edu.tw/en/publications/first-demonstration-of-beol-compatible-3d-vertical-fenor/)。优先 FENOR-04；仅当期刊未覆盖所需器件细节时再取会议版。拟保存 `tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf`。

取得文件后，请告知已完成的 ID。无需先提取数字、整理参数或替本轮决定统一外围延时。
