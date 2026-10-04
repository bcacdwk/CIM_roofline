# A：公共读出、初始化与计时

采用 V1.4 `8a88abf85844c0e1ba17cc771ea535fff6040456` 的独立 SAR、DFF、Adder/AdderTree、Mux/RowDecoder/SwitchMatrix 等模块作为公共低压电路入口。主工艺选择 **22 nm、conventional CMOS、LSTP、300 K**，不新增 28 nm 表。`Technology.cpp:641–768` 的 22 nm LSTP 是 PTM 参数表：VDD=0.85 V、Vth=0.419915 V、CACTI effectiveResistanceMultiplier=1.77。SAR 延迟本身仍是固定宏模型。原生存储几何、PL/SL/BL 寄生、电压、脉冲和恢复均由参考设计输入提供，不能按该工艺自动缩放。SRAM 的 SubArray 长宽直接乘 `tech.featureSize`，所以本探针里的 16×16 SRAM 只是受支持的机制见证，**不作为 v3 电荷域 SRAM 宏替身**。

## 可直接调用的接口

所有路径均相对锁定核心 `Inference_pytorch/NeuroSIM/`；精确定位和文件哈希见 `source_map.json`。

|入口|实际输入与实现|原始返回与负责阶段|不覆盖|
|---|---|---|---|
|Technology::Initialize + formula::{CalculateGateCapacitance,CalculateOnResistance,horowitz}|node、roadmap、transistor type；宽度 m、温度 K、输入斜率和负载 F/Ω；表列电流/电容、布局解析、门级 RC/Horowitz|面积 m²、电容 F、阻值 Ω、门延迟 s；低压门和显式互连负载|器件切换动力学、复杂阵列瞬态、charge pump、特殊高压总时序|
|SarADC::Initialize(lanes,levelOutput,Hz,numReadCellPerOperationNeuro), CalculateUnitArea, CalculateArea, CalculateLatency(numRead)|码级数=2^bits；固定 `(log2(levelOutput)+1) ns × numRead`|readLatency 秒，area m²；单 ADC 转换 primitive；并行 lanes 影响面积而不乘单次时长|前端建立/积分、参考校准、mux 时间、符号轮次、保持、完整输出数字重构|
|MultilevelSenseAmp::Initialize / CalculateLatency(columnResistance,mux,numRead)|current mode 查参考电阻 Rref 的延迟表取两端最大；voltage mode 固定 1 ns；再乘 mux×numRead|readLatency 秒；选定公共感测宏模型|该函数并不按传入每列阻值解瞬态；不能映射复杂差分/IBMD/破坏性读恢复|
|DFF::Initialize(count,Hz), CalculateArea, CalculateLatency(ramp,numRead)|同步 `numRead`；异步 `numRead/(2*Hz)`|同步周期，异步秒；声明容量的寄存资源及其计时|没有证明相应组合逻辑可在该频率收敛；不是免费缓存或额外读码保持|
|Adder::Initialize(bits,count,Hz), CalculateArea, CalculateLatency(ramp,capLoad,numRead)|门电阻、电容、进位链 Horowitz；同步转换段在本版被注释|始终秒；明确位宽和负载的加法延迟|不能凭调用它增加参考案例没有的并行通道|
|AdderTree::Initialize(fanin,inputBits,trees,Hz), CalculateArea(height,width,NONE), CalculateLatency(numRead,fanin,capLoad)|第一层指定 inputBits，后续每层使用 2-bit adder 的本版近似；未指定 width/height 会 exit(-1)|异步秒；同步 ceil(physical_s×自身 clkFreq)×numRead 周期；本版原样数字归约|不是任意 HCA/BFA 实现；不自动证明 initiation interval|
|ShiftAdd::Initialize / CalculateLatency(numRead)|非脉冲模式组合 adder+DFF；异步假定可与 cell.readPulseWidth 隐藏；同步返回 numRead 周期|有状态的数字重构；不能与外层同一重构再加一次|其流水假定不自动适用于 v3；主接口选择显式串行调度，除非参考已有资源证明 overlap|
|Mux/RowDecoder::Initialize→CalculateArea→CalculateLatency|拓扑输出数、负载 F/Ω、斜率、numRead/numWrite|门级 RC 秒；公共选通/驱动|不能自动代替 CIMSEL/TBL/PL 等专用高压或模拟前端|
|SubArray::CalculateLatency(ramp,columnResistance,CalculateclkFreq)|完整上游 SRAM/RRAM/FeFET 子阵列组织及已配置内部数字模块|true 返回感测关键路径秒；false 同步返回聚合周期，异步返回聚合秒|不作为十例默认宏入口；V1.4 聚合 writeLatency 未实现，规范接口 null|

