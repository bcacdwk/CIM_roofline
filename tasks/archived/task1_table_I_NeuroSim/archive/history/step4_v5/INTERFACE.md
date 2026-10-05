# V5 independent service contract · 5.0.0 (P0)

This is the P0 input/output boundary, not a completed seven-case backend. Only an executed, physically qualified case may publish a service point. The integrator owns shared code; case authors own their assigned `cases/<case_id>/` evidence and candidates. Proposed public-code changes go to the integrator. No history or result/replay module is a computational dependency.

## Authoritative input

One `cases/<case_id>/inputs.json` contains `schema_version: "5.0.0"`, `case_id`, `implementation_id`, `identity`, `logical`, `base_parameters`, `parameter_metadata`, `scenarios`, `sources`, `service_policy`, and `backend_plan`. Case IDs are `pcm`, `mram`, `nor2d`, `fenor3d`, `feram`, `gc04`, `nand3d`. `implementation_id` changes if topology, resources, precision or encoding changes materially. A probe has `point_eligibility: "probe_only"` and never becomes an eighth formal case.

- `logical`: positive integer `K`, `N`, `input_bits`, `weight_bits`; positive `bytes_per_input`, `bytes_per_weight`; explicit `signed`, `output_qualification`. Dimensions and precision are case choices; no implicit 256×31, equal area or ADC count.
- `identity`: material, cell/access topology, physical organization, encoding, port ownership, process separation and required rails. Device process and peripheral model process are separate. A 40 nm device is not silently driven by a 22 nm MOS assumption.
- `base_parameters`: named finite numeric/bool physical and engineering inputs, in SI except explicit units. No old full read/write service time is permitted as an unclassified shortcut. External complete P/E or feedback-write services remain admissible only via the primitive ledger below.
- `parameter_metadata`: exactly one entry per base field, each with `unit`, `source_ids`, `role` (`physical_evidence`, `architecture_choice`, `external_primitive`, `operating_condition`), and applicability. Optional `min`/`max` constrain values; they do not imply a measured distribution.
- `scenarios`: exactly named `optimistic`, `reference`, `pessimistic` when formal range is ready; each has `overrides`, `meaning`, `evidence`. Reference may stand alone during development. Overrides only existing base fields. A changed resource/topology is disclosed as a design scenario; thermal auto-sizing is never called same-chip PVT. No generic 300/350/400 K inheritance.
- `sources`: entries keyed by stable ID, with `kind` from the four classes below, source path or URL plus exact locator, evidence type (measured/simulated/spec/model/engineering), applicability and exclusions. Primary physical evidence may refer to locally existing literature without copying papers into V5.
- `service_policy`: initial state, accepted input/write ports and buffering, output-ready and matrix-compute-ready endpoints, request overlap, read/write resource arbitration, retry bound/failure outcome, maintenance and supply-startup boundary.
- `backend_plan`: locked branches/modules, required native calls, adapter and external primitive coverage. Presence of an enum or class is not execution evidence. This descriptive field becomes a build manifest after implementation.

Resolved parameters alone generate headers and constructor settings; assigned fields must be returned after actual initialization in `resolved.json`. A field-to-consumer map plus targeted counterfactual checks demonstrate consumption. Unknown overrides, nonfinite values, unsupported biases/geometries, absent sources, physical contradictions, or failed write/readback terminate the configuration rather than being clamped.

The minimal parser requires nonempty identity/backend descriptions, source `path` or `url`, `locator`, `evidence_type`, `applicability`, `exclusions`; external primitives additionally require `includes`, `excludes`, `domain`. Parameter `role` and `applicability`, scenario `meaning`/`evidence`, and logical `signed`/`output_qualification` are mandatory. Use explicit “none: reason” descriptions where a mechanism is absent. `service_policy` keys are `initial_state`, `input_port`, `write_port`, `output_endpoint`, `resident_endpoint`, `request_overlap`, `arbitration`, `retry`, `maintenance`, `supply_startup`. These checks establish minimally reviewable syntax/coverage, not physical validity. Runtime path components including `root/runs` may not be symlinks.

