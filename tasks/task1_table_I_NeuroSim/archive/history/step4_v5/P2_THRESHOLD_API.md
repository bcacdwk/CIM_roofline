# P2 isolated threshold-port API v0

`threshold_probe.py` is an actual independent native build/execute entry. It does not change P1 or publish full service points:

```sh
python3 -B /absolute/path/step4_v5/threshold_probe.py --run-id unique-name
python3 -B /absolute/path/step4_v5/threshold_probe.py --request /local/request.json --run-id another-name
```

Runtime output is under `runs/step4-v5/p2/integrator-<id>`. Exact sources, applied decoder patch, request header, physical compact ports, native R/C/area/delays and executable hashes are retained. All runs are `probe_only`. No legacy read access or P/E time enters this frontend.

`probes/threshold_port_request.json` is a synthetic square-law/subthreshold fixture. Its model solves a real per-column drain equation and a shared-source equation for two stored threshold states, with one selected row/layer and all unselected branches. It computes actual Vgs/Vds, selected/off current and gate/BL/SL capacitances from explicit physical pitches and terminal capacitances. The default four layers increase capacity/load/leakage; active layers stay one. These are engineering fixture parameters, not extracted NOR/FeNOR material data.

For NOR/FeNOR authors, set `front_end: "case_terminal_ports"` and supply nonempty `frontend_identity`, `source_ids`, `applicability`, `operating_states`, and `terminal_ports` with exactly:

- `actual_gate_load_F`
- `actual_BL_load_F`
- `actual_SL_load_F`
- `sense_current_high_A`
- `sense_current_low_A`

They must come from the author's state/bias/geometry/selection network, with a declared domain and finite positive values. Geometry, process, selected/unselected gate biases, rows/cols/layers/read mux, MUX target and clock remain explicit numerical parameters in the request. Case-terminal mode needs only the common native/selection parameters; the synthetic beta/threshold/leakage/geometry parameters are neither required nor consumed in that mode. Do not disguise unavailable material values as synthetic values to obtain a formal point. The formal author adapter/complete-service connection is the next integration step.

The native executable directly instantiates patched `RowDecoder`, `Mux`, `VoltageSenseAmp` and `DFF`; it never calls RRAM SubArray initialization or writing. The VSA uses a local current-operator carrier (`1/I` with a bookkeeping 1V), solely so its original current-difference formula consumes actual port currents. That value is never used for FET geometry, string/transient resistance, channel selection or programming. Real transient development and reference qualification still belong to the nonlinear case network; the reported native endpoint VSA time is diagnostic.

A native gate driver is marked compatible only for selected gate=actual native Vdd and unselected gate=0. Negative/high gate rails remain explicitly incompatible with that driver until an external characterized gate-port primitive is supplied. A positive native delay is not proof of gate-bias compatibility. No LevelShifter or enum silently supplies a voltage rail.

Necessary case work for the next API: actual reference/sense transient and precharge, electrical gate-port driver at native or external bias, complete layer/row/write/erase lifecycle and local digital schedule. FeNOR must retain layer selection and shared BL/SL/off-state current; NOR must retain three-terminal threshold state and a separate complete P/E engine. P1 digital/hold/verify modules may be reused once their physical port loads are connected; this probe alone is not their completed service.

## Positive lower-rail terminal controls (v2, 2026-10-05)

Five explicit architectural inputs are now available: `gate_driver_width_F`,
`precharge_width_F`, `reference_switch_target_ohm`, `precharge_voltage_V`, and
`precharge_error_fraction`. Diagnostic defaults are 32 F, 16 F, 1000 Ω, the
requested drain rail, and 0.002; formal case inputs must state their choice.
These are selected circuit dimensions, not measured NOR material parameters.

The native row decoder establishes address at native VDD. Each physical WL has
an explicit two-input NAND (address AND global-enable) followed by an INV whose
positive supply is the requested gate rail. The final PMOS resistance is scaled
by `(nativeVDD−Vth)/(gateRail−Vth)` as a stated first-order low-field port model;
`gate_driver_*`, `gate_rise_tau_s`, `gate_fall_tau_s`,
`native_gate_address_s`, `gate_enable_control_s`, and `gate_enable_NAND_s` expose
its dimensions, physical load, and separate propagation/ramp components. A case
must integrate its FET current during this gate transition; decoder time is not
an arbitrary dwell at fully-on current. Negative rails, rails above native VDD,
or nonpositive PMOS overdrive remain incompatible. This extension does not
provide a high-voltage generator, negative driver, or a level-shifter guarantee.

Each sensed data input and reference capacitor has its own PMOS precharger from
the declared read rail, driven by native-VDD control. There are `2×sense_count`
prechargers. All storage WLs and the reference TG are OFF during precharge;
the selected data BL is reached through the already-selected read MUX.
`precharge_data_lumped_RC_s` conservatively charges the lumped sensed load through
PMOS plus the native MUX resistance; the reference expression uses only its
PMOS. These are linear RC diagnostics. The case must check actual bias-dependent
MOS current and any internal nodes, and owns the tolerance/initial-voltage domain.
Both data and reference precharger drains enter the respective matched node load.

The reference is a **full complementary TG** between its precharged capacitor
and the passive resistor to quiet return. Its resistor-side node starts at zero
while isolated. `reference_TG_drain_each_side_F` is added once at each of these
two nodes; the capacitor-side drain is included in the matching-cap calculation,
not silently added a second time. `reference_capacitor_node_total_F` matches the
actual sensed data capacitance; `reference_match_cap_F` is the explicit remaining
passive capacitance, with a nonnegative feasibility gate. Matching capacitor area
is not predicted by a CMOS standard-cell area model and must remain separately
reported in resources.

The first control INV drives the P gate and the second INV input; the second
INV drives the N gate. The reported P falling and N rising time constants and
N launch delay are distinct. A case may integrate these transitions or use an
explicit finite timing envelope; a single `max(delay)` does not make the two
analog branches start together. Native `reference_TG_nominal_R_ohm` and read-MUX
resistance are sizing targets, not valid DC resistance at every common mode.
Native N/P widths, Vth and Ion are exposed for a consistent case bias model.

The VSA result remains an internal latch/timing abstraction as described in
`SENSE_BOUNDARY.zh.md`: case sense development replaces its constant-current
endpoint development; native local precharge/control phases and actual downstream
hold capture are assigned once. The model does not establish comparator offset,
noise, regeneration, or complete timing closure.
