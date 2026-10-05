# GC-04 component service interface

本接口只提供适用外围；GC 存储节点、漏电、读晶体管、反馈写和刷新次序由案例
模型实现。旧 `_3T1C`/HybridCell 没有被用作 GC 单元。

`prepare_components(resolved)` 可先返回 `frontend: {kind: gc_current, request: ...}`。
其字段模板为 `probes/gc_current_request.json`。构建后可由
`prepare_additional_components(resolved, raw)` 返回 `digital: {kind: gc_digital,
request: ...}`，让数字驱动实际消费 `RWL_control_load_per_logical_row_F`。
`evaluate(resolved, raw)` 接收两组真实输出。正式输入须在作者账本中注明各字段
身份，模板不是正式 GC 参数来源。每一服务点的新源码/构建/输入哈希仅含实际选用
的组件和案例支持文件；报告、candidate_points、reference_snapshot 不在计算包内。

## 三节点与两个单端 ADC

每一物理分支依次为：阵列 BL (`array_read_node_C_F`，补到来源限定 50 fF)、
8:1 bank TG、积分节点 (`integration_node_C_F`)、采样 TG、CDAC 节点
(`ADC_node_C_F`)。CDAC 从预充直到积分结束一直连接，随后 SAMP 断开保持；
不存在迟接 CDAC 的免费电荷，也没有零输入电容 ADC。每对是两条这样的分支，
共 256 个原生单端 11 bit SAR、256 个积分器、256 个采样节点，再以 128 个
12 bit subtractor 求有符号差。它是明确重设计，不把原文差分 ADC 免费等价成
原生单端 SAR。原生 SAR 未提供 Cin；20 fF 等输入电容由案例明确选择和检查。

`bank_mux_resistance_basis_ohm` 与 `sample_switch_resistance_basis_ohm` 是
Training Mux 构造器的输入基值。该上游内部还用 IR_DROP_TOLERANCE 缩放 R、
LINEAR_REGION_RATIO 缩放 W。输出同时保留实际 nominal R、N/P W、drain 和
低场过驱动模型的电阻包络。**构造器输入不等于实际偏置电阻。**正式瞬态须使用
一致的实际 W/Vth/Ion 模型，或清楚说明包络近似的适用域。

program 与 read 共用 BL 但 bank TG 在 program 时关闭；OFF 的 BL 侧 drain
仍加到 program 负载。每个积分公共端同时看到全部 8 个 bank TG drain。对
每条物理 BL 另加匹配电容，只有原始阵列负载加关断 drain 不超过 50 fF 时才可
沿用来源的该负载反馈写服务。若未知固定负载使 half-row 几何转用不成立，应在
案例保留条件或判定不可行，而非放宽 50 fF 上限。

## RWL 与短/长脉冲

RWL 使用实际 N/P 尺寸的推挽 INV，idle=1 V、active=0 V；阵列每行前有真实
PWM/mask NAND。`RWL_fall_tau_s`/`RWL_rise_tau_s` 含实际栅负载与线阻，
`RWL_mask_to_driver_s` 与 PWM 分发延迟单独导出，不能把完整传播死区算成
满电流积分时间。RWL 与 SN 耦合电荷属于案例状态模型。

短/长 PWM 用原生非反相 INV delay pairs、两 tap MUX、pulse NAND 和已加载的
分发驱动表示。导出 native pair delay、两 tap 数、面积、实际 RWL 输出 RC 和
要求的脉宽。它**需要对来源支持的可调延迟线做脉宽校准**；
`PWM_*_calibration_factor` 只是所需调节比例，不代表 NeuroSim 已证明模拟偏置
可实现、抖动或 Q4 精度。case 应报告该显式工作条件并进行有限脉宽误差诊断。
短 tap 的统一校准计入 tap MUX 延迟；长 tap 只增加整数 delay-pair 数并使用同一校准因子，`PWM_actual_long_s` 因而可能略长于请求值，case 必须消费实际值。两个 tap 不能独立无资源调节。
外部请求时钟触发 delay line，100/200 ns 时钟不负责产生 3–5 ns 积分宽度。

## 数字与保持

模板 `gc_digital_request.json`：128×12 bit difference hold、256×11 bit raw hold、
16 路 32 bit 加减与可变固定移位路由、64×8 bit input hold、128 bit resident
目标、独立 128 bit refresh sign hold、64×32 bit result hold、16 bit Xsum。
Xsum 真实串行 64 次加法，最小正确数宽为 14 bit，选 16 bit。模拟差码的输入
bit/weight plane 重构与 Xsum 修正由案例调度，每个物理加/减、capture 和源选择
必须计一次；原生 DFF 的半周期不能自动视作完整吞吐间隔。

新 streaming 请求只清 result/Xsum；resident progress、refresh progress 与
16 bit deadline 拥有独立 clear/hold/递增电路。刷新不可清空 resident progress
或未授权的结果状态。两个 8 bit group counter 表示 0..255，terminal carry /
完成状态需由案例时序明确解释；不得以模 256 回卷代表无限续写。

## 实际维护计量

案例 `maintenance` 至少含 `basis: actual_event_schedule`、`feasible`、
`schedule_policy`、`event_summary`，以及秒单位：`raw_stream_s`、
`raw_resident_s`、`long_term_stream_interval_s`、`long_term_resident_interval_s`、
`single_admitted_stream_latency_s`、`single_resident_post_refresh_latency_s`、
`max_group_writeback_gap_s`、`retention_limit_s`。raw 必须与阶段总和一致，所有
间隔须有限正值，实际最大写回间隔不得越过保持界。不可行调度不会导出正式 rho/tau。

输出保留 raw rho/tau、物理 single latency 与单次 resident latency；正式长期
rho/tau 使用事件调度产生的有效服务间隔，U/RI 同时重算。有效间隔不改名为
物理单次延迟。刷新 payload 恒为零；alpha/availability 只能作对照，不能替代
原子不可抢占、guard、逐组 age 和 resident 跨刷新轨迹。

## 追加的实际控制和寄生端口

WWL 另有每行三输入选择门、独立 push-pull driver、行地址译码和 global-enable，
由 `wwl_gate_load_F`、`wwl_wire_ohm`、`wwl_driver_target_ohm`、
`wwl_active_voltage_V` 驱动实际 W/R/C/面积；GC M3 通道仍在有来源的反馈写原语内。
RWL 的 bank 资格是第三个真实 mask 输入，因此未选 bank 保持 idle；它不是只靠
关 ADC bank TG 来假设未选 cell 不活动。2-way bank decoder 显式使用两个 INV，
避免上游 1-bit decoder 的缺失路径/零面积。

`external_hold_cap_F` 在 CDAC 节点单独增加，始终进入积分负载。采样 TG 的
N/P gate C，以及 native capIdealGate、capOverlap、capFringe 和实际温度 Ioff
表值已经导出，用于案例计算关断注入/馈通与保持边界；单凭互补 TG 不假设注入相消。
被动电容总 F 单列，未将电容面积伪称原生 SAR 已包含。

数字新增真实 10-bit operation-index adder/hold、独立 done bit、clear 和 keep；
不复用 retention deadline。completion 使用对应操作数的 ripple carry tap
（1024 操作为 bit10，256 操作为 bit8），保存固定10-bit资源，可用于较小设计。
ADC/difference 阶段保持 index，只有真实 MAC 更新递增一次；微阶段调度仍需案例
明确，不能把所有 Python 循环变量都当成同一个免费计数器。
