# V2 验收与 SRAM DCIM 补选（R1 / V3）

2026-09-08。**V2 的 5/5 包到齐、已重命名，主文/附件身份匹配；本轮下载 PDF 0 份。** 四篇主文和一份 SI 均已检查正文及关键图表，未进入正式参数分析。

## 到件

| ID | 内容 | 页数 | 当前文件 |
|---|---|---:|---|
| PCM-06 | 主文 | 8 | [PCM-06_2021_RowWise_ClosedLoopProgramming.pdf](literature/07_pcm/PCM-06_2021_RowWise_ClosedLoopProgramming.pdf) |
| RRAM-06 | 主文 | 2 | [RRAM-06_2019_AutoForming_AutoWrite.pdf](literature/05_rram/RRAM-06_2019_AutoForming_AutoWrite.pdf) |
| SACIM-05 | 主文 | 5 | [SACIM-05_2024_GlobalBitlineCombining_8bit.pdf](literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf) |
| MRAM-06 | 主文 | 24 | [MRAM-06_2025_LosslessParallelSpintronicCIM.pdf](literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM.pdf) |
| PCM-04-SI | 技术 SI | 18 | [PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf](literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf) |

MRAM-06 是 24 页主文+Methods/Extended Data，另有已归档的 15 页 SI，二者不重复。PCM-04 的 18 页 SI 包含所需方法和 Figs.S1–S11。原名与哈希见 [到件记录](metadata/intake_v2_completed.json)。

## 新正文改变的判断

### SACIM-05 — 核心

28 nm 实测 6T SRAM macro；32 个 cell 共享 HIPCC，本地/全局 BL 与普通读写路径明确。8-bit 输入分成四组 2-bit DAC 电压并行输入；GBL-comb 将同位权部分和合并，SAR 数量由 96 减到 69，并以数字移位累加形成输出。

不是一个独立 8-bit DAC 直接驱动全部字线。voltage-stacking 有初始化、采样、叠加三阶段；输出数字位数不代表模拟无误精度；仍未明确普通写入的绝对完整服务周期。

