# 共享外围证据与估算依据

原文是数值和结构的证据，公共资源政策属于明确参考选择。PDF页码为本地页序；文献原值、偏置、模式与报告性质保留在共享JSON。原生K、N不是共同固定条件，R0只提供非绑定介质的128×128算例。

## 原生尺寸与计数

ACIM R0有8输入bit×8输出组，64求值、64转换批、128数拍、8192标量转换。DCIM R0有256计算轮；每32×16×8bit tile读入一次，在4096bit示意感测宽度下有32读批、32次新增捕获，跨8输入位复用。真实案例需独立声明SA数量与带宽。静态连接已含在完整MAC周期时read_ns=0，不重复感测。

参考物理读时间ACIM25ns/DCIM10ns，共同参考TI/TA/TD=5/20/5ns，直接更新16Byte/60ns。独立手算：A0=64×30+64×20+128×5+10=3850ns；ADC翻倍A1=2250ns；1024模拟槽/240ns保持、每求值5ns捕获的A2=2210ns。D0=32×10+(256+32+2)×5=1770ns；32输出/8192bit感测保持D1=16×10+(128+16+2)×5=890ns。扩展读资源是结构对照，不能混入同配置三情景。

## 资源、完整周期与维护

R1–R8及resource_policy给出共同政策。驱动、ADC与保持的数量和额定能力在三情景内固定；较快边沿需同一安装硬件承受其最大电流/负载，典型电流不是供给上限。现有SA捕获、SRAM静态读连接和完整程序周期覆盖阶段不重复收费。新增保持与端口须真实列账；不使用全矩阵shadow。

原生页块保留参考页、增强信号复制和完整erase/program；它们不增加有效逻辑payload。维护函数仅表达已证明共用串行预留，alpha>0不能独自证明每个非抢占任务可在有限窗口调度。固定刷新期限、批边界guard、累加器生命期和依赖由案例说明。

## 接口独立检查

K70/N35、输入3bit、行32、平面8且并行3、输出组17/ADC8/数字5：81求值、189转换批、297重构轮/594数拍、2520标量转换。保持51槽、至少110ns；read7ns与参考外围时完整服务7975ns。该例同时覆盖输入、行、输出和平面尾组。

K64/N32、DS100ns、TR3200ns：rho0.64GB/s、tau0.64GB/s、RI*=1、U*=32。N扩大两倍而求值输入共享、写端串行时，TR6400ns/DS100ns令U*=64；两路同倍则U*=32。该差异说明宏级阈值不可无条件套Table II。

35Byte整矩阵以16Byte写事务需16+16+3共三周期；三页24Byte有效payload加一参考页，每页384bit装入、program100ns、erase1000ns、TD5ns时，完整块时间1500ns、payload72Byte。参考页不计有效字节但付完整时间。

## CMOS-02 → 10 ns 采样锚点 → 10–50 ns 读出时隙

- [原 PDF](../../../literature/00_cmos_periphery/CMOS-02_2021_AsynchronousSAR.pdf)：pp.2–6 Figs.1–7 为 SAR/CDAC、采样、逐次比较与时序保护；p.7 测量条件；p.8 Figs.10–12；p.9 Tables 1–2。
- **直接实测**：28 nm，名义 10 bit，100 MS/s，0.9 V、室温。输入 buffer 和参考电路在芯片中，总功耗 1.1 mW，其中 buffer/reference 占 0.66 mW；活性区 0.026 mm² 包含这些功能。用于说明完整条件，未用于面积反推共享因子。
- p.7 在 1 MHz 输入下写 SNDR 55.13 dB、SFDR 61.92 dB、ENOB 8.86 bit；p.8 Fig.10 写 SNDR 56.91 dB、ENOB 8.86 bit。两处标注不一致。按 `(SNDR−1.76)/6.02`，55.13 对应约 8.865 bit，56.91 对应约 9.161 bit，因此保留原值并采用“约 8 bit 有效”条件。奈奎斯特输入 p.7/9 为 SNDR 51.54 dB、ENOB 8.27 bit；按公式约 8.269 bit。
- p.9 Table 1 是 **post-layout simulation** 的 PVT 表，不和室温硅测混为一组。
- **换算**：100 MS/s → 10 ns/样本。该值是采样周期，包含采样和全部 SAR 决策；不能再次乘十位比较次数。原文并未给出参考 CIM 复用负载的一次独立转换定值。
- **本文选择**：名义 10-bit SAR、约 8-bit 有效读出目标；完整可复用时隙 `T_A=10–50 ns`，推荐 20 ns。10 ns 保留原采样周期锚点，20/50 ns 是复用选择、采样、共模/参考适配与局部锁存的工程预算，不是测得的降速系数。介质积分/跨阻放大等在介质输入中另计。

## CMOS-03 → 128-cell 负载及完整读写终点 → 输入/写控制量级

