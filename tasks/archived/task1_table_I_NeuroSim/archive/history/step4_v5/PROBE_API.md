# V5 binary-port prototype API v0

This executable is real circuit integration, **not a complete PCM/MRAM service backend**. Current callable entry:

```sh
python3 -B /absolute/path/step4_v5/native_probe.py --run-id unique-id
python3 -B /absolute/path/step4_v5/native_probe.py --request /local/path/request.json --run-id another-id
```

Each call builds a fresh copy of locked MLPInferenceV3.0 `6098feabaf17b8209a8edbef4a9c963b5f015132` under `$NEUROSIM_ROOT/runs/step4-v5/p1/integrator-<id>` (default `$HOME/neurosim`). It copies exact core and required root Param sources, applies the registered V5 column-load patch, generates `request.h`, builds C++, runs, verifies error text/finite mandatory outputs/consumption and writes source/input/binary hashes. No old results, ADC timing slot, existing binary, network weights or training data enter it. A failed run remains in its local directory. Nothing is exported automatically.

## Minimal request to case authors

Copy the shape in `probes/binary_port_request.json` to your local run or your owned case directory. It is an explicit synthetic circuit fixture, not a source of material values. `point_eligibility` must remain `probe_only`. The exact numeric request fields are:

| Fields | Port meaning |
|---|---|
| `technology_nm`, `temperature_K` | Native peripheral CMOS design point. Current supported nodes: 130, 90, 65, 45, 32, 22 nm; integer temperature 300–400 K. Not material-temperature evidence. |
| `device_node_nm` | Material identity marker, returned as such; never used to assert same-chip process compatibility. |
| `rows`, `cols`, `read_mux`, `write_mux` | Physical single array. Current native diagnostic uses 8 binary cells/synapse; cols divisible by 8×read_mux and write_mux; muxes at least 2 to avoid uninitialized absent native decoders. This restriction is prototype support, not a chosen final hardware architecture. |
| `cell_pitch_x_m`, `cell_pitch_y_m` | Physical pitches in metres, converted once to native peripheral F so the requested dimensions reach actual initialized lines. |
| `resistance_on_ohm`, `resistance_off_ohm`, `access_resistance_ohm` | Two ohmic state ports at the declared read point, with separate access resistance. Ron<Roff. Native access transistor is auto-sized; actual F/metres returned and layout fit is enforced by the native model. |
| `read_voltage_V`, `access_voltage_V`, `write_port_voltage_V` | Read bias and selected access/write decoder port conditions. `write_port_voltage_V` only initializes selection hardware; it proves no programming current or pulse. |
| `wire_ohm_per_m`, `extra_column_cap_F` | Explicit line model and added nonnegative sensed-node capacitance. Include scope/source; do not infer them from old full read access. |
| `clock_Hz` | Native clock argument; VSA contains 2/f per read group, DFF native capture returns seconds. It is not yet a timing-certified final macro clock. |

A normal case input remains the authoritative contract in INTERFACE.md. The author should provide physical inputs, source IDs, applicable voltage/current/temperature domain, and list missing evidence; the integrator maps those fields to the diagnostic request. Do not alter common C++ or pick synthetic fixture values as defaults.

## Actual executed path and output ownership

`SubArray` is initialized as `Type::RRAM` (generic resistive carrier), `CMOS_access`, `digitalModeNeuro=true`, `parallelRead=false`, one active row, one input pulse. Initialize → CalculateArea → CalculateLatency really executes native WL/column decoder and driver, read MUX, VoltageSenseAmp, Adder, DFF and Subtractor. This enum is never the material identity. No complete signed INT8 service is claimed from the native aggregate.

Native decomposition in `resolved.json` includes selection, MUX, VSA, unsigned adder/capture, dummy subtraction, shiftadd (disabled=0), full aggregate, and write **selection only**. It also returns actual access width, line dimensions/R/C, MUX widths/resistance, physical SA/adder/accumulator counts and area. Additional input-vector, write-target and signed-output DFFs plus a native 25-bit Subtractor are instantiated and returned separately. Their physical existence is demonstrated; a full input selector, signed-control schedule, transport and verify comparator/status path are still required before macro service qualification. They are not silently added to native included stages.

