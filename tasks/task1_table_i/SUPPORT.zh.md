# Table I 中文支撑说明

基线：`6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`。访问日期：2026-09-07。主表、底表及 Task 3 导出均限于本任务，尚未合入论文。

## 1. 这张表展示什么，如何读取

Table I 展示明确实现、精度和本地服务边界下的硬件供给。12 行覆盖 SRAM ACIM、SRAM DCIM、DRAM、gain-cell eDRAM、3D NAND、2D NOR Flash、RRAM、MRAM、PCM、FeRAM，以及两个年份的 3D FeNOR／vertical FeFET。它不是介质常数表，也不是等面积、等容量、等功耗的排名。

矩阵统一按 **n_out × n_in** 表达；输入／权重格式同时保留名字和位宽。ρ 是完整声明精度求值所服务的逻辑输入 Byte/s；τ 是使逻辑驻留状态可计算的写入 Byte/s。主表有六项 ρ、一项兼容 τ 和 RI*。其余格用长横线表示“当前证据不足以在此边界确定”，不表示不能实现。

证据码有两个独立维度：第一位 M＝实测芯片、D＝实测器件、S＝仿真；第二位 D＝原文直接报告参数、C＝本文换算能力。主表中的 M/C 不表示论文原样报告了本文的 ρ。底表另允许 reference_scenario／conditional_estimate；这些参考情景没有混入主表。PCM 的芯片和准确率是实测，但所用吞吐时间来自 RTL，因此速率标 S/C。

数字都在原生本地边界计量。SRAM 输入缓冲预备、芯片外 SPI／USB 装载、跨核路由等是否属于边界，在各记录中写明；不能将本地阵列能力直接当作主机端服务能力。模拟计算保留文献的输出量化与误差条件，完整位宽服务不等于无误差整数累加。

可审阅入口：[`output/table_i.pdf`](output/table_i.pdf)、[`data/main_table.csv`](data/main_table.csv)、[`data/hardware_records.json`](data/hardware_records.json)。数据追踪链为 `row_id → hw_record_id → ev_evidence_id → t1_source_id → 页码/图/节`。

## 2. 口径与来源方法

使用已通过 Task 0 的模型：Q_S、Q_R 是逻辑 payload，ρ、τ 是相应服务能力。位串行、空间位切片、ADC 转换、互补器件、verify 和必要的编程准备影响时间或物理占用，不重复增加逻辑 payload。这里整数按本地边界的逻辑 bit-packed 格式换算 b＝bits/8；不假定主机一定采用这种打包方式。BIPOLAR1 表示 {−1,+1}，不能视为 UINT1 或普通二补码 INT1。NeuRRAM 的输入为 sign-magnitude；位宽相同不能自动匹配另一输入编码。

所有转换内部使用 Byte、second、OP；1 GB/s＝10^9 Byte/s，1 Kibit＝1024 bit。只有确认完整逻辑 MAC 的文献才使用 1 MAC＝2 OP。计算采用完整输入服务间隔，不使用单个时钟、单比特原语或 ADC 输出带宽替代。原始值见 [`data/extractions.json`](data/extractions.json)，SI 换算、中间量和能力标签由脚本输出到 [`data/normalized_extractions.json`](data/normalized_extractions.json) 与硬件记录。

来源以作者／机构提供的原始论文及制造商 datasheet 为主。共登记 21 项来源，14 项全文 PDF 保存在默认忽略的 `sources/local-only/`。两篇仓库 FeFET 文件原位保留，稳定副本、原路径和 SHA-256 见 [`sources/repository_copies.json`](sources/repository_copies.json)。本目录不默认公开任何全文；元数据、提取事实和自己的笔记可以独立审阅和复算。

3D NAND 的原始文章正文通过公开全文网页读取，未获得可用 PDF，Table 1 图片未能检查；因此没有由缺失的时序表补造吞吐。FeRAM datasheet 通过制造商 PDF 的网页工具读取，直接下载返回空／访问响应，未伪装成本地 PDF。Dyamond、D6CIM 期刊扩展版、Chiu MRAM 等只取得题录／摘要的来源明确标记，不声称阅读全文。