- [原 PDF](../../../literature/00_cmos_periphery/CMOS-03_2012_SRAM_Assist.pdf)：p.1 动态 read/write 定义与 back-to-back 约束；p.3 IV-C 参考条件、Fig.4 位线负载；pp.4–5 assist 比较。
- **作者模型**：HD 28 nm 6T、0.120 μm² cell、TT、标称 1 V；周期 50 FO4（在 1 V 约 1 ns），WL 脉宽 25 FO4（半周期），SA offset 0.1 V，BL capacitance 15 fF（128 cells）。p.3 明确列出，不是 compiler 实测保证。
- **用途**：128 输入项示例的负载依据；区分 WL 脉冲与完整更新服务；说明负载、终点及连续操作要共同进入时间。
- **本文选择**：不从 1 ns 减去 cell 延迟。与两个 ACIM 宏共同支持 `T_I=2–10 ns` 的简单二电平输入/公共复位预算；与 CMOS-07、数字宏共同支持数 ns 级控制节拍。写事务控制 `T_W=2T_D=4–20 ns` 是两拍调度推导，不是该文报道的 SRAM 写周期。

## CMOS-07 → 455 MHz / 1.54 ns 的不同粒度 → 局部写接口检查

- [原 PDF](../../../literature/00_cmos_periphery/CMOS-07_2023_LowPower_DualPort_SRAM_AuthorRevision.pdf)：pp.1–2 Figs.1–2 为同步 2RW 8T 端口；pp.4–6 为 WL tracking；p.8 V-B 说明 eFlash 平台；p.9 Tables II–III、Fig.21。
- **直接实测/表列典型条件**：28 nm eFlash CMOS，较高 core/SRAM 阈值；48 Kbit、48-bit word、1K words、MUX4；典型 read access 1.54 ns、frequency 455 MHz。Table III 给出 28 nm 典型电压 1.05 V，Fig.21 的功耗测量标 25°C、TT；这些是各自原条件，未将它们合成为全 PVT 时序保证。
- **换算**：455 MHz → 2.1978 ns，展示约 2.20 ns 的可重复时钟周期。1.54 ns 是 read access，不能代替完整更新周期。7 nm 的 0.58 ns/1207 MHz 不用于共同 28 nm 速度依据。
- **用途/选择**：用完整普通 SRAM 服务交叉检查数 ns 级接口预算，保留双端口、高阈值平台及原字宽。`T_W=4–20 ns` 仍为参考调度的两拍控制，不声称原文单独测了外围 4–20 ns。

## SACIM-03 → 多位输入与 reset/evaluate/readout → 一位输入预算

- [原 PDF](../../../literature/01_sram_acim/SACIM-03_2023_Hierarchical_Attenuator.pdf)：p.2 II-A/B、Figs.1–3；p.3 Fig.5 与 III；p.4 Figs.6–8；p.5 Table II。
- **直接结构/实测**：28 nm，128×256 个 9T1C，128 路 4-bit DAC，64 个 4-bit flash ADC；每次 128 个四位输入与 64 组 128×4b 权重求值，四位 ADC 输出。输入 DAC 为 4-to-16 decoder、16 档电压、开关选择。电荷 reset/evaluation/readout 明确分阶段。
- **原始时间及文内差异**：p.3 III 为 0.9 V 下 100 MHz；p.5 Table II 同列 0.9 V；结论却写 1.2 V 下 100 MHz。参考设计采用其结构与整体周期量级，电压差异按原文分别记录。
- **换算/用途**：100 MHz → 10 ns 完整宏周期；四位 flash 的宏周期不等于共同十位 SAR 转换时间。Fig.5 的 ISS 预判提前，不增加 MAC 吞吐周期，故没有把它另加为一个串行“精确 ns”阶段。
- **本文选择**：以该宏和 SACIM-05 提供本地输入完整服务的量级交叉证据，R0 算例采用 128 路一位二电平输入，`T_I=2–10 ns`、推荐 5 ns；属于简化输入电路及带缓冲负载的工程预算。未将该文的多位 DAC 当作已测独立一位驱动器，也未提取不存在的分项绝对时间。

## SACIM-05 → 四组两位输入、叠加与重构 → 模块边界和共享规则

- [原 PDF](../../../literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf)：p.2 III-A/B、Fig.4；p.3 III-C/D、Fig.5；p.4 Fig.6/10；p.5 Fig.11 及相邻正文。
- **直接结构/实测**：28 nm、384-kb 宏；32 个 cell 共享 HIPCC；8-bit 输入分四组 2-bit，经四电平 DAC 并行输入；每个部分和累加 16 项。八位权重通过多个二进制列与四组输入结构映射，不等于一个 cell 存八位。
- 相同位权的 GBL-comb 把 ADC 从 96 个减少为 69 个（p.3 末段，写为每 sub-bank；与 p.2 的每 output-channel 标签存在上述差异）；之后数字 shift-and-add 重构。p.4 Fig.6 有 initial、voltage sampling、voltage stacking 三阶段，各阶段对应独立开关状态。
- **原值**：p.4 Fig.10 给出 8/8/20 bit 输入/权重/输出、16 channels、1.0 V 下 access time 3.6 ns；p.5 Fig.11/正文给出 0.9 V 下 3.8 ns、1.0 V 下 3.6 ns。
- **用途/选择**：用于完整宏级交叉检查、低位输入并行与数字重构的结构依据。20-bit 输出不是无误有效精度。没有从 3.6 ns 中拆出独立 DAC、SAR、cell 或 adder 延迟。
- `T_I=2–10 ns`、`T_A=10–50 ns` 均按各自定义选择；不会把原文较快宏周期并入 SAR 范围下端。R0每平面 16 ADC、总 128、共享 8 是本参考配置，既不照抄 69，也不作面积除法。

