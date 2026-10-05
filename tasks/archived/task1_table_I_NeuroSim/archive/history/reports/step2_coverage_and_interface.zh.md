# Step 2：后端覆盖与可执行接口

本次为 `faf8a42165e5d3655ec0fe70f4597e4baebe3f6f`（`task1_neurosim_step2`）上的收敛修订。原机制测试与独立复跑证据保留；当前规则见接口 **3.0.0**，新增修订结果单独关联。只做接口与迁移回归，不进入 Step 3。

**修订验收 PASS，最终独立复跑 PASS。** 原466条机制检查、新408条收敛检查、9条输出接口检查及独立额外164条审计均通过。两次最终运行1792个数值字段一致；十例原有时间回放最大差为4.656612873077393e-10 ns的浮点舍入，没有修改器件参数或增加修正系数。

## 采用方案

采用 **V1.4、22 nm conventional CMOS、LSTP、300 K** 作为公共低压 primitive 后端。主调用为独立 `SarADC`、`Adder/AdderTree`、明确容量的 `DFF`；保持原生阵列和服务，外层显式组织重复与资源占用。原 `main` 继续作为整网回归，**不作为 Table I 宏级入口**。不合并不同版本源码，不增补 28 nm 技术表。

十例保留 v3 身份、几何、编码、访问方向及资源。电荷域 SRAM、PCM 电压前端、RRAM CIMSEL/TBL、NOR/NAND 完整 P/E、MRAM 互补 IBMD、FeRAM 破坏性读恢复、硅 CMOS GC-04 的 current-programming/刷新、垂直 FeFET 的 strip/layer 负载均由明确原生阶段提供。未拆分的完整周期作为 opaque block；不扣除臆测外围后重复加回。

输入接口版本为 **3.0.0**，十例典型输入在 `configs/cases/`；`contracts/case.schema.json`、`output.schema.json` 和 `parameter_policy.json` 定义校验和政策。数字时钟归属、RRAM默认依赖和资源字段有不兼容的语义修订，因此升主版本，沿用目录。`contracts/coverage.csv` 与本报告的十例阶段表从配置生成。它们是接入规格，不是十例新仿真结果。

Step 3 的两个先行案例固定为 **01 SRAM ACIM、05 RRAM**，采用下文的混合服务接口。当前轮不运行完整十例、不生成新 rho/tau/PPA 表。

## 版本与证据

