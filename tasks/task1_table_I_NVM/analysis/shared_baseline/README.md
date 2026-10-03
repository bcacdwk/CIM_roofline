# Table I 共享估算基线

本方法比较所选原生参考配置的输入服务能力 ρ、resident 更新服务能力 τ 与 RI*。统一逻辑字节、INT8 默认精度和本地服务边界；各案例独立选择有依据的原生 K、N、物理组织和更新模式，不宣称等面积或相同计算量的性能排名。128×128、16 KiB 只用于算例和辅助平均成本展示。

## 阅读与资源政策

- [完整中文方法 PDF](output/shared_baseline.pdf)，[外围与资源](tex/01_cmos_periphery.tex)，[计数与两表接口](tex/02_estimation_method.tex)。
- [共享参数与 R1–R8 规则](data/shared_parameters.json)，[原文证据定位](notes/evidence.zh.md)。
- [生成算例及结构数据](data/sensitivity_results.json)，[计算与检查 API](scripts/check_shared.py)。

输入从整向量本地寄存边界捕获，寄存器为 `K*b_S*8` bit；N 个输出各用足够容器，INT8 默认 `16+ceil(log2 K)` bit。捕获、提交各一 TD，完整宏周期已包含者不重复加。上游传输、下游搬运另属系统映射。

数字路径共同允许至多 32 项×16 输出×8 bit、4096-bit 单 tile 保持，跨全部输入位复用。SA 数和读 bit/批独立声明；新增保持每实际读取批捕获一 TD，已有 SA 捕获或静态连接不重复收费。单 bank 不能边计算边覆盖；部分和寄存器维持到完整向量结束，不提供全矩阵 shadow。原生 D6 16 项保留原周期。

ACIM 通用资源参考为 8 个二元位平面、每平面 16 ADC、16 重构通道和每轮两拍。原生完整证据可支持其他组织，但必须列出资源、模拟动态范围、精度及恢复。ADC 名义 10 bit、约 8 有效 bit 的公共时隙不自动适用于所有行数；模拟保持有槽数、隔离、负载与保持窗口成本。

外部更新单域，128-bit 编码数据接口；至多 128 个二元目标是共同配置资格，真实并行仍由原生选通、驱动、电流、耐压和负载确定。页、块、互补编码、参考页、SET/RESET、program/verify 和内部恢复均按实际资源计。驱动数量、额定电流、ADC 数和保持容量在三情景内固定；服务时间可随相容条件变化，硬件必须承受最快情景所需负载。FeFET 约 7.7 mA 和 FeRAM 约 4 mA 加 PL 是各自典型边沿需求示例，不是统一供给上限。

公共 `(TI,TA,TD)` 为短 `(2,10,2)`、参考 `(5,20,5)`、长 `(10,50,10)` ns。真实案例应扫描主导条件，三情景采用同组织、同资源额定能力的相容读写；扩充资源、预擦除 burst、维护临界及不可行单列。维护前与长期有效能力分存，维护不增加 Q_R。

## Table I 到 Table II

对 `W[N,K]`，完整装载一次、求值 U 个向量：

```text
Q_S = U*K*b_S             Q_R = K*N*b_R
RI = U*b_S/(N*b_R)
rho = K*b_S/Delta_S       tau = K*N*b_R/T_R
U* = T_R/Delta_S = (N*b_R/b_S)*RI*
INT8: U* = N*RI*
```

T_R 是该矩阵、更新模式与硬件配置的完整装载服务；Delta_S 是完整向量服务间隔，有流水时不同于一次端到端 latency。两路时间平衡不保证峰值同时达到。扩展到算子后按输入共享、重放、分时及共享写资源重算；仅两路同比扩展时宏级 U* 沿用。FFN、Attention、多分支分别按阶段映射，不改 Table II 入口计数。

## 计算 API

所有时间参数单位 ns，吞吐 Byte/s。所有依赖维度的服务调用必须传 `logical`；全局 `L` 只代表共享演示形状。`R` 为资源示例，不替代案例账本。

