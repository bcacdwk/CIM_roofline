# 数字路径与写资源语义：Step 2 定向修订

本文件给 supervisor 集成用；规范配置仍是唯一机器真源。`digital_resources.py::revise_case` 在原 `specify/add_bindings` 和时钟修订后执行，不修改 v3 时间、阶段次数、嵌套调度、时钟归属或共享绑定。`run_checks(cases, policy)` 检查配置；`run_native(root, out, cxx)` 在全新的本地目录编译原生模块对照。这里没有十例新 PPA。

## 展示与状态

每段新增 `coverage.kind`（原生模块 / 混合阶段 / 保留原生服务）及 `dominant_timing_provider`，报告应显示这两项，不把含长原生服务的整段称为“NeuroSim 主调用”。四个状态有不同范围：`route_defined` 是已定义接口，`native_module_probe_run` 只代表构件机制，`case_path_pending` 是尚待实际负载/寄存路径实例化，`native_budget_retained` 是当前继续用原预算。任何十例整条数字算术路径都没有因本轮构件探针升级为 qualified。

每段 `call.operation_plan` 列运算、周期安排、寄存器边界、可复用构件、缺失逻辑及下一步。缺失逻辑继续占用 v3 原预算；它既非零延迟，也不靠罗列 Adder/AdderTree/DFF 获得时序依据。

| 路径 | 明确运算与当前界线 |
|---|---|
| SRAM ACIM / RRAM 两拍重构 | 128 个 10-bit SAR 结果在两拍内保持；八权重平面有符号归约、输入位移位/符号、输出累加。没有新中间寄存器；第二拍需要时重新组合归约。树至累加器的完整组合路径、源驱动和 setup 尚待 pilot。 |
| NOR / MRAM / FeRAM / FeNOR 数字 MAC | 已保持权重 tile 与输入寄存器 → 输入门控/符号扩展 → 32 项归约 → 位移/输入最高位负号 → 输出累加寄存器。一次输入位只占既有一拍，树、控制和累加的实际串接路径仍 pending。 |
| D6CIM | 保留原完整 16 项 HCA/BFA MAC 周期，包含门控、原生读、归约、符号与累加；generic DCIM 256×256 树不替代该周期。 |
| NAND affine / merge / sign | 四拍边界依次为既有 896-bit affine-count、320-bit magnitude-sum、168-bit polarity-difference 和 6960-bit output/accumulator。10-bit code×Q8.16 gain、Q12.12 offset、round/saturation、base-4 merge、极性减法、符号累加均明确列出。64 个 affine multiplier 的延迟没有被 AdderTree 覆盖，当前四拍算术预算保留。 |
| NAND 装载校准 | 16 arithmetic lanes ×16 channel batches，24 division ticks＋4 other ticks / batch，加 2 边界 ticks＝450；减法、除法递推、round/store、残差和阈值判断均须映射。除法器及工作寄存器未由当前构件实现，保留完整算术预算；原生模拟与共享 ADC 保持独立组成。 |
| PCM 重构/终验 | 重构的源代码保持、归约与累加实际路径待实例化；终验是原电压前端＋共享 SAR＋已有比较一拍。数字端点比较/异常逻辑不冒称 analog window comparator。 |
| GC 重构/刷新 | 重构代码保持与 release/arbitration 待实例化。刷新使用已有 128 sign-decoder/code-hold，形成 256 encoded bits，两次端口传输后调用完整 current-feedback rewrite；不增加全矩阵 shadow，也不省略译码/控制路径。 |

NAND 阶段寄存资源来自 v3 `check_nand.py::native_configuration`（约 179–187 行）；450 tick 算式在 `scenario`（231–234 行）。原预算是既有设计输入，并不代表本轮完成电路时序收敛。

## AdderTree 模型的实际范围

锁定 `8a88abf85844c0e1ba17cc771ea535fff6040456`、`Inference_pytorch/NeuroSIM/AdderTree.cpp::CalculateLatency`（123–173 行）首层以给定输入宽度调用 `Adder`，其后每层以 2 bit 调用，异步返回秒，同步才 ceil 到周期。`Adder.cpp::CalculateLatency`（138–229 行）本身以晶体管电阻、电容、Horowitz 及位宽相关的中间进位链计算；延迟仍是模型，非门级 STA。

