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

`raw_delta_S_ns` 与 `raw_T_R_ns` 保留单次物理服务时间；有效能力使用长期服务间隔 `effective_delta_S_ns` 与 `effective_T_R_ns`。对可用率 `a`，有效间隔为 raw/a。GC-04 为易失性 gain-cell eDRAM：保持限 400000 ns，5.5 ns 时钟下采用 399998.5 ns 整数拍刷新帧，包含 66176 ns 刷新 busy 与 115.5 ns guard，可用率约 0.8342706285。其 raw 时间为 3707/21120 ns，有效服务间隔约 4443.4023/25315.5263 ns；后两者是长期服务成本，不能解释为单次请求延迟。图表中的 GC 两率均计入维护。

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

## 数据与使用

[统一完整精度数据](data/ten_case_results.json) 是表图的唯一权威入口；逐例输入、资源和来源保留在各案例目录。完整复算使用 [计算入口](shared/run_evaluation.py)，只重绘使用 [绘图入口](11_summary_figures/build_figures.py)，命令和正式文件见 [任务说明](../README.md) 与 [表图说明](11_summary_figures/README.zh.md)。复算不读取历史结果作答案，重绘不编译 NeuroSim。

本评估只提供十例典型点，缺少与这些配置相容且完整可追溯的成对范围，因此不生成三情景圆图。表图显示约两位有效数字，CSV/JSON 和绘制坐标保留机器结果完整精度。
