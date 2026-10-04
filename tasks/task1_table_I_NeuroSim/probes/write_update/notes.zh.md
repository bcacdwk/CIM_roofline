# Step 2 驻留更新：采用结论与原生探针

采用 V1.4 的可调用低压写驱动/译码模块作为后续组成件；**不采用 V1.4 的 `SubArray.writeLatency=0` 作为更新时间，不采用 Training 的更新估计器直接给十例完整装载计时**。Training 与 MLP 仅提供明确边界的机制参考。十例已有完整 program/erase、SET/RESET、恢复/刷新和终验周期由 `v3_native_service` 保留；普通 SRAM 的低压驱动可在 Step 3 组成独立事务，但本轮没有替换 v3 周期。

精确 SHA、文件哈希、路径、行范围见 [source_map.json](source_map.json)。V1.4 为 `8a88abf85844c0e1ba17cc771ea535fff6040456`；Training V2.1 为 `f80a4345f70dcb1ddfd003d3ddcfbd067b55a79a`；MLP V3.0 为 `6098feabaf17b8209a8edbef4a9c963b5f015132`。

## 实际调用与覆盖

|入口|实际输入/初始化依赖|返回及单位|服务范围与本项目决定|
|---|---|---|---|
|V1.4 `SRAMWriteDriver::Initialize` → `CalculateArea` → `CalculateLatency`|列数、列写活动率、实际每次写单元数；面积步骤产生 inverter capacitance；输入 ramp、列负载 F/Ω、numWrite|对象 `writeLatency`，秒；两级 inverter 的 RC/Horowitz 延迟乘 numWrite|仅位线驱动；不含完整 SRAM cell 翻转、数据输入、译码、发布。可做 `neurosim_native` primitive，由 `neurosim_composed` 外层明确组合。|
|V1.4 `SubArray::CalculateLatency`|已经初始化且面积/电容已算的子阵列，读阻值向量与计时模式|开头置 `writeLatency=0`；SRAM 与 eNVM 的写时延语句被注释|写返回规范化为 `null` + `NOT_IMPLEMENTED_IN_V1_4_AGGREGATION`。不是 0 ns；A 组的真实 SubArray 运行另行复核这个零。|
|Training `GetWriteUpdateEstimation`|新旧**电导 S**矩阵、Param 的 Gmax/Gmin；cell 最大 LTP/LTD level 数、写 V/秒，array 已初始化的线电容|activityCol/Row 无量纲；平均/总脉冲 int；writeDynamicEnergyArray J|已知旧状态的增量估计。阈值 `(Gmax-Gmin)/max(levelLTP,levelLTD)`；低于阈值跳过，达到阈值则 ceil；不输出完整事务时间。|
|Training `SubArray::CalculateLatency` 的 RRAM/FeFET conventionalParallel|活动率、`totalNumWritePulse`、`numWriteCellPerOperationNeuro`、实际 cell 脉宽；Initialize→CalculateArea→CalculateLatency|`writeLatencyArray=totalNumWritePulse*cell.writePulseWidth` 秒；总写为外围最大路径加阵列脉冲时间|活动率和重复是调度输入；脉宽来自输入，不由物理开关动态求解。未涵盖 verify、重试、erase-page、guard、cooldown、恢复或发布。|
|Training `SubArray::CalculateLatency` 的 SRAM|普通 SRAM 几何、电容、活动率、有效写并行；driver/decoder/precharger|秒；有活跃的 cell RC + WL + precharger + driver 聚合|可核对普通 SRAM 写组成；不是 ACIM 电荷域读前端，也没有十例服务语义。|
|MLP `DigitalNVM::Read(voltage)`|二元导通状态、V；关闭噪声时直接 V×G|读电流 A|纯器件电气 primitive；访问管/线阻是在 `Array::ReadCell` 层加到分母。不是 MTJ 翻转动力学、差分 IBMD 或读码保持。|
|MLP `DigitalNVM::Write(bitNew, wireCapCol)`|目标 bit、列线 F、外部 LTP/LTD 电压与脉宽|更新 bit/conductance；writeEnergy J；无 latency 返回|在高低电导端点间直接赋值，并估算脉冲能耗；默认 10 ns 脉冲是输入，不是求解结果。不能替代 MRAM 两相写+绝对状态终验。|

