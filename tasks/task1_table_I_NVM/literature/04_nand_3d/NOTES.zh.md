# 04 — 3D NAND Flash

MLC/TLC、QLC 与 SLC 器件/模式分开。制造商芯片、实际 SLC 器件和 RC/外围模型互补；不使用 SSD 带宽代表 local NAND 服务。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="NAND-01"></a>
## NAND-01 — Micron 3D NAND Flash Memory Technology

**核心** · 2016 · 厂商技术产品简表，02/16 · [全文](NAND-01_2016_Micron_3DNAND.pdf)

**身份与版本：** Micron Technology。完整正式论文/技术资料。

**用途与结构：** Micron 官方资料虽为两页 flyer，正文实际有 MLC/TLC 分列的 read/program/erase typ/max、页／块尺寸和具体料号，值得保留。

**正文定位：** p.2，产品／时序表。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；MLC 2b/c；TLC 3b/c（分列）。

**使用限制：** 不是完整部件 datasheet，部分并行命令／busy 约束仍缺；2016 年而非近期下载年。

**文档编号：** 3d-nand-flyer.pdf，02/16。

<a id="NAND-02"></a>
## NAND-02 — A 2Tb 4b/Cell 6-Plane 3D-Flash Memory with 37.6Gb/mm^2 Bit Density and >85MB/s Write Throughput

**核心** · 2026 · 2026 IEEE International Solid-State Circuits Conference (ISSCC) · [全文](NAND-02_2026_Sandisk_KIOXIA_6Plane_QLC.pdf)

**身份与版本：** Jayanth M. Thimmaiah, Ryuji Yamashita, In-Soo Yoon, Jason Li, Cynthia Hsu, Takuya Ariki, Naoki Ookuma, Yosuke Kato, Koichiro Hayashi, Kazuki Yamauchi, Indra K V, Masahiro Kano, Sirisha Bhamidipati, Sneha Bhatia, Seema Malhotra, Naoki Ojima, Ella Wu, Zhiyong Yang, Frank W. Tsai, Mathias Bayle, Naoyuki Minami, Yasuyuki Fujihara, Kei Kitamura, Tomofumi Kitani, Takuyo Kodama, Takaya Handa, Naoaki Kanagawa, Yuki Ishizaki, Susumu Fujimura, Yoshinao Suzuki, Mario Sako, Yumi Higashi, Yoshihisa Watanabe, Toshiyuki Kouchi, Aravinth V, Chin-Yi Chen, Xiang Yang, Guirong Liang, Jenny Wang。完整正式论文/技术资料。

**用途与结构：** Sandisk/KIOXIA 2026 原始 QLC 芯片；六 plane、物理/逻辑 page 区别、verify 与读搜索明确，还含 QLC 芯片的 SLC burst 模式。

**正文定位：** p.1，架构与模式；pp.2–3，Figs.15.1.1–7。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；QLC 4b/c，6-plane；另含 SLC burst 操作模式，分别使用。

**使用限制：** die program throughput 包含内部并行；SLC burst 不是独立 SLC 产品；完整 erase 条件仍不足。