The native CMOS-access VSA originally received wire-only `capBL`. The V5 mapping places the initialized access drain on the sensed column, so `patches/mlp_binary_column_load.patch` passes `capCol` instead. This is a scoped port correction, not a claim that every upstream topology has the same drain placement. The original wire-only VSA is separately evaluated as a diagnostic; `native_sa_input_cap_F`, `upstream_wire_only_sa_input_cap_F` and optional external-load evaluation make consumption visible. Patch SHA is in the V5 lock and each build manifest.

All native latency returns here are **seconds**. VSA includes `2/f` per column group; native DFF includes its own clock abstraction. Neither is converted again. `native_write_selection_s` excludes material pulses, retry, verify, final restoration and successful matrix completion. It cannot become T_R.

## Electrical qualification and special front ends

The prototype evaluates a passive two-column discharge bound at the actual R/line/MUX/C values. Its maximum differential signal must exceed the native 100 mV VSA threshold before a passive interpretation is possible. A 0.1 V read bias cannot be extended indefinitely using constant ΔI to create unavailable swing. Failure reports `INFEASIBLE for passive unregulated port`; it never publishes a normal service point. Passing this limited bound does not establish reference circuit, offset/noise, read-disturb or accuracy qualification.

A regulated current clamp/reference could change this bound only with an explicit implemented/characterized front end. Do not present passive 0.1 V array bias and a separate 0.5 V sensing node as one implicit rail. A different threshold needs an explicit engineering/evidence basis and offset/margin condition. The current callable prototype does **not yet** accept saturated NAND string current via static V/I, polarization charge via ordinary R, or GC integration via this two-terminal ohmic interface.

For such case adapters, return a compact candidate record to the integrator with: actual terminal names and biases; state/selection-dependent I–V or charge; dynamic/port capacitance and small-signal relation; settling and valid operating domain; current/voltage compliance; native peripheral modules/ports to connect; external primitive coverage. The integrator will add a distinct matching front-end entry when these are known, preserving the same stage/hash/invalid semantics.

## Program/verify adapter record (coverage contract; complete runner pending)

Provide separate direction primitives: `primitive_id`, source IDs, `current_A` or terminal I–V, rail(s), allowed load, complete waveform duration, whether rise/fall/quench/cool are included, required write-lane count/shared return-current limit, verification/readback rule and finite attempts. Explicitly state initial/target state and how target is held. Per pulse the common service sequence is admission/target capture → real select/setup → one primitive waveform → uncovered return/recovery → same physical read path → comparison/status → bounded retry/failure. A black-box complete P/E engine instead declares its included internal verify/pump/recovery and skips duplicate charging. Success emits payload once; exhausted attempts emit no valid rate. This record is not an existing universal PCM/MRAM programming implementation.

## API v1 case service entry (frozen initial callable boundary)

The shared `run.py --case pcm --scenario reference --run-id unique` now supports an author adapter at `cases/pcm/case_adapter.py` and authoritative `cases/pcm/inputs.json`. Substitute the requested case ID. Other small adapter dependencies must be declared as case-relative `adapter_files` in inputs.json; only .py/.json/.csv files under the case directory are copied. It invokes the adapter from the local source snapshot, freshly builds the same native backend and then computes complete serial services from the adapter's explicit stages. It never publishes `formal_eligibility=true` before independent review.

`prepare(resolved)` receives `{input, resolved_parameters, scenario, config_id, input_sha256, qualification}` and returns the exact native probe request shown above. `sense_threshold_V` is now a required numerical input, written into the real native VSA field. Its engineering/noise/offset qualification belongs in case evidence. Native exports `sa_precharge_per_group_s`, `sa_control_per_group_s` (=2/f), `sa_effective_node_cap_F`, and `sa_native_linear_develop_per_group_s`. A physical case network replaces the last term with its actual threshold-crossing time; do not add both. Native endpoint ΔI timing and full endpoint swing are diagnostics and cannot qualify a midpoint-reference decision.

`evaluate(resolved, native_raw)` returns this structure (symbolic field descriptions):