Training `ProcessingUnitInitialize` 把 `numWriteCellPerOperationNeuro` 默认设为整列数，`numWriteCellPerOperationMemory=numCol/8`。实际 wrapper 同时取 Param 的相同 LTP/LTD 电压，令 `cell.writeVoltage=sqrt(VLTP²+VLTD²)`，脉宽取二者平均；不能不加说明地把不同 SET/RESET 电压或脉宽塞成一个值。`ProcessingUnitCalculatePerformance` 仅在 `trainingEstimation` 开启时估计并返回写更新；调用顺序是估计 → 写活动/脉冲赋给 SubArray → `CalculateLatency/CalculatePower` → writeLatencyWU 聚合。绕过神经网络 wrapper 的 probe 直接调用相同原生函数。

FeFET 分支的极化项假定 Pr 与 G 线性映射，并用外部 polarization、V、面积估算 **J**。脉冲数仍由电导差决定，脉宽仍是输入；没有 Landau-Khalatnikov、畴翻转或极化时间动态，不能写成 FeFET 极化速度预测。

## 探针事实与适用限制

`run.py` 将本组规范源、上游未修改 `.cpp/.h` 复制到新的本地目录，记录每个文件 SHA256；用真实 GCC 编译原 `ProcessingUnit.cpp` 与模块，无粘贴版被测函数。每个 Training 样本是新进程。输入旧状态为 2×4 全部 `4*2^-20 S`，Gmin=`2^-20 S`、Gmax=`9*2^-20 S`，最大 LTP/LTD level=8，因而最小步长精确为 `2^-20 S`，避免浮点阈值偶然性。

|样本|修改后的非默认码|手算行 SET+RESET 最大脉冲|原生总脉冲|原生列/行活动率|
|---|---|---:|---:|---|
|unchanged|无|0|0|0 / 0|
|set|第0行前两列6,5|2|2|0.25 / 0.25|
|reset|第0行前两列2,3|2|2|0.25 / 0.25|
|mixed|第0行前两列6,1|2+3|5|0.125 / 0.25|
|two_set_rows|第0行6,5；第1行首列5|2+1|3|0.125 / 0.5|
|all_set|全体6|2+2|4|0.5 / 0.5|

`mixed` 的 SET、RESET 行都应被分别登记；原函数 `if ... else if ...` 只登记 SET 行，因此丢失 RESET 的活动率。若按双相平均，列/行活动率应是 0.25 / 0.5，实际只得到 0.125 / 0.25。`two_set_rows` 的选中列总数3/行数2在传入 ceil 前进行整数除法，结果1，不能实现应有的向上取整2。探针保存这些独立计数与上游不符事实，不改公式、不改物理预期。

同一组估计分别设置写并行度 1 与4，原生脉冲数完全相同。特别是 all_set 的 2×4 数据，每单元2个脉冲：P=1 的真实独立写头调度需16个脉冲时隙，P=4 需4；原估计器两者都给4。原因是它从未读取写并行度；**每行 SET 最大值+RESET 最大值**隐含行内并行。外围时延层会计算 `ceil(numCol*activityColWrite/P)`，但阵列脉冲层不相应分批。后续受限写头（例如 PCM 32 IDAC、RRAM 编程 rail）必须由外层事务分批后调用 primitive，不可把这个脉冲估计器当完整写调度。

另一个 128×128、32 nm LSTP、300 K 的上游默认尺寸调度探针将上述活动率作为合成输入，只核查宽度在外围层的作用，**与2×4增量事务区分**。构造采用静态存储对象先将未显式初始化标量清零，再集中设置电气参数与模式，执行 Technology→SubArray Initialize→CalculateArea→CalculateLatency；没有共享 Param.cpp 修改。它不是十例的工艺/几何选择。all_set 的脉冲段恒为200 ns；P=1/P=4 的包含外围总时间分别为2956.6133900098002 / 889.1533475024502 ns。初次尝试8×8曾触发上游 DFF 宽度报错；该失败保留本地，最终改为已支持的128×128尺寸并要求日志无 Error。

另有 V1.4 `SRAMWriteDriver` 原函数探针使用22 nm LSTP、300 K，16列、10 fF/500 Ω显式负载，比较 numWrite=1/2与实际写并行度1/8。`CalculateArea`产生的输入/输出电容为正；numWrite在primitive内使时延恰好翻倍，而并行lane数不乘到单次驱动时长上。该结果仅覆盖driver，不代表普通SRAM完整写已经打通。

