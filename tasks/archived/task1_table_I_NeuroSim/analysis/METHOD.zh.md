# NeuroSim 与器件估计结合的 CIM 评估

本评估结合文献支持的器件与阵列服务估计、NeuroSim 电路模型，以及明确的映射和调度政策，计算 resident–streaming 两路服务能力。十例各采用一套参考配置；逻辑规模、物理资源与数值条件不同，结果描述这些实现的服务能力，不构成等面积、等工作量或统一精度下的材料排名。

## Payload 与完整服务

设逻辑矩阵为 `W[N,K]`，输入元素与权重元素各占 `bytes_per_input`、`bytes_per_weight` Byte：

```text
B_S = K × bytes_per_input
B_R = K × N × bytes_per_weight
rho = B_S / Δ_S
tau = B_R / T_R
RI* = rho / tau
U* = T_R / Δ_S = N × bytes_per_weight / bytes_per_input × RI*
```

十例都以 8-bit signed 输入和权重定义逻辑 payload，各占 1 Byte；这不等于所有模拟路径都已达到精确 INT8 运算。`B_S` 是一次完整输入向量，streaming 边界包括该向量规定输出的前端、转换、数字重构及交接。`B_R` 是整个 resident 矩阵；resident 边界覆盖全部局部事务、必要擦除、编程、读验、校准和数据装载。更新组大小不能替代完整矩阵的分子。内部位平面、互补编码、NAND 参考页和刷新占用资源与时间，不增加逻辑 payload。

表图使用十进制 MB/s = 10⁶ Byte/s。`RI*` 是硬件两路服务比；`U*` 是匹配完整矩阵与完整输入向量时的服务交叉点，不是工作负载实际复用次数。扩大到算子或实际应用时，还需确认输入共享、重放、映射与资源分时。

`raw_delta_S_ns` 与 `raw_T_R_ns` 保留单次物理服务时间；有效能力使用长期服务间隔 `effective_delta_S_ns` 与 `effective_T_R_ns`。对可用率 `a`，有效间隔为 raw/a。GC-04 为易失性 gain-cell eDRAM。典型情景的保持限 400000 ns，5.5 ns 时钟下采用 399998.5 ns 整数拍刷新帧，包含 66176 ns 刷新 busy 与 115.5 ns guard，可用率约 0.8342706285。其 raw 时间为 3707/21120 ns，有效服务间隔约 4443.4023/25315.5263 ns；后两者是长期服务成本，不能解释为单次请求延迟。图表中的 GC 两率均计入维护。

## 模型、资源与时序

公共低压条件为 22 nm、LSTP、300 K、0.85 V；器件本身的工艺和电压仍按各例输入保留。NeuroSim 上游为 `2DInferenceV1.4`，SHA `8a88abf85844c0e1ba17cc771ea535fff6040456`，锁定信息及版权引用入口见 [来源锁](../provenance/neurosim.lock.json)。正式复算从锁定源码核对并在非同步运行区新建副本、构建可执行文件。

实际调用 `DFF`、`Adder`、`SarADC` 的初始化、面积和延迟接口，并使用 `Technology` 与 `formula/Horowitz` 构建具体门级组合路径。SAR 延迟采用上游名义码宽拟合；DFF/Adder 提供寄存边界、门尺寸、电容与路径依据。数字连线按每段 10 μm、0.2 fF/μm 的局部工程条件计入，DFF 边界含有负载反相器近似。这里没有调用原生 `SubArray` 来统一预测十种材料，也没有把局部数字线模型替代 PL/BL/string/SL 等器件负载。返回的局部模块面积不是完整宏 PPA。

各例 `resolved.json` 保存逻辑到物理映射、安装资源、活动并行度、保持区与装载组织。资源容量不自动等于并行服务数；既有 ADC、sense 节点、驱动、bank 和保持寄存区按生命周期复用，不假定额外 bank、跨批重叠或 streaming 与更新免费并行。

数字时钟以 5 ns 为目标，按满足合法路径资格的下限向上取 0.5 ns 网格。完整周期操作先对齐启动边沿，传播后在末端捕获；后端已含目的 setup 时不重复计费。纯采样或 ready 发布按 `ceil((t+setup)/P)P` 捕获，器件完整服务已含捕获时保持其原边界。允许两拍的数据路径要求输入、选择、SAR 码及旧累加值保持到第二拍；中间 phase 更新至捕获使能仍按单拍检查。二元数字 MAC 的早稳输入组、逐拍输入 bit、反馈与首拍新权重分别核查，没有删除 mux 或负载。

每例 `stage_sources.json` 区分直接 NeuroSim 模块、由公开门模型计算的组合路径、文献/工程服务预算及接口边沿调度。器件读、写、擦除、恢复与电流编程等服务仍由来源预算提供；普通数字外围和 SAR 的计算不能独立验证这些预算。来源和输入哈希见 [输入来源](../provenance/input_sources.json)，逐例输入与结果由 [统一数据](data/ten_case_results.json) 的路径字段定位。

## 参考实现与适用条件