## SDCIM-01 → 约 2.8 ns/拍、64 拍/局部 VMM → 数字节拍与完成计数

- [原 PDF](../../../literature/02_sram_dcim/SDCIM-01_2023_D6CIM.pdf)：p.1 Fig.1 与 II-A；p.2 继续解释完整 VMM；p.3 测量正文；p.4 Table I、Fig.10。
- **直接结构**：28 nm；128×128 bit 数据阵列，8-bit 权重对应 128×16 逻辑 VMM；16 HCA/BFA 通道；普通 write data 128 bit。完整八位 VMM 需 64 clocks，既有输入 bit 次数，也有局部输入空间分组，不将 64 拍简单归因为权重逐 bit 串行。
- **原值/换算**：正文最大频率 360 MHz @1.1 V，Fig.10 标 363 MHz；两者对应约 2.8 ns/拍。Table I 全电压范围 30–360 MHz，不把 30 MHz @低电压纳入近标称公共范围。
- **本文选择**：数字节拍 `T_D=2–10 ns`，推荐 5 ns；16 输出通道与 128-bit 普通写口为结构锚点。R0的128×128 逻辑矩阵不是复制八个独立 D6CIM 服务单元，纯合成R0行分组独立选择为32项；256计算步、保持后32个满tile读批分别计数。该文的普通写端口未直接提供独立完整写周期。

## SDCIM-03 → 3 ns/拍、8 拍 INT8 → 位串行数字服务

- [原 PDF](../../../literature/02_sram_dcim/SDCIM-03_2022_DynamicLogic_INT8.pdf)：p.1 正文与 p.2 Figs.11.7.2–5。
- **直接实测**：28 nm，0.8 V，3 ns clock；INT8 输入八拍展开，先在 memory mode 装入权重，再切 CIM mode。每次输入 bit 进行动态逻辑 precharge/evaluation/D-FF sampling；32 项 post-sum 结构支持R0选择的 32 输入项数字组。
- **来源粒度**：外部 LVDS 可达 2 GHz 是测试时钟能力；引言 SRAM <1 ns 是背景陈述；两者都不用作参考完整 VMM 速率。八拍只对应原宏声明的计算维度。
- **本文选择**：3 ns 为 `T_D=2–10 ns` 的直接锚点之一，5 ns 留出移植与局部负载预算。主参考将物理阵列响应和公共数字服务分开相加；若后续采用原文完整宏周期，须替代已覆盖部分，不能再加同样的 precharge、读出和逻辑时间。

## SDCIM-05 → 1/2 MAC 拍与独立 32-bit 写口 → 结构交叉核查

- [原 PDF](../../../literature/02_sram_dcim/SDCIM-05_2026_DigitalTranspose_AccurateApprox.pdf)：pp.3–5 Figs.4–7；p.10 Fig.21 与正文；p.11 Table III，均按本地 13 页正式 PDF 页序。
- **直接结构**：上下两组 cyclic-weight-mapping SRAM，图示各有 64×64 个四位单元；普通读写 32-bit，计算时提供 256-bit 驻留向量。INT4/FP8 一 MAC 拍，INT8/BF16 输入按 MSB/LSB 四位段使用两 MAC 拍。
- **明确取用**：Table III @0.9 V，AC 模式 INT4 access 1.0 ns、INT8 2.1 ns；AP 为 0.9/1.9 ns。作为更并行数字结构的速度量级交叉依据，不当作本文 32×16 每组运算在固定电压下的已测定值。
- **保留差异**：p.10 FP8 正文将 2.5 ns 归 AC、2.7 ns 归 AP，Table III 相反；本文不将这些值拼接为 INT8 时钟。正文多处 32 kB，Table III 写 32 Kb，与两组图示结构的 32768 bit 相符；容量取结构作解释，不静默修改原文。Fig.6 省略 write circuitry，32-bit 端口也未给独立写周期。
- **本文选择**：支持对完整拍数、模式及普通写口分开处理；公共数字节拍为 2–10 ns。R0采用一个 128-bit 局部写接口，这是基于 SDCIM-01 的配置选择，不声称所有 SRAM/介质都已有该端口。