**出版标识：** [DOI](https://doi.org/10.1109/isscc49663.2026.11409136)。

<a id="NAND-03"></a>
## NAND-03 — A 321-Layer 2Tb 4b/cell 3D-NAND-Flash Memory with a 75MB/s Program Throughput

**核心** · 2025 · 2025 IEEE International Solid-State Circuits Conference (ISSCC) · [全文](NAND-03_2025_SKhynix_321Layer_QLC.pdf)

**身份与版本：** Wanik Cho, Chanhui Jeong, Jongwoo Kim, Jongseok Jung, Keunseon Ahn, Jayoon Goo, Sangkyu Lee, Kayoung Cho, Tei Cho, Dauni Kim, Gwan Park, Yushin Ahn, Sooyeol Chai, Gwihan Ko, Sunyoung Jung, Eunwoo Jo, Taehun Park, Jinhyun Ban, Cheoljoong Park, Jae Hyun Park, Sanghoon Oh, Sojin Jeong, Youngjun Kwak, Kyungsoo Jeong, Jinyeop Kim, Minchol Shin, Eunho Yang, Taisik Shin, Youngil Kim, Jiseong Mun, Chanyang Ryu, Huihyeon Park, Changwan Ha, Jong Tai Park, Peng Zhang, Sooyong Park, Rezaul Haque, Hang Tian, Sunghwa Ok, Wonbeom Choi, Junyoun Lim, Dongkyu Yoon, Sechun Park, Wonsun Park, Kichang Gwon, Seungpil Lee, Hwang Huh, Woopyo Jeong, Jungdal Choi。完整正式论文/技术资料。

**用途与结构：** SK hynix 321-layer QLC 实际芯片，给出 page-program 时间、六 plane 与 page 大小；HV 供电、WL 电阻与干扰条件可支持特殊驱动分析。

**正文定位：** p.1，programming／HV 配置；p.2，Fig.30.5.6。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；QLC 4b/c（不是 TLC）。

**使用限制：** 75 MB/s 是 die 并行 program 结果；不能当作单 page latency 或外部 I/O 速度。

**出版标识：** [DOI](https://doi.org/10.1109/isscc49661.2025.10904748)。

<a id="NAND-04"></a>
## NAND-04 — System-Technology Codesign of 3-D NAND Flash-Based Compute-in-Memory Inference Engine

**核心** · 2021 · IEEE JXCDC 7(1), 61–69 · [全文](NAND-04_2021_NAND_Codesign.pdf)

**身份与版本：** Wonbo Shim, Shimeng Yu。完整正式论文/技术资料。

**用途与结构：** 给出 NAND 串读、映射、64-block subarray 边界和 RC／HSPICE 求值方法，可复用估算思路。

**正文定位：** pp.2–4，II、Table 1、Fig.3；后续建模小节。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；CIM 选定阈值态／权重编码，不能自动等同商品 TLC 页模式。

**使用限制：** Table 1 是作者估计；外围为 32 nm 并另用高压器件，不能称统一 28 nm 实测。器件数据与 NAND-05 有来源关联。

**证据关系：** 与 NAND-05 的 Macronix 器件依据有关联；模型和器件测量不是两次独立硅验证。

**出版标识：** [DOI](https://doi.org/10.1109/jxcdc.2021.3093772)。

<a id="NAND-05"></a>
## NAND-05 — Optimal Design Methods to Transform 3D NAND Flash into a High-Density, High-Bandwidth and Low-Power Nonvolatile Computing in Memory (nvCIM) Accelerator for Deep-Learning Neural Networks (DNN)

**核心** · 2019 · IEDM, 38.1.1–38.1.4 · [全文](NAND-05_2019_3DNAND_nvCIM.pdf)

**身份与版本：** Hang-Ting Lue, Po-Kai Hsu, Ming-Liang Wei, Teng-Hao Yeh, Pei-Ying Du, Wei-Chen Chen, Keh-Chung Wang, Chih-Yuan Lu。完整正式论文/技术资料。

**用途与结构：** 实际 16-layer 64 Gb SLC SGVC 器件与电流分布，用 SSL／BL／SL 解释多位输入及 SLC 复制编码；补直接 SLC 结构证据。

**正文定位：** pp.1–2，器件与映射；pp.3–4，Figs.1–16。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；实际 16-layer 64 Gb SLC SGVC 器件，multi-bit 用 SLC 复制/选择编码。

**使用限制：** 多位感测及 accelerator 指标含设计预估，不是完整已流片 CIM 性能；缺完整 SLC program/erase 服务。

**证据关系：** 器件结果与 NAND-04 建模存在来源关系。

**出版标识：** [DOI](https://doi.org/10.1109/iedm19573.2019.8993652)。