定位：p.2 III-A/B、Fig.4；pp.3–4 III-C/D、IV、Figs.5–10；p.5 Fig.11。 [SACIM-05](LITERATURE_CATALOG.md#SACIM-05)

### RRAM-06 — 核心

实际 40 nm 2 Mb bipolar ReRAM；两组 IO/column 控制、等待组内完成、地址跳过、timeout 和 FORMING/SET/RESET 终止机制清楚。HRPW 把 page RESET 放在 idle，再对所需 cell SET，支持显式更新步骤/资源占用建模。

Fig.9 使用 normalized time unit，Fig.10 也是归一化时间/相对改善；全文没有因此补出绝对 page 延时。99% 改善包含 hidden-RESET，不能解释为省掉 RESET，FORMING 也不能算作每次更新。

定位：p.1 AF/ARST/ASET 与测量小节；p.2 Figs.3–10。 [RRAM-06](LITERATURE_CATALOG.md#RRAM-06)

### PCM-06 — 核心

14 nm PCM 原始逐行 CLT；同一 row 的 512 列共享幅度 DAC而各列使用独立脉宽。每次脉冲后读验，FPGA 算误差并装入下一轮脉宽；次级 PCM 可补偿过冲，器件/周期差异有实际测量。

“Fully on-chip MAC”不代表闭环调谐控制全部片上。60/120/240 ns 是示例脉冲，1.2 ns/tick 是读数编码；都不是完整写入周期。原文明确为连续模拟目标，不是固定离散级的商品 MLC。与 PCM-02 同技术线，不新增独立工艺证据。

定位：pp.3–5 III/IV、Figs.2–9；p.4 Fig.6；p.5 闭环算法。 [PCM-06](LITERATURE_CATALOG.md#PCM-06)

### MRAM-06 — 核心

实际 40 nm STT-MRAM 数字 CIM；bitcell 内乘法/数字化，64 bank 各 256×4，输入 MSB-first 位串行、bank 内并行乘加，多精度由累加和 bank 合并实现。写互补 MTJ 分两步，测试按 row 写后读验，错误 row 重写。

“Fully parallel”不是任意多位 MVM 一拍完成：4-bit 输入用四拍。数字无损算术也不保证所有电压下存储读无误；p.4 区分低压实测读错误与较高电压无观测错误。不能将最佳能效、时钟及无错条件拼接为同一工作点；未给出完整写验绝对周期。

定位：pp.2–5 Figs.2/3；pp.8–9 Methods；p.15 Extended Data Fig.2；已归档 SI Fig.2。 [MRAM-06](LITERATURE_CATALOG.md#MRAM-06)

### PCM-04 — 补充

补充材料确认 0.13 μm 平台、190 nm BEC 的 T-shaped 器件、外部源表/脉冲发生器和示波器；亚纳秒为特定材料/偏置下的器件 SET 结果，适合作材料时间尺度对照。

SI Fig.S6 刻意采用 2 ms 脉冲间隔避免累积作用，既不能把脉宽当连续写服务，也不能把 2 ms 当介质必需延时。S5/S6 的 700 ps 示例偏置不同，应保留各自条件；不支持整阵列或多级闭环写入速度。

定位：主文 pp.2–4；SI p.2 §2、p.8 Fig.S5、p.9 Fig.S6。 [PCM-04](LITERATURE_CATALOG.md#PCM-04)

## SRAM DCIM 为什么补这两篇

| ID | 互补作用 | 已核验程度 |
|---|---|---|
| [SDCIM-04](LITERATURE_CATALOG.md#SDCIM-04) | 有符号整数 MAC、符号扩展以及精度可调加法树；补现有 bit-serial/dynamic logic 之外的数字服务 | IEEE 官方摘要及出版记录；主文待审 |
| [SDCIM-05](LITERATURE_CATALOG.md#SDCIM-05) | 28 nm 数字 transpose SRAM，FF/BP 的局部方向/计算复用，精确与近似模式 | IEEE SSCS/作者网页/Crossref；主文待审；同主题 ISSCC 2025 不重复请求 |

现有 SDCIM-01/02/03 保留，新增后专属来源由 3 增至 5。两篇新候选的作者组合与原三篇不同；不是把同一芯片会议版/期刊版凑成两份。SDCIM-05 的确切扩展声明和测试继承关系留待期刊正文确认。

## 仍缺什么、哪些不用

- **当前明确的待下载文件只有 SDCIM-04/05 两篇主文。** 旧 V2 请求全部关闭，未发现新的必需附件。
- **没有新发现需要整篇删除的无关主文。** RRAM-06 虽只给归一化时间，仍补实际写入控制与 hidden-RESET 方法；保留并限制用途。PCM-04 的 SI 到件后改为材料补充，不能用亚纳秒值支撑连续阵列写入。
- **原来的归并/对照处理继续有效**：FENOR-03/04 同包；FENOR-05 是 FeNAND，仅作拓扑对照；旧 Everspin brief、SRAM 会议前作/slides 留版本目录，不占独立核心。
- **技术依据仍有边界缺口**：RRAM-06 的绝对 page 时间；3D NAND SLC 完整 program/erase 与 plane 约束；通用 28 nm compiler 完整时序库。现有材料已提供操作步骤、单器件响应和外围服务依据，不能因此判为不可估算。待确定具体参考模式后再决定是否需要补资料，本轮不继续泛化索取。
- **不追加以下 DCIM 候选**：hybrid-domain/current/TDC 论文不能仅因题名含 digital 就归为 DCIM；同主题 2025 ISSCC 转置稿不和 2026 JSSC 一起索取；两周期 Winograd 整处理器仍是有价值候补，但当前两篇更直接补局部 signed MAC/transpose，暂不扩大阅读负担。

本次已修正 11 个分类 README 中旧的“PDF 被 .gitignore 排除”说明；PDF 开放 Git 的用户设置保持。只更新 rebuild，未暂存/提交/推送，未改主论文或 Table II。
