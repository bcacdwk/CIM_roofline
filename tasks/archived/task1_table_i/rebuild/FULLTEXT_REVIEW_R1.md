# R1 正文适用性审阅（V3 更新）

截至 2026-09-08，**60 条本地主文已完成用途筛选**；43 核心、14 补充、1 条件保留、1 版本归并、1 结构对照。新增 SDCIM-04/05 仅核验题录/摘要，尚不计入全文审阅。

最新 V2 五包的正文发现、去留及 SRAM DCIM 补选理由见 [本轮报告](V2_INTAKE_AND_DCIM_REVIEW.md)。页码为本地 PDF 页序；本轮不做最终参数/吞吐范围。

## 00 — 28 nm CMOS 外围参考资料

**[CMOS-01](LITERATURE_CATALOG.md#CMOS-01) — 补充** · [本地 PDF](literature/00_cmos_periphery/CMOS-01_undated_IGADACT01C_v002.pdf)

正文定位：pp.1–2，Features／Specifications。

保留用途：官方明确 28 nm HPM、DAC 类型及输出电流／compliance 条件，适合作为输入服务的 IP 可实现性参考。

不能据此声称：没有指定 CIM 容性负载的建立时间；300 MHz 不能直接当作阵列输入稳定服务。文件未署出版日期。

本轮/此前处理：降为补充；统一输入时序优先由 SACIM-03 的实际 CIM 路径支撑。

**[CMOS-02](LITERATURE_CATALOG.md#CMOS-02) — 核心** · [本地 PDF](literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf)

正文定位：pp.2–6，Figs.1–7；pp.7–8，Figs.8–12。

保留用途：28 nm 实测差分 SAR；正文区分采样、逐次比较、CDAC 建立和时序保护。测试含输入 buffer 与参考电路，实测频谱随输入频率变化。

不能据此声称：PVT 表是后仿真；有效精度低于名义 10 bit。正文与 Fig.10 的 SNDR 数字不一致，后续不可混抄；CIM 共模与负载适配仍须建模。

本轮/此前处理：正文确认原用途，保留。

**[CMOS-03](LITERATURE_CATALOG.md#CMOS-03) — 核心** · [本地 PDF](literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf)

正文定位：pp.1–3，动态读写定义、IV-A／IV-C；pp.4–5，assist 比较。

保留用途：给出读写成功终点、back-to-back 服务、WL 脉宽与 BL 电容的显式参考条件；适合通用 SRAM 写入换算方法。

不能据此声称：28 nm、50 FO4 时钟及 128-cell 负载属于作者模型假设，不能写成量产 compiler 或流片保证。

本轮/此前处理：正文确认原用途，保留。

**[CMOS-04](LITERATURE_CATALOG.md#CMOS-04) — 补充** · [本地 PDF](literature/00_cmos_periphery/CMOS-04_2011_DualPort_SRAM.pdf)

正文定位：pp.2–6，Figs.6–14；pp.7–9，Table I、Figs.15–20。

保留用途：实测 28 nm 双端口 SRAM；局部 32 kb macro、64-bit word、双端口同址冲突与筛选方法清楚。

不能据此声称：shmoo 横轴是两端口 clock skew，不是读／写周期；Table I 没有独立的普通写入服务时间。

本轮/此前处理：降为端口冲突与局部边界补充；C 轮补 CMOS-07。

**[CMOS-05](LITERATURE_CATALOG.md#CMOS-05) — 补充** · [本地 PDF](literature/00_cmos_periphery/CMOS-05_2025_Interleaved_DAC.pdf)

正文定位：pp.3–4，III-A／III-B；pp.4–5，测量。

保留用途：28 nm 实测 8-bit 四通道交织电流舵 DAC，交织、相位校正和输出负载条件明确。

不能据此声称：16 GS/s 是四路交织输出；单 sub-DAC、100 Ω 差分负载、片外编码条件与 CIM 字线负载不同。未报告 CIM 输入建立保证。

本轮/此前处理：从通用输入基线候选降为其他负载下的 28 nm 交叉参考。

**[CMOS-06](LITERATURE_CATALOG.md#CMOS-06) — 条件保留** · [本地 PDF](literature/00_cmos_periphery/CMOS-06_2025_ReconfigurableSAR.pdf)

正文定位：pp.3–6，Fig.1、冗余转换、性能小节。

保留用途：28 nm SAR 的完整转换序列、两种精度模式、参考 buffer 开销及输入范围有明确设计依据。

不能据此声称：性能为仿真，且本地为 advance/accepted PDF；不提供独立流片验证。

本轮/此前处理：保留设计参考，不能将 headline GS/s 标成实测。

**[CMOS-07](LITERATURE_CATALOG.md#CMOS-07) — 核心** · [本地 PDF](literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf)

正文定位：作者修订稿 pp.1–2，Figs.1–2；pp.4–6，WL tracking；pp.8–9，Table II。

保留用途：C 轮找到的公开作者稿：实际 28 nm eFlash CMOS 平台上的同步 2RW 8T SRAM，区分 clock、WL 脉冲、read access 与端口操作；Table II 有 macro 配置和频率。

不能据此声称：28 nm 为 eFlash 优化的高阈值工艺；不能等同一般 logic SRAM compiler。本文与 CMOS-04 有作者重叠。公开 R2 稿含排版占位，不宣称正式版；当前内容足够用途判断，无需重复请求。

本轮/此前处理：新增共同感测／SRAM 服务核心候选，补 CMOS-04 未直接给周期信息的缺口；已在用户停止下载指令前归档。

## 01 — SRAM ACIM

**[SACIM-01](LITERATURE_CATALOG.md#SACIM-01) — 核心** · [本地 PDF](literature/01_sram_acim/SACIM-01_2022_Scalable_IMC.pdf)

正文定位：pp.4–7，CIMU／CIMA 与 BPBS；p.9，V-A／Table III。

保留用途：可区分本地 CIMA、SIMD、片上网络及权重装载网络；完整精度需位平面与数字累加配合。实测数字时钟与 ADC 输出服务率分列。

不能据此声称：目标 500 MHz 与受封装供电限制的实测频率不同；28 MB 权重 buffer 未集成在原型中；整芯片吞吐不能直接作为 local macro 服务。

本轮/此前处理：正文确认原用途，保留。

**[SACIM-02](LITERATURE_CATALOG.md#SACIM-02) — 核心** · [本地 PDF](literature/01_sram_acim/SACIM-02_2025_PICO_RAM.pdf)

正文定位：pp.4–7，Figs.4–14；pp.8–10，测量与 PVT。

保留用途：实测 65 nm 电荷域 macro；同一组电容依次用于两阶段 DAC、MAC、移位累加与 ADC，说明外围开销可重用，不能简单串加独立转换器延时。

不能据此声称：本地为作者稿，2024 预印本与 2025 期刊记录关联；65 nm 不是共同 28 nm 的直接速度证据。

本轮/此前处理：正文确认原用途，保留。

**[SACIM-03](LITERATURE_CATALOG.md#SACIM-03) — 核心** · [本地 PDF](literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf)

正文定位：p.2，扩展版说明、Figs.1–3；p.3，Fig.5／III；p.4，Figs.6–8。

保留用途：2023 期刊明确新增流片测量；28 nm 128×256 9T1C 阵列、128 路 4-bit 输入 DAC、64 路 4-bit ADC，给出 reset/evaluation/readout 关系与 die photo。

不能据此声称：2022 会议稿为相同工作前作，不能另算独立实测证据；4-bit ADC 输出不等于完整无损 MAC 精度；普通权重写入周期仍未闭合。

本轮/此前处理：提升为共同 28 nm 输入／求值桥接的核心来源；纠正仅依据会议前作的仿真印象。

**[SACIM-04](LITERATURE_CATALOG.md#SACIM-04) — 核心** · [本地 PDF](literature/01_sram_acim/SACIM-04_2023_C2C_ChargeDomain.pdf)

正文定位：p.5，Fig.10；pp.7–9，Figs.16–20；pp.10–11，测量。

保留用途：实际 22 nm 电荷域 macro；DAC/MAC 建立可重叠，SAR 内部八步放在另一半周期；R2R 驱动选型明确考虑 C2C 无法驱动的扇出负载。

不能据此声称：完整周期与内部 SAR 步骤不能混用；工艺不是 28 nm。

本轮/此前处理：正文确认原用途，保留。

**[SACIM-05](LITERATURE_CATALOG.md#SACIM-05) — 核心** · [本地 PDF](literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf)

正文定位：p.2 III-A/B、Fig.4；pp.3–4 III-C/D、IV、Figs.5–10；p.5 Fig.11。

保留用途：28 nm 实测 6T SRAM macro；32 个 cell 共享 HIPCC，本地/全局 BL 与普通读写路径明确。8-bit 输入分成四组 2-bit DAC 电压并行输入；GBL-comb 将同位权部分和合并，SAR 数量由 96 减到 69，并以数字移位累加形成输出。

不能据此声称：不是一个独立 8-bit DAC 直接驱动全部字线。voltage-stacking 有初始化、采样、叠加三阶段；输出数字位数不代表模拟无误精度；仍未明确普通写入的绝对完整服务周期。

本轮/此前处理：V2 主文已到，实际提供共同 28 nm 输入/ADC 共享、局部读写和完整求值桥接，正式保留。

## 02 — SRAM DCIM

**[SDCIM-01](LITERATURE_CATALOG.md#SDCIM-01) — 核心** · [本地 PDF](literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf)

正文定位：p.1，Fig.1、完整 VMM 步骤；pp.2–4，架构／测量。

保留用途：28 nm 数字 6T macro；128-bit 普通写入端口与 CIM 控制分开；8-bit 128×16 VMM 需要 64 个时钟，提供完整精度服务粒度。

不能据此声称：一个 clock 不是一次完整 8-bit VMM；写端口宽度不等于已量测独立写入周期。

本轮/此前处理：补正写端口为 128 bit，避免与输出维度 16 混淆。

**[SDCIM-02](LITERATURE_CATALOG.md#SDCIM-02) — 补充** · [本地 PDF](literature/02_sram_dcim/SDCIM-02_2023_BitReconfigurable_CIM.pdf)

正文定位：pp.2–4，Figs.3–8；p.5，测量比较。

保留用途：65 nm 数字 macro 给出重构运算、n-bit 加法、位串行乘法和 carry 写回的逐周期关系。

不能据此声称：精度与运算类型改变所需周期；不能把 65 nm headline TOPS/W 直接映射为共同 28 nm 服务。

本轮/此前处理：正文确认原用途，保留。

**[SDCIM-03](LITERATURE_CATALOG.md#SDCIM-03) — 核心** · [本地 PDF](literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf)

正文定位：p.1，memory/CIM 模式、8-clock 展开；p.2，Figs.11.7.2–6。

保留用途：28 nm 动态逻辑数字 macro；先存权重再计算，8-bit 输入按八拍展开，并有可选 post-sum 维度。

不能据此声称：文中引言的普通 SRAM 小于 1 ns 属背景陈述；测得 clock 与完整精度输出须区分。35 页作者 slides 是同源解释资料。

本轮/此前处理：正文确认原用途，保留。

## 03 — 2D NOR Flash

**[NOR-01](LITERATURE_CATALOG.md#NOR-01) — 核心** · [本地 PDF](literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf)

正文定位：pp.7、22–32；p.45，Table 16；AC timing 小节。

保留用途：完整厂商 datasheet 明确 512-byte 写 buffer、32-byte ECC page、128 KB erase sector；内置擦除含 pre-program，typ/max 和负载／温度脚注可追溯。

不能据此声称：这是 65 nm GL-S 军规器件；effective per-word 数字是整 buffer 摊销值；读接口时序不是 CIM 模拟求值时间。

本轮/此前处理：正文确认原用途，保留。

**[NOR-02](LITERATURE_CATALOG.md#NOR-02) — 核心** · [本地 PDF](literature/03_nor_2d/NOR-02_2019_W25Q128JV_RevG.pdf)

正文定位：p.14，BUSY；pp.37–43，program／erase；pp.65–66，AC 表。

保留用途：Winbond Rev.G 给出 1–256-byte page program、4/32/64 KB 擦除、BUSY 完成定义及 typ/max；正文指出 Quad 输入加速可能被内部编程时间淹没。

不能据此声称：SPI 传输率不能替代编程完成或 cell 读出；只支持普通 binary 存储模式的更新时间尺度。

本轮/此前处理：正文确认原用途，保留。

**[NOR-03](LITERATURE_CATALOG.md#NOR-03) — 补充** · [本地 PDF](literature/03_nor_2d/NOR-03_2022_SST26VF064B_RevK.pdf)

正文定位：pp.10–14，状态／命令；pp.25–31，编程／挂起；pp.45–49，AC；p.82，SFDP。

保留用途：Microchip 独立产品系列补 page、erase、suspend/resume 与 self-timed BUSY；正式时序表和 SFDP 超时定义可交叉核查。

不能据此声称：SFDP 最大 timeout 不应冒充 typ；与 NOR-04/05 同为 SST 相关生态，不将其全部视为独立器件团队。

本轮/此前处理：正文确认原用途，保留。

**[NOR-04](LITERATURE_CATALOG.md#NOR-04) — 核心** · [本地 PDF](literature/03_nor_2d/NOR-04_2017_EmbeddedNOR_Classifier.pdf)

正文定位：pp.1–2，II–IV；pp.3–4，Figs.4–16。

保留用途：实际嵌入式 NOR 模拟分类器，区分输入串行装载与网络内部传播；权重细调、half-select disturb 和神经元外围均影响整体服务。

不能据此声称：实测原型与更先进 ESF3 工艺预测分开；细调设定精度并非最精确单 cell 示范值；同 NOR-05 的研究关系不独立。

本轮/此前处理：正文确认原用途，保留。

**[NOR-05](LITERATURE_CATALOG.md#NOR-05) — 核心** · [本地 PDF](literature/03_nor_2d/NOR-05_2016_NOR_ModelBased_Tuning.pdf)

正文定位：pp.1–2，模型与 Fig.1 调谐流程。

保留用途：100-cell 实验提供 write-verify 算法、脉冲数与目标调谐精度的关系，是普通 Flash 到模拟权重更新的重要桥接。

不能据此声称：固定脉冲数不是完整更新时间；不是大规模并行 array 写入保证；与 NOR-04 同团队。

本轮/此前处理：正文确认原用途，保留。

## 04 — 3D NAND Flash

**[NAND-01](LITERATURE_CATALOG.md#NAND-01) — 核心** · [本地 PDF](literature/04_nand_3d/NAND-01_2016_Micron_3DNAND.pdf)

正文定位：p.2，产品／时序表。

保留用途：Micron 官方资料虽为两页 flyer，正文实际有 MLC/TLC 分列的 read/program/erase typ/max、页／块尺寸和具体料号，值得保留。

不能据此声称：不是完整部件 datasheet，部分并行命令／busy 约束仍缺；2016 年而非近期下载年。

本轮/此前处理：正文确认原用途，保留。

**[NAND-02](LITERATURE_CATALOG.md#NAND-02) — 核心** · [本地 PDF](literature/04_nand_3d/NAND-02_2026_KIOXIA_6Plane_QLC.pdf)

正文定位：p.1，架构与模式；pp.2–3，Figs.15.1.1–7。

保留用途：Sandisk/KIOXIA 2026 原始 QLC 芯片；六 plane、物理/逻辑 page 区别、verify 与读搜索明确，还含 QLC 芯片的 SLC burst 模式。

不能据此声称：die program throughput 包含内部并行；SLC burst 不是独立 SLC 产品；完整 erase 条件仍不足。

本轮/此前处理：修正厂家归属为 Sandisk/KIOXIA，取消“完全没有 SLC 模式来源”的笼统缺口。

**[NAND-03](LITERATURE_CATALOG.md#NAND-03) — 核心** · [本地 PDF](literature/04_nand_3d/NAND-03_2025_SKhynix_321Layer_QLC.pdf)

正文定位：p.1，programming／HV 配置；p.2，Fig.30.5.6。

保留用途：SK hynix 321-layer QLC 实际芯片，给出 page-program 时间、六 plane 与 page 大小；HV 供电、WL 电阻与干扰条件可支持特殊驱动分析。

不能据此声称：75 MB/s 是 die 并行 program 结果；不能当作单 page latency 或外部 I/O 速度。

本轮/此前处理：正文确认原用途，保留。

**[NAND-04](LITERATURE_CATALOG.md#NAND-04) — 核心** · [本地 PDF](literature/04_nand_3d/NAND-04_2021_NAND_Codesign.pdf)

正文定位：pp.2–4，II、Table 1、Fig.3；后续建模小节。

保留用途：给出 NAND 串读、映射、64-block subarray 边界和 RC／HSPICE 求值方法，可复用估算思路。

不能据此声称：Table 1 是作者估计；外围为 32 nm 并另用高压器件，不能称统一 28 nm 实测。器件数据与 NAND-05 有来源关联。

本轮/此前处理：正文确认原用途，保留。

**[NAND-05](LITERATURE_CATALOG.md#NAND-05) — 核心** · [本地 PDF](literature/04_nand_3d/NAND-05_2019_3DNAND_nvCIM.pdf)

正文定位：pp.1–2，器件与映射；pp.3–4，Figs.1–16。

保留用途：实际 16-layer 64 Gb SLC SGVC 器件与电流分布，用 SSL／BL／SL 解释多位输入及 SLC 复制编码；补直接 SLC 结构证据。

不能据此声称：多位感测及 accelerator 指标含设计预估，不是完整已流片 CIM 性能；缺完整 SLC program/erase 服务。

本轮/此前处理：正文确认原用途，保留。

## 05 — RRAM

**[RRAM-01](LITERATURE_CATALOG.md#RRAM-01) — 核心** · [本地 PDF](literature/05_rram/RRAM-01_2022_NeuRRAM.pdf)

正文定位：p.10，Methods：编程／控制；p.27，Extended Data Fig.12。

保留用途：NeuRRAM 正文含完整 set-read/reset-read 闭环、导电目标容差、超时条件与 MVM 实测；读／写测试条件可以分开记录。

不能据此声称：1–10 ns 控制脉冲能力不能替代实际微秒级 program/verify 配置；全网效果与 local MVM 分开。出版页未列独立技术 SI PDF，不再笼统请求附件。

本轮/此前处理：正文确认原用途，保留。

**[RRAM-02](LITERATURE_CATALOG.md#RRAM-02) — 核心** · [本地 PDF](literature/05_rram/RRAM-02_2025_HybridProgramming.pdf)

正文定位：pp.3–6，Figs.2–8；后续芯片测试。

保留用途：28 nm 实测 macro，分段 WL、单 cell verify、八步 ADC 与 1T1R/2T2R 混合闭环相互对应；提供程序步骤与容差。

不能据此声称：速度改善主要按平均脉冲数比较，不能从倍数独立得到绝对完整写周期。

本轮/此前处理：C 轮补 RRAM-06 的本地 page SET/RESET 控制证据。

**[RRAM-03](LITERATURE_CATALOG.md#RRAM-03) — 补充** · [本地 PDF](literature/05_rram/RRAM-03_2022_Weebit_28nm.pdf)

正文定位：pp.2–5，raw reliability、读扰与 Program and verify。

保留用途：Weebit/CEA-Leti 实际阵列对照 raw 与 P&V 的分布，说明固定脉冲、温度、可靠性终点改变可用写策略。

不能据此声称：重点是可靠性；读扰应力脉冲不是完整 array access。不能提供独立的完整 CIM 求值周期。

本轮/此前处理：正文确认原用途，保留。

**[RRAM-04](LITERATURE_CATALOG.md#RRAM-04) — 补充** · [本地 PDF](literature/05_rram/RRAM-04_2016_MB85AS4MT.pdf)

正文定位：pp.7–13，WRITE/WIP；p.17，AC：tWC；pp.19–21，接口图。

保留用途：正式 ReRAM 产品资料区分写 buffer、串行数据接收与非易失提交；tWC 表按数据翻转比例给出内部完整写周期。

不能据此声称：内部 tWC 为毫秒量级，不能用 5 MHz SPI 或单 cell ns 切换替换，也不能强行推广到其他 RRAM。

本轮/此前处理：保留真实慢产品作为完整周期／层级反例，不能因不符期望量级而删除。

**[RRAM-05](LITERATURE_CATALOG.md#RRAM-05) — 核心** · [本地 PDF](literature/05_rram/RRAM-05_2023_WeightedHybrid_2T1R.pdf)

正文定位：p.3，Fig.4；pp.5–7，Figs.10、18；测量环境。

保留用途：28 nm 2T1R 混合阵列，binary HRS/LRS 与不同晶体管尺寸构造空间权重；完整读流程含 PH0 稳定和 PH1–4 参考扣除。

不能据此声称：Fig.18 实测 66 ns 与估计优化 13 ns 必须分列；测试板外部 DAC 供偏置；缺完整写入/verify 周期。

本轮/此前处理：纠正 headline 优化值可能被误当实测及“多 bit 等于多级 RRAM cell”的风险。

**[RRAM-06](LITERATURE_CATALOG.md#RRAM-06) — 核心** · [本地 PDF](literature/05_rram/RRAM-06_2019_AutoForming_AutoWrite.pdf)

正文定位：p.1 AF/ARST/ASET 与测量小节；p.2 Figs.3–10。

保留用途：实际 40 nm 2 Mb bipolar ReRAM；两组 IO/column 控制、等待组内完成、地址跳过、timeout 和 FORMING/SET/RESET 终止机制清楚。HRPW 把 page RESET 放在 idle，再对所需 cell SET，支持显式更新步骤/资源占用建模。

不能据此声称：Fig.9 使用 normalized time unit，Fig.10 也是归一化时间/相对改善；全文没有因此补出绝对 page 延时。99% 改善包含 hidden-RESET，不能解释为省掉 RESET，FORMING 也不能算作每次更新。

本轮/此前处理：V2 正文确认方法有用；纠正“可能补齐绝对 page 时间”的期待，仅将归一化结果用于方法/比例参考。

## 06 — MRAM

**[MRAM-01](LITERATURE_CATALOG.md#MRAM-01) — 核心** · [本地 PDF](literature/06_mram/MRAM-01_2022_ResistanceSum_Crossbar.pdf)

正文定位：pp.6–8，Methods：MTJ write/read、weight update、operating frequency。

保留用途：28 nm 电阻串联求和、TDC 读出及互补 MTJ 权重；Methods 明确一行左侧、右侧分两次并行编程，每次一个写时钟。

不能据此声称：两写步骤、read resistance sum 和 ordinary STT RAM 感测不是同一机制；正文 scaling 是分析。出版附件为视频，不缺另一份技术 SI PDF。

本轮/此前处理：正文确认原用途，保留。

**[MRAM-02](LITERATURE_CATALOG.md#MRAM-02) — 补充** · [本地 PDF](literature/06_mram/MRAM-02_2023_Spintronic_CIM.pdf)

正文定位：pp.2–4、p.7 Fig.4、Methods；SI pp.3–10，Notes 1–4。

保留用途：22 nm STT macro 的正文明确 near-memory 数字 dot-product：sense 输出送数字引擎；SI 提供 PUF 写回、普通感测和访问时间测量边界。

不能据此声称：PUF 双 cell 写回不能替代一般权重更新；稀疏/ ReLU early termination 不等于固定全精度服务；非 Jung 电阻求和路径。

本轮/此前处理：降为近存数字替代情景；已自动补齐真正的 13 页 SI；C 轮另找 MRAM-06 的 bitcell 内数字乘法。

**[MRAM-03](LITERATURE_CATALOG.md#MRAM-03) — 核心** · [本地 PDF](literature/06_mram/MRAM-03_2019_SelfWriteTermination.pdf)

正文定位：pp.3–7，Figs.7–21，read timing／write termination。

保留用途：28 nm 1T1MTJ 实测 macro，local subarray/SA、预充与 offset cancel、写稳定与自终止信号明确；读写成功率随时间/温度改变。

不能据此声称：读写指标附 BER 条件；自终止的节能收益不自动证明缩短固定外部写周期。

本轮/此前处理：正文确认原用途，保留。

**[MRAM-04](LITERATURE_CATALOG.md#MRAM-04) — 补充** · [本地 PDF](literature/06_mram/MRAM-04_2018_2T2MTJ_ReadMacro.pdf)

正文定位：p.1，CREVSA；p.2，Figs.30.3.2–6。

保留用途：28 nm 2T2MTJ 实测快速读，包含预充、发展与感测三阶段，可独立核查读侧电路量级。

不能据此声称：互补物理单元与逻辑 bit 数不同；读 access 不能替代写时间或 CIM 多位求值。

本轮/此前处理：正文确认原用途，保留。

**[MRAM-05](LITERATURE_CATALOG.md#MRAM-05) — 补充** · [本地 PDF](literature/06_mram/MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf)

正文定位：pp.15、41–48，WRITE/ERASE；pp.69–71，AC；pp.81–82，修订史。

保留用途：用户下载的是 2026-07-23 v3.7，已替代原请求 v3.4；支持 back-to-back 写且无页跨越限制，给出读写命令与恢复条件。

不能据此声称：封装 xSPI 不是局部 cell 服务；ERASE 是产品兼容命令，不能据命令名称断言 STT 介质须先物理擦除。旧 brief 信息由 v3.7 覆盖。

本轮/此前处理：接受更新版本，不算缺件；额外 2023 brief 移入 versions，退出有效证据计数。

**[MRAM-06](LITERATURE_CATALOG.md#MRAM-06) — 核心** · [本地 PDF](literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM.pdf)

正文定位：pp.2–5 Figs.2/3；pp.8–9 Methods；p.15 Extended Data Fig.2；已归档 SI Fig.2。

保留用途：实际 40 nm STT-MRAM 数字 CIM；bitcell 内乘法/数字化，64 bank 各 256×4，输入 MSB-first 位串行、bank 内并行乘加，多精度由累加和 bank 合并实现。写互补 MTJ 分两步，测试按 row 写后读验，错误 row 重写。

不能据此声称：“Fully parallel”不是任意多位 MVM 一拍完成：4-bit 输入用四拍。数字无损算术也不保证所有电压下存储读无误；p.4 区分低压实测读错误与较高电压无观测错误。不能将最佳能效、时钟及无错条件拼接为同一工作点；未给出完整写验绝对周期。

本轮/此前处理：V2 正文与 SI 齐，作为区别 Jung 模拟求和/Chiu near-memory 的核心机制；补正摘要可能引出的单周期印象。

## 07 — PCM

**[PCM-01](LITERATURE_CATALOG.md#PCM-01) — 核心** · [本地 PDF](literature/07_pcm/PCM-01_2023_PCM64_Core.pdf)

正文定位：pp.2–3，diagonal programming/ADC；Methods 与 p.10，Power measurements。

保留用途：64-core 芯片的 diagonal selection 一次选不同 row/column 的器件，局部 write DAC、SET/RESET 形状与读 ADC 边界清楚。

不能据此声称：论文的部分 latency 由 RTL 得到，不能全部称直接测量；14 nm、四 PCM/cell 与其他芯片不同。附加视频不是必需时序文献。

本轮/此前处理：正文确认原用途，保留。

**[PCM-02](LITERATURE_CATALOG.md#PCM-02) — 核心** · [本地 PDF](literature/07_pcm/PCM-02_2023_AnalogAI_Speech.pdf)

正文定位：p.3，Fig.1f；pp.9–10，Methods：weight programming、controller、calibration。

保留用途：14 nm 芯片支持 row-wise 同时调谐 512 个权重，但一次选每权重的一个 PCM；闭环、校正与 tile 控制在正文交代。

不能据此声称：约 1 GHz controller clock 不是一次完整 MVM 或写入；写算法细节转引 ref.4，值得获取原始 2021 TED。

本轮/此前处理：C 轮新增 PCM-06，同一 IBM 技术线的细节补充，不算独立工艺交叉验证。

**[PCM-03](LITERATURE_CATALOG.md#PCM-03) — 核心** · [本地 PDF](literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf)

正文定位：p.1，Figs.11.3.2–6 的说明；pp.2–3，图与 summary。

保留用途：40 nm 实测 PCM CIM，8-bit weight 以 2 SLC+3 MLC 编码，8-bit input 默认八拍；VSA 四阶段与 sparsity 重排解释求值粒度。

不能据此声称：低功耗全 MLC 与混合模式不同；input-reordering 的跳过拍数依赖数据；没有完整 SET/RESET 更新周期。

本轮/此前处理：正文确认原用途，保留。

**[PCM-04](LITERATURE_CATALOG.md#PCM-04) — 补充** · [本地 PDF](literature/07_pcm/PCM-04_2017_Subnanosecond_Nucleation.pdf)

正文定位：主文 pp.2–4；SI p.2 §2、p.8 Fig.S5、p.9 Fig.S6。

保留用途：补充材料确认 0.13 μm 平台、190 nm BEC 的 T-shaped 器件、外部源表/脉冲发生器和示波器；亚纳秒为特定材料/偏置下的器件 SET 结果，适合作材料时间尺度对照。

不能据此声称：SI Fig.S6 刻意采用 2 ms 脉冲间隔避免累积作用，既不能把脉宽当连续写服务，也不能把 2 ms 当介质必需延时。S5/S6 的 700 ps 示例偏置不同，应保留各自条件；不支持整阵列或多级闭环写入速度。

本轮/此前处理：18 页 SI 已补齐，移除缺件/等待标签；有用但只留材料对照，不作为 PCM 完整写入核心。

**[PCM-05](LITERATURE_CATALOG.md#PCM-05) — 补充** · [本地 PDF](literature/07_pcm/PCM-05_2024_PCM_Drift.pdf)

正文定位：p.3，§2.1–2.2；后续漂移补偿验证。

保留用途：28 nm FD-SOI 相关 PCM 原始器件测试明确 75 ns SET/RESET、幅值／compliance 和多次序列；用读后等待跟踪漂移。

不能据此声称：75 ns 是实验单脉冲；1000 次测试序列不是每次逻辑写入的必需脉冲数；SNN 补偿结果不能直接转为 local CIM 服务。

本轮/此前处理：正文确认原用途，保留。

**[PCM-06](LITERATURE_CATALOG.md#PCM-06) — 核心** · [本地 PDF](literature/07_pcm/PCM-06_2021_RowWise_ClosedLoopProgramming.pdf)

正文定位：pp.3–5 III/IV、Figs.2–9；p.4 Fig.6；p.5 闭环算法。

保留用途：14 nm PCM 原始逐行 CLT；同一 row 的 512 列共享幅度 DAC而各列使用独立脉宽。每次脉冲后读验，FPGA 算误差并装入下一轮脉宽；次级 PCM 可补偿过冲，器件/周期差异有实际测量。

不能据此声称：“Fully on-chip MAC”不代表闭环调谐控制全部片上。60/120/240 ns 是示例脉冲，1.2 ns/tick 是读数编码；都不是完整写入周期。原文明确为连续模拟目标，不是固定离散级的商品 MLC。与 PCM-02 同技术线，不新增独立工艺证据。

本轮/此前处理：V2 主文补齐 PCM-02 ref.4 的实际算法与外围调度，保留核心方法证据。

## 08 — FeRAM（HfO₂-based）

**[FERAM-01](LITERATURE_CATALOG.md#FERAM-01) — 核心** · [本地 PDF](literature/08_feram_hfo2/FERAM-01_2023_C2FeRAM.pdf)

正文定位：pp.2–3，Figs.3–6、II–III。

保留用途：C2FeRAM 的 2T2C 路径解释非破坏读与电流求和；行写入明确先 write-0 再 write-1，MLC 需 verify；离散 FeCAP/MOS 实验支持器件机制。

不能据此声称：大阵列／网络 latency 为模型，3D 集成为提议；不能当作完整已流片 28 nm FeRAM CIM。非破坏性读也不消除浮置节点漏电恢复。

本轮/此前处理：正文确认原用途，保留。

**[FERAM-02](LITERATURE_CATALOG.md#FERAM-02) — 核心** · [本地 PDF](literature/08_feram_hfo2/FERAM-02_2021_UltrathinHZO_1T1C.pdf)

正文定位：pp.1–2，II-B／III-B；pp.3–4，Figs.3、8–10。

保留用途：SK hynix 8 Gb 1T1C、5 nm HZO 真正阵列；SAWAR 读后明确重写；write-recovery 扫描显示极化随写时间继续增加。

不能据此声称：20 ns 对应部分极化响应，不是全部 cell/完整周期通用终点；5 nm 薄膜厚度不是 CMOS 工艺节点。

本轮/此前处理：正文确认原用途，保留。

**[FERAM-03](LITERATURE_CATALOG.md#FERAM-03) — 核心** · [本地 PDF](literature/08_feram_hfo2/FERAM-03_2020_SoC_1T1C_HZO.pdf)

正文定位：p.1，64 kbit array demonstration；p.2，Figs.8–11。

保留用途：Sony/NaMLab 的 64 kbit HZO 1T1C 实测读写 shmoo；Fig.9 明确读状态翻转和 data writeback 阶段。

不能据此声称：8 ns sense 与 14 ns write 是分别测量，不把单独 sense 当成含恢复的读周期；不是 28 nm 外围流片。

本轮/此前处理：正文确认原用途，保留。

**[FERAM-04](LITERATURE_CATALOG.md#FERAM-04) — 核心** · [本地 PDF](literature/08_feram_hfo2/FERAM-04_2023_NVDRAM_32Gb.pdf)

正文定位：p.2，Memory Cell／Component Performance；p.4，Fig.13。

保留用途：正文明确 5.7 nm 掺杂 HfZrOx 电容、双层 1T1C；Fig.13 同时给 sensing、writeback、precharge 和完整 tRC，确属本轮 HfO₂ FeRAM。

不能据此声称：短 tWR 将部分恢复代价转到 tRP；不能摘取 10 ns 宣称完整写入结束。LPDDR5 兼容不等于 DRAM 相同阵列时序。

本轮/此前处理：正文与图像确认材料归属及恢复周期；PDF 字体编码异常但页面正常，不需要重新下载。

**[FERAM-05](LITERATURE_CATALOG.md#FERAM-05) — 补充** · [本地 PDF](literature/08_feram_hfo2/FERAM-05_2024_Codoped_Hafnia.pdf)

正文定位：pp.4–7，switching kinetics／Methods；已归档 SI。

保留用途：La/Ta 共掺 hafnia 原始材料测量提供厚度、偏置、成核/畴壁与极化终点，适合解释同类器件时间差异。

不能据此声称：外延薄膜/电极/测量层级不同于集成 1T1C array；高速切换不是 macro 服务。

本轮/此前处理：正文确认原用途，保留。

**[FERAM-06](LITERATURE_CATALOG.md#FERAM-06) — 补充** · [本地 PDF](literature/08_feram_hfo2/FERAM-06_2025_Ferroelectric_Memristor.pdf)

正文定位：pp.3–5，FeCAP/混合阵列；p.9，Methods；已归档 SI。

保留用途：真实共集成 FeCAP 与 memristor 及权重转移实验，给 FeCAP 电压/时间扫描、读写节点与外部脉冲测量条件。

不能据此声称：推理主路径是 memristor；全突触含多 FeCAP 和两个 memristor，不能把混合推理性能归为纯 FeRAM CIM；网络部分为仿真。

本轮/此前处理：保留 HfO₂ 电容测量，降低纯 FeRAM 求值桥接权重。

## 09 — Gain-cell eDRAM

**[GC-01](LITERATURE_CATALOG.md#GC-01) — 核心** · [本地 PDF](literature/09_gain_cell_edram/GC-01_2022_GainCell_CIM.pdf)

正文定位：p.1，三步 MAV／Measurement Results；p.2，Figs.2–7。

保留用途：65 nm 2T1C gain-cell CIM 的读写端口分离、BL 输入预充、泄漏夹位和 ST-ADC 有明确电路与测试证据。

不能据此声称：2-bit 输入顺序展开及 complementary weight 不等于单次完整 8-bit 运算；不能取普通 1T1C DRAM 代替。

本轮/此前处理：正文确认原用途，保留。

**[GC-02](LITERATURE_CATALOG.md#GC-02) — 核心** · [本地 PDF](literature/09_gain_cell_edram/GC-02_2018_MixedVT_4T_GainCell.pdf)

正文定位：pp.4–8，Figs.4–11；pp.9–10，retention/availability。

保留用途：28 nm 4T IFGC 实测 128×32 macro，WWL 升压与时序、SA、读写频率和保持分布；直接支撑刷新占用与局部边界。

不能据此声称：5 µs 刷新对应文中约 99% bit 可靠性条件，不是全 bit 无误保证；平均保持不能代替最差 cell。

本轮/此前处理：正文确认原用途，保留。

**[GC-03](LITERATURE_CATALOG.md#GC-03) — 核心** · [本地 PDF](literature/09_gain_cell_edram/GC-03_2024_OxideGainCell.pdf)

正文定位：pp.2–4，top-down macro/refresh；pp.4–6，器件规格。

保留用途：以 28 nm macro 模型将保持、读取电流和刷新阻塞联系起来，能支持从 oxide 器件到 local service 的透明换算。

不能据此声称：GEMTOO/Timeloop 是设计评估，非实测完整 oxide CIM 芯片。

本轮/此前处理：正文确认原用途，保留。

**[GC-04](LITERATURE_CATALOG.md#GC-04) — 核心** · [本地 PDF](literature/09_gain_cell_edram/GC-04_2024_DynamicCascoded_MLC.pdf)

正文定位：pp.4–7，Figs.4–11；p.8，Fig.12／measurement。

保留用途：65 nm 3T1C MLC gain-cell，电流写入自校正，先电压粗写再电流精写；完整 CIM 含 precharge、DTC 求值和 SAR。

不能据此声称：5 ns 仅粗写；60 ns 建立结论在 Fig.12 仿真中，不能称实测完整更新；180 ns compute 与保持漂移精度相关。

本轮/此前处理：正文确认原用途，保留。

**[GC-05](LITERATURE_CATALOG.md#GC-05) — 核心** · [本地 PDF](literature/09_gain_cell_edram/GC-05_2025_DualMode_GainCell.pdf)

正文定位：pp.2–3，4T GC+STU 架构；pp.6–8，Figs.13–20。

保留用途：16 nm 4T gain-cell 存储配 7T stationary unit 的数字 CIM，明确 storage update、stationary update、self-refresh 和计算重叠模式。

不能据此声称：计算使用 stationary 数据；更新 storage 不代表同一权重立即参加计算。INT/FP 服务不同，也不是 3T1C 电荷域方案。

本轮/此前处理：正文确认原用途，保留。

## 10 — 3D FeNOR／vertical FeFET

**[FENOR-01](LITERATURE_CATALOG.md#FENOR-01) — 核心** · [本地 PDF](literature/10_fenor_3d/FENOR-01_2025_3DNOR_FeFET.pdf)

正文定位：p.1，Fabrication/Speed/Simulation；pp.2–3，Figs.2–12。

保留用途：指定 Zhou 2025 文件确认 8×8×3 IGO/HZO NOR-type；PGM/ERS、read-after-write、层间差异及 cell 逻辑有实际测量。

不能据此声称：NN benchmark 与大阵列延时为模拟；单 cell/小阵列测试不等于全精度 macro 周期。根目录原稿保持不动。

本轮/此前处理：正文确认原用途，保留。

**[FENOR-02](LITERATURE_CATALOG.md#FENOR-02) — 核心** · [本地 PDF](literature/10_fenor_3d/FENOR-02_2026_Vertical_FeFET_Array.pdf)

正文定位：p.1，array/disturb/benchmark；pp.2–3，Figs.7–11。

保留用途：指定 Zhou 2026 文件实际为 3D-AND FeFET；32×32×4 制造结构与 16×16×4 验证范围分开，写入/半选/相邻扰动方案有直接依据。

不能据此声称：20 ns 为偏置和结构限定的 switching；TCAD/SPICE read 与密度预测不当作实测宏；不因简称 FeNOR 忽略 AND 结构。

本轮/此前处理：正文确认原用途，保留。

**[FENOR-03](LITERATURE_CATALOG.md#FENOR-03) — 版本归并** · [本地 PDF](literature/10_fenor_3d/versions/FENOR-03_2024_BEOL_Vertical_FeNOR.pdf)

正文定位：pp.1–2，Figs.1–14；对照 FENOR-04 p.2。

保留用途：2024 会议稿记录首个 BEOL vertical FeNOR、脉冲窗口和阵列逻辑；2025 TED 正文明确扩展此稿。保留以追踪测试条件和版本差异。

不能据此声称：不再独立占一个核心交叉来源；同一数据不能双重计数；正文文本层乱码，图像已核验。

本轮/此前处理：归入 FENOR-04 同一证据包，保留原稳定 ID 与版本文件。

**[FENOR-04](LITERATURE_CATALOG.md#FENOR-04) — 核心** · [本地 PDF](literature/10_fenor_3d/FENOR-04_2025_FeNOR_CIM_Design.pdf)

正文定位：p.2，版本声明；pp.4–6，Figs.7–14、III–IV。

保留用途：ZnO/MFMIS 3D FeNOR 器件、阵列电流逻辑实测，与 4096×4096 网络/外围仿真分开；扩展版补写入偏置与变异条件。

不能据此声称：大阵列 4096×4096 不是流片尺寸；高电压时 charge injection 影响 MW；system energy 不作为实测统一外围。

本轮/此前处理：正文确认原用途，保留。

**[FENOR-05](LITERATURE_CATALOG.md#FENOR-05) — 结构对照** · [本地 PDF](literature/10_fenor_3d/comparisons/FENOR-05_2023_Vertical_FeNAND.pdf)

正文定位：pp.2–5，Results／FeNAND；Methods 与已归档 SI。

保留用途：实际垂直 HfZrOx/InZnOx FeNAND，支持串联选择、pass bias、层间编程等对照，有助解释 NOR/AND 与 NAND 拓扑差异。

不能据此声称：不是 FeNOR，不能占 FeNOR 核心速度来源或直接迁移 NOR 并行度。

本轮/此前处理：退出 FeNOR 核心，保留在对照目录并显式命名 FeNAND。

**[FENOR-06](LITERATURE_CATALOG.md#FENOR-06) — 核心** · [本地 PDF](literature/10_fenor_3d/FENOR-06_2026_GateStack_FeNOR.pdf)

正文定位：pp.1–2，B/C；p.3，Figs.5–10。

保留用途：2026 EDTM 对照 MFS/MFIS/MIFS/MIFIS，写速度随栅堆栈与偏置改变，可解释 Zhou 系列与其他 FeNOR 差异。

不能据此声称：与 Zhou 同团队，不能当独立外部验证；耐久与写速测试偏置不同，不能拼接最优点。

本轮/此前处理：正文确认原用途，保留。