```python
logical = S.logical_configuration(K=64, N=32, b_S=1, b_R=1)
ds, counts, hold = S.acim_service(acim_config, profile, read_ns, logical)
ds, counts = S.dcim_service(dcim_config, profile, read_ns, logical)
br, dr, batches, beats = S.direct_service(write_config, td, logical, resident=write_port)
front, beats = S.front_ns(encoded_bits, td, first_data_in_command, resident=write_port)
load = S.full_load_service(logical, [
    {"payload_Byte": 16, "service_ns": dr, "count": 128}
])
interface = S.mapping_metrics(logical, delta_S_ns=ds, T_R_ns=load["T_R_ns"])
maintained = S.apply_maintenance(interface, period_ns, busy_ns, guard_ns)
```

`acim_counts(a,v,logical)` 与 `dcim_counts(d,logical)` 提供计数。`dcim_config` 声明 `read_bits_per_batch`、`read_reuse_input_slices`、`hold_source`、`weight_latch_bits`；`hold_source` 为 `added_latch` / `existing_capture` / `static_connection` / `none`。新增捕获默认每读批 1 TD，可显式设置 `capture_ticks_per_read_batch`；只有已完整覆盖时才能不重复收取。静态连接沿用完整 MAC 周期时传 `read_ns=0`，其 `read_rounds` 表示潜在感测批计数，不是又执行了这些感测。更细能耗分析需另记录实际选通次数。

`full_load_service` 接收实际 payload/time/count 的事务列表并断言 payload 恰覆盖一次矩阵；尾批、零 payload 的设置或校准事务均保留时间。输入 payload 可为字节的分数，但必须对应整数精度 bit。

```python
block = S.native_block_service([
    {"logical_payload_Byte": 24, "encoded_load_bits": 384,
     "program_full_ns": 100, "count": 3},
    {"logical_payload_Byte": 0, "encoded_load_bits": 384,
     "program_full_ns": 100, "count": 1}  # reference page
], erase_ns=1000, td=5, resident=write_port)
```

每页含完整 program，额外 verify 不重复加；参考、校准、复制页 payload 为零但完整计时，调用者证明有效权重能被选通求值。多个块用 `full_load_service` 聚合。`page_service(x,td,resident=None)` 保留均匀有效页的摊销接口。

`mapping_metrics` 返回：`K,N,b_S,b_R,B_S_Byte,full_resident_payload_Byte,T_R_ns,delta_S_ns,rho_Byte_per_s,tau_Byte_per_s,RI_star,U_star,average_update_ns_per_16KiB`。兼容字段 `B_R_Byte`、`delta_R_ns`、`ridge` 分别与完整 payload、T_R、RI_star 相同。每 16 KiB 平均成本只按 `T_R*16384/(K*N*b_R)` 换算，不是一次实际请求延迟。

`apply_maintenance` 返回 `raw/effective/availability/feasible/period_ns/busy_ns/guard_ns/maintenance_payload_Byte`。仅用于两路共享同一串行预留的已声明调度；alpha 大于零是占用可行条件，调用者仍须证明非抢占边界、刷新期限、部分和保持和足够有限窗口。alpha 小于等于零时有效时间、能力、RI*、U*为空，原始能力保留。不隐含流水或 demand-write refresh credits。

每例结果顶层使用 `native_configuration` 保存 K、N、b_S、b_R、有效容量、物理容量/编码/复制、输出位宽和资源；每情景的 `mapping_interface` 直接保存公共映射结果，保留原有局部事务字段用于复算。

## 模式、参数作用范围与数值服务

`inputs.service_modes` 为正常求值、写后终验、装载校准及恢复/刷新声明实际操作、偏置/负载/建立终点、来源与资格条件。相同物理量或明确的共同能力政策只保留一个参数值；各服务以 `parameter_bindings` 绑定该值。相同数值不证明模式相同，不同数值也必须由实际操作区别支持。完整页 program 中已包含的内部 verify 标为 `included_in_cycle`，不重复加入。

