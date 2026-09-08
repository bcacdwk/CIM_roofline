# 08 — FeRAM（HfO₂-based）

主体为真实 HfO₂ 系 1T1C 电容阵列、C2FeRAM 机制与电容器件测量。破坏性读后恢复、两步行更新与混合 FeCAP/memristor 中的 FeCAP 证据分别标明。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="FERAM-01"></a>
## FERAM-01 — A 2-Transistor-2-Capacitor Ferroelectric Edge Compute-in-Memory Scheme with Disturb-Free Inference and High Endurance

**核心** · 2023 · IEEE Electron Device Letters 44(7), 1088–1091 · [全文](FERAM-01_2023_C2FeRAM.pdf)

**身份与版本：** Xiaoyang Ma, Shan Deng, Juejian Wu, Zijian Zhao, David Lehninger, Tarek Ali, Konrad Seidel, Sourav De, Xiyu He, Yiming Chen, Huazhong Yang, Vijaykrishnan Narayanan, Suman Datta, Thomas Kaempfe, Qing Luo, Kai Ni, Xueqing Li。作者接受稿；实际离散器件实验和电路/架构模型分开使用。

**用途与结构：** C2FeRAM 的 2T2C 路径解释非破坏读与电流求和；行写入明确先 write-0 再 write-1，MLC 需 verify；离散 FeCAP/MOS 实验支持器件机制。

**正文定位：** pp.2–3，Figs.3–6、II–III。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；HfO₂ 系 FeCAP；2T2C。

**使用限制：** 大阵列／网络 latency 为模型，3D 集成为提议；不能当作完整已流片 28 nm FeRAM CIM。非破坏性读也不消除浮置节点漏电恢复。