本轮起点与HEAD均为 `CIM_roofline@faf8a42165e5d3655ec0fe70f4597e4baebe3f6f`（`task1_neurosim_step2`），初始工作区仅根 `.DS_Store` 已修改，记录于 `provenance/step2_revision.initial.json`。此前Step 2创建起点为 `e519b923382d03d3e54c043f02c59c01a20919f3`；器件源始终为 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`。Step 1及原Step 2运行证据保留，不回退工作区。

|后端|完整 SHA|本轮用途|
|---|---|---|
|2DInferenceV1.4|`8a88abf85844c0e1ba17cc771ea535fff6040456`|主低压电路；初始化、读出、时钟、数字和写驱动探针|
|2DTrainingV2.1|`f80a4345f70dcb1ddfd003d3ddcfbd067b55a79a`|增量更新计数与写聚合机制，不提供完整覆盖写调度|
|MLPInferenceV3.0|`6098feabaf17b8209a8edbef4a9c963b5f015132`|DigitalNVM 电气/外部脉冲、hybrid 机制参考|
|2DInferenceDCIMV1.0-dev|`38eedf926fc1a712df3627f36bb82b097ba6b9cb`|256×256 特定组织与类型核验，不替换 D6CIM|
|2DInferenceV1.5-dev|`9825ef40bf14d12a72c99d8e32ff8c499aeddf24`|Cap 外部建立时间宏模型探针，不替换 FeRAM/GC|
|3DInferenceV1.0|`6d2ee9b9b5067c4c8660ad8cd0cbedcab477ba69`|沿用导航，未扩读/运行 3D 架构|

关键源码路径、函数、行范围和文件哈希统一登记于 `provenance/step2_source_map.json`；各探针目录的 `source_map.json` 与 `notes.zh.md` 保存详细证据。所有原生调用使用锁定源码本地副本，共享 worktree 不变。

## 具体计算入口和覆盖范围

以下 V1.4 路径均位于 `Inference_pytorch/NeuroSIM/`，精确行定位以源码映射为准。

|入口|实际输入及方法|返回与采用范围|未包含|
|---|---|---|---|
|`Technology::Initialize`，`formula::{CalculateGateCapacitance,CalculateOnResistance,horowitz}`|node/roadmap/type；温度 K、宽度 m、负载 F/Ω、斜率；PTM 表、解析布局和 RC/Horowitz|电容 F、阻值 Ω、面积 m²、物理延迟 s；低压门与已绑定线网|器件翻转动力学、完整复杂阵列瞬态、高压泵和恢复|
|`SarADC::Initialize(lanes,levelOutput,Hz,numReadCellPerOperationNeuro)` → `CalculateUnitArea/CalculateArea` → `CalculateLatency(numRead)`|levelOutput=2^bits；固定 `(bits+1) ns × numRead`|`readLatency` 秒；独立转换 primitive；数量影响面积/资源，不乘单次时长|前端积分/建立、mux、校准、数字重构、符号阶段|
|`MultilevelSenseAmp::CalculateLatency(columnResistance,mux,numRead)`|current 模式实际依参考电阻表取延迟；voltage 模式固定 1 ns，再乘 mux/numRead|秒；只在原生等效通路成立时作感测候选|不按任意实际列拓扑做瞬态求解；不是 IBMD/PL 破坏性读|
|`DFF::Initialize(count,Hz)` → `CalculateArea` → `CalculateLatency(ramp,numRead)`|明确安装/活动容量；同步返回 numRead，异步返回 numRead/(2Hz)|同步 cycles，异步 s；使用声明的输入、输出或读码保持资源|频率收敛证明、免费缓存或额外 holding bank|
|`Adder::CalculateLatency(ramp,capLoad,numRead)`|明确位宽、级联和实际输出负载，门 RC|始终秒；显式加法|自动扩通道/无成本数值归约|
|`AdderTree::Initialize(fanin,inputBits,trees,Hz)` → `CalculateArea(height,width,NONE)` → `CalculateLatency(numRead,fanin,capLoad)`|第一层给定位宽、后续级沿用上游 2-bit adder 近似；面积需指定布局尺寸|异步 s；同步 `ceil(physical_s*Hz)*numRead` cycles；公共数字组合候选|原生 HCA/BFA 同构证明、自动 II|
|`ShiftAdd::Initialize/CalculateLatency`|adder＋内部 DFF，numReadPulse 还影响寄存容量；异步会假定与读脉宽重叠|同步 NONSPIKING 返回 cycles；仅作机制对照，主方案用显式 Adder/AdderTree＋已有 DFF|不能再外加同一重构；不能设 numReadPulse=1 后忽略被缩减容量|
|`SRAMWriteDriver::Initialize` → `CalculateArea` → `CalculateLatency(ramp,capLoad,resLoad,numWrite)`|列写活动率、真实并行度、列 F/Ω；两级 inverter RC|`writeLatency` 秒；有效的单独低压驱动 primitive|数据装入、cell flip、译码/预充、完整写事务及最终发布|
|`SubArray::CalculateLatency(...,CalculateclkFreq)` → `ProcessingUnitCalculatePerformance` → main|上游子阵列电路加 row/mux/plane/input loops、PE/Tile/Chip 和层间流水|true 是感测关键路径秒；false 的同步结果是聚合 cycles，异步结果是 s|其宏组织、网络映射和流水不自动适用本项目|

`CalculateArea` 是依赖步骤：例如 DFF 在其中形成 capInv/capTgDrain，Adder 在其中形成门电容。即使不交付面积也不能跳过。`Param` 是全局指针，ProcessingUnit 还有全局 buffer/bus/adder 指针；SubArray 初始化会写回全局 wire/array 字段。对象保留可变状态，必须按配置新进程、新对象。

`SwitchMatrix::CalculateLatency` 的读 RC 实际使用全局 `unitcap/unitres/numColSubArray/buffernumber/drivecapin`，不能只传 capLoad/resLoad 就认为绑定了原生负载。其同步写还混合 RC 秒与 DFF cycles。本项目不采用该同步写返回，前端/选通负载未完成集中映射时继续用原生服务。LevelShifter 只覆盖局部门级 RC/面积，不覆盖完整 charge pump、偏置建立、退偏、恢复或写验。

## 初始化、工艺与时钟的主选择

主低压工艺为真实的 22 nm LSTP，Technology 表给 VDD=0.85 V、Vth=0.419915 V、effectiveResistanceMultiplier=1.77。原生 cell 特征尺寸、PL/BL/SL 寄生、偏置和耐压另存，不能自动乘 22 nm。Param 默认的器件 featuresize=40 nm 与 Technology 的 featureSize 也不是同一个字段。

采用配置驱动的集中初始化：在独立本地构建副本中，对经过白名单审阅的**基础输入赋值**生成 constructor specialization，保留原公式，保存精确 diff/哈希后重新构造；再集中设置原 main 才赋值的 precision/mapping 字段。固定工艺的机制探针只对白名单 shape/mux/bit 字段集中同步。不是任意运行时修改 Param：探针证实改 technode、Ron、row 后，featuresize、maxConductance、rowParallel 等可能仍保留旧值。

顺序固定为：冻结配置 → 构造 Param → InputParameter/Technology/MemCell → 新模块 Initialize → Area/电容 → 物理路径遍历 → 选 actual clock → 按 actual clock 重新创建计数对象/运行计数遍历 → 导出有效快照。快照包含模式、几何、原生负载、R/G、access、row/plane/mux、precision、码级数、校准系数、各对象实际 Hz 及来源，不以配置文件原值代替生效值。

主数字目标周期仍为 **5 ns（200 MHz）**。实际周期只取目标与该域已实例化的完整单周期寄存器间路径要求的最大值。独立模拟建立、SAR转换、program/erase/restore、完整本地SRAM写不约束公共数字周期；只有明确属于该寄存器间路径的单周期感测才例外。周期返回绑定实际 `clock_id`，只换算一次。此前32-input、23/29-bit AdderTree在测试负载下分别为1.9065398279794006 / 2.290447961367728 ns，只是特定构件证据，不能认证整条案例路径或NAND乘除法。SAR固定11 ns按独立服务占用转换资源，不会自动把所有数字拍改成11 ns。

已复现 V1.4 `main.cpp` 的换算问题：303–305 行只在目标太快时降低全局频率，321–326/406–411 行却始终乘第一遍感测 `clkPeriod`。受支持的小 SubArray 返回 sensing=12.642065656422386 ns、count=4 cycles；目标 10 MHz 时原 main 公式给 50.56826262568954 ns，按实际 100 ns 周期应为 400 ns。此见证由原生 SubArray 返回加原 main 转换式组成，并非另跑慢频率整网。保留它作为上游行为证据，不把其单周期感测假设推广到当前primitive组合服务。

物理服务连续计时；只有下一个**明确的数字消费者**接收结果时，才在已声明setup/握手裕量后等待合适数字边沿。边界等待单列，并注明等待期间仍保持哪些资源；没有额外并行、缓存或免费重叠。内部连续子阶段不分别向上取整，包装改变不改变边界。完整SRAM写保留 `native_sram_memory` 本地周期及已含命令/数据/恢复，公共接口只处理启动/完成边界；它不被当成lv_core周期，也不重复添加已含capture。

公开 `validated=true` 的实际默认系数保留并限定作用范围：alpha=1.44（LevelShifter area），beta=1.4（SubArray sensing delay），gamma=0.5（DFF energy），delta=0.15（Adder energy），epsilon=0.05（控制电路 energy），zeta=1.22（main 最终能效分母）。单独 SAR 不被重复乘 beta；它们不表示十个新参考宏均获实物验证。

## 计数和写入机制结论

PE 的输入向量循环已经逐个处理展开的 input bits；SubArray 的 numAdd 表示活动行组，mux/weight planes/shift-add 又在内部计数并存在 `MAX(extra-ADC_overlap,0)` 隐藏时间。主 driver 使用每 primitive 的 `numRead=1`，由配置中的服务计划独占外层重复；不对聚合返回再乘 input bits/planes。不直接采用上游网络流水，不把 latency 自动设成 initiation interval。II 没有调度/资源证明时保持 null。

数字服务保留既有v3 schedule预算；DFF周期只是计数工具。`operation_plan`列出运算、周期、寄存边界、构件候选、未覆盖逻辑及实例化要求。Adder/AdderTree输出仅是路径片段，不能认证完整路径；完整串接、信号到达条件和实际负载明确后，才可约束数字时钟。未覆盖运算不记零，不额外加一遍构件ceil周期；改变微结构时替换原schedule而非叠加。

`GetInputVector` 的 activity 是非零项/物理总行数；`GetColumnResistance` 是选中支路电导和加简化线/access 阻值，不是任意阵列晶体管瞬态。零输入可能改变电流/能量或某种原生 sequential 计数，但 v3 固定执行的符号相位、轮次不因此免除。原 `LoadInWeightData` 是算法 [-1,1] 归一化后量化分 cell，不是 v3 two's-complement 或 NAND split-sign/base-4 编码器。

V1.4 SubArray 的写聚合段被注释，实际零返回规范为 `null/NOT_IMPLEMENTED`。单独 SRAMWriteDriver 已实测：22 nm、16 列、10 fF/500 Ω负载下，numWrite=1 为 0.07883215781919818 ns，2 次恰翻倍；lane 1/8 不改变单次时长。这只验证驱动，主 SRAM pilot 的完整普通写周期仍保留。

Training `GetWriteUpdateEstimation` 接收新旧**电导 S**，以 `(Gmax-Gmin)/max(LTP_levels,LTD_levels)` 为步长，按每行 SET 最大脉冲＋RESET 最大脉冲累计。原生探针及独立计数发现：

- 同行 SET+RESET 的 `if/else-if` 漏记 RESET 行活动；部分 `ceil(int/int)` 已先截断。探针同时保存上游实际值和独立正确计数，不改预期凑通过。
- 2×4、每 cell 两脉冲的 all-SET，写并行度 P=1/4 时原函数都给4脉冲；独立有限写头调度分别需16/4时隙。并行度主要在后续外围重复中生效，阵列 `totalNumWritePulse*writePulseWidth` 不随其分批。
- Training wrapper 将 SET/RESET 脉宽平均，不能代替 v3 不同极性的完整脉冲、退偏、冷却、读验和重试。FeFET 极化项估算能量，外部脉宽仍为输入，不预测极化速度。
- MLP `DigitalNVM::Read` 是 V×G；access/线阻另由 Array 层承担。Write 直接赋二元端点并估计外部脉冲能耗；unchanged 分支甚至可残留旧 writeEnergy。它不替代互补 MTJ 写、IBMD 或绝对终验。

首次装载、任意完整覆盖、已知旧值增量为不同 request_kind。前两者必须计数据进入、完整原生操作和发布；相同旧值不是免费装载。完整 P/E、原生 write/restore/refresh 的唯一提供方及嵌套次序见配置。Training/MLP 仅提供机制和边界对照。

## 十例路线与原生资源

下表由十例规范配置生成，逐阶段函数、输入、返回单位、依赖、循环、资源、包含项和来源在 `contracts/coverage.csv` 与 JSON；没有手填十例性能值。

<!-- GENERATED_CASE_ROUTES_START -->
| 案例 | 逻辑 K×N | 原生模块入口（非案例闭合） | 混合/候选阶段 | 保留原生完整服务 |
|---|---:|---|---|---|
| 01_sram_acim | 128×128 | input_capture, sar, output_commit | reconstruct | charge_front, sram_write |
| 02_sram_dcim | 128×16 | input_capture, output_commit |  | native_mac, sram_write |
| 03_nor_2d | 128×128 | input_capture, operand_capture, output_commit | digital_mac, page_load, sector_erase | binary_read, page_program |
| 04_nand_3d | 4608×240 | input_capture, sar, output_commit | input_magnitude_sign, affine_merge_sign〔原算术预算〕, resident_encode, page_load, load_calibration〔原算术预算〕 | native_wl, native_bl_sl, page_program, block_erase |
| 05_rram | 128×64 | input_capture, sar, output_commit, attempt_done | digital_reconstruct, program_attempts, resident_front | analog_front, rail_setup, endpoint_verify, rail_exit |
| 06_mram | 256×32 | input_capture, operand_capture, output_commit, polarity_turn | digital_mac, encoded_load, terminal_verify | binary_read, direction_write |
| 07_pcm | 256×128 | input_capture, sar, output_commit | digital_reconstruct, resident_front, program_reset_set, endpoint_verify | analog_front |
| 08_feram_hfo2 | 128×128 | input_capture, output_commit | digital_mac, external_load | binary_read, external_polarization_write |
| 09_gain_cell_edram | 64×64 | input_capture, sar, output_commit | digital_reconstruct, resident_load, refresh_read, refresh_decode_load_rewrite | analog_front, current_program |
| 10_fenor_3d | 128×128 | input_capture, operand_capture, output_commit | digital_mac, resident_load, terminal_verify | binary_read, two_phase_write, post_pulse_guard |
<!-- GENERATED_CASE_ROUTES_END -->

资源的安装量与活动量分别保存。尤其 NOR/NAND 的协议页口不冒充未知晶体管写头数量；MRAM 的全阵列 IBMD 与活动4096-bit tile分开；FeRAM 的4096路恢复与128路外部更新分开；FeNOR 的偏置节点数与128个选中写目标分开。无 ADC 的五个数字案例不会获得 SAR。NAND 保留64 blocks及页/参考校准，GC 保留八 binary endpoint planes和有限刷新码保持，均无免费全矩阵 shadow。

DCIM 仅支持上游256×256；其 parallel_weightprecision、numCol/4 和 addertree 组织不是16项 HCA/BFA。V1.5 Cap 的原 `SubArray::CalculateLatency` 探针显示 colDelay=`chargeDelay/128*numRowParallel`：5 ns 输入在128/64行分别给5/2.5 ns。此外部宏时间并不计算 HZO PL恢复或GC刷新。V1.5软件 DAC precision 不改变硬件bit-serial路径。MLP HybridCell 是一个3T1C LSB加两个PCM MSB及WeightTransfer，不是GC-04。

## 输入输出接口与两项 pilot

`case.schema.json` 把逻辑 payload、物理组织、按模式器件参数、公共低压后端、安装/活动资源、服务/循环和 parameter binding 分开。每个输入来源保留文件 SHA256 与 JSON pointer/函数位置。旧 b_S=b_R=1 是 Byte/INT8 element；内部互补、位平面、复制只增加物理占用，不再次增加 B_S/B_R。

每阶段输出由 `output.schema.json` 约束：原始 value/unit/scope、clock_id、转换后物理 ns、单次 latency、次数、resource occupancy、可证明 II、已含子阶段/重复维度、配置/源/补丁身份。真正零值为 OK/0；未实现必须 null＋原因。完整 resident T_R 与单 transaction 分开；维护 raw/effective 分开，busy time与guard随替换阶段重算，内部维护不计 workload 写入 Byte。

物理秒/ns返回的 `clock_id` 为null；路径候选另用 `constraint_clock_id` 和 `combinational_path_fragment` 标记。只有带完整寄存边界、single_cycle、实际负载证据且已实例化的完整 `combinational_path` 才能约束数字时钟；pending和service_duration均拒绝。只有cycles携带换算clock_id。直接使用ns字段时，`rho_Byte_per_s=1e9*B_S_Byte/delta_S_ns`、`tau_Byte_per_s=1e9*B_R_Byte/T_R_ns`，RI/U恒等式不变。

唯一绑定主政策：digital_tick由实际lv_core时钟提供；adc_batch由所选SAR primitive提供；专用input/reset预算按原生来源，完整front已含者不重复加。RRAM改为独立 `binary_verify_sense_ns=20 ns`，保留v3参考预算及来源，不受SAR位数/转换公式驱动；数字Comparator也不提供模拟窗口建立/判断模型。原 `T_B=T_A` 仅保留为明确命名、默认关闭的能力政策对照。依赖分别标记实际共享电路、共享物理参数与人为能力政策；PCM终验、GC刷新、NAND校准实际共享的ADC/前端继续同步变化。

**01 SRAM ACIM pilot**：Python规范层验证128×128、8 binary planes、每plane16 ADC、16数字通道、128真实写驱动；从配置生成集中构造输入与module request，C++以17位精度返回typed JSON。调用 `SarADC::Initialize(128,1024,actual_Hz,...)` 及area/latency，numRead=1；128 ADC是8×16并行资源，不乘单次转换时间。10-bit转换码经规定标定、符号/位权扩展为18-bit归约叶子，tree fanin=8、trees=16；最终accumulator/output为23-bit。输入/输出DFF复用1024/2944-bit既有寄存，SAR代码保持至两拍数字处理完成，不在此期间开始下一转换。无新增ShiftAdd bank或免费中间暂存；必要时重新计算tree，并把tree＋adder完整串接路径计入时钟约束。保留20 ns完整电荷前端和5 ns完整普通SRAM写周期的原生输入；streaming为64次前端/转换、既定数字重构与边界周期，resident为1024个16 B事务。驱动probe可以作为独立诊断，不能在完整5 ns周期上再追加。pilot交付是“原生前端/写＋公共转换/数字”的组合，非原生SubArray替身。

**05 RRAM pilot**：验证128×64、8 planes、32活动项、每plane16 ADC、16数字通道；128 lane program rail与256 binary-window comparators分开。正常CIM与memory/verify各有自己的前端/偏置/负载对象。CIM阶段使用SAR primitive和显式数字重构，128次前端/转换；写为512个16 B事务，典型2次RESET尝试＋1次SET尝试，每次局部建立→脉冲→退偏→相应窗口读验，全矩阵rail只建立/退出一次。CIM SAR变化不再驱动独立20 ns窗口时隙；TI/TD、前端和写控制按各自真实消费者传播。前端、有限尝试、窗口、rail及最终发布沿用v3，不调用Training直接生成T_R；新模型的案例实例化与完整结果留待Step3。

两项pilot都需要补齐原生输出/线网负载到primitive的集中映射、实际时钟和复用寄存的调度证明；这些是具体适配工作，不改变主后端或器件身份。未覆盖的高压完整操作、IBMD动态、PL恢复和GC保持/刷新继续已有原生provider。三情景、完整十例扩展和论文表图均在后续阶段。

后续公式保留 `rho=B_S/delta_S`、`tau=B_R/T_R`、`RI_star=rho/tau`、`U_star=T_R/delta_S=(N*bytes_per_weight/bytes_per_input)*RI_star`。本轮只对逻辑计数和合成数值检查恒等式，不生成十例新性能。

## 探针、复跑与验收

统一入口（可从任意 cwd 调用；默认只写本地）：

```sh
TASK_DIR="<REPO_ROOT>/tasks/task1_table_I_NeuroSim"
python3 "$TASK_DIR/scripts/check_step2.py" --root "$HOME/neurosim"
# 指定全新的复核目录，仍不写管理区：
python3 "$TASK_DIR/scripts/check_step2.py" --run-id "review-step2-$(date -u +%Y%m%dT%H%M%SZ)" --no-export
```

使用 `NEUROSIM_ROOT/NEUROSIM_CXX` 可覆盖路径；已有目录不覆盖。`--export` 才按白名单导出小型summary/command/配置检查，完整源码副本、编译日志和失败现场留在本地。无新增依赖。规范源/配置先复制本地快照并记哈希；每个机制样本的可变对象按新进程隔离。

本轮统一运行和独立复核见 `results/step2/latest.json`、`reports/step2_revision_review.json` 及STATUS。之前的审计和结果保留在 `reports/step2_review.json` 与原运行目录；下表是此前已通过的机制证据，新修订检查另列。

|原检查组|归档结果|主要证据|
|---|---|---|
|公共读出/初始化/时钟|PASS，52断言|SAR 9/11ns、numRead重复、DFF单位、慢目标时钟、面积依赖与实际写零|
|驻留更新|PASS，69断言|Training六状态×两并行度、有限写头独立计数、SRAMWriteDriver、MLP状态|
|特殊分支|PASS，17断言|DCIM组织/type、V1.5原Cap建立时间、bit-serial/hybrid边界|
|编码/资源/服务计划|PASS，328断言|INT8/65536对NAND split-sign编码、容量/资源/尾批、60次源哈希/310字段定位、嵌套次序|
|输出接口|PASS，8检查|cycle/seconds唯一换算、缺失写值null、错误/NaN和缺时钟拒绝|
|独立语义与复跑|功能PASS|50个primitive来源/SI换算、41条上游映射、容量双射、负例、最终新目录复跑|

前一轮集成运行是 `runs/step2/step2-integration-reviewed/`，独立运行是 `runs/step2/step2-independent-review-final-20261004T1517/`。当时修复了秒返回的换算clock_id及MRAM完整方向写槽的重复数字绑定。本轮保留这些修复及其复跑证据；升级后的完整路径约束字段采用 `constraint_clock_id`。

共享上游及原NVM/Table II/论文只读，Step 1和原Step 2结果证据保留。`.DS_Store`只记录，不作研究或回退。没有新增安装、DNN依赖、模型或数据；完整日志/失败现场留在本地。本轮交付审计单独保存为 `provenance/step2_revision_delivery.json`，不覆盖前一轮交付记录。没有Git暂存、提交或推送。

## 本轮收敛：数字覆盖与资源量纲

每阶段用少量状态分别表达 `route_defined`、`native_module_probe_run`、`case_path_pending`、`native_budget_retained`。构件可调用或机制探针通过，不等于实际案例负载/整条算术路径通过；本轮没有把任何十例完整数字路径升级为qualified。CSV新增阶段类别、主要时间提供方和案例状态，不再把长原生时段加少量控制统称“NeuroSim主调用”。

- NAND affine四拍依次覆盖：10-bit码乘Q8.16 gain并加Q12.12 offset/舍入，base-4 merge，极性减法，符号/输出累加；边界是既有896/320/168-bit阶段寄存与6960-bit输出容器。乘法、舍入/饱和和完整串接负载仍缺相容实例化，保留四拍原预算。
- NAND装载校准保留 `16×(24+4)+2=450` 拍算术预算，明确除法递推、工作寄存、系数舍入/存储、残差/阈值路径；ADC和原生前端单独组成，不以Adder/DFF列表替代除法器。
- 数字MAC列出输入门控、32项带符号归约、移位/符号、累加和源/目的寄存边界；D6仍保留完整16项HCA/BFA周期。SRAM ACIM/RRAM保留SAR码两拍，无新增中间bank；PCM/GC的代码保持、比较/刷新解码及仲裁具体列为pending。未覆盖运算保留预算，不能零延迟。

V1.4 AdderTree首层给定位宽、后续2-bit的返回在六组原模块探针中符合 `D(W)+(depth−1)D(2)`。它对应特定树进位到达近似；逐层完整位宽串行和采用不同到达/边界假设，仅作模型对照，不是唯一正确oracle。没有将该近似预设为bug，也没有用32输入树认证NAND乘除法或任意树外逻辑。原生负载和实际信号到达条件仍须在pilot中验证。

`resources.write_semantics`替代两个含混的write_driver_count字段，量纲区分电气输出、已知program channels、选中存储目标、互补/编码因子、逻辑Byte、bit/beat端口和更新域。FeNOR保持288偏置输出/128选中cell；GC是128 pair programmer/256 branch/128 pair目标；MRAM每事务64互补pair、128 MTJ状态、8 Byte，两相128/64 MTJ命令；NOR/NAND分别保留2048/13824页目标而内部写头仍未知。容量、事务数和并行度用这些具体量与单位检查，偏置节点或接口位宽替代目标数的负例必须拒绝。

编码量采用 `encoded_bits_per_load_unit`＋`load_unit_scope`，不把单页输入写成整矩阵事务的编码位数。每装载单元目标批数乘每事务装载单元数得到事务批数：NOR为64页，NAND为6144页（含零payload/参考页），PCM一个256-bit装载单元对应8个32-cell plane批；其他保持原组织。未知内部pulse/head数仍未知，RRAM有限尝试和MRAM两相另外计。独立review发现并促成修复的单位/批数拒绝检查，现同时覆盖准确单位、整数计数、phase/pair和这些乘积关系。

## 本轮收敛：原有时间回放与新政策测试分离

`probes/interface_revision/legacy_replay.py`只读取规范primitive、完整原生预算与嵌套调度；不导入/调用旧计算器，不读取最终delta_S/T_R作为输入。聚合完成后才打开保存的v3结果作只读比较；每个差异关联阶段ledger与调度context。关闭替换的模式保持旧TI/TA/TD，明确关闭本轮新时钟选择和边界对齐。

十例典型配置分别核对streaming和完整resident；GC另核对refresh busy、非抢占guard、availability和维护后服务。共享GC ADC的扰动检查同时作用正常求值/刷新并重算guard。回放是接口迁移回归，不是十例NeuroSim性能表；没有修正系数，不以保持旧排序约束未来新模型。

新政策由独立合成测试验证：数字路径/资源固定时，模拟7→17 ns不改变5 ns数字周期；模拟8→14 ns的完成差额分解为服务+6 ns、边界等待−1 ns。真正组合路径3→7 ns使数字周期变为7 ns。内部2+2 ns只在唯一消费者处等1 ns，而非每段取整；包装等价、重复转换、缺时钟、缺负载及pending路径负例均检查。RRAM SAR位数变化不驱动窗口，窗口参数只驱动读验；PCM/GC/NAND真实共享ADC/前端和数字控制的实际消费者则同步变化。

本轮新增408项由时钟/依赖44项、数字覆盖/资源343项、原AdderTree对照7项、旧时间回放14项组成。独立review还禁止回放聚合阶段打开任何results.json后重新执行，确认仅在聚合后比较；额外提高GC program_complete时，busy和max guard按实际阶段重算。发现的R1资源单位/批数拒绝缺口已修复，初次现场保留本地；不把最终结果相等当作完整负例覆盖的替代。

最终集成：`runs/step2/step2-revision-unit-reviewed/`；独立复跑：`runs/step2/step2-revision-independent-final-20261004/`（从 `/tmp`、`--no-export`）。新增白名单输出在 `results/step2/step2-revision-unit-reviewed/`，审计在 `reports/step2_revision_review.json`。旧结果目录、原审计和Step 1证据保留。无剩余阻塞，本轮到此停止。