新 `addertree_probe.cpp` 对 8 / 32 输入以及 8 / 18 / 23 bit，实际运行锁定原模块。它比较：

1. 原树返回；
2. 独立构造的 `D(W)+(depth-1)D(2)`；
3. `D(W)+D(W+1)+...` 的逐层完整位宽串行模型。

第二式复现原生特定树进位到达近似；第三式采用每层均完整进位传播的不同到达/边界假设，只作模型对照，不是正确性 oracle。源码没有给足以证明所有混合符号、任意负载和门控串接时序的说明，因此不能从此推断一个普适误差，也不将 2-bit 处理预设为 bug。原生构件适用于保留该树模型假设的候选归约；不认证 NAND affine multiplier/divider 或树外附加逻辑。CalculateArea 必须先执行以生成后续延迟电容依赖。

## 写资源的量纲

移除 `real_write_driver_count`、`physical_write_driver_count` 两个泛字段。`resources.write_semantics` 分别记录电气输出、已知 program channels、被选存储目标、每目标的互补物理单元、逻辑 Byte、端口 bit/beat、更新域、完整装载事务数。规范调度从 payload/目标/相位直接计算，不从电气偏置节点或端口位宽推断编程并行度。

| 特殊对象 | 保留量与用于事务计算的量 |
|---|---|
| FeNOR | 288 electrical bias outputs／288 bias nodes，8 strips，128 selected cells，16 Byte / transaction，1 domain，1024 transactions；独立 program head 数未报告。288 不变但不再作为独立编程目标。 |
| GC | 128 pair programmers，256 electrical branches，128 complementary pair targets，256 encoded bits、16 logical Byte，256 transactions。 |
| MRAM | 128 drive lanes，64 complementary pair targets＝128 MTJ states＝64 logical bits＝8 Byte；两相分别 128 / 64 active MTJ，1024 transactions。 |
| PCM | 32 IDAC channels 与 32 selected cells，8 串行 weight-plane batches 组成一笔 32 Byte transaction，1024 transactions。256-bit transaction buffer 不等于 256 physical write channels。 |
| NOR | 128-bit port；2048 native page targets，256 Byte / page，64 pages，4 sectors 构成一次完整矩阵 transaction。内部 write head 数未知。 |
| NAND | 128-bit nominal port；data/reference useful rate 48 / 128 encoded bit/beat；每页选 13824 targets，5760 data＋384 reference pages；program heads 未知。编码后的 cell 和 reference 不计作新 workload Byte。 |

`encoded_bits_per_load_unit` 明确表示一个装载单元，`load_unit_scope` 对 NOR/NAND 为 `native_page`，其余为 `resident_transaction`，不再把一页的 encoded bits 命名为整笔矩阵事务。`load_units_per_transaction` 分别为 NOR 64、NAND 6144（含 384 个不增加 workload payload 的参考页），其他为 1；`program_batches_per_load_unit` 对 PCM 为 8 个串行平面，其他为 1。二者乘积才是 `program_batches_per_transaction`。batch 表示原生选择/编程服务的目标组；未知内部写头、RRAM 有限重试、MRAM 两相操作均不能从该元数据批数推断或删去。

新检查既检查具体整数和单位，又检查容量与编码、每笔完整 payload、相位目标和原生 page 数。所有参与计数的 quantity 都检验准确单位（包括 `program_channel` / `pair_programmer`、`storage_cell/<target_unit>`、`encoded_bit`、`update_domain`）和正整数/显式未知状态；批数从所选目标、互补单元、编码和平面/页组织重新推导。负例包括将 FeNOR 288 bias outputs 换入 128 targets、将 port width 换入 MRAM/PCM/页目标、把 pair programmer 或 update domain 标成 bit/beat、把编码单元/互补因子标成 Byte、使用数值相同的浮点计数，以及把任意批数改为 13，均必须拒绝。原始 `resources.native_declared` 只作为 v3 证据保留。独立审查补充后的 helper 自检为 343 条 PASS；本次仅改接口数量检查，没有重跑或修改原生 C++ 公式。

## pilot 待完成

SRAM ACIM / RRAM 仅在下一轮实例化既有 SAR 结果保持、八平面组合归约至输出累加的实际负载与寄存边界。当前两拍预算和无新增中间寄存器不变。RRAM 独立窗口感测另由时钟/依赖修订保持原生预算，数字 Comparator 不提供其模拟窗口建立时间。
