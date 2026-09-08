# R0 文献候选目录

核验日期：2026-09-08。55 条候选记录，按明确版本关系保守归并为 54 个资料包；资料包数量不等于独立实验数量。

现有主文 26 份（仓库复用 12，本轮公开取得 14）；另归档 3 份补充材料、2 份会议前作／作者报告。

本目录回答“可支持哪一块后续估算”，不要求单篇闭合两路吞吐。全文可用只表示可进入审阅，不表示已经确认其中参数可直接用于共同参考。P1 为关键依据，P2 为互补／交叉核查，P3 为相关版本或候补；人工顺序另见 [下载清单](DOWNLOAD_REQUESTS_V1.md)。

年份采用实际卷期／会议或 datasheet 修订时间，公开稿日期另记。GUC v002 未署日期，保留 undated，未把上传路径日期当发表年。旧文保留理由逐项说明。所有原始 PDF 仅本地使用，由本任务 [.gitignore](.gitignore) 排除。

## 分组入口

- [00 — 28 nm CMOS 外围参考资料](#00_cmos_periphery)：6 条主归属 + 2 条共享引用
- [01 — SRAM ACIM](#01_sram_acim)：4 条主归属 + 2 条共享引用
- [02 — SRAM DCIM](#02_sram_dcim)：3 条主归属 + 2 条共享引用
- [03 — 2D NOR Flash](#03_nor_2d)：5 条主归属
- [04 — 3D NAND Flash](#04_nand_3d)：5 条主归属
- [05 — RRAM](#05_rram)：5 条主归属
- [06 — MRAM](#06_mram)：5 条主归属
- [07 — PCM](#07_pcm)：5 条主归属
- [08 — FeRAM（HfO₂-based）](#08_feram_hfo2)：6 条主归属
- [09 — Gain-cell eDRAM](#09_gain_cell_edram)：5 条主归属
- [10 — 3D FeNOR／vertical FeFET](#10_fenor_3d)：6 条主归属

<a id="00_cmos_periphery"></a>

## 00 — 28 nm CMOS 外围参考资料

共同参考需要分别覆盖转换、输入驱动、局部感测／mux 和数字求值。这里组合官方 IP 产品资料、实际 28 nm 原始电路论文及两篇共享 CIM macro 来源；商业 IP 公布的采样率不等于给定 CIM 负载下的建立时间。公开 memory compiler 的完整时序库仍缺，不采用来源不明的商业 compiler 手册镜像。

共享：[SDCIM-01](LITERATURE_CATALOG.md#sdcim-01)、[SACIM-03](LITERATURE_CATALOG.md#sacim-03)。只保存一份主文件，身份和路径见其主资料卡。

<a id="cmos-01"></a>

### CMOS-01 — IGADACT01C — 28nm HPM 1.8V/0.9V 10bit 300MHz Current Steering DAC [3ch]

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Global Unichip Corporation (GUC)；官方 Product Brief，v002（未署发行日期）；发行日期未署 |
| 链接 | [官方页面](https://www.guc-asic.com/en/solutions/IPPortfolio/MixedSignalFront-EndIP) · [机构／作者／原厂入口 1](https://www.guc-asic.com/upload/2025_07_01/4_20250701210629mn8737Faf18.pdf) |
| 用途标签 | 28 nm 外围服务；输入驱动；DAC 转换服务 |
| 预期支撑 | 官方具体 DAC IP 简表确认真实 28 nm 工艺、分辨率、转换率、输出电流及 compliance 条件；为统一输入服务提供出发点。缺指定容性负载的 settling 和详细接口时序，不足以单独定最终延时。 |
| 层级／优先级 | 外围电路／IP 产品规格；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（官方 IP 明确 HPM 工艺） |
| 访问与判断 | 本轮公开取得全文，已核验。已核验官方两页 PDF 的产品编号、文档编号、工艺、输出条件和转换服务类别；详细负载建立指标未公开。 |
| 主文位置 | [CMOS-01_undated_IGADACT01C_v002.pdf](literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 身份核验说明 | 两页原文未署发行日期；URL 的 2025-07-01 是上传路径，不能作为发表年。文件名用 undated。另有 2022Q3 产品总览索引作为版本线索，不再请求内容较粗的总览。 |
| 相关版本 | 2022 — The Best Data Converter Total Solution Provider；官方总览的网页索引确认 2022Q3 与 N28 IP 表；直接下载返回 HTML。具体 v002 简表已足够初筛，不再请求较粗总览。 [官方／作者入口](https://www.guc-asic.com/upload/media/2022_event/Data_Converter.pdf) |

<a id="cmos-02"></a>

### CMOS-02 — A 28 nm CMOS 10 bit 100 MS/s Asynchronous SAR ADC with Low-Power Switching Procedure and Timing-Protection Scheme

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Fang Tang；Qiyun Ma；Zhou Shu 等（完整作者见 manifest）；Electronics；2021-11-19 |
| 链接 | [DOI: 10.3390/electronics10222856](https://doi.org/10.3390/electronics10222856) · [出版页面](https://www.mdpi.com/2079-9292/10/22/2856) · [机构／作者／原厂入口 1](https://dr.ntu.edu.sg/server/api/core/bitstreams/803899ac-0885-46c7-af0a-9106d5013c97/content) |
| 用途标签 | 28 nm 外围服务；ADC 转换；输入建立 |
| 预期支撑 | 核查 SAR 转换／采样节拍、分辨率与有效精度、输入与参考建立条件；同一设计的 timing-protection 说明如何防止把内部 SAR 步骤误作完整服务。 |
| 层级／优先级 | 外围电路（实测 ADC）；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据 |
| 访问与判断 | 本轮公开取得全文，已核验。已看机构公开正式 PDF 的题名、摘要和架构／measurement 小节；确有实测转换器、时序保护及精度评价。未决定其与 CIM 输入条件的适配。 |
| 主文位置 | [CMOS-02_2021_AsynchronousSAR.pdf](literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |

<a id="cmos-03"></a>

### CMOS-03 — SRAM Assist Techniques for Operation in a Wide Voltage Range in 28-nm CMOS

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Brian Zimmer；Seng Oon Toh；Huy Vo 等（完整作者见 manifest）；IEEE Transactions on Circuits and Systems II: Express Briefs；2012-12 |
| 链接 | [DOI: 10.1109/tcsii.2012.2231015](https://doi.org/10.1109/tcsii.2012.2231015) · [出版页面](https://ieeexplore.ieee.org/document/6424019/) · [机构／作者／原厂入口 1](https://people.eecs.berkeley.edu/~krste/papers/zimmer-ieeetcasII-2012.pdf) · [机构／作者／原厂入口 2](https://citeseerx.ist.psu.edu/document?doi=8d786312b6f1a1727b8d26304236576dcc1f3f12&repid=rep1&type=pdf) |
| 用途标签 | 28 nm 外围服务；读写时序；负载与驱动条件 |
| 预期支撑 | 读写 assist、WL 脉冲与 bitline 负载条件共同约束普通 SRAM 写入估计；可作为显式条件的参考设计依据，不能宣称其仿真假设是量产 compiler 保证值。 |
| 层级／优先级 | 器件／SRAM 局部电路（建模与仿真）；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（模型条件） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | DOI 登记与作者发表页一致；网页可读原文片段，作者 PDF 返回 404、CiteSeerX 连接超时。 |
| 旧资料保留理由 | 直接公开 28 nm 局部 SRAM 的负载与 assist 时序建模条件，仍适用于基础方法核查。 |

<a id="cmos-04"></a>

### CMOS-04 — A 28 nm Dual-Port SRAM Macro With Screening Circuitry Against Write-Read Disturb Failure Issues

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yuichiro Ishii；Hidehiro Fujiwara；Shinji Tanaka 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2011-11 |
| 链接 | [DOI: 10.1109/jssc.2011.2164021](https://doi.org/10.1109/jssc.2011.2164021) · [出版页面](https://ieeexplore.ieee.org/document/6008511/) |
| 用途标签 | 28 nm 外围服务；局部读写；操作粒度与冲突 |
| 预期支撑 | 独立核查双口 SRAM 的局部读写边界、感测与 write-read disturb 条件；补仅有 assist 仿真而无实际 macro 的不足。双口机制不能无条件代表单口 SRAM。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | 实测 28 nm SRAM 基础 macro；保留用于普通读写服务和端口冲突核查。 |

<a id="cmos-05"></a>

### CMOS-05 — A 28-nm 8-Bit 16-GS/ DAC With >60 dBc/>40 dBc SFDR Up To 2.3 GHz/5.4 GHz Using 4-Channel NRZ-Output-Overlapped Time-Interleaving

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Sihao Chen；Chengyu Huang；Limeng Sun 等（完整作者见 manifest）；IEEE Transactions on Circuits and Systems II: Express Briefs；2025-02 |
| 链接 | [DOI: 10.1109/tcsii.2024.3518084](https://doi.org/10.1109/tcsii.2024.3518084) · [出版页面](https://ieeexplore.ieee.org/document/10802956/) |
| 用途标签 | 28 nm 外围服务；DAC／驱动；采样与建立的区别 |
| 预期支撑 | 核查真实 28 nm 电流舵 DAC 的分辨率、输出方式、各子 DAC 节拍及负载条件，补 IP 简表缺少的电路机制。高带宽四路交织输出不是单个 CIM 字线驱动的直接替代；是否包含可用阶跃建立指标待全文判断。 |
| 层级／优先级 | 外围电路（DAC 原始设计，实测属性待主文核查）；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（CIM 负载适配未确认） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | 出版登记题名写作 16-GS/（缺 s）；此处保留登记形式，待正式 PDF 核对排印。 |
| 日期说明 | 期刊卷期为 2025-02；DOI 字符串含 2024，不将其当作最终卷期年份。 |

<a id="cmos-06"></a>

### CMOS-06 — A high-speed single channel reconfigurable 1-GS/s to 1.5-GS/s, 8-bit to 6-bit SAR ADC in 28 nm CMOS

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Qing Su；Xuan Guo；Hanbo Jia 等（完整作者见 manifest）；IEICE Electronics Express；2025-06-25 |
| 链接 | [DOI: 10.1587/elex.22.20250220](https://doi.org/10.1587/elex.22.20250220) · [出版页面](https://www.jstage.jst.go.jp/article/elex/22/12/22_22.20250220/_article) · [机构／作者／原厂入口 1](https://www.jstage.jst.go.jp/article/elex/advpub/0/advpub_22.20250220/_pdf) |
| 用途标签 | 28 nm 外围服务；ADC 精度与节拍；独立模型交叉核查 |
| 预期支撑 | 补第二团队的 28 nm 单通道 SAR；可核查分辨率改变如何影响完整转换服务和输入带宽。不能只凭最高采样率假设 CIM 精度与驱动已经满足。 |
| 层级／优先级 | 外围电路（28 nm 后仿真，非实测）；P2 |
| 工艺／状态边界 | 直接的 28 nm 模型／后仿真条件，不是实测芯片 |
| 访问与判断 | 本轮公开取得全文，已核验。已核验公开接受版封面与正文题名、作者；第 4 节明确 Simulation results，比较表标注 post-layout。仅作电路模型交叉核查；具体输入负载／精度适配留待 R1。 |
| 主文位置 | [CMOS-06_2025_ReconfigurableSAR.pdf](literature/00_cmos_periphery/CMOS-06_2025_ReconfigurableSAR.pdf) |
| 版本／附件 | J-STAGE advance publication（公开日期 2025-05-07；期刊登记 2025-06-25）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |


<a id="01_sram_acim"></a>

## 01 — SRAM ACIM

用不同团队的电荷域／电容阵列 macro 核查完整多位求值、ADC 使用方式和局部边界。共享 CMOS-03／04 补普通 SRAM 读写基础；不同工艺的 macro 只作结构与量级交叉参考，不能直接冠以统一 28 nm 的性能。

共享：[CMOS-03](LITERATURE_CATALOG.md#cmos-03)、[CMOS-04](LITERATURE_CATALOG.md#cmos-04)。只保存一份主文件，身份和路径见其主资料卡。

<a id="sacim-01"></a>

### SACIM-01 — Scalable and Programmable Neural Network Inference Accelerator Based on In-Memory Computing

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Hongyang Jia；Murat Ozatay；Yinqi Tang 等（完整作者见 manifest）；IEEE JSSC 57(1), 198–211；2022 |
| 链接 | [DOI: 10.1109/JSSC.2021.3119018](https://doi.org/10.1109/JSSC.2021.3119018) · [机构／作者／原厂入口 1](https://www.princeton.edu/~nverma/VermaLabSite/Publications/2022/JiaOzatayTangValaviPathakLeeVerma_JSSC2022.pdf) |
| 用途标签 | 完整多位求值；操作粒度与局部并行度；CIM 求值桥接 |
| 预期支撑 | 分清位相位、ADC 和数字重构，寻找输入 payload 对应的完整求值边界；可用普通 SRAM 写入描述补接口线索。 |
| 层级／优先级 | 阵列／局部 macro 及整芯片；P1 |
| 工艺／状态边界 | 其他工艺的量级交叉参考（65 nm） |
| 访问与判断 | 已有全文，已复制并核验。原 PDF 的阵列、ADC、BPBS SIMD 与测量章节已初筛；完整求值结构可用，普通权重写入服务仍待补。 |
| 主文位置 | [SACIM-01_2022_Scalable_IMC.pdf](literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf) |
| 版本／附件 | Published paper；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/jia2022.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_jia2022 |

<a id="sacim-02"></a>

### SACIM-02 — PICO-RAM: A PVT-Insensitive Analog Compute-In-Memory SRAM Macro With In Situ Multi-Bit Charge Computing and 6T Thin-Cell-Compatible Layout

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Zhiyu Chen；Ziyuan Wen；Weier Wan 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2025-01 |
| 链接 | [DOI: 10.1109/jssc.2024.3422826](https://doi.org/10.1109/jssc.2024.3422826) · [出版页面](https://ieeexplore.ieee.org/document/10634317/) · [机构／作者／原厂入口 1](https://arxiv.org/abs/2407.12829) · [机构／作者／原厂入口 2](https://arxiv.org/pdf/2407.12829) |
| 用途标签 | CIM 求值桥接；输入 DAC／ADC 共享；完整多位求值 |
| 预期支撑 | 补原位多位电荷计算及 DAC／MAC／ADC 复用同组电容的实现，检查输入方式与精度条件；与 Jia 的位串行路径互补。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 其他工艺的量级交叉参考（65 nm） |
| 访问与判断 | 本轮公开取得全文，已核验。已核验作者全文题名、原位电容计算与测试 macro；接受稿足够做 R0，不重复请求正式版。 |
| 主文位置 | [SACIM-02_2025_PICO_RAM.pdf](literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf) |
| 版本／附件 | 作者 arXiv 接受稿；首次公开 2024-07，期刊卷期 2025-01；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |

<a id="sacim-03"></a>

### SACIM-03 — A 28nm 32Kb SRAM Computing-in-Memory Macro With Hierarchical Capacity Attenuator and Input Sparsity-Optimized ADC for 4b Mac Operation

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Kanglin Xiao；Xiaoxin Cui；Xin Qiao 等（完整作者见 manifest）；IEEE Transactions on Circuits and Systems II: Express Briefs；2023-06 |
| 链接 | [DOI: 10.1109/tcsii.2023.3234620](https://doi.org/10.1109/tcsii.2023.3234620) · [出版页面](https://ieeexplore.ieee.org/document/10008052/) |
| 用途标签 | 28 nm 外围服务；CIM 求值桥接；ADC 与局部读出 |
| 预期支撑 | 28 nm 9T1C 电荷域 macro 连接阵列、权重电容衰减器与 flash ADC，补独立 ADC 无法说明的 CIM 读出条件。稀疏性优化的模式与完整精度节拍需全文确认。 |
| 层级／优先级 | 局部 macro 电路设计；公开 2022 前作为仿真；P2 |
| 工艺／状态边界 | 直接的 28 nm 设计依据；已得前作是仿真，不宣称两版均实测 |
| 访问与判断 | 相关 2022 会议前作已取得；2023 主文未取得。已核验 2022 会议 PDF 的题名、作者和 28 nm 电荷域结构；第 III 节为 Simulation Results，已有 input-sparsity 方案；2023 扩展内容和证据类型待正式主文。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 相关版本 | 2022 — A Computing-in-Memory SRAM Macro Based on Fully-Capacitive-Coupling With Hierarchical Capacity Attenuator for 4-b MAC Operation；相关会议前作，明确为仿真且已有 input-sparsity ADC；同团队／相近结构不另计独立来源，2023 扩展的内容差异仍需核查。 [官方／作者入口](https://confcats-event-sessions.s3.amazonaws.com/iscas22/papers/1140.pdf)；本地：[SACIM-03_2022_Hierarchical_Attenuator_ISCAS.pdf](literature/01_sram_acim/SACIM-03_2022_Hierarchical_Attenuator_ISCAS.pdf) |

<a id="sacim-04"></a>

### SACIM-04 — A Charge Domain SRAM Compute-in-Memory Macro With C-2C Ladder-Based 8-Bit MAC Unit in 22-nm FinFET Process for Edge Inference

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Hechen Wang；Renzhi Liu；Richard Dorrance 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2023-04 |
| 链接 | [DOI: 10.1109/jssc.2022.3232601](https://doi.org/10.1109/jssc.2022.3232601) · [出版页面](https://ieeexplore.ieee.org/document/10008405/) · [机构／作者／原厂入口 1](https://rdorrance.com/publications/) · [机构／作者／原厂入口 2](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10008405) |
| 用途标签 | CIM 求值桥接；完整多位求值；独立结构交叉核查 |
| 预期支撑 | Intel C-2C ladder 的完整 8-bit 电荷域 MAC 补独立团队证据，核查位并行输入、求值粒度与输出精度。22 nm 节拍不直接作为 28 nm 基线。 |
| 层级／优先级 | 阵列／局部 macro；P2 |
| 工艺／状态边界 | 其他工艺的量级交叉参考（22 nm FinFET） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |


<a id="02_sram_dcim"></a>

## 02 — SRAM DCIM

数字求值需区分单个时钟、位串行步骤和完整精度输出。D6CIM、动态逻辑 macro 与可重构数字 macro 提供互补实现，共享 CMOS-03／04 解释普通写入与读写冲突；未要求单篇同时闭合两路吞吐。

共享：[CMOS-03](LITERATURE_CATALOG.md#cmos-03)、[CMOS-04](LITERATURE_CATALOG.md#cmos-04)。只保存一份主文件，身份和路径见其主资料卡。

<a id="sdcim-01"></a>

### SDCIM-01 — D6CIM: 60.4-TOPS/W, 1.46-TOPS/mm2, 1005-Kb/mm2 Digital 6T-SRAM-Based Compute-in-Memory Macro Supporting 1-to-8b Fixed-Point Arithmetic in 28-nm CMOS

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Jonghyun Oh；Chuan-Tung Lin；Mingoo Seok；ESSCIRC, 413–416；2023 |
| 链接 | [DOI: 10.1109/ESSCIRC59616.2023.10268725](https://doi.org/10.1109/ESSCIRC59616.2023.10268725) · [机构／作者／原厂入口 1](https://par.nsf.gov/servlets/purl/10526026) |
| 用途标签 | 28 nm 外围服务；数字累加／位串行；普通写入粒度 |
| 预期支撑 | 区分数字时钟与完整精度 VMM；普通写口宽度可提供后续参考写入情景的粒度依据。写周期仍需共同 SRAM 条件或扩展版确认。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据 |
| 访问与判断 | 已有全文，已复制并核验。原会议全文已核验宏结构、位串行调度、普通写端口与测量章节。2026 期刊扩展版只作版本线索，不重复计数或立即请求。 |
| 主文位置 | [SDCIM-01_2023_D6CIM.pdf](literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf) |
| 版本／附件 | Published paper；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/d6cim2023.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_d6cim2023 |
| 相关版本 | 2026 — D6CIM: 60.4-TOPS/W All-Digital 6T-SRAM-Based Compute-in-Memory Macro Supporting 1-to-8 b Fixed-Point Arithmetic in a 28-nm CMOS；期刊扩展版题录线索；会议稿已足够 R0，暂不重复请求或另计独立证据。 [官方／作者入口](https://doi.org/10.1109/TCSI.2026.3665839) |

<a id="sdcim-02"></a>

### SDCIM-02 — A Digital Bit-Reconfigurable Versatile Compute-In-Memory Macro for Machine Learning Acceleration

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Xin Zhang；Yuncheng Lu；Bo Wang 等（完整作者见 manifest）；IEEE Transactions on Circuits and Systems II: Express Briefs；2023-05 |
| 链接 | [DOI: 10.1109/tcsii.2023.3257058](https://doi.org/10.1109/tcsii.2023.3257058) · [出版页面](https://ieeexplore.ieee.org/document/10068798/) · [机构／作者／原厂入口 1](https://repository.sutd.edu.sg/esploro/outputs/journalArticle/A-Digital-Bit-Reconfigurable-Versatile-Compute-In-Memory-Macro/9912748209846) |
| 用途标签 | 数字求值与控制；操作粒度；独立量级交叉核查 |
| 预期支撑 | 可编程加法及位串行乘法提供独立实现，检查不同运算的完整服务粒度；65 nm 实测只支持结构和量级交叉核查。 |
| 层级／优先级 | 阵列／局部 macro；P2 |
| 工艺／状态边界 | 其他工艺的量级交叉参考（65 nm） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="sdcim-03"></a>

### SDCIM-03 — A 1.041-Mb/mm^2 27.38-TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-less SRAM Compute-in-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Bonan Yan；Jeng-Long Hsu；Pang-Cheng Yu 等（完整作者见 manifest）；2022 IEEE International Solid- State Circuits Conference (ISSCC)；2022-02-20 |
| 链接 | [DOI: 10.1109/isscc42614.2022.9731545](https://doi.org/10.1109/isscc42614.2022.9731545) · [出版页面](https://ieeexplore.ieee.org/document/9731545/) · [机构／作者／原厂入口 1](https://scholars.duke.edu/publication/1519651) · [机构／作者／原厂入口 2](https://www.icacworkshop.cn/2022/slides/ICAC_2022_14.3_Yan_Bonan.pdf) |
| 用途标签 | 28 nm 外围服务；数字求值与控制；完整精度输出 |
| 预期支撑 | 动态逻辑 ADC-less 28 nm macro 与 D6CIM 互补，核查预充／求值步骤、精度及数字控制节拍；不能把介绍段的通用 SRAM 速度当作本 macro 完整求值。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据 |
| 访问与判断 | 同篇作者报告已取得；正式主文暂缺。已核验同篇作者 35 页报告的题名、作者与 macro 框图；正式主文的完整时序定义未审阅。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 相关版本 | 2022 — A 1.041Mb/mm2 27.38TOPS/W Signed-INT8 Dynamic-Logic-Based ADC-Less SRAM Compute-In-Memory Macro in 28nm with Reconfigurable Bitwise Operation for AI and Embedded Applications；同篇论文的 35 页作者报告；提供原作者图和实现说明，不冒充正式主文；可先审阅，正式版暂缓。 [官方／作者入口](https://www.icacworkshop.cn/2022/slides/ICAC_2022_14.3_Yan_Bonan.pdf)；本地：[SDCIM-03_2022_DynamicLogic_INT8_AuthorSlides.pdf](literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8_AuthorSlides.pdf) |


<a id="03_nor_2d"></a>

## 03 — 2D NOR Flash

三家厂商的存储资料提供编程、擦除、busy 和操作粒度定义，两篇早期原始 NOR 模拟计算论文连接普通存储与精细电导调谐。普通存储时序可以支撑更新依据，但 SPI／并行封装输出速度和模拟 CIM 求值不是同一边界。

<a id="nor-01"></a>

### NOR-01 — S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Infineon Technologies；厂商 datasheet，002-18741 Rev. *E；2024-09-04 |
| 链接 | [官方页面](https://www.infineon.com/dgdl/Infineon-S29GL01GS_S29GL512S_S29GL256S_S29GL128S_128_Mb_256_Mb_512_Mb_1_Gb_GL-S_MIRRORBIT_Flash_Parallel_3-DataSheet-v06_00-EN.pdf?fileId=8ac78c8c7d0d8da4017d0ee99af9726b) |
| 用途标签 | 读侧时间尺度；编程／擦除周期；字／buffer／sector 粒度 |
| 预期支撑 | Infineon GL-S 并行 NOR 提供 random/page read、write-buffer、sector erase 和完成状态定义，补串行 NOR 之外的独立厂家依据。MirrorBit 的物理存储与模拟权重精度不混同。 |
| 层级／优先级 | 整芯片存储规格，含局部操作定义；P2 |
| 工艺／状态边界 | 数字 NOR／MirrorBit，军规产品条件；非模拟精度声明 |
| 访问与判断 | 官方 PDF 网页内容可读；本地文件未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | 官方 106 页 PDF 网页正文页 1 核验题名、文号、日期；直接下载为空。该链接实为军规版，不能当普通商规版本；保留其操作定义，温度／寿命／时序必须随产品条件。 |

<a id="nor-02"></a>

### NOR-02 — W25Q128JV — 3V 128M-BIT Serial Flash Memory with Dual/Quad SPI

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Winbond Electronics；厂商 datasheet，Revision G；2019-04-08 |
| 链接 | [官方页面](https://www.winbond.com/hq/support/documentation/?__locale=en&pno=W25Q128JV) · [机构／作者／原厂入口 1](https://www.winbond.com/resource-files/w25q128jv%20revg%2004082019%20plus.pdf) |
| 用途标签 | 编程／擦除周期；操作粒度；接口与内部 busy 区分 |
| 预期支撑 | Winbond 普通 NOR 的 page program、sector/block/chip erase 与 busy 状态可支撑完整更新步骤；串行读频率仅为接口定义。 |
| 层级／优先级 | 整芯片存储规格；P1 |
| 工艺／状态边界 | 普通数字 NOR（未作多级模拟精度假设） |
| 访问与判断 | 本轮公开取得全文，已核验。公开 PDF 封面修订／日期与身份一致；目录、program／erase 指令和 AC timing 表已定位。 |
| 主文位置 | [NOR-02_2019_W25Q128JV_RevG.pdf](literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 旧资料保留理由 | 具体修订的完整 datasheet，操作定义清楚；门户另列 2025 更新，R0 不把二者混为同一版本。 |

<a id="nor-03"></a>

### NOR-03 — SST26VF064B/SST26VF064BA — 2.5V/3.0V 64-Mbit Serial Quad I/O (SQI) Flash Memory

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Microchip Technology；厂商 datasheet，DS20005119K；2022-03 |
| 链接 | [官方页面](https://www.microchip.com/en-us/product/SST26VF064B) · [机构／作者／原厂入口 1](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/SST26VF064B-SST26VF064BA-2-5V-3-0V-64-Mbit-Serial-Quad-IO--SQI--Flash-Memory-20005119K.pdf) |
| 用途标签 | 编程／擦除周期；操作粒度；独立量级交叉核查 |
| 预期支撑 | Microchip SuperFlash 家族补不同 NOR 工艺／擦除方式的独立产品基线，核对 page program、擦除及 ready 条件，不从串行接口估 cell 速度。 |
| 层级／优先级 | 整芯片存储规格；P1 |
| 工艺／状态边界 | 普通数字 SuperFlash NOR |
| 访问与判断 | 本轮公开取得全文，已核验。已核验正式 PDF；第 67 页 revision history 确认 K 版为 March 2022，目录包含写入／擦除过程和 AC 规格。 |
| 主文位置 | [NOR-03_2022_SST26VF064B_RevK.pdf](literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |

<a id="nor-04"></a>

### NOR-04 — Fast, Energy-Efficient, Robust, and Reproducible Mixed-Signal Neuromorphic Classifier Based on Embedded NOR Flash Memory Technology

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Xinjie Guo；Farnood Merrikh Bayat；Mohammad Bavandpour 等（完整作者见 manifest）；IEDM, 6.5.1–6.5.4；2017 |
| 链接 | [DOI: 10.1109/IEDM.2017.8268341](https://doi.org/10.1109/IEDM.2017.8268341) · [机构／作者／原厂入口 1](https://web.ece.ucsb.edu/~strukov/papers/2017/iedm2017.pdf) |
| 用途标签 | CIM 求值桥接；输入驱动与输出边界；阵列结构 |
| 预期支撑 | 实际嵌入式 NOR 模拟分类器连接浮栅阵列、门电压输入和模拟输出；提供估算结构，不能把整个分类任务延迟视作一个局部 MVM。 |
| 层级／优先级 | 阵列与两层网络实验；P2 |
| 工艺／状态边界 | 模拟调谐浮栅权重 |
| 访问与判断 | 已有全文，已复制并核验。原论文题名、ESF1 阵列和输入／输出结构已初筛；普通数字 NOR 与其模拟调谐不是同一写入终点。 |
| 主文位置 | [NOR-04_2017_EmbeddedNOR_Classifier.pdf](literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf) |
| 版本／附件 | Author-hosted original manuscript；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 旧资料保留理由 | 直接基于 embedded NOR 的原始 CIM 实验，可连接厂商普通存储能力与模拟读出。 |
| 交叉证据边界 | 相关实验／团队族：ucsb_esf1；同族条目不自动视作独立交叉验证。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/nor2017.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_nor2017 |

<a id="nor-05"></a>

### NOR-05 — Model-Based High-Precision Tuning of NOR Flash Memory Cells for Analog Computing Applications

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Farnood Merrikh Bayat；Xinjie Guo；Michael Klachko 等（完整作者见 manifest）；Device Research Conference；2016 |
| 链接 | [官方页面](https://web.ece.ucsb.edu/~strukov/papers/2016/DRCflash2016.pdf) |
| 用途标签 | 写入／编程周期；擦除与更新方式；精度与 verify |
| 预期支撑 | 反馈调谐论文补完整模拟状态建立方法与擦除作用，保留目标误差、脉冲和反馈过程的区分。与 NOR-04 同 ESF1 技术路线，不当作独立团队验证。 |
| 层级／优先级 | 器件／小阵列；P1 |
| 工艺／状态边界 | 模拟多级调谐 |
| 访问与判断 | 已有全文，已复制并核验。已有作者全文显示小阵列调谐、编程与擦除脉冲及反馈算法；不在 R0 组合成总写入时间。 |
| 主文位置 | [NOR-05_2016_NOR_ModelBased_Tuning.pdf](literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf) |
| 版本／附件 | Author-hosted original manuscript；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 旧资料保留理由 | 原始模拟 NOR 精细调谐方法，直接补普通 datasheet 无法描述的权重更新过程。 |
| 交叉证据边界 | 相关实验／团队族：ucsb_esf1；同族条目不自动视作独立交叉验证。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/nor_tuning2016.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_nor_tuning2016 |


<a id="04_nand_3d"></a>

## 04 — 3D NAND Flash

Micron 的 MLC／TLC 技术资料与 SK hynix、KIOXIA 的 QLC 原始芯片论文分开登记状态模式；后两篇桥接资料解释 NAND 串、字线选择与 CIM 求值。重点保留页／块／plane／die 的层级差异，未用 SSD 带宽代表阵列；SLC 专用工作模式的直接候选仍是缺口。

<a id="nand-01"></a>

### NAND-01 — Micron 3D NAND Flash Memory Technology

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Micron Technology；厂商技术产品简表，02/16；2016-02 |
| 链接 | [官方页面](https://www.micron.com/products/storage/nand-flash/3d-nand/part-catalog) · [机构／作者／原厂入口 1](https://assets.micron.com/adobe/assets/urn%3Aaaid%3Aaem%3A3e6db2c4-d096-425e-91f4-1355e5262cc3/renditions/original/as/3d-nand-flyer.pdf) |
| 用途标签 | 读侧时间尺度；编程／擦除周期；页／块／plane 粒度 |
| 预期支撑 | 官方表分别列 2b/c MLC 和 3b/c TLC 的 tR、tPROG、tBERS、页块与 plane 组织，可为完整普通存储操作提供粗粒度依据。是技术简表，详细约束仍需后续 datasheet 核查。 |
| 层级／优先级 | 厂商器件／die 规格简表；P1 |
| 工艺／状态边界 | MLC 2b/c；TLC 3b/c（分列） |
| 访问与判断 | 官方 PDF 网页内容可读；本地文件未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | 官方 PDF 网页索引可读产品表，页脚 ©2016／02/16 已确认；本地 curl 返回 Request Rejected HTML。 |
| 旧资料保留理由 | 厂商直接列出页／块／plane 和完整操作时间定义；成熟 NAND 基础来源，不是 2026 新产品参数。 |

<a id="nand-02"></a>

### NAND-02 — A 2Tb 4b/Cell 6-Plane 3D-Flash Memory with 37.6Gb/mm^2 Bit Density and >85MB/s Write Throughput

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Jayanth M. Thimmaiah；Ryuji Yamashita；In-Soo Yoon 等（完整作者见 manifest）；2026 IEEE International Solid-State Circuits Conference (ISSCC)；2026-02-15 |
| 链接 | [DOI: 10.1109/isscc49663.2026.11409136](https://doi.org/10.1109/isscc49663.2026.11409136) · [出版页面](https://ieeexplore.ieee.org/document/11409136/) · [机构／作者／原厂入口 1](https://www.kioxia.com/ja-jp/rd/technology/topics/topics-92.html) |
| 用途标签 | 编程周期；plane 并行条件；独立产品交叉核查 |
| 预期支撑 | KIOXIA 第十代 QLC 原始芯片资料补 plane 并行与写入组织；题名 write throughput 仍需全文区分内部编程与 die 级数据路径。 |
| 层级／优先级 | 阵列／die 与整芯片；P1 |
| 工艺／状态边界 | QLC 4b/c；6-plane |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="nand-03"></a>

### NAND-03 — A 321-Layer 2Tb 4b/cell 3D-NAND-Flash Memory with a 75MB/s Program Throughput

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Wanik Cho；Chanhui Jeong；Jongwoo Kim 等（完整作者见 manifest）；2025 IEEE International Solid-State Circuits Conference (ISSCC)；2025-02-16 |
| 链接 | [DOI: 10.1109/isscc49661.2025.10904748](https://doi.org/10.1109/isscc49661.2025.10904748) · [出版页面](https://ieeexplore.ieee.org/document/10904748/) |
| 用途标签 | 编程周期；操作粒度与局部并行度；独立量级交叉核查 |
| 预期支撑 | SK hynix 321 层 QLC 实际芯片补独立厂商依据，核对编程步骤、页／plane 组织及吞吐定义。其题名数值不能被旧稿误记为 KIOXIA 或 TLC。 |
| 层级／优先级 | 阵列／die 与整芯片；P1 |
| 工艺／状态边界 | QLC 4b/c（不是 TLC） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="nand-04"></a>

### NAND-04 — System-Technology Codesign of 3-D NAND Flash-Based Compute-in-Memory Inference Engine

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Wonbo Shim；Shimeng Yu；IEEE JXCDC 7(1), 61–69；2021-06 |
| 链接 | [DOI: 10.1109/jxcdc.2021.3093772](https://doi.org/10.1109/jxcdc.2021.3093772) · [出版页面](https://ieeexplore.ieee.org/document/9468674/) · [官方页面](https://doi.org/10.1109/JXCDC.2021.3093772) · [机构／作者／原厂入口 1](https://www.researchgate.net/publication/352865690_System-Technology_Codesign_of_3-D_NAND_Flash-Based_Compute-in-Memory_Inference_Engine) |
| 用途标签 | CIM 求值桥接；字线／位线与重构；局部阵列边界 |
| 预期支撑 | 解释 NAND 物理组织如何映射 CIM、外围共享与必要求值阶段；补商品页读与电流求和之间的估算桥梁。原始参数表图像必须补齐。 |
| 层级／优先级 | 阵列／外围与系统仿真；P1 |
| 工艺／状态边界 | CIM 选定阈值态／权重编码，不能自动等同商品 TLC 页模式 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | 复用前轮原文网页线索；前轮 Table 1 原图未取得，本轮没有将它升级为已核实全文。 |
| 旧资料保留理由 | 直接连接 NAND 物理组织与 CIM 外围的 codesign 方法；虽略超五年仍提供缺少的估算桥梁。 |

<a id="nand-05"></a>

### NAND-05 — Optimal Design Methods to Transform 3D NAND Flash into a High-Density, High-Bandwidth and Low-Power Nonvolatile Computing in Memory (nvCIM) Accelerator for Deep-Learning Neural Networks (DNN)

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Hang-Ting Lue；Po-Kai Hsu；Ming-Liang Wei 等（完整作者见 manifest）；IEDM, 38.1.1–38.1.4；2019-12 |
| 链接 | [DOI: 10.1109/iedm19573.2019.8993652](https://doi.org/10.1109/iedm19573.2019.8993652) · [出版页面](https://ieeexplore.ieee.org/document/8993652/) · [官方页面](https://doi.org/10.1109/IEDM19573.2019.8993652) · [机构／作者／原厂入口 1](https://ieee-iedm.org/wp-content/uploads/2026/05/2019-IEDM-Archive.pdf) |
| 用途标签 | CIM 求值桥接；局部并行组织；NAND 结构依据 |
| 预期支撑 | 产业团队原始 nvCIM 研究补 block／string 组织与输入读出映射，连接 NAND-04 所引用硬件；是否包含编程条件尚需全文。 |
| 层级／优先级 | 阵列／局部 macro；P2 |
| 工艺／状态边界 | nvCIM 阈值／操作模式待全文确认 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | 直接 NAND CIM 原始硬件／结构桥接，是后续 codesign 的关键来源。 |


<a id="05_rram"></a>

## 05 — RRAM

厂商 ReRAM datasheet 和 Weebit／CEA-Leti 原始测量补普通写入与器件条件；三种 CIM 实现补差分编码、读出和编程策略。比较时必须保留 binary／multi-level、单脉冲／闭环完成的区别，不能把厂家 SPI 时钟当作 cell 切换时间。

<a id="rram-01"></a>

### RRAM-01 — A compute-in-memory chip based on resistive random-access memory

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Weier Wan；Rajkumar Kubendran；Clemens Schaefer 等（完整作者见 manifest）；Nature 608, 504–512；2022 |
| 链接 | [DOI: 10.1038/s41586-022-04992-8](https://doi.org/10.1038/s41586-022-04992-8) · [机构／作者／原厂入口 1](https://par.nsf.gov/servlets/purl/10406027) |
| 用途标签 | CIM 求值桥接；闭环编程；状态精度与验证 |
| 预期支撑 | 器件目标电导、差分映射、program/verify 与读出结构为多级 RRAM 参考设计提供互补依据；外控测量与集成外围估计须分开。 |
| 层级／优先级 | 阵列／局部 macro 及整芯片；P1 |
| 工艺／状态边界 | 模拟多级、差分权重 |
| 访问与判断 | 已有全文，已复制并核验。本地正式正文含 Methods 与 Extended Data；已初筛编程、核结构和求值章节。 |
| 主文位置 | [RRAM-01_2022_NeuRRAM.pdf](literature/05_rram/RRAM-01_2022_NeuRRAM.pdf) |
| 版本／附件 | Published article including Methods and Extended Data；主文含 Methods／Extended Data；独立补充包尚未完整核验，R1 如依赖其中信息再定向补，不重复请求主文。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/neurram2022.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_neurram2022 |

<a id="rram-02"></a>

### RRAM-02 — A 28 nm 576K RRAM-based computing-in-memory macro featuring hybrid programming with area efficiency of 2.82 TOPS/mm2

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Siqi Liu；Songtao Wei；Peng Yao 等（完整作者见 manifest）；Journal of Semiconductors 46(6), 062304；2025 |
| 链接 | [DOI: 10.1088/1674-4926/24100017](https://doi.org/10.1088/1674-4926/24100017) · [机构／作者／原厂入口 1](https://www.jos.ac.cn/article/doi/10.1088/1674-4926/24100017) |
| 用途标签 | 28 nm 读出；写入／编程方式；操作粒度 |
| 预期支撑 | 实际 28 nm macro 的混合编程、差分校验和 ADC 共享可连接器件与统一外围；相对编程改进不等于已公开绝对写入时长。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（专用 RRAM 外围）；多级／2T2R 差分 |
| 访问与判断 | 已有全文，已复制并核验。已核验正式 PDF 与编程／共享结构；是否足够确定绝对服务间隔留待 R1。 |
| 主文位置 | [RRAM-02_2025_HybridProgramming.pdf](literature/05_rram/RRAM-02_2025_HybridProgramming.pdf) |
| 版本／附件 | Publisher PDF; June 5, 2025；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/liu2025.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_liu2025 |

<a id="rram-03"></a>

### RRAM-03 — High temperature stability embedded ReRAM for 2x nm node and beyond

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | G. Molas；G. Piccolboni；A. Bricalli 等（完整作者见 manifest）；2022 IEEE International Memory Workshop (IMW)；2022-05 |
| 链接 | [DOI: 10.1109/imw52921.2022.9779293](https://doi.org/10.1109/imw52921.2022.9779293) · [出版页面](https://ieeexplore.ieee.org/document/9779293/) · [机构／作者／原厂入口 1](https://www.weebit-nano.com/wp-content/uploads/2022/06/IMW2022_Weebit_High-temperature-stability-embedded-ReRAM-or-RRAM-for-2x-nm-node-and-beyond.pdf) |
| 用途标签 | 器件编程条件；binary 存储；独立产业交叉核查 |
| 预期支撑 | Weebit／CEA-Leti 28 nm ReRAM 实测提供与 CIM 团队不同的操作／可靠性条件；初筛确认不只有宣传页，后续检查时序与写入终点是否充分。 |
| 层级／优先级 | 器件／测试阵列；P2 |
| 工艺／状态边界 | 数字存储；多级适用性未主张 |
| 访问与判断 | 本轮公开取得全文，已核验。厂商公开作者稿含论文正文、工艺和阵列测量；封面为转载说明，实际题名在后续页。 |
| 主文位置 | [RRAM-03_2022_Weebit_28nm.pdf](literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf) |
| 版本／附件 | Weebit 厂商托管作者接受稿，前附 IEEE 作者转载声明；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |

<a id="rram-04"></a>

### RRAM-04 — MB85AS4MT — Memory ReRAM 4M (512 K × 8) Bit SPI

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Fujitsu Semiconductor；厂商 datasheet，DS501-00045-1v0-E；2016-12 |
| 链接 | [官方页面](https://www.fujitsu.com/global/documents/products/devices/semiconductor/memory/reram/MB85AS4MT-DS501-00045-1v0-E.pdf) · [机构／作者／原厂入口 1](https://download.mikroe.com/documents/datasheets/MB85AS4MT.pdf) |
| 用途标签 | 普通写入完成；操作粒度；存储时序定义 |
| 预期支撑 | 少见公开商用 ReRAM datasheet，提供 write-buffer 与内部写入／busy 语义；只能交叉核查普通存储完整事务，不能拿 SPI 频率替代 RRAM cell 读出。 |
| 层级／优先级 | 整芯片存储规格；P2 |
| 工艺／状态边界 | 普通数字存储 |
| 访问与判断 | 本轮公开取得全文，已核验。Fujitsu 原厂数据表从开发板厂商合法文档镜像取得，封面确认 2016.12 和文件编号；不声称该器件为 28 nm。 |
| 主文位置 | [RRAM-04_2016_MB85AS4MT.pdf](literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 旧资料保留理由 | 公开商用 ReRAM 原始 datasheet 稀少，保留完整普通存储时序定义。 |

<a id="rram-05"></a>

### RRAM-05 — A 28-nm RRAM Computing-in-Memory Macro Using Weighted Hybrid 2T1R Cell Array and Reference Subtracting Sense Amplifier for AI Edge Inference

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Wang Ye；Linfang Wang；Zhidao Zhou 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2023-10 |
| 链接 | [DOI: 10.1109/jssc.2023.3280357](https://doi.org/10.1109/jssc.2023.3280357) · [出版页面](https://ieeexplore.ieee.org/document/10145046/) |
| 用途标签 | 28 nm 专用感测；CIM 求值桥接；局部并行组织 |
| 预期支撑 | foundry RRAM 的解耦存储／计算路径及 reference-subtracting sense amplifier 补另一类 28 nm 阵列读出结构，防止只依赖 NeuRRAM 单实现。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（专用 RRAM 外围）；WH-2T1R／权重映射待全文核查 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |


<a id="06_mram"></a>

## 06 — MRAM

Jung 的电阻求和与 Chiu 的集成 spintronic macro 提供求值桥接，1T1MTJ／2T2MTJ 存储 macro 和 Everspin STT 产品资料补读写服务。器件机制、互补单元和自终止写入需分别保留；这里没有把不同 MTJ／感测实现混为单一实测芯片。

<a id="mram-01"></a>

### MRAM-01 — A crossbar array of magnetoresistive memory devices for in-memory computing

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Seungchul Jung；Hyungwoo Lee；Sungmeen Myung 等（完整作者见 manifest）；Nature 601, 211–216；2022 |
| 链接 | [DOI: 10.1038/s41586-021-04196-6](https://doi.org/10.1038/s41586-021-04196-6) · [机构／作者／原厂入口 1](https://ciqm.harvard.edu/uploads/2/3/3/4/23349210/jung2022.pdf) |
| 用途标签 | 读写服务；CIM 求值桥接；互补单元与局部并行度 |
| 预期支撑 | 实际电阻求和 MRAM 阵列与 TDC 读出给出读写及互补编码线索；仅支持其实际器件／求值机制，不自动代表所有 MRAM。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 二值互补 MTJ；电阻求和／TDC |
| 访问与判断 | 已有全文，已复制并核验。已有正式正文含 Methods 与 Extended Data，阵列、更新、时钟边界已初筛。 |
| 主文位置 | [MRAM-01_2022_ResistanceSum_Crossbar.pdf](literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf) |
| 版本／附件 | Published article including Methods and Extended Data；主文含 Methods／Extended Data；独立补充包尚未完整核验，R1 如依赖其中信息再定向补，不重复请求主文。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/jung2022.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_jung2022 |

<a id="mram-02"></a>

### MRAM-02 — A CMOS-integrated spintronic compute-in-memory macro for secure AI edge devices

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Y.-C. Chiu；W.-S. Khwa；C.-S. Yang 等（完整作者见 manifest）；Nature Electronics 6, 534–543；2023 |
| 链接 | [DOI: 10.1038/s41928-023-00994-0](https://doi.org/10.1038/s41928-023-00994-0) · [机构／作者／原厂入口 1](https://www.nature.com/articles/s41928-023-00994-0) |
| 用途标签 | CIM 求值桥接；局部并行度；独立 macro 交叉核查 |
| 预期支撑 | CMOS 集成 spintronic macro 补真实局部服务机制、精度和写入路径；与 Jung 的电阻求和实现分开核查。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | STT-MRAM；具体求值／写入步骤待全文 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="mram-03"></a>

### MRAM-03 — A 1-Mb 28-nm 1T1MTJ STT-MRAM With Single-Cap Offset-Cancelled Sense Amplifier and In Situ Self-Write-Termination

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Qing Dong；Zhehong Wang；Jongyup Lim 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2019-01 |
| 链接 | [DOI: 10.1109/jssc.2018.2872584](https://doi.org/10.1109/jssc.2018.2872584) · [出版页面](https://ieeexplore.ieee.org/document/8493263/) |
| 用途标签 | 写入完成与终止；感测服务；28 nm 专用外围 |
| 预期支撑 | 1T1MTJ 存储 macro 的 self-write-termination 和 offset-cancelled sense amplifier 补完整写入终点及局部读出，避免将外部脉冲等同普通写周期。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（专用 MRAM 外围）；binary 1T1MTJ STT-MRAM |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | 实测 28 nm STT-MRAM 自终止写入／感测电路，直接支撑局部服务与更新完成定义。 |

<a id="mram-04"></a>

### MRAM-04 — A 28nm 32Kb embedded 2T2MTJ STT-MRAM macro with 1.3ns read-access time for fast and reliable read applications

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Tzu-Hsien Yang；Kai-Xiang Li；Yen-Ning Chiang 等（完整作者见 manifest）；2018 IEEE International Solid - State Circuits Conference - (ISSCC)；2018-02 |
| 链接 | [DOI: 10.1109/isscc.2018.8310394](https://doi.org/10.1109/isscc.2018.8310394) · [出版页面](https://ieeexplore.ieee.org/document/8310394/) |
| 用途标签 | 读侧时间尺度；感测与操作粒度；结构交叉核查 |
| 预期支撑 | 互补 2T2MTJ 局部读出补与 1T1MTJ 不同的面积／可靠性／感测组织；题名 read-access 指标仅是读入口，不能当完整多位 MVM。 |
| 层级／优先级 | 阵列／局部 macro；P2 |
| 工艺／状态边界 | 直接的 28 nm 证据（专用 MRAM 外围）；binary 2T2MTJ STT-MRAM |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | 直接 28 nm 互补 MRAM 阵列原始电路，有助区别不同读机制。 |

<a id="mram-05"></a>

### MRAM-05 — EMxxLX — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Everspin Technologies；官方 datasheet，v3.4；2025 |
| 链接 | [官方页面](https://www.everspin.com/design-support) · [机构／作者／原厂入口 1](https://www.everspin.com/file/158451/download) |
| 用途标签 | 直接更新语义；字节粒度；普通存储交叉核查 |
| 预期支撑 | 商业 STT-MRAM 的字节读写、无需物理擦除及 NOR 兼容模拟命令用于更新方式核查。xSPI 速率仅是产品端口服务；工艺未由此 datasheet 证明为 28 nm。 |
| 层级／优先级 | 整芯片／封装接口；P2 |
| 工艺／状态边界 | 功能与时序定义参考（该文件不证明 28 nm）；binary STT-MRAM；NOR erase 指令可模拟 |
| 访问与判断 | 官方 PDF 网页内容可读；本地文件未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-05_2025_EMxxLX_v3p4.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | 网页工具可读 81 页官方 v3.4 PDF；直接下载返回 404，候补人工获取。 |


<a id="07_pcm"></a>

## 07 — PCM

两种 IBM 多核／多 tile 实验和 TSMC 的 SLC／MLC macro 用于局部求值与并行写入，ST 合作器件测量及 Sc-Sb-Te 原始论文补材料与写入终点差异。SET、RESET、模拟精度与完整编程过程分别核查；两个 IBM 芯片是不同实验，但不是完全独立的工艺团队交叉证据。

<a id="pcm-01"></a>

### PCM-01 — A 64-core mixed-signal in-memory compute chip based on phase-change memory for deep neural network inference

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Manuel Le Gallo；Riduan Khaddam-Aljameh；Milos Stanisavljevic 等（完整作者见 manifest）；Nature Electronics 6, 680–693；2023 |
| 链接 | [DOI: 10.1038/s41928-023-01010-1](https://doi.org/10.1038/s41928-023-01010-1) · [机构／作者／原厂入口 1](https://arxiv.org/pdf/2212.02872) |
| 用途标签 | CIM 求值桥接；并行 writehead；多级编程与校验 |
| 预期支撑 | 完整多相位求值、writehead 组织和闭环编程为 PCM 局部参考情景提供结构；预印本的测量／RTL 时序需保留证据类型。 |
| 层级／优先级 | 阵列／局部 macro 及整芯片；P1 |
| 工艺／状态边界 | 模拟多级 PCM、差分映射 |
| 访问与判断 | 已有全文，已复制并核验。现有 arXiv 全文含宏结构和编程说明；未将预印本数值声明为已与期刊逐项相同，不重复要求内容相近正式版。 |
| 主文位置 | [PCM-01_2023_PCM64_Core.pdf](literature/07_pcm/PCM-01_2023_PCM64_Core.pdf) |
| 版本／附件 | arXiv:2212.02872, PDF dated December 7, 2022; pre-publication version；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 交叉证据边界 | 相关实验／团队族：ibm_pcm_platform；同族条目不自动视作独立交叉验证。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/pcm64.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_pcm64 |

<a id="pcm-02"></a>

### PCM-02 — An analog-AI chip for energy-efficient speech recognition and transcription

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | S. Ambrogio；P. Narayanan；A. Okazaki 等（完整作者见 manifest）；Nature；2023-08-23 |
| 链接 | [DOI: 10.1038/s41586-023-06337-5](https://doi.org/10.1038/s41586-023-06337-5) · [出版页面](https://www.nature.com/articles/s41586-023-06337-5) · [机构／作者／原厂入口 1](https://www.nature.com/articles/s41586-023-06337-5.pdf) · [机构／作者／原厂入口 2](https://research.ibm.com/publications/an-analog-ai-chip-for-energy-efficient-speech-recognition-and-transcription) |
| 用途标签 | CIM 求值桥接；行并行编程；局部与系统边界 |
| 预期支撑 | 不同 IBM 芯片的模拟 tile、并行编程及脉宽输入用于交叉核查服务组织；只使用可识别局部边界，不以语音系统总体性能替代本地操作。 |
| 层级／优先级 | 阵列／tile、芯片与系统；P1 |
| 工艺／状态边界 | 模拟多级、2/4 PCM-per-weight |
| 访问与判断 | 本轮公开取得全文，已核验。已取得正式正文含 Methods／Extended Data；初筛确认 tile 架构、输入和编程组织，未做吞吐换算。 |
| 主文位置 | [PCM-02_2023_AnalogAI_Speech.pdf](literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；主文含 Methods／Extended Data；独立补充包尚未完整核验，R1 如依赖其中信息再定向补，不重复请求主文。 |
| 交叉证据边界 | 相关实验／团队族：ibm_pcm_platform；同族条目不自动视作独立交叉验证。 |

<a id="pcm-03"></a>

### PCM-03 — A 40-nm, 2M-Cell, 8b-Precision, Hybrid SLC-MLC PCM Computing-in-Memory Macro with 20.5 - 65.0TOPS/W for Tiny-Al Edge Devices

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Win-San Khwa；Yen-Cheng Chiu；Chuan-Jia Jhang 等（完整作者见 manifest）；2022 IEEE International Solid- State Circuits Conference (ISSCC)；2022-02-20 |
| 链接 | [DOI: 10.1109/isscc42614.2022.9731670](https://doi.org/10.1109/isscc42614.2022.9731670) · [出版页面](https://ieeexplore.ieee.org/document/9731670/) |
| 用途标签 | CIM 求值桥接；binary／multi-level；操作粒度 |
| 预期支撑 | TSMC／NTHU PCM macro 补独立产业团队与 SLC/MLC 模式差异，核查写入、读出精度和求值服务，避免仅依 IBM 平台确定范围。 |
| 层级／优先级 | 阵列／局部 macro；P1 |
| 工艺／状态边界 | hybrid SLC／MLC（分模式） |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="pcm-04"></a>

### PCM-04 — Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Feng Rao；Keyuan Ding；Yuxing Zhou 等（完整作者见 manifest）；Science；2017-12-15 |
| 链接 | [DOI: 10.1126/science.aao3212](https://doi.org/10.1126/science.aao3212) · [出版页面](https://www.science.org/doi/10.1126/science.aao3212) |
| 用途标签 | 器件写入时间尺度；材料差异；独立量级交叉核查 |
| 预期支撑 | Sc-Sb-Te 原始研究用于解释材料／成核条件导致的极快写入报道。保留它作为条件性器件基线，不将单次晶化脉冲替代 GST 多级阵列完整写入。 |
| 层级／优先级 | 器件／材料；P2 |
| 工艺／状态边界 | Sc-Sb-Te 晶化／相变条件；非默认多级 PCM 写入 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | 关键器件写入基线，能解释跨材料时间尺度差异，不能用于拼接最佳芯片参数。 |

<a id="pcm-05"></a>

### PCM-05 — Phase Change Memory Drift Compensation in Spiking Neural Networks Using a Non-Linear Current Scaling Strategy

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Joao Henrique Quintino Palhares；Nikhil Garg；Yann Beilliard 等（完整作者见 manifest）；Journal of Low Power Electronics and Applications；2024-10-22 |
| 链接 | [DOI: 10.3390/jlpea14040050](https://doi.org/10.3390/jlpea14040050) · [出版页面](https://www.mdpi.com/2079-9268/14/4/50) · [机构／作者／原厂入口 1](https://mdpi-res.com/d_attachment/jlpea/jlpea-14-00050/article_deploy/jlpea-14-00050.pdf) |
| 用途标签 | SET／RESET 与多级编程；测试条件；独立量级交叉核查 |
| 预期支撑 | ST 合作的 Ge-rich GST 器件测量提供多级编程脉冲、终态与漂移测试条件，用来补高速 headline 之外的实际操作约束。外围／网络仿真与器件测量分开。 |
| 层级／优先级 | 器件测量与电路／网络仿真；P2 |
| 工艺／状态边界 | Ge-rich GST 多级 PCM；SET／RESET 分开 |
| 访问与判断 | 本轮公开取得全文，已核验。已核验正式全文与 PCM Characterization 小节：确有器件编程和测试方法，不是仅综述漂移。 |
| 主文位置 | [PCM-05_2024_PCM_Drift.pdf](literature/07_pcm/PCM-05_2024_PCM_Drift.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |


<a id="08_feram_hfo2"></a>

## 08 — FeRAM（HfO₂-based）

仅将实际 HfO₂ 系电容存储／相关阵列作为主体：C2FeRAM 桥接、Sony／SK hynix／Micron 阵列、共掺杂 hafnia 器件和 FeCAP–memristor 集成研究互补。破坏性读／恢复、极化判读与模拟状态的完成条件留待全文审阅；传统 PZT 商用 F-RAM 不占核心候选。

<a id="feram-01"></a>

### FERAM-01 — A 2-Transistor-2-Capacitor Ferroelectric Edge Compute-in-Memory Scheme with Disturb-Free Inference and High Endurance

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Xiaoyang Ma；Shan Deng；Juejian Wu 等（完整作者见 manifest）；IEEE Electron Device Letters 44(7), 1088–1091；2023 |
| 链接 | [DOI: 10.1109/LED.2023.3274362](https://doi.org/10.1109/LED.2023.3274362) · [机构／作者／原厂入口 1](https://par.nsf.gov/servlets/purl/10417066) |
| 用途标签 | CIM 求值桥接；读／恢复机制；写入步骤 |
| 预期支撑 | 2T2C C2FeRAM 将 HZO 电容与非破坏性求值连接，可解释普通 1T1C 破坏性存储读和计算读的差别；不能将分立实验写成完整实测 CIM。 |
| 层级／优先级 | HfO₂ 系 FeCAP 器件实验与电路仿真；P1 |
| 工艺／状态边界 | HfO₂ 系 FeCAP；2T2C |
| 访问与判断 | 已有全文，已复制并核验。作者接受稿题名、FeCAP 实验和电路方案已初筛；页面 running header 模板字样保留为版本说明。 |
| 主文位置 | [FERAM-01_2023_C2FeRAM.pdf](literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf) |
| 版本／附件 | Accepted manuscript; running header still template text; use PDF page numbers；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/c2feram2023.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_c2feram2023 |

<a id="feram-02"></a>

### FERAM-02 — Low Voltage and High Speed 1Xnm 1T1C FE-RAM with Ultra-Thin 5nm HZO

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Minchul Sung；Kwangmyoung Rho；Jayong Kim 等（完整作者见 manifest）；2021 IEEE International Electron Devices Meeting (IEDM)；2021-12-11 |
| 链接 | [DOI: 10.1109/iedm19574.2021.9720545](https://doi.org/10.1109/iedm19574.2021.9720545) · [出版页面](https://ieeexplore.ieee.org/document/9720545/) |
| 用途标签 | 读写时间尺度；1T1C 阵列操作；低压条件 |
| 预期支撑 | SK hynix 的超薄 HZO 1T1C FE-RAM 补实际低压读写与状态判读条件；需全文核对读取是否含恢复、操作粒度和偏置。 |
| 层级／优先级 | 器件／存储阵列；P1 |
| 工艺／状态边界 | 5 nm HZO；1T1C FeRAM |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="feram-03"></a>

### FERAM-03 — SoC Compatible 1T1C FeRAM Memory Array Based on Ferroelectric Hf0.5Zr0.5O2

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Jun Okuno；Takafumi Kunihiro；Kenta Konishi 等（完整作者见 manifest）；2020 IEEE Symposium on VLSI Technology；2020-06 |
| 链接 | [DOI: 10.1109/vlsitechnology18217.2020.9265063](https://doi.org/10.1109/vlsitechnology18217.2020.9265063) · [出版页面](https://ieeexplore.ieee.org/document/9265063/) · [机构／作者／原厂入口 1](https://publica.fraunhofer.de/entities/publication/03fdad8b-f3a2-4201-9987-faacc3b81673) |
| 用途标签 | 阵列读写；局部操作粒度；独立交叉核查 |
| 预期支撑 | Sony／NaMLab／Fraunhofer 阵列集成研究补局部操作电路与 program/read 实验，避免只由电容切换脉冲估计 FeRAM 服务。 |
| 层级／优先级 | 器件／1T1C 阵列及外围；P1 |
| 工艺／状态边界 | Hf0.5Zr0.5O2；1T1C |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 旧资料保留理由 | HZO 1T1C SoC-compatible 原始阵列集成基线，直接补电容到阵列操作的桥梁。 |

<a id="feram-04"></a>

### FERAM-04 — NVDRAM: A 32Gb Dual Layer 3D Stacked Non-volatile Ferroelectric Memory with Near-DRAM Performance for Demanding AI Workloads

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | N. Ramaswamy；A. Calderoni；J. Zahurak 等（完整作者见 manifest）；2023 International Electron Devices Meeting (IEDM)；2023-12-09 |
| 链接 | [DOI: 10.1109/iedm45741.2023.10413848](https://doi.org/10.1109/iedm45741.2023.10413848) · [出版页面](https://ieeexplore.ieee.org/document/10413848/) |
| 用途标签 | 完整读写服务；操作粒度；大阵列交叉核查 |
| 预期支撑 | Micron 的 HfO₂ 系非易失铁电存储补器件到三维阵列的实际读写与外围实现；需从整芯片中辨识可用于局部参考的边界，不能把标题 near-DRAM 当数值时序。 |
| 层级／优先级 | 阵列／die 与整芯片；P1 |
| 工艺／状态边界 | HZO 1T1C 铁电存储；不归为普通 DRAM |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |

<a id="feram-05"></a>

### FERAM-05 — Enhanced polarization switching characteristics of HfO2 ultrathin films via acceptor-donor co-doping

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Chao Zhou；Liyang Ma；Yanpeng Feng 等（完整作者见 manifest）；Nature Communications；2024-04-03 |
| 链接 | [DOI: 10.1038/s41467-024-47194-8](https://doi.org/10.1038/s41467-024-47194-8) · [出版页面](https://www.nature.com/articles/s41467-024-47194-8) · [机构／作者／原厂入口 1](https://www.nature.com/articles/s41467-024-47194-8.pdf) |
| 用途标签 | 器件切换时间尺度；测试偏置与终点；独立交叉核查 |
| 预期支撑 | La/Ta 共掺杂 HfO₂ 电容给出切换动力学及测量条件，补产业阵列之外的材料维度；不以 PUND／脉冲宽度直接代替存储读写周期。 |
| 层级／优先级 | 器件／铁电电容；P2 |
| 工艺／状态边界 | 共掺杂 HfO₂ 铁电电容 |
| 访问与判断 | 本轮公开取得全文，已核验。正式全文已核验题名、铁电薄膜和 switching 测试；已定位并获取 Supplementary Information。 |
| 主文位置 | [FERAM-05_2024_Codoped_Hafnia.pdf](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；已取得官方 Supplementary Information；数据／视频附件未作批量下载。 |
| 本地补充材料 | [FERAM-05_2024_Codoped_Hafnia_Supplement.pdf](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia_Supplement.pdf) |

<a id="feram-06"></a>

### FERAM-06 — A ferroelectric–memristor memory for both training and inference

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Michele Martemucci；François Rummens；Yannick Malot 等（完整作者见 manifest）；Nature Electronics；2025-09-22 |
| 链接 | [DOI: 10.1038/s41928-025-01454-7](https://doi.org/10.1038/s41928-025-01454-7) · [出版页面](https://www.nature.com/articles/s41928-025-01454-7) · [机构／作者／原厂入口 1](https://www.nature.com/articles/s41928-025-01454-7.pdf) |
| 用途标签 | FeCAP 阵列写入；并行粒度；训练／推理桥接 |
| 预期支撑 | 同片 Si-doped HfO₂ 的 FeCAP 和 memristor 阵列补近期阵列级证据；本组只用 FeCAP 支路支持 FeRAM，不能混入 memristor 的读写指标。 |
| 层级／优先级 | FeCAP／memristor 阵列与计算实验；P2 |
| 工艺／状态边界 | Si:HfO₂ FeCAP 为本组主体；memristor 支路另区分 |
| 访问与判断 | 本轮公开取得全文，已核验。已核验公开正式 PDF；初筛确认两类阵列分开测试，附补充资料。 |
| 主文位置 | [FERAM-06_2025_Ferroelectric_Memristor.pdf](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；已取得官方 Supplementary Information；数据／视频附件未作批量下载。 |
| 本地补充材料 | [FERAM-06_2025_Ferroelectric_Memristor_Supplement.pdf](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor_Supplement.pdf) |


<a id="09_gain_cell_edram"></a>

## 09 — Gain-cell eDRAM

硅 gain-cell 实测存储、2T1C／3T1C CIM 和 oxide gain-cell 设计依据共同覆盖读写端口、保持和刷新。bulk、FD-SOI、氧化物通道和不同状态精度分开标注，普通 1T1C DRAM 不进入这一组。

<a id="gc-01"></a>

### GC-01 — Gain-Cell CIM: Leakage and Bitline Swing Aware 2T1C Gain-Cell eDRAM Compute in Memory Design with Bitline Precharge DACs and Compact Schmitt Trigger ADCs

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Shanshan Xie；Can Ni；Pulkit Jain 等（完整作者见 manifest）；VLSI Symposium, 112–113；2022 |
| 链接 | [DOI: 10.1109/VLSITechnologyandCir46769.2022.9830338](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338) · [机构／作者／原厂入口 1](https://sites.utexas.edu/CRL/files/2022/06/Gain_cell_CIM_VLSI2022.pdf) |
| 用途标签 | 完整求值；读写端口；保持与泄漏 |
| 预期支撑 | 明确 gain-cell 结构和输入位相位／ADC 读出，提供局部计算组织；写入路径与 refresh 条件需在后续与存储来源组合。 |
| 层级／优先级 | 2T1C gain-cell 局部 macro；P1 |
| 工艺／状态边界 | 65 nm CMOS 2T1C gain-cell；数字权重 |
| 访问与判断 | 已有全文，已复制并核验。原始 VLSI 全文已核验 2T1C 结构、独立读写端口、数据流和测量图；与 2021 年普通 1T1C eDRAM 区分。 |
| 主文位置 | [GC-01_2022_GainCell_CIM.pdf](literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf) |
| 版本／附件 | Published paper；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 复制来源 | `tasks/task1_table_i/sources/local-only/gaincell2022.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_gaincell2022 |

<a id="gc-02"></a>

### GC-02 — An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Robert Giterman；Alexander Fish；Narkis Geuli 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2018-07 |
| 链接 | [DOI: 10.1109/jssc.2018.2820145](https://doi.org/10.1109/jssc.2018.2820145) · [出版页面](https://ieeexplore.ieee.org/document/8356248/) · [机构／作者／原厂入口 1](https://www.eng.biu.ac.il/temanad/publications/) · [机构／作者／原厂入口 2](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8356248) |
| 用途标签 | 28 nm 读写服务；保持／刷新；普通 gain-cell 粒度 |
| 预期支撑 | 28 nm bulk 4T gain-cell 存储原始实测补读写端口、retention 与刷新边界；approximate storage 的错误容忍条件不能忽略。 |
| 层级／优先级 | 实测 gain-cell 局部 macro；P1 |
| 工艺／状态边界 | 直接的 28 nm 证据（gain-cell 存储）；28 nm bulk mixed-VT 4T gain-cell |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 身份核验说明 | Crossref 题名的内联 LaTeX 格式规范为 VT；未改变题意。 |
| 旧资料保留理由 | 直接实测 28 nm gain-cell 读写／保持基线，而非以普通 DRAM 参数替代。 |
| 相关版本 | 2017 — An 800 Mhz mixed-VT 4T gain-cell embedded DRAM in 28 nm CMOS bulk process for approximate computing applications；相关会议版；优先本条期刊文，不同时索取，不增加独立证据数。 [官方／作者入口](https://doi.org/10.1109/esscirc.2017.8094587) |

<a id="gc-03"></a>

### GC-03 — Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Shuhan Liu；Koustav Jana；Kasidit Toprasertpong 等（完整作者见 manifest）；IEEE Transactions on Electron Devices 71(5), 3329–3335；2024-05 |
| 链接 | [DOI: 10.1109/TED.2024.3372938](https://doi.org/10.1109/TED.2024.3372938) · [出版页面](https://poplab.stanford.edu/pdfs/Liu-DesignOSFETgainCell-ted24.pdf) |
| 用途标签 | 读写设计方法；保持与刷新；28 nm 映射桥接 |
| 预期支撑 | oxide／hybrid gain-cell 设计指南连接器件、互连和 macro 服务，提供可复算建模方法；28 nm macro 结果属于模型／仿真，不是统一实测芯片。 |
| 层级／优先级 | 器件依据与局部 macro 仿真／建模；P2 |
| 工艺／状态边界 | 直接的 28 nm 模型条件／其他工艺器件依据（须逐项区分）；OS–OS／hybrid gain-cell，保留不同通道结构 |
| 访问与判断 | 本轮公开取得全文，已核验。已核验作者正式 PDF、模型与器件来源；具体参数尚未采集。 |
| 主文位置 | [GC-03_2024_OxideGainCell.pdf](literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |

<a id="gc-04"></a>

### GC-04 — A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Jiahao Song；Xiyuan Tang；Haoyang Luo 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2024-03 |
| 链接 | [DOI: 10.1109/jssc.2023.3339887](https://doi.org/10.1109/jssc.2023.3339887) · [出版页面](https://ieeexplore.ieee.org/document/10360848/) |
| 用途标签 | 写入建立；多级状态；CIM 求值与保持 |
| 预期支撑 | 电流编程动态 cascode 3T1C 多级 eDRAM 补不同于二值 2T1C 的写入／保持和求值步骤；保留其模拟状态接受条件。 |
| 层级／优先级 | 3T1C gain-cell 型局部 macro；P1 |
| 工艺／状态边界 | 3T1C current-programmed dynamic-cascode MLC |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 相关版本 | 2023 — A Calibration-Free 15-level/Cell eDRAM Computing-in-Memory Macro with 3T1C Current-Programmed Dynamic-Cascoded MLC achieving 233-to-304-TOPS/W 4b MAC；相关会议版；优先本条期刊文，不同时索取，不增加独立证据数。 [官方／作者入口](https://doi.org/10.1109/cicc57935.2023.10121207) |

<a id="gc-05"></a>

### GC-05 — An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Ping-Chun Wu；Win-San Khwa；Jui-Jen Wu 等（完整作者见 manifest）；IEEE Journal of Solid-State Circuits；2025-01 |
| 链接 | [DOI: 10.1109/jssc.2024.3470215](https://doi.org/10.1109/jssc.2024.3470215) · [出版页面](https://ieeexplore.ieee.org/document/10716755/) |
| 用途标签 | 完整精度求值；局部并行度；近期产业交叉核查 |
| 预期支撑 | 16 nm 产业 gain-cell macro 的 integer／floating-point 两模式补现代控制及精度组织。对 28 nm 仅为结构与量级交叉参考，不直接移用速率。 |
| 层级／优先级 | gain-cell 局部 macro；P2 |
| 工艺／状态边界 | 其他工艺的量级交叉参考（16 nm）；16 nm gain-cell；INT／FP 分模式 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 相关版本 | 2024 — 34.2 A 16nm 96Kb Integer/Floating-Point Dual-Mode-Gain-Cell-Computing-in-Memory Macro Achieving 73.3-163.3TOPS/W and 33.2-91.2TFLOPS/W for AI-Edge Devices；相关会议版；优先本条期刊文，不同时索取，不增加独立证据数。 [官方／作者入口](https://doi.org/10.1109/isscc49657.2024.10454447) |


<a id="10_fenor_3d"></a>

## 10 — 3D FeNOR／vertical FeFET

两篇指定 Zhou 原稿原位复制，并补 Feng 的 BEOL 3D FeNOR、POSTECH 三维 FeFET 及直接相关栅堆栈研究。Feng 会议／期刊两项保守合为一个资料包，Zhou 系列显式记录同团队关系；2026 原稿正文写明 AND-type，不因类别简称 FeNOR 改写其结构。

<a id="fenor-01"></a>

### FENOR-01 — 3D NOR-type FeFETs with Record Endurance of 10^11, Fast Erase of 50 ns, and Immediate Read-After-Write for In-Memory Learning

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yuejia Zhou；Runteng Zhu；Wenpu Luo 等（完整作者见 manifest）；Symposium on VLSI Technology and Circuits；2025-06-08 |
| 链接 | [DOI: 10.23919/vlsitechnologyandcir65189.2025.11074820](https://doi.org/10.23919/vlsitechnologyandcir65189.2025.11074820) · [出版页面](https://ieeexplore.ieee.org/document/11074820/) · [官方页面](https://doi.org/10.23919/VLSITechnologyandCir65189.2025.11074820) |
| 用途标签 | 器件读写时间尺度；更新步骤；局部阵列结构 |
| 预期支撑 | 指定原稿支撑 IGO／HZO 三层 NOR-type 器件脉冲、写后读及阵列结构；不能把脉冲宽度和层数直接变为完整 CIM 服务。 |
| 层级／优先级 | 器件／三层小阵列与 CIM 仿真；P1 |
| 工艺／状态边界 | IGO／HZO；NOR-type；器件偏置分条件 |
| 访问与判断 | 已有全文，已复制并核验。根目录原始 3 页题名、作者与正文结构已核验；页 1 与器件／阵列图快速初筛，未提取新范围。 |
| 主文位置 | [FENOR-01_2025_3DNOR_FeFET.pdf](literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf) |
| 版本／附件 | User-supplied 3-page manuscript; no version/date identifier on PDF；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 交叉证据边界 | 相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。 |
| 复制来源 | `2025--Yuejia Zhou--3D NOR-Type FeFETs with Record Endurance of 1011 , Fast Erase of 50 Ns, and Immediate Read-After-Write for In-Memory Learning.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_zhou2025 |

<a id="fenor-02"></a>

### FENOR-02 — 3D Vertical FeFET Array with Record Endurance (>10^12), Fast Writing (±2V, 20 ns), Disturb Immunity, and Kb-scale Verification for High Density 1T RAM

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yuejia Zhou；Yuancheng Yang；Liang Chen 等（完整作者见 manifest）；Symposium on VLSI Technology and Circuits T11.1；2026-06-14 |
| 链接 | [DOI: 10.1109/vlsitechnologyandcir65830.2026.11577291](https://doi.org/10.1109/vlsitechnologyandcir65830.2026.11577291) · [出版页面](https://ieeexplore.ieee.org/document/11577291/) · [官方页面](https://vlsi26.mapyourshow.com/8_0/sessions/session-details.cfm?ScheduleID=251) |
| 用途标签 | 器件读写；写扰与并行选择条件；局部阵列验证 |
| 预期支撑 | 指定原稿补半选／相邻单元扰动、写入方案、Kb 图案验证和读出建模。正文明确 AND-type vertical array；单 cell、图案验证与外围仿真分别保留。 |
| 层级／优先级 | 器件／四层阵列与 TCAD／SPICE；P1 |
| 工艺／状态边界 | IGO／HZO；AND-type vertical FeFET；SL/SS 与 O-rich/O-poor 分条件 |
| 访问与判断 | 已有全文，已复制并核验。根目录原稿 3 页已核验；2026-06-14 出版登记和作者／题名匹配。DOI 元数据把 > 误编码为 ¾，规范题名按 PDF 的 >10^12 保留。 |
| 主文位置 | [FENOR-02_2026_Vertical_FeFET_Array.pdf](literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf) |
| 版本／附件 | User-supplied 3-page manuscript; no version/date identifier on PDF；R0 未识别必须另取的补充文件；未将“未识别”写成“不存在”。 |
| 交叉证据边界 | 相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。 |
| 复制来源 | `2026--Yuejia Zhou--3D Vertical Fefet Array with Record Endurance (¾1012 ), Fast Writing (± 2 V, 20 Ns), Disturb Immunity, and Kb-Scale Verification for High Density 1T Ram.pdf`；逐字节 SHA-256 一致，原文件保留；前轮 ID：t1_zhou2026 |

<a id="fenor-03"></a>

### FENOR-03 — First Demonstration of BEOL-Compatible 3D Vertical FeNOR

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yang Feng；Dong Zhang；Chen Sun 等（完整作者见 manifest）；2024 IEEE Symposium on VLSI Technology and Circuits (VLSI Technology and Circuits)；2024-06-16 |
| 链接 | [DOI: 10.1109/vlsitechnologyandcir46783.2024.10631352](https://doi.org/10.1109/vlsitechnologyandcir46783.2024.10631352) · [出版页面](https://ieeexplore.ieee.org/document/10631352/) · [机构／作者／原厂入口 1](https://scholar.nycu.edu.tw/en/publications/first-demonstration-of-beol-compatible-3d-vertical-fenor/) |
| 用途标签 | 阵列结构；写扰与更新方式；独立团队交叉核查 |
| 预期支撑 | Feng 团队的 ZnO/MFMIS side-fin 3D FeNOR 补独立结构与写入／扰动线索。优先先取 FENOR-04 期刊文，避免一开始重复下载；两项的实验复用关系待全文确认。 |
| 层级／优先级 | 器件／BEOL 三维阵列；P3 |
| 工艺／状态边界 | ZnO／MFMIS BEOL vertical FeNOR |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 交叉证据边界 | 相关实验／团队族：feng_beol_fenor_2024_2025；同族条目不自动视作独立交叉验证。 FENOR-03／04 同团队直接相关系列，保守合为一个资料包；实验复用关系须全文核验。优先 FENOR-04。 |

<a id="fenor-04"></a>

### FENOR-04 — Efficient Large Scale Neural Network Acceleration With 3-D FeNOR-Based Computing-in-Memory Design

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yang Feng；Dong Zhang；Chen Sun 等（完整作者见 manifest）；IEEE Transactions on Electron Devices；2025-05 |
| 链接 | [DOI: 10.1109/ted.2025.3554164](https://doi.org/10.1109/ted.2025.3554164) · [出版页面](https://ieeexplore.ieee.org/document/10957835/) · [机构／作者／原厂入口 1](https://ieeexplore.ieee.org/ielam/16/11004132/10957835-aam.pdf) |
| 用途标签 | CIM 求值桥接；局部读出／并行条件；独立团队交叉核查 |
| 预期支撑 | 直接 3D FeNOR-CIM 原始研究补读出／权重映射和器件到参考设计的桥接，优先获取较完整的期刊版本。与 FENOR-03 高度相关，保守计一个资料包，不称两份独立交叉证据。 |
| 层级／优先级 | 器件／阵列及计算建模；P1 |
| 工艺／状态边界 | MFMIS 3D FeNOR；计算映射待全文 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 交叉证据边界 | 相关实验／团队族：feng_beol_fenor_2024_2025；同族条目不自动视作独立交叉验证。 FENOR-03／04 同团队直接相关系列，保守合为一个资料包；实验复用关系须全文核验。优先 FENOR-04。 |

<a id="fenor-05"></a>

### FENOR-05 — Highly-scaled and fully-integrated 3-dimensional ferroelectric transistor array for hardware implementation of neural networks

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Ik-Jyae Kim；Min-Kyu Kim；Jang-Sik Lee；Nature Communications；2023-01-31 |
| 链接 | [DOI: 10.1038/s41467-023-36270-0](https://doi.org/10.1038/s41467-023-36270-0) · [出版页面](https://www.nature.com/articles/s41467-023-36270-0) · [机构／作者／原厂入口 1](https://www.nature.com/articles/s41467-023-36270-0.pdf) |
| 用途标签 | 器件编程；三维阵列读出；独立结构交叉核查 |
| 预期支撑 | POSTECH 的真实三维 FeNAND／FeFET 阵列用于条件性的器件编程、垂直集成及 VMM 结构交叉核查。其串联 NAND 读路径不是 Zhou 的 NOR／AND，不能作为直接 FeNOR 读出速度或并行度证据。 |
| 层级／优先级 | 器件／三维 FeFET 阵列与计算实验；P2 |
| 工艺／状态边界 | HfZrOx 三维 FeNAND；串联选择、multiple layers／VMM 实验 |
| 访问与判断 | 本轮公开取得全文，已核验。已核验正文摘要明确 3D FeNAND，以及补充材料；仅保留直接相关的垂直 FeFET 编程和集成信息，不视为直接 FeNOR 独立验证。 |
| 主文位置 | [FENOR-05_2023_Integrated3D_FeFET.pdf](literature/10_fenor_3d/FENOR-05_2023_Integrated3D_FeFET.pdf) |
| 版本／附件 | 本地正式 PDF（已核验身份）；已取得官方 Supplementary Information；数据／视频附件未作批量下载。 |
| 本地补充材料 | [FENOR-05_2023_Integrated3D_FeFET_Supplement.pdf](literature/10_fenor_3d/FENOR-05_2023_Integrated3D_FeFET_Supplement.pdf) |

<a id="fenor-06"></a>

### FENOR-06 — Gate Stack Engineering of 3D Oxide Channel FeNOR Memory with High-Speed and Reliabilitity

| 字段 | 内容 |
| --- | --- |
| 身份／日期 | Yuejia Zhou；Ru Huang；Kechao Tang；2026 10th IEEE Electron Devices Technology & Manufacturing Conference (EDTM)；2026-03-01 |
| 链接 | [DOI: 10.1109/edtm65772.2026.11498024](https://doi.org/10.1109/edtm65772.2026.11498024) · [出版页面](https://ieeexplore.ieee.org/document/11498024/) |
| 用途标签 | 器件读写与偏置；栅堆栈差异；更新约束 |
| 预期支撑 | 直接比较 3D oxide-channel FeNOR 的 MFS/MFIS/MIFS/MIFIS 栅堆栈，有助解释脉冲与状态窗口的差异。来自 Zhou 相关团队，只作为机制补充，不增加独立团队数量。 |
| 层级／优先级 | 器件／三维 FeNOR；P2 |
| 工艺／状态边界 | 3D oxide-channel FeNOR；不同栅堆栈分条件 |
| 访问与判断 | 题录／摘要可读，主文未取得。仅依据核验后的题录、官方摘要或产品页面预判用途；尚未确认全文包含可直接使用的时间、精度、负载及并行约束。 |
| 主文位置 | 拟下载：`tasks/task1_table_i/rebuild/literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf` |
| 版本／附件 | 拟获取正式主文；机构／作者接受稿内容完整也可；未确认是否有独立 supplement；人工包请同时保存出版社列出的技术补充（如有）。 |
| 交叉证据边界 | 相关实验／团队族：zhou_igo_vertical；同族条目不自动视作独立交叉验证。 |

## 筛除与未纳入

- 前轮 Ambit、Dyamond 和普通 1T1C eDRAM-CIM 不属于本轮 gain-cell 类别；未新增独立 DRAM 类别。
- 传统 PZT 商用 F-RAM datasheet 不用于 HfO₂ FeRAM 核心证据。
- 检索中的 single-finger eDRAM 2024 条目尚未确认符合 gain-cell 结构，未为凑数列入精选；题录搜索记录只供追溯。
- 未经核实的 memory compiler 手册镜像、无时序／结构内容的厂商宣传页和 SSD 总吞吐未用于共同局部服务基线。
- 不把同团队会议／期刊扩展版、作者稿与正式版计算为独立的第三方交叉验证。
