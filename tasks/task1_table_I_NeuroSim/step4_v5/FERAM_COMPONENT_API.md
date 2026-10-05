# FeRAM case charge terminal interface

通过 `run_components.py` 的 `kind: polarization` 使用 `special_probe.py`。
请求为 `kind: polarization, front_end: case_charge_ports,
point_eligibility: component_only`，另给 `source_ids`、`applicability` 和案例的电荷
分支/适用域记录。`parameters` 最小字段：

- `technology_nm, temperature_K, rows, read_columns, clock_Hz`
- `sense_target_V, sense_pitch_m, destructive_domain_bits, restore_lanes`
- `BL_wire_extra_cap_F, HV_access_drain_cap_F_each, HV_access_R_ohm`
- `LV_decoder_output_load_F`

外围实际 BL 总电容为线/其他显式电容、每列所有 `rows` 个额定 HV access drain
和原生 SA Cin 之和。没有把低压原生 access 当成高压器件。`HV_access_R_ohm`
只回传为来源明确的有效端口；案例自行解极化/介电电荷与传输，不能把旧完整读时隙
伪装成 RC。内部保留的 `native_access_R_ohm` 是原生诊断值，与该正式路径无关。

返回 SA 的 `native_SA_internal_cap_F`、`native_voltage_sense_s`、
`native_sense_included_enable_s`（原生已含 `1/f`）、完整破坏域的实际 hold bit 与
capture，以及按真实 level-shifter LV 输入负载计算的 `native_LV_decoder_s/area`。
HV supply、level conversion、plate/access/return 的额定域和服务由案例可见保守块承担；
公共接口不生成隐藏的 HV 保证。`native_WL_gate_compatible=0` 表示原生低压门
不能直接驱动 HV gate，允许案例用已说明的额定端口接替。

case-charge 模式不返回 synthetic charge 解/裕量/切换域 PASS。案例 evaluate 使用
真实 SA Cin 后自行给出电荷守恒、读状态/恢复范围、128路保持与写回资源、参考与
精度资格。原 synthetic polarization fixture 留作机制诊断，不能代替 HZO 极化。

真实接口探针 `polarization-external-charge-port-r2-20261005`：130nm、32行，
每cell access drain 4.22314355fF、wire107.86fF，native SA7.13784fF →总250.138fF；
LV decoder load653fF →8.218ns；200ns周期下 SA200.0696ns（含200ns enable）、
128bit hold capture100ns。该探针的 access R1000Ω是接口示例，正式模型由案例同源
端口替换；这不是一个已接受的服务点。