SAR 的 65 nm 测试只将独立 `Technology(65,LSTP)` 传入 primitive，其他公共 array/wire 参数未被使用；它验证固定转换公式对该 Technology 输入的不变性，不能说明整套 65 nm SubArray 已初始化。

## 调用链、可变状态及初始化决策

上游 `Param` 是 `extern Param *param` 全局对象。ProcessingUnit 还持有全局 adderTree/bus/buffer 指针。`SubArray::Initialize` 会写回 `param->arraywidthunit/arrayheight/columncap/unitcap/unitres` 等；各 FunctionUnit 保存上一次面积、电容和延迟。因此每个独立配置必须新进程和新对象，不能把对象缓存跨配置复用。

规范顺序为：基础输入冻结 → Param 构造或审查过的集中初始化 → InputParameter/Technology/MemCell 绑定 → 子模块 Initialize → CalculateArea（即使不交付面积）→ 物理延迟 → 周期/服务调度。DFF::CalculateArea 在 135–154 行填 capInv/capTgDrain，Adder::CalculateArea 在 122–135 行填门电容；跳过面积会把后续负载变成未初始化状态。ProcessingUnitInitialize 本身先做 SubArray Initialize 和 CalculateArea。

本轮 probe 的集中初始化白名单只允许固定 22 nm 工艺下改变行列、rowParallel、mux、位平面、输入位数、码级数和时钟，并同步填 `numColPerSynapse/synapseBit/cellBit/numRowPerSynapse/dumcolshared`；随后才创建电路对象。未变更的 wire/access/material 构造链继续取上游默认。对 Step 3 的任意器件和原生负载接入，建议**从配置生成构建副本中的 Param 初始基本赋值，再让原构造派生块执行**，并显式填入原 main 才设置的输入位数与 synapse mapping 字段；或者实现等价且可审查的集中派生函数。不要修改锁定源树，也不散落修改各对象。

探针记录默认→错误后修改示范：technode 22→65 仍留下 featuresize=40 nm；Ron 100 kΩ→50 kΩ 仍留下 maxConductance=10 µS；numRowSubArray 128→16 仍留下 numRowParallel=128。故“字段已改”不等于参数生效。

有效快照至少保存 Param（工艺、温度、模式、row/col/parallel、mux、levelOutput/dumcolshared、cellBit/input/synapse/planes、全部校准系数、wireWidth/Metal0/Metal1/单位电阻、读写电压和 access/Ron/Roff/Gmin/Gmax）、InputParameter/Technology（实际 F/VDD/roadmap）、MemCell（独立器件几何、负载、状态）、模块 lanes/容量/输入位宽/clkFreq、CalculateArea 后的负载与初始化顺序。适用范围为原生支持模式，否则显式 composition。

## 时钟、重复次数和边界

`main.cpp:290–305` 第一遍通过层级性能函数取最大 sensing `clkPeriod`，仅当 target 过快才降低全局 `param->clkFreq`。第二遍 `main.cpp:321–326` 和 `406–411` 却始终用 sensing `clkPeriod` 将周期乘成秒。若 target 更慢，这一转换错误；而原有 SubArray 和 DFF 等又保存初始化时的 clkFreq，不应假设只改全局会同步全部对象。项目避开该聚合入口：先取得感测及所用组合逻辑的物理关键路径，`actual_period=max(target_period,critical_sensing,critical_digital,critical_driver)`；再以确定的 actual clock 新建计数对象/新进程。结果 cycles 绑定 clock_id，仅换算一次。

实测受支持 16×16 SRAM、8-bit SAR、mux2、8 active rows/group、两组、target 10 MHz：感测 12.642065656422386 ns；同步聚合 4 cycles；原 main 式给 50.56826262568954 ns，正确 target 下为 400 ns。这里输出 `upstream_main_conversion_ns` 是把原 main 转换式用于原生实测值的最小见证，不声称又运行了一次整网 main。

计数归属：