下表“输出位数”是保存重构结果的容器宽度；不表示模拟有效位数或实际任务准确率。二元数字路径的精确 signed 运算以存储和感测正确为条件；模拟路径保留标定后近似部分和的数值契约。

| 参考实现 | K×N | 输出位数 | 主要实现与适用条件 |
|---|---:|---:|---|
| [SRAM ACIM](01_sram_acim/resolved.json) | 128×128 | 23 | 9T1C 电荷耦合参考实现，八个二元权重平面、HCA bypass；标定后近似部分和。 |
| [SRAM DCIM](02_sram_dcim/resolved.json) | 128×16 | 23 | 所选二元 SRAM 数字实现；八个存储位编码一个权重，条件精确 signed 运算。 |
| [2D NOR](03_nor_2d/resolved.json) | 128×128 | 23 | 二元感测后数字 MAC；条件精确 signed 运算，完整装载包含持续擦写。 |
| [3D NAND](04_nand_3d/resolved.json) | 4608×240 | 29 | 正负幅值分组、输入符号相位、两位 digit 与物理复制；含参考页和校准，保持既定小信号、量化与组边界误差条件。 |
| [RRAM](05_rram/resolved.json) | 128×64 | 23 | WH-2T1R 参考实现；八个二元位平面、无额外差分复制；标定后近似部分和。 |
| [MRAM](06_mram/resolved.json) | 256×32 | 24 | 64 个 IBMD bank，互补 MTJ 编码；既有读出及保持资源上的条件精确 signed 运算，写后两支绝对状态读验。 |
| [PCM](07_pcm/resolved.json) | 256×128 | 24 | 32 个实际电流通道；SAR、九级类码及数字重构；RESET/完整 SET 和终验保留。列相关阈值、阈值存储及标定有效性为条件。 |
| [HZO FeRAM](08_feram_hfo2/resolved.json) | 128×128 | 23 | HZO 1T1C 二元 FeCAP；条件精确 signed 运算，破坏性读后恢复计入服务。原生 PL 负载仍为工程条件。 |
| [GC-04 gain-cell eDRAM](09_gain_cell_edram/resolved.json) | 64×64 | 22 | 65 nm 3T1C current-programmed dynamic-cascode；八个伪差分位平面，128 路 ADC。易失性、含完整周期刷新；反复刷新误差未独立闭合。 |
| [垂直 AND FeFET](10_fenor_3d/resolved.json) | 128×128 | 23 | 图中简称 3D FeFET；八个二元 FeFET 编码一个权重，32 条横向 row lane，不把四层堆叠当作四路并行输入；条件精确 signed 运算。 |

NAND 的 Q8.16 仿射乘法、舍入和校准除法沿用非零算术周期预算，完整门级时序尚未闭合；9 ns 周期只认证已实例化路径。PCM 的阈值条件、FeRAM 的 PL 负载及 GC 的重复刷新误差也不能由公共后端计时替代验证。电气时序是声明拓扑与负载下的结构包络，不是提取后 STA、实物精度、完整阵列 PPA 或 workload 准确率认证；未知聚合写参数仍保留未知值。

## 成对工程情景与范围来源

每例提供 optimistic / reference / pessimistic 三组同时应用的服务预算，并在同一器件身份、逻辑精度、映射、资源、偏置假设和调度规则下分别执行完整 streaming、resident 及维护过程。reference 保持原参考数据逐值不变。每个情景中的两率来自同一次参数组合，不把独立读写极值任意拼成一点，也不按既有性能比例缩放。情景标签不保证 RI* 或 U* 单调；它们仍由同点两路服务计算。

下表按“乐观 / 典型 / 悲观”列出实际变动的输入服务预算。每例 [scenarios.json](01_sram_acim/scenarios.json) 结构均保存具体 source pointer、原文件 SHA-256、单位换算、证据类别、消费阶段与保留条件；表内链接分别指向各例完整范围来源。

