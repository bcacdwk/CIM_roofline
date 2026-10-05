# V5 separate-component service API

This entry isolates P2/P3 extensions from the frozen P1 binary kernel:

```sh
python3 -B /absolute/path/step4_v5/run_components.py --case nor2d --scenario reference --run-id unique
```

The authoritative `inputs.json` still follows INTERFACE.md. `case_adapter.py` implements:

```python
def prepare_components(resolved):
    return {
        'frontend': {'kind': 'threshold', 'request': threshold_request},
        'digital': {'kind': 'digital', 'request': digital_request},
    }

def evaluate(resolved, native):
    # native['frontend'] and native['digital'] are separately built native outputs.
    # Return the same status/checks/resources/stream_stages/resident_stages contract
    # as P1; each stage refers to its actual component/source and operation count.
    ...
```

The runner copies only canonical runtime files and case `adapter_files`, executes independent fresh component source/build directories (at most two concurrently), and binds every result to the actual component manifests. It excludes `candidate_points`, `reference_snapshot`, summaries, results, reports and legacy/replay files from compute support. Whole-package and computational manifests are separate. No formal review qualification is granted automatically.

The threshold request is documented in P2_THRESHOLD_API.md. A native-incompatible gate may be replaced only by an explicit `external_gate_port` record in the model response: `qualified`, `source_ids`, `domain`, and `stage_ids`. All IDs must exist in the authoritative ledger/stage records, with actual adapter/external-primitive gate-drive stages. This is a minimal coverage guard; independent review must still assess the actual voltage/current/load domain and consumed timing. The native gate delay cannot represent an unsupported high/negative rail.

`digital_probe.py` is a real standalone native operator bank with **no SubArray or material simulation**. Its exact request shape is `probes/digital_service_request.json`, with `point_eligibility: "component_only"`:

|Parameter|Meaning|
|---|---|
|`technology_nm`, `temperature_K`, `clock_Hz`|Actual supported native CMOS design condition; clock must satisfy emitted half-cycle path policy.|
|`logical_K`, `logical_N`, `mac_lanes`, `accumulator_bits`|Logical vector/output shape and actual parallel arithmetic resources. Current binary word interface is signed INT8; the accumulator container is explicit.|
|`weight_hold_rows`, `weight_hold_outputs`|Actual simultaneously retained weight tile. This may be one full output row (NOR) or a many-row/output-tile buffer (vertical AND). It is not a free full-matrix shadow.|
|`weight_capture_bits`|Actual parallel bits captured from one physical read. Partial captures have feedback keeps and native address decoding.|
|`input_port_bits`, `resident_port_bits`, `program_lanes`|Actual input/target intake widths and parallel programming mask lanes; physical programming itself remains case-specific.|
|`operand_route_cap_F`, `program_control_cap_F`|Additional real data/control endpoint loads. Declare source/scope; zero route C is only an explicit local fixture approximation.|

The digital bank contains native input/row/bit selection, weight tile row/group selection, shift selection, zero masks, actual wide add/subtract and result choice, per-group result holds, target selection and equality/failure/sticky/retry, plus clear AND gates and control drive. It distinguishes physical and logical groups. Sign-extension fanout into eight shift choices is explicit; the timing proxy covers the largest fanout. Numerical output format does not imply analog precision.

Use actual emitted stage fields and counts. `digital_mac_comb_s` includes its connected selection/mask/add/sub/result/keep/clear graph; `digital_halfcycle_min_period_s` is the declared conservative scheduling constraint, not STA. Do not add both an aggregate path and its same sub-stages. For a tile smaller than N, logical input rows may need to be selected repeatedly for each output tile; the original full input payload is still counted once. Capacity, capture batches and tile traversal must be independently reconstructed by the case/reviewer.

Current additional component kinds for polarization/SAR or gain-cell integration are not yet installed in this registry. Their physical state models must remain separate when added. Missing kinds fail explicitly rather than falling back to a resistive or ordinary-capacitor model.