- `ProcessingUnitCalculatePerformance` 的 `k<numInVector` 外层逐个已展开输入位向量调用 SubArray。因此 input-bit/pixel 计数已在 PE 层循环，不再给 PE 返回乘输入位数。
- SubArray 的 `numAdd` 来自 rowParallel 分组；同步并行路径 `readLatencyADC=mux×numAdd`。weight planes 体现在映射列数与 numCellPerSynapse；数字 shift-add 已在 SubArray 内，并通过 `MAX(extra - ADC overlap,0)` 等式隐藏部分时间。
- 不拿这种内置流水吞吐当作 v3 稳态服务间隔。主组合调用以 primitive 每次延迟+显式计数为真源；latency、resource occupancy、已证明 II 分开，II 未证明保持 null。
- `GetInputVector` 以非零元素数/物理配置总行数得到 activity；`GetColumnResistance` 以选中的 input==1 支路求和等效电导（包含简化串联线/access 电阻），再按 row groups 分摊。零输入在 parallel 读仍保留 mux×numAdd 计数，sequential 路径则 activity 会降低行数。v3 固定符号相位/轮次始终由外层 service 固定执行，绝不免费消失。
- 上游 `ceil(param->numRowSubArray/param->numRowParallel)`、部分 `ceil(numCol/numColMuxed)` 在参数为整数时先做整数除法。该 probe 明确拒绝不整除组织；未来 composed adapter 必须用整数 ceildiv 处理 tail 并计费，或给出拒绝理由。
- `Chip::LoadInWeightData` 从算法范围 [-1,1] 归一化映射到量化正码，再拆 cell 状态。它不是 v3 INT8 two's-complement 或 NAND split-sign/base-4 编码器，不作为配置输入转换。

## 默认政策与完整覆盖的界线

`validated=true` 保留上游实际系数：alpha=1.44 用 LevelShifter area；beta=1.4 用 SubArray sensing-cycle latency；gamma=0.5 用经 validated 参数启用的 DFF dynamic energy；delta=0.15 用 Adder dynamic energy；epsilon=0.05 用 RowDecoder/MultilevelSAEncoder/Comparator 等控制电路 dynamic energy；zeta=1.22 在 main 最终能效分母中使用（源码注释写 1.23，实际值取 1.22）。这些是**所在模块已应用的作用范围**，不得把 beta 再乘单独 SAR 原始值后又乘整个服务，不得把 validated 宣称为十个新参考宏均经验证。

22 nm 支持 public SAR/DFF/AdderTree/低压驱动路径；目标数字周期采用 5 ns，实际周期必须经对应组合逻辑、负载及感测路径上调。DFF 同步返回 1 cycle 不构成 timing closure；32 fanin、23/29-bit 归约与输出 DFF 的实测为：23-bit 输入归约 1.9065398279794006 ns，29-bit 输入归约 2.290447961367728 ns，均折为 1 个 5 ns 周期，之后显式另计输出 DFF 的 1 cycle；输出负载为 7.8554633692596e-17 F。当前支持 5 ns 数字目标，真实原生负载须再检查。宏级前端超出 5 ns 时按显式阶段/实际时钟处理；不修改固定 SAR primitive 为 5 ns。

V1.4 `SubArray::CalculateLatency` 先将 writeLatency=0，SRAM 和 RRAM/FeFET 聚合写段被注释。probe 中执行后的零只证明缺实现，输出为 null+NOT_IMPLEMENTED_IN_V1_4_AGGREGATION。LevelShifter 用门级两个 pull-up RC 段，不含完整高压泵、脉冲建立、退偏、恢复、重试或终验；这些阶段继续 v3_native_service，不拼凑一个器件材料名称来覆盖。

完整运行日志及失败现场只在本地。a02 曾因 AdderTree area 未提供宽度而按原版要求拒绝，a03 起提供 100 µm 测试布局宽度；此探针宽度仅为模型初始化所需的输出电路布局条件，不加入十例配置。

## 执行结果

`python3 probes/read_timing/run.py --root "$NEUROSIM_ROOT" --out "$NEUROSIM_ROOT/runs/step2/<fresh-name>" --cxx "$CXX"` 从任意 cwd 可用。最终开发运行 `runs/step2/read-timing-a04` 为 PASS，52 条断言；SAR 8/10-bit 单次 9/11 ns，numRead=2 为 18/22 ns；1/8 lanes、10 MHz/1 GHz、22/65 nm 均符合固定公式。全部 C++ 源码按原锁 SHA 原样复制并记录 SHA-256，不修改上游公式。云端仅 probe.cpp、runner、notes 和 source_map；完整输出在本地，supervisor 可白名单导出 summary.json/commands.json。

### SwitchMatrix 必须特别绑定

`SwitchMatrix::CalculateLatency:237–279` 的 readLatency 实际由全局 `param->unitcap/unitres/numColSubArray/buffernumber/drivecapin` 的分布 RC 计算，不直接使用形参 capLoad/resLoad。采用该模块时需把原生行网转换为这些绑定（保持长度/电容/电阻），不能仅改变形参。read 路径已注释 DFF 加项；write 路径仍把 RC 秒与 `dff.readLatency` 相加，同步模式会把周期混入秒。最终 probe 直接记录其 `wl_driver_write_mixed_raw` 与 DFF raw，并在同步/异步之间验证这个问题。规范写返回不采用它；单独读驱动只取 RC 秒，寄存计数另列且不能重复。这是又一个避用同步整体写返回的具体理由。
