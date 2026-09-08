# 07 — PCM

两类 IBM 芯片及逐行闭环、混合 SLC/MLC 宏和独立材料/器件测量互补。SET/RESET、连续模拟权重、离散状态及脉冲测试终点分别使用。

以下页码为本地 PDF 页序，从第 1 页计数（含封面）。记录的是原文条件与用途，不是最终 ρ、τ 或 RI* 估算。

<a id="PCM-01"></a>
## PCM-01 — A 64-core mixed-signal in-memory compute chip based on phase-change memory for deep neural network inference

**核心** · 2023 · Nature Electronics 6, 680–693 · [全文](PCM-01_2023_PCM64_Core.pdf)

**身份与版本：** Manuel Le Gallo, Riduan Khaddam-Aljameh, Milos Stanisavljevic, Athanasios Vasilopoulos, Benedikt Kersting, Martino Dazzi, Geethan Karunaratne, Matthias Braendli, Abhairaj Singh, Silvia M. Mueller, Julian Buechel, Xavier Timoneda, Vinay Joshi, Urs Egger, Angelo Garofalo, Anastasios Petropoulos, Theodore Antonakopoulos, Kevin Brew, Samuel Choi, Injo Ok, Timothy Philip, Victor Chan, Claire Silvestre, Ishtiaq Ahsan, Nicole Saulnier, Vijay Narayanan, Pier Andrea Francese, Evangelos Eleftheriou, Abu Sebastian。与 2023 正式论文对应的作者稿，包含 Methods/Extended Data。

**用途与结构：** 64-core 芯片的 diagonal selection 一次选不同 row/column 的器件，局部 write DAC、SET/RESET 形状与读 ADC 边界清楚。

**正文定位：** pp.2–3，diagonal programming/ADC；Methods 与 p.10，Power measurements。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；模拟多级 PCM、差分映射。

**使用限制：** 部分 latency 由 RTL 得到，不能全部称直接测量；14 nm、四 PCM/cell 与其他芯片条件不同。

**证据关系：** 与 PCM-02/06 同为 IBM 相关技术生态；不同芯片/编程组织不代表完全独立的材料工艺证据。