```text
status: valid | conditional | infeasible | blocked
qualification: explicit precision/model identity
conditions: list of necessary model conditions
program_outcome: success | failed | blocked
scheduling: serial_nonoverlap
physical_checks: [{id, passed: bool, critical: bool, evidence}]
resources: {logical/physical capacity, encoding/reference, ports/lanes, holds, ...}
stream_stages: [stage, ...]
resident_stages: [stage, ...]
case-specific diagnostics: any extra JSON fields
```

Each stage has `id`, `duration_s` (one operation/batch), positive integer `count`, `source_class` (the four INTERFACE classes), `source_ids` (keys from authoritative inputs), `resources`, `includes`, and `excludes`. A zero duration requires `zero_reason`. Native stages additionally have `native_return_unit`, `included_internal_clock_phases`; cycles require `conversion_clock_id` and `conversion_clock_Hz`, while `duration_s` is already converted once. Stages explicitly describe nonoverlapping work. The common aggregator multiplies duration by count and sums; it does not infer hidden parallel lanes or correctness.

Any failed critical check or failed programming outcome suppresses normal rates. Eligible candidate output requires positive complete stream/resident services, successful final state, and the explicit nonoverlap policy. It computes logical payload and rho/tau/RI*/U* from those same services, labels results `not_reviewed`, and stores native exact source/input/binary hashes, case model/stage records, resources and conditions. This first API does not yet aggregate refresh or pipeline overlap; GC will add an explicit maintenance contract before using it.

Additional actual fields now include native Vdd/Vth, NMOS Ion per metre and initialized access width×Ion at the native bias. They are an on-current capability check, not a PCM thermal I–V estimate. `actual_access_bias_matches_native` identifies whether the requested gate bias agrees with the technology table. `write_port_voltage_V` is only a requested port identity in the latency path; its marker is not evidence of an actual high-voltage driver.

The additional signed datapath exposes native 25-bit Adder latency/area/input capacitance/parallel lanes, 25-bit holds for **all** cols/8 output groups, an eight-way shifted-weight MUX, its selector, and accumulator-feedback MUX. These replace neither native short unsigned arithmetic nor each other implicitly. Full service authors must use only the actual required path and count load/hold/group/control stages. Reference devices, matched reference capacitors and precharge must also be present in resources/latency; no midpoint-reference is supplied for free by the native endpoint formula.

API v1 low-rail precharge request fields are also mandatory: `precharge_width_F` and `precharge_error_fraction` (strictly between 0 and 1). They are explicit engineering choices; current fixture uses 8F and 1%. Native exports low-rail NMOS headroom/R/added-drain C/control/RC, actual data+reference branch count and area. `WL_enable_setup_s`/`WL_release_s` and gate area provide an explicit all-WL-off state during precharge. `write_WL_select_one_s` includes the enable setup. `write_column_driver_one_edge_s` is native TG control RC; original write-pulse proxy stays separately visible. See `provenance/PORTING.zh.md` for voltage/coverage limits.

API v1 functional closure adds two required integer request fields: `input_port_bits` and `resident_port_bits`. Whole ingress groups must divide the held vector/target. They instantiate capture-feedback MUXes/selectors so partial beats preserve other bits. Necessary runtime license `.txt` notices may be included via `adapter_files` (still small, case-local and no symlinks).

The final gate/hold path exports `data_zero_mask_s`, `add_sub_result_select_s`, `accumulator_keep_s`, `weight_group_select_s`, `weight_keep_s`, `verify_target_select_s`, `program_target_select_s`, `program_target_mask_logic_s`, `group_select_s`, `input_ingress_select_s` and `target_ingress_select_s`, with matching `*_area_m2` resources. `extra_25bit_adder_s`, `signed_correction_s`, shifted/feedback MUX delays and the digital period gate now use these real downstream loads. Old preliminary disconnections are retained only in explicitly named `*_pre_connection_diagnostic` fields. Full-group registers always receive old-state feedback when their group is not selected; zero inputs go through an actual 25-bit mask. Adder/subtractor output choice is an explicit MUX.