**出版标识：** [DOI](https://doi.org/10.1109/LED.2023.3274362)。

<a id="FERAM-02"></a>
## FERAM-02 — Low Voltage and High Speed 1Xnm 1T1C FE-RAM with Ultra-Thin 5nm HZO

**核心** · 2021 · 2021 IEEE International Electron Devices Meeting (IEDM) · [全文](FERAM-02_2021_UltrathinHZO_1T1C.pdf)

**身份与版本：** Minchul Sung, Kwangmyoung Rho, Jayong Kim, Junho Cheon, Kiyoung Choi, Dohee Kim, Hoseok Em, Gyeongcheol Park, Jungwook Woo, Yeongyu Lee, Jaehyeon Ko, Moonhoi Kim, Gwangyeob Lee, Seung Wook Ryu, Dong Sun Sheen, Yangsung Joo, Seiyon Kim, Chang Hyun Cho, Myung-Hee Na, Jinkook Kim。完整正式论文/技术资料。

**用途与结构：** SK hynix 8 Gb 1T1C、5 nm HZO 真正阵列；SAWAR 读后明确重写；write-recovery 扫描显示极化随写时间继续增加。

**正文定位：** pp.1–2，II-B／III-B；pp.3–4，Figs.3、8–10。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；5 nm HZO；1T1C FeRAM。

**使用限制：** 20 ns 对应部分极化响应，不是全部 cell/完整周期通用终点；5 nm 薄膜厚度不是 CMOS 工艺节点。

**出版标识：** [DOI](https://doi.org/10.1109/iedm19574.2021.9720545)。

<a id="FERAM-03"></a>
## FERAM-03 — SoC Compatible 1T1C FeRAM Memory Array Based on Ferroelectric Hf0.5Zr0.5O2

**核心** · 2020 · 2020 IEEE Symposium on VLSI Technology · [全文](FERAM-03_2020_SoC_1T1C_HZO.pdf)

**身份与版本：** Jun Okuno, Takafumi Kunihiro, Kenta Konishi, Hideki Maemura, Yusuke Shuto, Fumitaka Sugaya, Monica Materano, Tarek Ali, Kati Kuehnel, Konrad Seidel, Uwe Schroeder, Thomas Mikolajick, Masanori Tsukamoto, Taku Umebayashi。完整正式论文/技术资料。

**用途与结构：** Sony/NaMLab 的 64 kbit HZO 1T1C 实测读写 shmoo；Fig.9 明确读状态翻转和 data writeback 阶段。

**正文定位：** p.1，64 kbit array demonstration；p.2，Figs.8–11。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；Hf0.5Zr0.5O2；1T1C。

**使用限制：** 8 ns sense 与 14 ns write 是分别测量，不把单独 sense 当成含恢复的读周期；不是 28 nm 外围流片。

**出版标识：** [DOI](https://doi.org/10.1109/vlsitechnology18217.2020.9265063)。

<a id="FERAM-04"></a>
## FERAM-04 — NVDRAM: A 32Gb Dual Layer 3D Stacked Non-volatile Ferroelectric Memory with Near-DRAM Performance for Demanding AI Workloads

**核心** · 2023 · 2023 International Electron Devices Meeting (IEDM) · [全文](FERAM-04_2023_NVDRAM_32Gb.pdf)

**身份与版本：** N. Ramaswamy, A. Calderoni, J. Zahurak, G. Servalli, A. Chavan, S. Chhajed, M. Balakrishnan, M. Fischer, M. Hollander, D. P. Ettisserry, A. Liao, K. Karda, M. Jerry, M. Mariani, A. Visconti, B. R. Cook, B. D. Cook, D. Mills, A. Torsi, C. Mouli, E. Byers, M. Helm, S. Pawlowski, S. Shiratake, N. Chandrasekaran。完整正式论文/技术资料。

**用途与结构：** 正文明确 5.7 nm 掺杂 HfZrOx 电容、双层 1T1C；Fig.13 同时给 sensing、writeback、precharge 和完整 tRC，属于 HfO₂ 系电容 FeRAM。

**正文定位：** p.2，Memory Cell／Component Performance；p.4，Fig.13。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；HZO 1T1C 铁电存储；不归为普通 DRAM。

**使用限制：** 短 tWR 将部分恢复代价转到 tRP；不能摘取 10 ns 宣称完整写入结束。LPDDR5 兼容不等于 DRAM 相同阵列时序。

**出版标识：** [DOI](https://doi.org/10.1109/iedm45741.2023.10413848)。

<a id="FERAM-05"></a>
## FERAM-05 — Enhanced polarization switching characteristics of HfO2 ultrathin films via acceptor-donor co-doping

**补充** · 2024 · Nature Communications · [全文](FERAM-05_2024_Codoped_Hafnia.pdf)

**身份与版本：** Chao Zhou, Liyang Ma, Yanpeng Feng, Chang-Yang Kuo, Yu-Chieh Ku, Cheng-En Liu, Xianlong Cheng, Jingxuan Li, Yangyang Si, Haoliang Huang, Yan Huang, Hongjian Zhao, Chun-Fu Chang, Sujit Das, Shi Liu, Zuhuang Chen。本地正式 PDF（已核验身份）。

**用途与结构：** La/Ta 共掺 hafnia 原始材料测量提供厚度、偏置、成核/畴壁与极化终点，适合解释同类器件时间差异。

**正文定位：** pp.4–7，switching kinetics／Methods；已归档 SI。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；共掺杂 HfO₂ 铁电电容。

**使用限制：** 外延薄膜/电极/测量层级不同于集成 1T1C array；高速切换不是 macro 服务。

**出版标识：** [DOI](https://doi.org/10.1038/s41467-024-47194-8)。

**技术补充：** [SI](FERAM-05_2024_Codoped_Hafnia_Supplement.pdf)，34 页，已归档。

<a id="FERAM-06"></a>
## FERAM-06 — A ferroelectric–memristor memory for both training and inference

**补充** · 2025 · Nature Electronics · [全文](FERAM-06_2025_Ferroelectric_Memristor.pdf)

**身份与版本：** Michele Martemucci, François Rummens, Yannick Malot, Tifenn Hirtzlin, Olivier Guille, Simon Martin, Catherine Carabasse, Adrien F. Vincent, Sylvain Saïghi, Laurent Grenouillet, Damien Querlioz, Elisa Vianello。本地正式 PDF（已核验身份）。

**用途与结构：** 真实共集成 FeCAP 与 memristor 及权重转移实验，给 FeCAP 电压/时间扫描、读写节点与外部脉冲测量条件。

**正文定位：** pp.3–5，FeCAP/混合阵列；p.9，Methods；已归档 SI。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；Si:HfO₂ FeCAP 为本组主体；memristor 支路另区分。

**使用限制：** 推理主路径是 memristor；全突触含多 FeCAP 和两个 memristor，不能把混合推理性能归为纯 FeRAM CIM；网络部分为仿真。

**出版标识：** [DOI](https://doi.org/10.1038/s41928-025-01454-7)。

**技术补充：** [SI](FERAM-06_2025_Ferroelectric_Memristor_Supplement.pdf)，18 页，已归档。