## Source classes and primitive coverage

1. `native_circuit`: exact locked upstream circuit path and SHA.
2. `adapter`: minimal extension, defect correction or cross-branch port, with patch SHA and physical port semantics.
3. `external_primitive`: material switching/retention/characterized port or opaque engine, with load/bias/domain and an explicit `includes`/`excludes` list.
4. `service_policy`: mapping, scheduling, port counts, bounds and engineering choices.

A primitive may dominate time. It cannot be split into invented stages or billed twice with native modules for the same included work. Prior full read accesses are comparison-only unless an explicit black-box route is justified and carries that limitation. Legacy final throughput and full slots never enter new calculations.

## Runtime boundary and outputs

Canonical sources/configs stay here. `--root` then `NEUROSIM_ROOT` then `$HOME/neurosim` resolve the local root, corroborated against its machine paths. Each run creates a new `runs/step4-v5/<phase>/<role>-<id>/`, copies/hashes the small canonical package, obtains exact locked sources, applies small registered patches, constructs, initializes, calculates area/capacitances, then latency/services. No binary reuse is formal evidence. All caches, downloads, compilation and complete traces live outside cloud storage. Overwrite and symlink export are rejected.

Per configuration: `input.json`, `source_manifest.json`, `resolved.json`, `stages.json`, `resources.json`, `diagnostics.json`, `result.json`, `execution.json`. Large traces remain local. A stage has stable ID, source class/IDs, duration in seconds, actual operation/batch count, resources, dependencies, and included work. Every native return records `native_return_unit` (`seconds` or `cycles`) and `included_internal_clock_phases`. A cycles return additionally records `conversion_clock_id` and its actual `conversion_clock_Hz`; a seconds return is never multiplied by the clock again. A module's included precharge/enable/capture phases cannot be billed again. Nonzero/zero exit codes alone are not sufficient: native error text, missing mandatory outputs, nonfinite values and invalid nonpositive service durations reject the run. Individual absent stages may be zero only with explicit coverage explanation. DAG/overlap scheduling is explicit; serial summation is allowed only under declared nonoverlap.

`result.json` reports `config_id`, canonical/build hashes, implementation/scenario identity, `status` (`valid`, `conditional`, `infeasible`, `blocked`, `probe_only`), conditions and precise unresolved issues. It includes logical payload, physical capacity/encoding, initialized sizes/RC/biases, single physical request latency, raw streaming interval, complete resident time, maintenance work and raw/effective rates. No positive normal service point is exported for infeasible/blocked/failed configurations. `conditional` cannot hide a known violated condition.

For B_S=K×bytes_per_input, B_R=K×N×bytes_per_weight:

`rho=B_S/delta_S`, `tau=B_R/T_R`, `RI_star=rho/tau`, `U_star=T_R/delta_S=(N×bytes_per_weight/bytes_per_input)×RI_star`.

All rates are logical Byte/s internally and decimal MB/s in tables. Physical duplicates/references/verify/restore/refresh add time/resources, never payload. Single latency and continuous interval are distinct. GC-04 separately exposes raw, physical single-request and sustainable effective services; `raw/availability` is not single-request latency. Restore scope and retention/writeback feasibility must be checked before rates exist.

Precision is a distinct qualification: binary sensed exact local arithmetic, fixed-point format, nominal analog approximation and measured accuracy cannot be merged by container width. Physical failures cannot be cured solely by timing elongation.

## Isolation, review and history

Final formal computation must run with only V5 canonical files, small original parameter data and locked upstream source. Comparison/plot is a separate postprocessing entry and may read V4's already-produced nine points. V4 fixed-architecture thermal redesign scenarios retain their original IDs, qualifications and values; V5 ranges carry each device's own meanings. Review binds final input/shared-code hashes and new source/build/run directories and independently reconstructs counts/physics; it is not an equality-only summary check.