器件图使用文本提取配合原图查看；用于计算的数值来自正文或图中明确的数字标签，没有依赖连续曲线插值。因此本轮没有伪造“读图置信区间”。速率是报告工作点的本地调度能力／独立测试标定，所有记录都保留 `use_as_strict_upper_bound=false`；是否可作为某个映射的严格上界，需要下一轮结合边界和服务调度验证。

## 3. 各代表实现：事实、配置、换算及适用条件

### I-01：SRAM ACIM，Jia 等，JSSC 2022

记录 `hw_sram_acim_jia2022_4b`；证据 `ev_jia`；来源 [`t1_jia2022`](https://doi.org/10.1109/JSSC.2021.3119018)。PDF pp.5–6、Figs.7–9 给出阵列及 BPBS SIMD；PDF p.9／期刊 p.206 的 Sec.V-A 给出测试时钟；PDF p.11／p.208 的 Table IV 提供独立总吞吐对照。

原始配置是每核 1152 行 ×256 列二值 SRAM／电容计算单元，256 个 8-bit SAR ADC；芯片共有 16 核。选取原文实际测试的 4-bit 输入、4-bit 权重模式：4 列组成一份逻辑权重，故逻辑矩阵为 **64×1152**；4 个输入位相位形成完整多位求值。BPBS SIMD 每个数据通路复用 4 列，数字逻辑 200 MHz，ADC 输出 20 MS/s。20 MS/s 是每一位相位的阵列服务节奏，不是 4-bit 向量的完成率。

输入 payload＝1152×4/8＝576 Byte，完整间隔＝4/(20×10^6)＝200 ns，因而 **ρ＝2.88 GB/s**，主表显示 2.9。逻辑驻留容量＝64×1152×0.5＝36,864 Byte，与 1152×256/8 的物理二值存储容量一致。按 16 核反算得到 11.79648 TOPS，与 Table IV 的 11.8 TOPS 一致。

边界包含 CIMA 和 BPBS 多位重构，不包括 OCN 和输入缓冲填充。0.8 V、200 MHz／20 MS/s 是测试条件；500 MHz 是 timing closure 目标。原文给出普通 SRAM 写入能量，没有给可用于 τ 的完整权重装载时序和端口粒度，故 τ、RI* 未定。架构讨论中的大容量权重缓冲不能作为已集成容量，更不能用其假设带宽填补写入服务。

### I-02：SRAM DCIM，D6CIM，ESSCIRC 2023

记录 `hw_sram_dcim_d6cim2023_u8`；证据 `ev_d6`；来源 [`t1_d6cim2023`](https://doi.org/10.1109/ESSCIRC59616.2023.10268725)。PDF p.1／p.413 Sec.II-A、Fig.1；PDF p.3／p.415 Sec.III；PDF p.4 Fig.10。

128×128 个 6T 单元，以 8 列组成一个 8-bit 权重，形成 **16×128** 逻辑矩阵，16 组 HCA/BFA 输出。选用支持的 UINT8 输入／权重模式，完整输出为 23 bit。原文明示一次完整 8-bit VMM 需要 **64 clocks**，不是一拍：输入位及阵列内分组复用均已包含。

在正文报告的 1.1 V、约 360 MHz 工作点，输入 payload＝128 Byte，间隔＝64/360 MHz＝177.777… ns，所以 **ρ＝0.72 GB/s**。16×128 Byte＝2048 Byte，与 16 Kibit 容量一致。Fig.10 使用 363 MHz 标签，本文采用正文约 360 MHz，避免赋予不存在的精度。

Fig.1 的普通写端口宽 128 bit，但没有证明普通写可在同一计算工作点一拍完成。检索了 TCAS-I 2026 扩展版的 DOI／摘要和作者入口，未取得全文；因此主表没有将“一拍 SRAM 写”当成实测 τ。

单独保留参考情景 `ref_d6_one_write_clock`：若 128-bit 写端口确实每个 360 MHz 时钟接受一整行，且无额外准备时间，则 τ_ref＝16 Byte×360 MHz＝5.76 GB/s，RI*_ref＝0.125。它逐项列出假设，仅位于 [`data/reference_scenarios_evaluated.json`](data/reference_scenarios_evaluated.json)，不是 D6CIM 的已测 Roofline。后续验证写入时序即可检验该情景，而不是再选一个“通用 SRAM 带宽”。

### I-03：DRAM，Ambit

记录 `hw_dram_ambit2017`；证据 `ev_ambit`；来源 [`t1_ambit2017`](https://doi.org/10.1145/3123939.3124544)。PDF pp.7–8，Fig.8、Sec.5.3；PDF p.10 Table 3。

这是传统 1T1C DRAM 存储阵列内部利用电荷共享、三行同时激活和感放实现布尔逻辑的设计，证据来自 SPICE 与系统仿真，不是 near-memory CPU，也不是已完成的多位 MVM macro。其优化的 AAP（ACTIVATE–ACTIVATE–PRECHARGE）为 49 ns。Fig.8 的完整 AND 序列包含 4 个 AAP，故为 **196 ns**，连完整 AND 都不能直接写成 49 ns，更不能将它当作整数 MVM 时间。

因此逻辑 MVM 的 n_in、n_out、ρ、τ、RI* 均不推定。保存 8 KB 模型行尺寸及典型 512／1024 行 subarray 线索，但不把 rank 行宽直接分配给每颗 DRAM 芯片。下一步若匹配整数算子，需要乘法、进位、累加、归约、保留行和复制序列。

还检索了实测 1T1C DRAM Dyamond 的 VLSI 2024 原文及 JSSC 2025 扩展版。作者清单和机构摘要说明计算位于 bitline sense amplifier 附近，但全文不可得，无法从摘要闭合精度和两路服务。因此保留为候选，不用摘要的能效或容量构造能力值。

### I-04：eDRAM／gain-cell，Xie 等，VLSI 2022

记录 `hw_edram_gaincell_xie2022_8b`；证据 `ev_gaincell`；来源 [`t1_gaincell2022`](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830338)。PDF p.1 dataflow；PDF p.2 Figs.2、7。

这里是 65 nm、32 Kibit **2T1C gain-cell eDRAM**，读写端口分离；与上一行的传统 DRAM、以及 2021 年的 1T1C eDRAM 均区分。eDRAM 表示嵌入方式，gain-cell 表示单元／读出结构，两者不是互斥介质。

Fig.2 示出 27 输入的 MAV 组，8 份权重位并行，输入每次 2 bit，4 个相位形成 8-bit 输入／8-bit 权重和 16-bit 数字组合结果。Fig.7 报告该精度 access time＝20 ns，2-bit 相位为 5 ns。选择**一个 1×27 逻辑服务组**：payload＝27 Byte，ρ＝27/(20 ns)＝**1.35 GB/s**，主表显示 1.4。

这是一组完整精度 access schedule 的换算，未宣称为外部接口的独立吞吐测试。原文宏观吞吐 22 GOPS 为舍入值，不能仅据此反推、再乘上 8 个独立输入组。32 Kibit 是父 macro 存储量，不能当作每次活跃矩阵。单元互补存储的详细 macro 排布、普通写周期／并行字宽、刷新 duty 以及精确有符号编码仍需匹配；τ 和 RI* 未定。

### I-05：3D NAND，Shim–Yu，JXCDC 2021

记录 `hw_nand_shim2021_int8`；证据 `ev_nand`；来源 [`t1_nand2021`](https://doi.org/10.1109/JXCDC.2021.3093772)，原始正文 pp.62–64 Sec.II。这是基于芯片参数的仿真设计。

一个 subarray 为 64 blocks，每 block 为 13,824 BL×32 WL×3 SSL。3 SSL 表示 2-bit 权重、4 blocks 组成一个 8-bit 输出；3 份 BL 复制表示每相位 2-bit 输入。选取 **16×4608、8b/8b** 活跃矩阵，一次只选择一层 WL，输入需 4 相位。每份活跃逻辑权重对应 36 个物理单元，不能按 8 个 bitcell 粗算。

原文 303 ns、12 ns 分别是 WL、BL 建立估计，不是完整求值。Table 1 原图及完整重构时序未取得，因此只保留 `ρ=4608 Byte/(4T_phase+T_reconstruction+WL建立摊销)`。两种阈值状态均需 write-verify，τ 还缺编程并行度、完成时间和擦除策略；也追查了引用的 Lue IEDM 2019 芯片论文，但仅获得正式摘要。没有移用商品 NAND 页写带宽。

### I-06：2D NOR Flash，Guo 等，IEDM 2017

记录 `hw_nor_guo2017`；证据 `ev_nor`、`ev_nor_tuning`；来源 [`t1_nor2017`](https://doi.org/10.1109/IEDM.2017.8268341)，PDF pp.1–2 Sec.II–III、pp.3–4 Figs.6、8、9、14。

180 nm ESF1 实测分类器，逻辑层为 784→64→10。加入偏置后，两份驻留矩阵是 64×785 和 10×65；互补浮栅单元数＝2×(785×64+65×10)＝101,780。权重为模拟态，约 30% 单元实际调谐，目标误差为 5%；这不是固定 4-bit 或 8-bit resident 格式。

平均分类时间低于 1 μs，之前还要串行装入 785-bit 输入寄存器，之后通过并行门电压驱动网络；10 个模拟电压输出在外部测量。非线性两层级联也不能压成一个常数权重矩阵。因此主表保留真实延迟条件，但没有把 98 Byte/1 μs 作为单 MVM ρ，更没有由该 workload 的平均延迟声称普遍严格上界。

追查了其直接引用的 [2016 年 ESF1 调谐原文](https://web.ece.ucsb.edu/~strukov/papers/2016/DRCflash2016.pdf)：10×10 测试阵列，10 次脉冲约 3% 精度、35 次约 0.3%；Fig.3 的 programming／erase 测试脉冲分别为 100 μs／2.5 ms，Fig.2 包括读取和模型反馈。它说明模拟精度、脉冲数量和部分擦除条件影响完整写入，却不是同一分类器的权重导入吞吐。正文没有提供两种脉冲次数、反馈时间和并行写入的兼容组合，故 τ、RI* 留空。

### I-07：RRAM，NeuRRAM，Nature 2022

记录 `hw_rram_neurram2022_4b`；证据 `ev_neurram` 与独立的 `ev_neurram_projection`；来源 [`t1_neurram2022`](https://doi.org/10.1038/s41586-022-04992-8)。正文 Fig.2h；Methods 的 RRAM programming／Power and throughput measurements；PDF p.28 Extended Data Table 1。

每核 256×256 个 1T1R，两个相邻行单元的电导差编码一份正负权重，故 forward 模式每核逻辑矩阵为 **256×128**。48 核总数不放大所选单核服务。选 4-bit sign-magnitude 输入和 6-bit 输出，完整输入积分及输出转换的测量延迟为 3.9 μs。每核输入 payload＝128×4/8＝64 Byte，得到 **ρ＝0.016410256… GB/s**。

原文的 256×256 逻辑 MVM 特性测试是把两份 128×256 segment 放到两个核。这里用单核 segment 边界，不将一颗 256×256 物理 RRAM 阵列写成同尺寸有符号逻辑矩阵；若后续需要完整 256 输入，必须加第二核和 FPGA 部分和累加／数据传输条件。

写入采用逐 cell 增量 SET／RESET 与读回：脉冲 1 μs，读取 1–10 μs，接受范围 ±1 μS，平均 8.52 次 SET／RESET，timeout 是 30 次极性反转，不是 30 个脉冲。99% 器件在该限制内成功。为处理电导松弛执行三轮编程，推理测试在编程后至少等待 30 分钟。verify 次数影响时间，不能再把同一目标重复计入 Q_R。

**56 μs/cell 是作者对完全集成 DAC／ADC 控制的预估**，实测设置由外部控制，完整编程时间没有报告。正文明确使用未量化的高精度目标权重；比较表中的“4-bit weight”对应软件精度／准确率比较，并不建立一个四位输入码本。因此 b_R、τ、RI* 未定，不能以 56 μs 搭配此行实测 ρ 声称已测 ridge。

### I-08：MRAM，Jung 等，Nature 2022

记录 `hw_mram_jung2022_binary`；证据 `ev_mram`；来源 [`t1_jung2022`](https://doi.org/10.1038/s41586-021-04196-6)。Fig.1 给出 64×64 逻辑阵列；Fig.2 给出 TDC；Methods PDF p.7 的 Crossbar array weight update 与 p.8 的 Operating frequency 提供兼容读写时序。

每个逻辑 bit-cell 有两条 MTJ–FET 路径，保存一份二值权重及其互补态。输入与权重都为 {−1,+1}，故 b_S＝b_R＝1/8 Byte。64 个串联电阻和输出同时通过 TDC 获取；采用实际含数字控制延时的 **11.1 MHz**，不使用仅由最大 29 ns 模拟延迟推出的 17.2 MHz。

一份向量的输入＝64/8＝8 Byte，每个时钟完成 native 二值求值：

`ρ = 8 Byte × 11.1 MHz = 0.0888 GB/s`。

原文写入按行进行：同一行 64 颗左 MTJ 同时写入，下一拍写 64 颗右 MTJ 的互补态；每次各占一拍，同样为 11.1 MHz。逻辑 resident payload 是 **64 个权重＝8 Byte**，不是两份互补值共 16 Byte。完整两拍后：

`τ = 8 Byte / (2 / 11.1 MHz) = 0.0444 GB/s`，`RI* = 2`。

独立整阵列复算：逻辑容量 512 Byte，64 行×2 拍＝128 拍，重载时间 11.531531… μs；512 Byte 除以该时间仍是 44.4 MB/s。写电压 1.5 V；不自行添加未报告的 verify 迭代，也不借用其他 MRAM 芯片的最快写脉冲。

该结果对应本地数据已准备、完整行更新、原生有误差 TDC 输出的边界。4-bit counter 的输出码并不意味着精确整数和，也不包括外部校准查表。部分行小更新的有效 payload 更少，τ 将下降；主机 SPI 送数、初始化与应用级精度映射还需另算。ρ 与 τ 是两个模式的能力，不表示已经证明两者同时运行无干扰。

### I-09：PCM，64-core IBM 芯片

记录 `hw_pcm_hermes64_4phase`；证据 `ev_pcm`；来源 [`t1_pcm64`](https://doi.org/10.1038/s41928-023-01010-1)。实际数值取自保存的 **2022-12-07 预印本**，PDF pp.2–3、7–8、10、18 Table I、25 Extended Data Table I；期刊发表于 2023 年，尚未逐项比较最终版差异。

14 nm 芯片的每核为 **256×256 逻辑权重**，每权重 4 个 PCM 器件，256 个 ADC。输入／输出是 8 bit，resident 为模拟电导。Table I 的 1-phase 为 133 ns，4-phase 为 520 ns；准确率测试采用 4-phase，故选后者。单核完整输入 256 Byte，ρ＝256/(520 ns)＝**0.492307692… GB/s**。64 核与 2 OP/MAC 交叉校验约为 16.13 TOPS，吻合原文 16.1 TOPS 的舍入值。

论文说明 latency 通过运行 RTL 得到，尽管芯片功耗及准确率实测，所用 ρ 仍标 S/C。没有把快一相模式与四相准确率拼成一个最佳记录。

写入的 diagonal decoding 可选 256 器件，但实际只有 **32 个并行 IDAC／writeheads**；每个特定 polarity/device-ID 的 diagonal 需要 8 组。流程先 RESET 四器件，再按 ODP／TDP SET 所需极性，最后迭代 program-and-verify。RESET 125 ns，SET 250 ns（50 ns trailing edge 是该波形参数，不无据再加一次），迭代脉冲 125 ns；verify 使用 512 ns 读及 256 ns precharge。终止条件为误差小于 5 ADC counts 或最多 30 次迭代；timeout 本身不证明达标。

完整编程时间仍需要迭代／成功分布和真实批次调度；8-bit I/O 也不能确定模拟 resident 的 b_R。因此不计算 τ 和 RI*。另一个 34-tile PCM 芯片的写入并行度不能移来填本行。

### I-10：FeRAM，C2FeRAM

记录 `hw_feram_c2feram2023`；证据 `ev_c2feram`；来源 [`t1_c2feram2023`](https://doi.org/10.1109/LED.2023.3274362)。保存的 accepted manuscript 仍带模板 running header，故采用 PDF pp.2–3 Figs.3–5 定位。

该 2T2C 包含 FeCAP、普通 plate capacitor 及 MOSFET，铁电态存放在电容中；不是 FeFET／FeNOR 的铁电栅结构。论文用分立器件验证读扰和耐久度，同时提出阵列和电流求和计算方案。实际 C_FE 约 165–195 pF、C_PL＝470 pF；仿真的 3–7 fF／5 fF 不能当作同一已测 macro。

写入方案先擦到 0，再选择性写 1。离散器件展示 10^6 次读后约 10^3 的 I_ON/I_OFF 及约 10^8 次 endurance；测试面积大于 2500 μm²。电流 MAC 波形和应用仿真未提供完整数字 MVM／ADC 间隔；实际并行写入量及 ready 时序也缺失。因此 ρ、τ、RI* 未定。保留这一行是为了准确展示 FeRAM CIM 证据所在层级。

另有厂商 CY15B101N 的普通 F-RAM 数据表，16-bit word、2.7–3.6 V、随机写 t_WC＝90 ns，可换算 **普通存储写带宽 0.022222… GB/s**。这个量保存在候选的 `native_storage_write_bandwidth`，不是 C2FeRAM 的 τ；40 ns page-write 模式又是另一模式。

### I-11：3D FeNOR，Zhou 2025

记录 `hw_fenor_zhou2025`；证据 `ev_zhou25`；来源 `t1_zhou2025`，仓库原始稿全文三页。PDF p.2 Figs.2–6、p.3 Fig.12 与 Table 1。

SEM／结构展示 **8×8×3＝192 cell**，不是 192 个并行写端口，也没有完整矩阵求值。重点核对如下：

| 检查项 | 同原文条件的结果 | 对本表的含义 |
|---|---|---|
| 写／擦 | Fig.4 的 +4.25 V／−3.25 V，均为 50 ns；Fig.5 的 endurance 使用这组条件 | 是器件切换脉冲，不能代替完整事务 |
| 状态精度 | 二值阈值态；脉冲 MW 与 DC MW 不同 | b_R 可表示单逻辑 bit；没有 MLC 精度依据 |
| read-after-write | Fig.4c delay <100 ns | 是写后读延迟证据，不是 MVM initiation interval |
| 读出 | Fig.3 的 I_D–V_G 读量测 V_DS＝0.1 V | 不等于完整 ADC 及列复用服务 |
| endurance | >10^11 cycles，末端 MW >0.3 V；温度未明确 | 不将 retention 的 85°C 条件移给 endurance |
| 不同测试 | Fig.6a 使用 −3.5 V；Fig.6b 三层比较使用 +4／−3 V、60 ns | 这些结果不与最短脉冲无条件组合 |
| 并行及验证 | 三层电学比较；并行编程数量／全阵列图案验证规模未报告 | 不乘层数或 cell 总数求 τ |
| CIM | Fig.12b 测得 1-bit×1-bit 四种电流；Fig.12a 是提出的 hybrid-bonded digital CIM，12c 为准确率仿真 | 没有多位完整 MVM／ADC 时间 |

Retention 在室温和 85°C 测到 4000 s，然后外推十年；本表区分测量与外推。ρ、τ、RI* 均留空。可写符号式 `τ=p_verified×(1/8 Byte)/T_full_write_ready`，但 p_verified 和完整事务时间缺失，不能代入 192、3 层或仅 50 ns 得到一个伪实测带宽。

### I-12：vertical FeFET，Zhou 2026

记录 `hw_fenor_zhou2026`；证据 `ev_zhou26`；来源 `t1_zhou2026`，仓库三页原始稿。正式 VLSI 2026 [T11.1 会议信息](https://vlsi26.mapyourshow.com/8_0/sessions/session-details.cfm?ScheduleID=251) 验证题名。该文自称 vertical AND-type FeFET memory，与上一年的 NOR-type 器件在同一覆盖类中分别记录，名称不强行改成同一架构。

| 检查项 | 同原文条件的结果 | 对本表的含义 |
|---|---|---|
| 最快写入配置 | Fig.4c,d 的 SL-HZO／O-poor channel，±2 V、20 ns；Fig.5b 的 >10^12 cycles 使用该配置 | 不把 O-rich 方案的 erase 条件拿来替换 |
| 其他工艺模式 | O-rich 方案的 program +2 V、20 ns，erase −2.5 V、50 ns | 独立于最优工艺模式 |
| read-after-write | Fig.3d <100 ns；读栅压 −0.5 V | 未给完整阵列读／ADC 求值能力 |
| 读扰 | Fig.5c 使用 −0.5 V、20 ns 脉冲超过 10^12 次 | 20 ns 是读扰施加宽度，不能冒充读延迟 |
| 物理规模与验证 | Fig.2 制作 4×32×32＝4096 cells；Fig.10 明确展示 4×16×16＝1024 cells 图案 | 表内只写 1 Kib 图案验证，不宣称全 4 Kib 验证 |
| disturb | 40 nm 垂直 pitch；HZO 生长 O-pulse 0.1 s 对比 1.6 s；V_w/3 方案及约 10^9 次 stress | 工艺沉积时间不是写脉冲；stress 也不是并行写吞吐 |
| 阵列／系统时间 | Fig.11 是 TCAD＋SPICE，32 WL 条件；256 层、8.37 Gb/mm² 是估计 | 不用物理层数放大并行服务，不补 ADC |
| 状态及可靠性 | 二值态；retention 测量 3000 s 后外推十年，测试温度未明确 | 与 FeRAM 电容态分开；不转成寿命平均 τ |

该文没有报告完整 CIM 求值。其贡献是器件切换、写后读恢复和阵列可靠性证据，不能由题名的 ±2 V／20 ns 构造完整 CIM 模式。ρ、τ、RI* 未定，记录仍明确保留在主表。

## 4. 未选入主表的候选及原因

完整硬件底表有 16 个记录，包括上述 12 行和以下 4 项：

| 记录 | 核对范围与保留信息 | 未选择的原因 |
|---|---|---|
| `hw_edram_xie2021_1t1c` | ISSCC 原始三页；16 Kibit 1T1C；DAC、MAV、ADC 波形及 4 MHz 实测／200 MHz 仿真区分 | 10 ns 是 MAV 阶段而非完整转换；2022 gain-cell 的完整精度 access 更清楚 |
| `hw_rram_liu2025` | JOS 原始九页；576×512 2T2R、64 ADC 八组列复用；hybrid 编程、5760 权重的 16 状态测试 | 绝对 pulse／verify 时长缺失；4.67× 速度以 pulse count 表征；1.5b×1.5b 归一化指标不等于原生 MVM |
| `hw_dram_dyamond2025` | 作者发表清单、机构原始摘要；同时追查 VLSI 2024 和 JSSC 2025 | 无全文，不把 headline TOPS/W、容量或架构名称当成完整时序证据 |
| `hw_feram_cy15b101n_storage` | 制造商 Rev.*A datasheet；90 ns random-word 与 40 ns page-write 区分 | 普通存储证据，不提供 CIM 可计算 resident 服务 |

Liu 2025 特别说明了“更快编程”和完整 τ 之间的差别：先单 1T1R 编程，再按 2T2R 差分电导闭环验证；测量了误差容限、失败率、松弛以及 32／128 输入并行下 MVM。它比仅报告 SET 脉冲更接近本模型，但仍缺绝对服务时钟。原文不同位置的 4.31／4.67 速度数字也不完全一致，本表没有据此产生秒级量。正文来源为 [JOS 原文](https://doi.org/10.1088/1674-4926/24100017)，不是新闻摘要。

另外登记了 D6CIM 2026 扩展版、Lue 2019 NAND 和 Chiu 2023 MRAM 等后续来源；它们是检索／追查条目，不伪造为已完整提取的硬件记录。访问失败、已读范围及后续所需信息见 [`sources/access_log.json`](sources/access_log.json)。早期历史验证稿只作为线索，没有进入本轮数值证据。

## 5. 证据支持的观察与下一轮匹配

1. **两路能力需要分别建立。** 多个 CIM 原文给出可靠的求值节奏，却没有完整 resident 写入事务。相反，FeNOR 短脉冲和普通 F-RAM 的写周期是真实证据，但不足以产生相同边界的 ρ 与 RI*。
2. **完整精度调度会改变看上去的阵列并行度。** D6CIM 需要 64 clocks；SRAM ACIM 与 gain-cell 需要输入位相位；PCM 的 1／4-phase 是不同模式；RRAM 差分行减少逻辑输入维数。只看阵列 cell 数或时钟会产生固定倍数错误。
3. **写入终止条件很关键。** MRAM 的两条互补路径必须都完成；RRAM 需要目标范围、失败和松弛条件；PCM 的可选 diagonal 数大于同时运行的 writeheads；NAND／NOR 要保留擦除与 verify 模式。重试不产生新逻辑 payload。
4. **本轮没有跨介质“典型 ridge 区间”。** 唯一闭合主表配对为特定 MRAM 的 RI*＝2；它不是 MRAM 材料常数。不同实现独立最大／最小值没有混合成区间，经验能力没有提升为所有任务的严格上界。

Task 3 可以先实例化有完整几何与输入格式的六条求值记录；若需要写入受限的 Roofline，仅 MRAM 当前有兼容实测配置换算，D6CIM 一拍写仅是单独假设情景。所有映射仍需检验输出误差／量化、输入编码、写入粒度、服务单元数量和边界数据准备。FeNOR 下一轮需要同一阵列的并行选择、写后 ready／verify 与完整求值时序；无需预先把它映射到任何 workload 类别。

### 可供论文改写的说明（约 300–600 字）

代表性实现表明，流式求值能力与驻留写入能力需要分别表征。前者取决于完整输入向量、输出精度和服务调度，后者取决于逻辑权重如何建立为可计算状态。即使同属 SRAM，模拟实现的输入位相位、ADC 和数字重构，与数字实现的位串行及分组复用，也会形成不同的服务间隔。非易失实现中，互补单元、模拟目标精度和编程校验进一步影响写入成本。已核对的 MRAM 阵列在同一工作点每拍进行二值求值、每行用两拍写入互补状态，因而可以建立配对比例；RRAM 和 PCM 的模拟编程则还需要完整收敛时间及状态格式，不能仅凭单次脉冲确定写入能力。两篇三维铁电晶体管文献提供了快速切换、写后读及可靠性证据，但没有报告完整 CIM 求值时序。因此，表中保留明确的器件结果和计量缺口，而不从层数或最快脉冲推定系统吞吐。不同精度、阵列规模和服务边界下的原生数值展示的是实现选择，后续仍须与参数化映射匹配，才能讨论两路能力的实际约束。