**出版标识：** [DOI](https://doi.org/10.1038/s41928-023-01010-1)。

<a id="PCM-02"></a>
## PCM-02 — An analog-AI chip for energy-efficient speech recognition and transcription

**核心** · 2023 · Nature · [全文](PCM-02_2023_AnalogAI_Speech.pdf)

**身份与版本：** S. Ambrogio, P. Narayanan, A. Okazaki, A. Fasoli, C. Mackin, K. Hosokawa, A. Nomura, T. Yasuda, A. Chen, A. Friz, M. Ishii, J. Luquin, Y. Kohda, N. Saulnier, K. Brew, S. Choi, I. Ok, T. Philip, V. Chan, C. Silvestre, I. Ahsan, V. Narayanan, H. Tsai, G. W. Burr。本地正式 PDF（已核验身份）。

**用途与结构：** 14 nm 芯片支持 row-wise 同时调谐 512 个权重，但一次选每权重的一个 PCM；闭环、校正与 tile 控制在正文交代。

**正文定位：** p.3，Fig.1f；pp.9–10，Methods：weight programming、controller、calibration。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；模拟多级、2/4 PCM-per-weight。

**使用限制：** 约 1 GHz controller clock 不是一次完整 MVM 或写入；写算法细节转引 ref.4，值得获取原始 2021 TED。

**证据关系：** PCM-06 是本工作明确引用的逐行编程依据，同技术线作方法补充。

**出版标识：** [DOI](https://doi.org/10.1038/s41586-023-06337-5)。

<a id="PCM-03"></a>
## PCM-03 — A 40-nm, 2M-Cell, 8b-Precision, Hybrid SLC-MLC PCM Computing-in-Memory Macro with 20.5 - 65.0TOPS/W for Tiny-AI Edge Devices

**核心** · 2022 · 2022 IEEE International Solid- State Circuits Conference (ISSCC) · [全文](PCM-03_2022_Hybrid_SLC_MLC.pdf)

**身份与版本：** Win-San Khwa, Yen-Cheng Chiu, Chuan-Jia Jhang, Sheng-Po Huang, Chun-Ying Lee, Tai-Hao Wen, Fu-Chun Chang, Shao-Ming Yu, Tung-Yin Lee, Meng-Fan Chang。完整正式论文/技术资料。

**用途与结构：** 40 nm 实测 PCM CIM，8-bit weight 以 2 SLC+3 MLC 编码，8-bit input 默认八拍；VSA 四阶段与 sparsity 重排解释求值粒度。

**正文定位：** p.1，Figs.11.3.2–6 的说明；pp.2–3，图与 summary。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；hybrid SLC／MLC（分模式）。

**使用限制：** 低功耗全 MLC 与混合模式不同；input-reordering 的跳过拍数依赖数据；没有完整 SET/RESET 更新周期。

**出版标识：** [DOI](https://doi.org/10.1109/isscc42614.2022.9731670)。

<a id="PCM-04"></a>
## PCM-04 — Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing

**补充** · 2017 · Science · [全文](PCM-04_2017_Subnanosecond_Nucleation.pdf)

**身份与版本：** Feng Rao, Keyuan Ding, Yuxing Zhou, Yonghui Zheng, Mengjiao Xia, Shilong Lv, Zhitang Song, Songlin Feng, Ider Ronneberger, Riccardo Mazzarello, Wei Zhang, Evan Ma。完整正式论文/技术资料。

**用途与结构：** 补充材料确认 0.13 μm 平台、190 nm BEC 的 T-shaped 器件、外部源表/脉冲发生器和示波器；亚纳秒为特定材料/偏置下的器件 SET 结果，适合作材料时间尺度对照。

**正文定位：** 主文 pp.2–4；SI p.2 §2、p.8 Fig.S5、p.9 Fig.S6。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；Sc-Sb-Te 晶化／相变条件；非默认多级 PCM 写入。

**使用限制：** SI Fig.S6 刻意采用 2 ms 脉冲间隔避免累积作用，既不能把脉宽当连续写服务，也不能把 2 ms 当介质必需延时。S5/S6 的 700 ps 示例偏置不同，应保留各自条件；不支持整阵列或多级闭环写入速度。

**出版标识：** [DOI](https://doi.org/10.1126/science.aao3212)。

**技术补充：** [SI](PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf)，18 页，已归档。

<a id="PCM-05"></a>
## PCM-05 — Phase Change Memory Drift Compensation in Spiking Neural Networks Using a Non-Linear Current Scaling Strategy

**补充** · 2024 · Journal of Low Power Electronics and Applications · [全文](PCM-05_2024_PCM_Drift.pdf)

**身份与版本：** Joao Henrique Quintino Palhares, Nikhil Garg, Yann Beilliard, Lorena Anghel, Fabien Alibart, Dominique Drouin, Philippe Galy。本地正式 PDF（已核验身份）。

**用途与结构：** 28 nm FD-SOI 相关 PCM 原始器件测试明确 75 ns SET/RESET、幅值／compliance 和多次序列；用读后等待跟踪漂移。

**正文定位：** p.3，§2.1–2.2；后续漂移补偿验证。

**工艺/模式：** 介质专用器件/阵列条件；不据此自动认定共同 28 nm 外围；Ge-rich GST 多级 PCM；SET／RESET 分开。

**使用限制：** 75 ns 是实验单脉冲；1000 次测试序列不是每次逻辑写入的必需脉冲数；SNN 补偿结果不能直接转为 local CIM 服务。

**出版标识：** [DOI](https://doi.org/10.3390/jlpea14040050)。

<a id="PCM-06"></a>
## PCM-06 — Fully On-Chip MAC at 14 nm Enabled by Accurate Row-Wise Programming of PCM-Based Weights and Parallel Vector-Transport in Duration-Format

**核心** · 2021 · IEEE Transactions on Electron Devices · [全文](PCM-06_2021_RowWise_ClosedLoopProgramming.pdf)

**身份与版本：** P. Narayanan, S. Ambrogio, A. Okazaki, K. Hosokawa, H. Tsai, A. Nomura, T. Yasuda, C. Mackin, S. C. Lewis, A. Friz, M. Ishii, Y. Kohda, H. Mori, K. Spoon, R. Khaddam-Aljameh, N. Saulnier, M. Bergendahl, J. Demarest, K. W. Brew, V. Chan, S. Choi, I. Ok, I. Ahsan, F. L. Lie, W. Haensch, V. Narayanan, G. W. Burr。完整正式论文/技术资料。

**用途与结构：** 14 nm PCM 原始逐行 CLT；同一 row 的 512 列共享幅度 DAC而各列使用独立脉宽。每次脉冲后读验，FPGA 算误差并装入下一轮脉宽；次级 PCM 可补偿过冲，器件/周期差异有实际测量。

**正文定位：** pp.3–5 III/IV、Figs.2–9；p.4 Fig.6；p.5 闭环算法。

**工艺/模式：** 14 nm PCM 专用外围，非共同 28 nm；连续模拟电导与 4 PCM/weight；CLT 与 FPGA 控制，非固定离散 MLC。

**使用限制：** “Fully on-chip MAC”不代表闭环调谐控制全部片上。60/120/240 ns 是示例脉冲，1.2 ns/tick 是读数编码；都不是完整写入周期。原文明确为连续模拟目标，不是固定离散级的商品 MLC。与 PCM-02 同技术线，不新增独立工艺证据。

**证据关系：** 为 PCM-02 的编程方法支撑，不另算独立工艺交叉验证。

**出版标识：** [DOI](https://doi.org/10.1109/ted.2021.3115993)。