Reference isolation fields are `reference_switch_R_ohm`, `reference_switch_gate_N_F`, `reference_switch_gate_P_F`, `reference_switch_drain_F`, `reference_switch_area_m2`, `reference_isolation_count`, `reference_enable_control_s`, `reference_isolation_edge_s`, `reference_control_area_m2`, `reference_control_gate_load_F`. It is a separately instantiated native TG per SA with a real control driver. Add its actual R to the reference network exactly once, and include its drain capacitance in the physical reference matching calculation (not twice). Its native switch model retains the stated voltage/load abstraction; it is not a characterization of arbitrary material/program bias.

Required read lifecycle: data WL and reference switch OFF → data/reference precharge → precharge release → data and reference enable/settle → bounded case network development → native VSA decision latch → data/reference release → digital weight hold/capture and reuse. Native VSA regeneration/holding is its explicit latch abstraction, not an extra free analog sample register. Offset/noise and latch behavior remain qualified by the case conditions. A permanently grounded reference during precharge is invalid.

`functional_probe.py --native-run <path>` independently exercises Boolean gates/ripple add/subtract and register enables against integer dot products for zero/extreme/mixed/cancellation/isolated/group-boundary vectors. Deliberately removing zero masks or group hold is detected. It also checks nominal write-mask/full-cover/failure detection and the isolated-precharge lifecycle. This is not an analog accuracy or write-success probability test. The reference service entry runs it once and stores the evidence bound to the actual native source manifest.

The reviewed applicability repairs add required `read_mux_IR_fraction`, `write_mux_target_ohm` and `write_current_A`. For CMOS digital **sequential** mode the native read MUX now targets one selected-cell total resistance times the declared fraction (default upstream single-cell fraction 0.5), while parallel mode retains its original row scaling. The old oversized target remains a diagnostic. Write column routing is a separate real native TG with its own specified resistance, widths, capacitances, area, current and voltage-drop checks; it must be included in the case's actual program-current/compliance network. Read-MUX R is never substituted for the write route.

Two off-state write TG drain capacitances are included in the sensed-node load (`write_off_drain_added_to_read_F`). The write edge's external load includes other connected read/precharge/source parasitics; the driver adds its own output drains once. `write_total_connected_cap_F` exposes the resulting load. Changes in write routing therefore propagate into read/precharge/reference matching as well as writing.

Data/reference enabling now uses an actual matched WL-enable replica. `WL_address_setup_s` is established while all accesses are off; then `WL_enable_edge_only_s` and `reference_isolation_edge_s` share the nominal matched step edge. The replica uses the same NAND/INV path, matched actual WL capacitance/line RC, a counted dummy fanout and a compensating `reference_enable_matching_cap_F`. `reference_enable_load_match_feasible` must pass. The reference switch uses its N branch (width doubled from the native complementary sizing to retain target R) while P gate is held at native Vdd. Reference R/C still enter the case's dynamic network. This is a matched lumped step-port model; residual skew/ramp/mismatch requires explicit margin conditions or finite case diagnostics, not an STA claim. Prior mismatched-controller/oversized-MUX candidates are superseded.

`service.py` records `computational_manifest.json` separately from full `snapshot_manifest.json`. The computational set is shared runtime code/kernel/patches/lock and only the selected case's input/model/adapter/support data. Governance documents, other cases and Markdown/license text are not treated as changes to that point's numerical model, while the full package remains traceable.

Independent review required explicit clear hardware. `state_clear_s` now includes actual clear control/AND path and native capture; `state_clear_comb_s`, `state_clear_bits`, `state_clear_gates`, `state_clear_area_m2` and fanout are returned. An active-low `CLEAR_N` control is buffered; a NAND+INV AND sits at every result/status/retry D input. `accumulator_keep_s`, sticky and retry timings include the clear gate on their normal paths. No reset is inferred from the generic native DFF. Cases must schedule clear before the first MAC and before the first resident verify/program state, using at least the real clear duration and their declared capture clock; subsequent successful row status initialization uses the same hardware. The functional probe now starts from nonzero previous registers and tests consecutive requests, plus a counterfactual with the clear removed. Earlier `PASS` only covered its then-declared local checks and cannot qualify the old missing-clear service.