MLP 原函数探针得到 0.5/24000=`2.0833333333333333e-5 A` 与0.5/8000=`6.25e-5 A`，10 ns外部脉宽，2 fF列负载时 SET/RESET 能耗=`8.353333333333333e-13 J`。连续 `Write(1)` 后再次 `Write(1)`，no-op 分支没有清空 `writeEnergy`，仍保留前次能耗。这是可变状态的又一证据，不能把字段当该次真实耗能；MRAM主服务不走此增量对象。

69个数值断言在本地最终版本通过。`PASS` 表示成功复现原函数行为并明确暴露路由限制，不表示上述有缺陷活动率可以用于完整装载。

## 事务接口与唯一提供方

|请求/阶段|本项目提供方|必须显式输入与保留|
|---|---|---|
|first_load 首次装载|`v3_native_service` 外层完整装载；有逐项可分电路才 `neurosim_composed`|定义初始状态/erase 前置、全矩阵逻辑 Byte、数据入口、所有物理 bank/plane、有效写头/域；不能假设所有 cell 原值已知。|
|arbitrary_overwrite 任意完整覆盖|`v3_native_service` 完整 program/erase 或覆盖事务|目标状态、页/sector/block粒度、两相写、建立/退偏/guard、终验/重试、全期间共享资源与最终发布。状态相同也不免除搬入和协议必需步骤。|
|known_state_delta 已知旧状态增量|后续显式采用的 `neurosim_composed` batching；Training仅参考|新/旧状态、最小步长、SET/RESET分别脉冲数/宽度/电压、行内批次和写头约束；禁止直接使用混合行活动率或以0更新量代表0装载时间。|
|SRAM 普通写低压选通/驱动|`neurosim_native` primitive → `neurosim_composed`|Initialize→Area→Latency；寄存/数据端口、decoder、precharger、cell flip、驱动各阶段的包含范围和真实并行度，不能只报 driver。|
|NVM 脉冲建立/SET/RESET/退偏/冷却/读验/重试|`v3_native_service`，独立外围才选择 V1.4 composed|不同极性的预算分别保留，不能套 Training 的平均脉宽；RRAM CIM通路与memory/verify通路分开。|
|NOR/NAND 完整P/E|`v3_native_service` opaque block|256 B页/4 KiB sector或NAND原生页/block口、完整P/E、独立更新域；不拆出臆测外围后再加NeuroSim。|
|MRAM/FeNOR 两相写、guard、绝对终验|`v3_native_service`|端点状态/互补编码、读码保持与写域；MLP DigitalNVM不预测这些阶段。|
|FeRAM restore / GC刷新与按模式释放|`v3_native_service`|读后恢复/保持/refresh周期、实际恢复和外部写并行度分别配置；内部维护不记 workload写入Byte。|

每阶段返回 `latency_ns`、`repeat_count`、`occupancy_ns`、`initiation_interval_ns`（未证实时null）、`included_substages`、`count_owner`、源码/输入身份。完整 T_R 与局部 transaction 分开，未实现写时延必须null+原因。输入数字端口宽度绝不充当物理写驱动数量。只保留 primitive 输出秒→ns的一次转换，Training 本组延迟是物理秒，没有再乘时钟周期。

Step 3 SRAM pilot 可先接 V1.4 `SRAMWriteDriver`、译码/预充电/数字输入寄存 primitive，单独形成普通SRAM写事务，同时保留 ACIM 电荷域前端与原生宏周期边界。RRAM pilot 保留 v3 RESET→有限 SET/verify→终验、rail 整体占用；CIM/read 与memory/verify建立不同负载对象，明确 v3 阶段与 V1.4 SAR/数字公共外围的替换范围。两者均不调用整网映射器生成默认 T_R。

## 复跑

从任意 cwd 调用 `python3 /管理区/probes/write_update/run.py --root "$NEUROSIM_ROOT" --out "$NEUROSIM_ROOT/runs/step2/一个新的目录" --cxx /实际/g++-版本`。只需 Step 1 的编译器/工作树，无新增依赖。输出 `summary.json`（含独立事务对照）、`commands.json`、`manifest.json` 与完整日志在本地。规范区无上游源码副本、binary/object/cache；独立 reviewer 使用新目录复跑，公共导出由 supervisor 完成。
