# Step 2 收敛：时钟与依赖

本文件说明 `clock_dependency.py` 的接口和独立小例子；没有运行十例新性能。源配置仍由唯一集成者生成。

## 数字周期与完整服务

公共数字目标仍为 **5 ns**。`actual_period_ns` 只受属于 `lv_core` 的真实单周期寄存器间完整组合路径约束。Adder/AdderTree 的裸返回标为 `combinational_path_fragment`；它们必须与该路径内的门控、符号逻辑、串接算术、负载和寄存器边界合并，才能升级为约束时钟的 `combinational_path`。原生探针测了一个片段，不能证明真实案例闭合。

SAR 转换、模拟建立/积分和完整 program/erase/restore 时间都是 `service_duration`。它们保留物理 ns，阻塞自己的声明资源，不因持续多个数字周期而改变全域周期。只有明确处在寄存器间单周期路径内的感测才属于时钟约束。原 SubArray 的 `CalculateclkFreq` / main 慢目标时钟探针保持原样；其证据不自动进入当前 primitive 组合服务的周期规则。

物理操作完成时保留连续时间；在**下一次声明的数字接受边界**统一对齐。下一合法边沿由完成时刻加显式接口 setup/handshake 余量确定。只有余量已经计入时，恰好到达合法边沿才不加额外周期。完整原生 block 内部不逐段向上取整；重新包装服务不会创建边沿。不得借此增加寄存器、流水、并行或重叠。真实 pilot 的边界/余量仍待实例化，旧时间回放完全绕过新对齐规则。

完整 SRAM 写周期继续按原生物理 5 ns 计时，它拥有既有 command/data/BL/WL/cell/recovery；不是声明其内部时钟等于公共数字时钟。接口边沿接受事务后保持完整周期，完成后仅在需要的下一数字接口处等待。不得再为其已经包含的 command/data capture 加一次 DFF。

`clockpolicy()` 拒绝把 service 挂成时钟约束、缺少寄存器边界/完整路径/实际负载证据的约束、仍 pending 的案例路径和 wrapper 级时钟覆盖。合成例显式标 `synthetic_fixture` 与 `synthetic_fixed_load`，不宣称案例 qualified。`normalize_time()` 要求 cycles 带已知 clock，秒/ns 不得带换算 clock，二次换算拒绝。物理路径若需标注所属时钟使用 `constraint_clock_id`，不参与单位换算。

## RRAM 与真实共享

RRAM 原文件 `tasks/task1_table_I_NVM/analysis/05_rram/data/inputs.json` 的 `/adopted_inputs/binary_sense_slot_ns` 明确把 T_B=T_A 称作**共同能力政策**，不是同一 ADC。原参考数值来自 shared 的 `/common_conditions/propagation/profile_values/reference/adc_batch`，为 20 ns。

新主配置把这个原参考值及两处来源保存为独立 `binary_verify_sense_ns=20 ns`。`endpoint_verify` 只消费 `input_step + memory_verify_front + binary_verify_sense_ns`；窗口判决和锁存已包含在独立 sense 预算内。CIM SAR 8/10-bit primitive 的 9/11 ns 不会替换这个预算。普通数字 Comparator 不是 memory 模拟窗口感测模型。

`rram_TB_equals_TA_capability_policy` 明确保留为 `enabled=false` 的对照政策。默认入口不执行它。参数依赖分为 `physical_shared_circuit`、`shared_physical_parameter`、`adopted_capability_policy`，单独原生项另标 `dedicated_parameter`。共同数值不等于共同电路。

PCM 的同一相容电压前端与 SAR 同时服务正常求值/终验；GC 的 common read overhead 与 SAR 同时服务正常求值/刷新，program_complete 同时服务外部装载/刷新重写；NAND 的 WL/BL/SL 和 SAR 同时服务正常求值/装载校准。每个模式的负载、偏置和次数继续保留；NAND 校准的 SAR/BL/SL 系数为 12，WL 为 2。数字周期同样传播至正常、写控、校准、终验及刷新中的真实数字步骤。

## 可运行小例子与结果

`run_checks(cases, policy)` 目前含 **44 条断言**，本地开发结果保存于 `$NEUROSIM_ROOT/runs/step2/revision-clock-dev/summary.json`；最终运行/独立复跑由统一入口归档。

- 固定数字路径 3 ns、目标 5 ns，把独立模拟服务从 7 改成 17 ns：周期仍为 5 ns；下一数字接受各等待 3 ns，随后两数字周期各为 10 ns，总完成 20/30 ns。明确保持资源只延长相应服务/边界等待，accumulator 占用不变。
- 同样固定数字路径和资源，模拟 8→14 ns 时边界等待为 2→1 ns，总完成 20→25 ns；增量为服务 +6 ns 与边界 −1 ns 的和，数字占用仍为 10 ns。
- 保留模拟 7 ns，把真实数字路径改成 7 ns：实际周期变为 7 ns，两拍占用 14 ns，总完成 21 ns。
- 透明嵌套包装得到相同周期/事件；2+2 ns 两个模拟内部阶段连续完成于 4 ns，只在唯一数字入口等待 1 ns，加两拍后总完成 15 ns。错误的内部逐段 ceil 会得到 20 ns，断言明确区分两者。
- 原生 SRAM 5 ns 与公共 7 ns 合成例：原生操作仍为 5 ns，下一数字入口等待 2 ns，不把原生写改成公共一拍。
- RRAM SAR 9→11 ns 不改窗口；窗口 20→27 ns 只改 endpoint_verify 的 7 ns 切片。PCM/GC/NAND 实际共享消费者逐一扰动，按各自系数同步变化。
- 十例数字周期 5→7 ns 的扰动按独立列出的数字 schedule 系数检查；包括 NAND 校准 450 拍、GC 刷新 decode/load 4 拍、NOR 擦除控制 2 拍、MRAM 终验 2 拍、FeNOR 终验 9 拍。

`resolve_binding_contributions()` 输出**依赖切片**，不是完整阶段 latency，也不是新 PPA。只计算选择的线性共享消费者；GC 的 refresh_period、FeNOR 的 max guard、RRAM 互斥 SET/RESET 和其余完整原生周期不由该函数求和。十例原时间完整回放由单独回放器聚合，不能用此切片代替。

集成顺序：旧 `specify()` → `add_bindings()` → `clock_dependency.revise_case()` → 数字覆盖/资源修订。公共 policy 将 `policy_fragment()` 的三块按语义并入既有文件；无需创建并行版本目录。版本为 3.0.0，因为默认 RRAM 依赖、时钟约束和资源语义都属于消费方需明确迁移的接口变化。