| 参考实现及来源 | 实际变化的服务预算，乐观 / 典型 / 悲观 | 来源与应用边界 |
|---|---|---|
| [SRAM ACIM](01_sram_acim/scenarios.json) | charge front：10 / 20 / 50 ns；完整 memory cycle：2.2 / 5 / 10 ns | 10 ns 完整宏量级锚及精度适配工程余量；写周期为跨宏完整同步周期预算。 |
| [SRAM DCIM](02_sram_dcim/scenarios.json) | native MAC round：4.3 / 5 / 10 ns；完整 memory cycle：2.2 / 5 / 10 ns | 4.3 ns 计算锚及工程窗口；写周期同源跨宏移植，公共低压时钟仍由当前后端计算。 |
| [2D NOR](03_nor_2d/scenarios.json) | 完整读：100 / 120 / 130 ns；page program：0.4 / 0.4 / 3 ms；sector erase：45 / 45 / 400 ms | 数据手册读等级的工程转移、完整编程与擦除典型/最大预算；正常读与 MAC 早稳资格共用读预算。 |
| [3D NAND](04_nand_3d/scenarios.json) | SL setup：530 / 640 / 750 ns；page program：300 / 300 / 600 μs；block erase：1 / 1 / 3.5 ms | 来源模型范围与中点、完整编程/擦除预算；SL 服务同时进入正常计算与校准。 |
| [WH-2T1R RRAM](05_rram/scenarios.json) | 局部高压建立、恢复各为：50 / 100 / 250 ns | 相同 128 驱动及负载下的工程余量；RESET/SET 固定 2/1 次、每次 1 μs，偏压、判定窗及 rail 不变。 |
| [MRAM](06_mram/scenarios.json) | IBMD read：5 / 5 / 10 ns；完整方向写槽：20 / 30 / 30 ns | 读预算用于计算、绝对状态终验及早稳资格；写槽保留完整方向写语义。5 ns 读与 20 ns 写为条件工程重组。 |
| [PCM](07_pcm/scenarios.json) | 共享电压前端：10 / 20 / 50 ns；drive transition：10 / 20 / 50 ns | 同一前端/驱动的条件预算；共享前端用于正常计算与端点终验，驱动切换进入完整 RESET/SET 服务。 |
| [HZO FeRAM](08_feram_hfo2/scenarios.json) | sense：8 / 20 / 50 ns；每相极化保持：14 / 50 / 100 ns；open/close 总开销：20 / 40 / 80 ns | 实测锚及条件性相位预算；极化和开闭成本同时传递到破坏性读恢复与外部写入。 |
| [GC-04 eDRAM](09_gain_cell_edram/scenarios.json) | 公共读相位开销：36 / 86 / 136 ns；完整编程：65 / 65 / 75 ns | 工程公共相位预算，非测得的阶段分解；完整编程含实测建立量级锚。正常读、刷新读与重写、guard 和可用率共同重算。 |
| [垂直 AND FeFET](10_fenor_3d/scenarios.json) | 完整 binary read：20 / 40 / 80 ns；bias transition：5 / 10 / 20 ns | 同一原生读和固定驱动的条件预算；读同时进入正常求值、终验及早稳资格，bias 同时进入写与释放。 |

SRAM 的 2.2 ns 写锚来自 28 nm eFlash 工艺、48-bit 2RW 8T 宏的 455 MHz/typical 1.05 V 完整同步周期；将其移植到选定 128-bit 存储接口是设计预算。DCIM 的 4.3 ns 锚来自另一 28 nm D6CIM 的 233 MHz/0.9 V 计算时钟，5/10 ns 为工程窗口。它们不是同芯片、同偏置的实测成对结果，公共数字后端仍为 0.85 V。DCIM 的 4.3/5/10 ns 是既定自主完整 `native_d6cim_mac` 轮次预算，不替代 NeuroSim 数字路径；其公共 `lv_core` 仍选 5 ns。两类 SRAM 的 2.2 ns 写服务受公共接纳边沿约束，因此乐观与典型的 τ 相同。

MRAM 来源中的 3 ns 读候选已实际执行并被现行固定拓扑的早稳检查拒绝；所需源 pin 建立约 3.3623 ns，故未进入普通情景（[排除检查](06_mram/excluded_candidate_checks.json)）。乐观改为已接受的 5 ns 读加来源完整 20 ns 方向写槽；两者共同适用仍是工程条件，不是沿用来源整对或同偏置实测保证。RRAM 只改变 resident 的局部建立/恢复，streaming 的三点 ρ 相同；NOR 乐观与典型的完整装载预算相同，τ 也重合。MRAM 乐观与典型的 ρ 相同。这样的单轴重合保留真实坐标，不能为获得视觉范围而拉开；实际十组三点无整点全重合。

未列入上表的参数、操作次数、bank/ADC/保持资源、公共工艺与连线、SAR nominal bits、数字选频规则、原生偏置和逻辑映射保持不变。公共后端和共享消费者仍实际执行；GC 的维护能力按各情景重新计算。NAND 未闭合算术、PCM 阈值/校准、FeRAM PL 负载及 GC 重复刷新误差没有凭这些情景获得额外认证。情景未覆盖的非理想性、负载和模型误差不能解释为零不确定性。

三点只是有限成对工程条件，不是统计置信区间、同一芯片 PVT 保证，也不是所有实现的严格快慢边界。圆沿用 log 空间中“两端等距且圆心距典型最近”的几何规则；完整规则与重合点处理见[表图说明](11_summary_figures/README.zh.md)。圆内任意读写组合未必可实现，圆大小不代表实测误差分布。

## 数据与使用

[典型完整精度数据](data/ten_case_results.json) 保留十例 reference；[三情景完整精度数据](data/paired_scenario_results.json) 保存成对情景，每个 reference 与典型数据逐值一致。表图均由这些机器数据派生；逐例输入、资源和来源保留在各案例目录。完整复算使用 [计算入口](shared/run_evaluation.py)，只重绘使用 [绘图入口](11_summary_figures/build_figures.py)，命令和正式文件见 [任务说明](../README.md) 与 [表图说明](11_summary_figures/README.zh.md)。复算不读取历史结果作答案，重绘不编译 NeuroSim。

三情景表、典型点图及成对圆图显示约两位有效数字；CSV/JSON 和绘制坐标保留机器结果完整精度。