```python
values = {**profile, "shared_front_ns": 20, "long_observation_ns": 768}
bindings = {
    "normal_evaluation": {"front_ns": "shared_front_ns", "ta": "adc_batch", "td": "digital_tick"},
    "endpoint_verify": {"front_ns": "shared_front_ns", "ta": "adc_batch", "td": "digital_tick"},
}
p = S.resolve_service_parameters(values, bindings, {"shared_front_ns": 768})
# 两个服务均从 p 取参数，再计算 Delta_S、完整 T_R 及映射。
```

API 返回 `{service: {local_slot: value}}`，拒绝未知参数、未知绑定及没有消费者的 override。同一物理通路仅增加最低观察要求时，终验必须同时绑定 `shared_front_ns` 和 `long_observation_ns`，实际前端取 `max(shared_front_ns, long_observation_ns)`；独立验收要求不能解除共同建立下限。只有实际采用不同路径或偏置、并有相应证据和资格条件时，才可将终验前端独立绑定到另一参数，同时保留仍然共用的转换和控制依赖。操作模式对照不代表共享前端较慢。共享参数不确定性保持绑定关系，仅改变一个源值。`T_I` 已含于完整前端 `F` 时由 `t_m=F-T_I` 分解，固定 `F` 的 `T_I` 扰动不会再增加完整周期；若考察固定残余 `t_m`，则 `F` 必须随 `T_I` 变化。两种条件不可混用。

`scenario_class` 明确区分 `paired_main`、`parameter_uncertainty`、`operation_mode_comparison`、`resource_comparison`、`maintenance_pressure`；有限重试选点另用 `finite_retry_sensitivity`。`input_step/adc_batch/digital_tick` 的可能消费者及已含周期规则见共享 JSON 的 `parameter_scope_policy`。每例检查实际消费者；涉及维护时须同步计算 `H`、guard、alpha 和两路原始/有效能力。通过参数解析只证明绑定，不代替实际阶段计数和物理资格判断。

活动行、编码、偏置或量程变化时，按真实分组和数字重构顺序检查确定性零值、小值、正负抵消及大幅值。理想代数恒等式与名义码宽量化后的重构分开保存，并保留动态范围、饱和、抵消和弱信号诊断。ADC 名义码宽、ENOB 和最终输出容器位宽分别声明；约 8 ENOB 可用 `full_scale/2**ENOB` 表示分辨能力量级，不能将其当成实际 8-bit 量化器或无来源的噪声分布。DCIM 精确整数、ACIM 近似部分和合同保持不变；该最小检查不设统一网络准确率门槛，也不证明器件变异或电路建立已经验证。

五个 ACIM 共用 [名义服务检查](scripts/check_nominal_services.py) 和 [完整诊断数据](data/nominal_service_diagnostics.json)：15 类确定性向量覆盖零输入/权重、小值、抵消、较大幅值、孤立单位及原生分组边界。每类保存真值、重构值、绝对残差；非零真值另报相对残差，零值单列。NAND 按电流、10-bit 量化、有限增益校准和实际符号/分组重构，同时保留原偏置编码的受限对照；GC 按理想积分电流、差分量程、10-bit 码和明确整数部分和舍入，保留舍入前残差与正端码饱和。

SRAM ACIM、RRAM、PCM 缺少新前端的完整传递和标定码表，共同检查止于已标定理想部分和与数字重构，并检查名义码数量是否足够容纳等级；其 `quantization_induced_bias_assessed=false`，物理 ADC 量化残差为空。不能把这三例的零代数残差称为模拟链通过。结构性 signed-INT8 映射资格与应用精度要求分别保存；受限编码点不得自动进入通用 signed workload 适配。名义诊断无误、时序公式复算一致以及器件或网络准确性验证是不同结论。

## 复算与构建

```sh
/opt/anaconda3/bin/python scripts/check_shared.py --emit
/opt/anaconda3/bin/python scripts/check_nominal_services.py --emit
BASELINE_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

默认检查只读，`--emit` 更新现有生成 TeX 与 `data/sensitivity_results.json`。检查包含非方阵和尾组、SA 分批和保持生命周期、编码与参考页、完整装载、不同精度、非对称扩展、维护临界及独立算术。构建需 XeLaTeX/latexmk；渲染需 pypdfium2/Pillow。机器精度不代表参数测量精度。
