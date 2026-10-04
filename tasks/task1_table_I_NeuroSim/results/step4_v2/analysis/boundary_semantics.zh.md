# Step4 V2 消费边界只读分析

无生产修改；分析脚本及 JSON 与本文同目录。固定 V1 后端、物理时间、SAR 和周期的微型试验不是新的器件参数选择。

## 唯一时序语义

1. **周期型操作**：源在 E0 有效，经已建模组合逻辑至 E1（或合法 E2）末端寄存。开始时间是 `ceil(t/T)*T`，耗时 nT；clock-Q、目的 setup 在完整路径资格中计。没有独立入口寄存，故不可在 E0 前再加同一个目的 setup。
2. **捕获/ready 边界**：只有已有接收寄存器采样/发布，不含另一个启动—传播—捕获操作。时刻为 `ceil((t+setup)/T)*T`，没有额外完整周期；setup 不删。
3. **原生已含接收**：保留完整原生服务。已有原生 setup/capture 不再建第二份；必要的公共端口准入仅做零 margin 的边沿限制。物理连续子阶段之间不对齐。

`T=10 ns, setup=0.05 ns`：物理完成 t=9.90/9.95/9.99/10.00/10.01 ns，完整单拍操作结束分别 20/20/20/20/30 ns；纯采样分别 10/10/20/20/20 ns。V1 的“先 setup 对齐再完整拍”分别 20/20/30/30/30 ns，是第三种带独立入口寄存的操作，不能无对应寄存器和资源而默认使用。

包装不变性：相同周期操作拆为 `boundary(margin=0)+phase1+phase2` 与原 `digital(cycles=2)` 一致，所测六个临界前后时刻均通过。相同捕获不能先加一个对齐 wrapper 再加 setup capture；t=9.90 的第一次对齐会把原本可在 E1 采样人为推至 E2。纯记录 wrapper 应不消费时间、不改变有效物理完成时间。把真实周期改为采样不属于包装变化，是必须有来源的阶段语义更正。

## 阶段分类建议

|阶段|V2语义与依据|
|---|---|
|NOR/FeNOR operand_capture|单组4096bit现有新增保持区采样：setup捕获边界、0额外周期；捕获次数和8ibit保持生命周期不变。原NVM的“one TD capture”是固定时间预算，未给额外入口/末端两组寄存，V2明确重解释成真实采样边界，legacy replay仍按旧预算。|
|MRAM operand_capture|保留完整1周期、去入口margin：原stage_coverage.stream明确“captures W and completes isolation handoff”，mapping.hold_lifetime给出capture/isolate/reset交接。需标注控制/隔离操作边界，不能当免费纯采样。|
|MRAM/FeNOR terminal_verify.capture|纯状态采样，保留setup、无额外周期；之后compare仍分别1拍/8拍，目标寄存/比较资源不变。|
|PCM endpoint_verify.compare|SAR本身已有代码状态，compare为组合比较/归约至mask/done的完整拍；不新增SAR→比较入口寄存，故入口margin=0，目的setup由完整比较路径约束。|
|GC refresh sign_decode|SAR状态→符号逻辑→已有128bit刷新code hold，完整1周期，入口margin=0，末端setup由gc_refresh_sign_path覆盖；后续encoded_load及完整current-program不变。|
|PCM/GC reconstruct.phase1/phase2|同一E0→E2传播窗口，phase1入口margin=0，无E1中间采样；phase2不得重复setup/重启。最终setup由重构数据路径计一次；E1更新capture-enable依然一拍。|
|NAND affine_calibration_budget|保留非零一拍算术预算，入口margin=0；未实例化完整乘/舍入路径，不因其后公共路径合法而声称全数字时序闭合。|
|NAND calibration_sample_capture|真实SAR→已有系数槽采样，保留setup boundary。每次结果在下次转换覆盖前捕获。|
|NAND page_ready/erase_set_ready|原生P/E BUSY解除后的外部状态采样，保留setup boundary；无额外内部verify/recovery。|
|NAND calibration divider/round/publish|现有有限周期预算保持非零，边界不另加setup；加法/DFF列表未闭合算术。|
|NOR sector_erase.completion|原有两控制拍中的completion拍，可保留完整控制operation，入口margin=0。|
|MRAM polarity_turn|现有两写方向之间的真实控制拍，入口margin=0；脉冲的原生退出已含在完整方向写周期。|
|FeRAM binary_read|已有破坏性读+恢复+捕获完整预算，只收费一次；不加第二捕获。MAC是完整周期、入口margin=0。|
|native page/current-program/FeRAM write ready|原生恢复后公共接收/发布，保留单次setup boundary；末尾matrix/refresh marker如只是同一状态标记，不再采样。|

## Pilot 一致性

三个 pilot 的所有 `digital` 事件入口 margin 都为0，已符合周期型规则。SRAM ACIM/DCIM原生写包含capture/setup，准入/matrix-ready为0 margin boundary；RRAM最终rail_exit后的matrix_publish是另一次真实ready接收，保留setup boundary。输入capture包括现有输出累加器clear及schedule admission；output_commit包括已有I/O/控制端点操作（ACIM无新输出副本bank，RRAM使用已有controller；DCIM从原生结果送既有output bank），不因命名中“capture/commit”便改成零周期。

用原后端/原生参数只读重建adapter计划并执行pilot schedule，均与验收值一致：01 ΔS=2890/TR=5120 ns；02 ΔS=330/TR=640 ns；05 ΔS=4490/TR=1911765 ns。当前未见需要修改pilot已验收物理/数字语义的证据。

## 固定周期对照与NAND预算

完整操作去入口margin会消除NOR每组读后多出的整拍：ΔS 7060→6740 ns、TR 205612280→205612240 ns；FeNOR ΔS4500→4180 ns、TR337920→327680 ns。NOR/FeNOR当前整数周期物理完成点下，单次capture边界与无margin的一拍capture恰同值，但前后微例可区分；不能靠参考点相等判断两种语义相同。

MRAM保留operand_capture而terminal capture改边界时，ΔS仍1782 ns、TR168960→146432 ns，少2次11 ns/事务。纯边界捕获仍实在占用采样寄存和互斥资源，不是零延迟原生读。

NAND保持T=9ns、SAR、容量、端口和所有资源不变，只把affine(1cycle/960批)、calibration division(24cycle/16批)及round-residual-store(4cycle/16批)乘2/4；最终2tick发布不乘。ΔS 685710→694350/711630 ns，增加1.2600%/3.7800%；TR1923285366→1923289398/1923297462 ns，仅增加0.0002096%/0.0006289%。不改变数量级；resident仍完全由原生P/E主导。可保留明确条件预算，无需本轮扩建乘除库。该敏感性不验证1cycle预算成立、也不证明任意未知开销均小。
