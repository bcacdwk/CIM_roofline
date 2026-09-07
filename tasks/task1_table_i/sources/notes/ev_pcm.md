# ev_pcm

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_pcm64

Location: Dated preprint PDF pp.2–3 architecture; pp.7–8 Methods programming; p.10 power/performance; p.18 Table I; p.25 Extended Data Table I

Supports: Measured PCM chip and accuracy; Table I latency obtained from RTL execution, so rate origin is simulation on measured-chip architecture. 4-phase mode used for accuracy experiments.

Does not support: Analog weight format not INT8. Eight-bit I/O does not establish resident payload size. Full weight programming time lacks convergence distribution and complete scheduling; 256 diagonal devices are not 256 simultaneous writeheads.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 256 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 256 | column | See key and source condition | measured_chip | directly_reported |
| `cores` | 64 | core | See key and source condition | measured_chip | directly_reported |
| `devices_per_weight` | 4 | cell/element | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `output_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `four_phase_latency` | 520 | ns | See key and source condition | simulation | directly_reported |
| `one_phase_latency` | 133 | ns | See key and source condition | simulation | directly_reported |
| `four_phase_tops` | 16.1 | TOPS | See key and source condition | simulation | directly_reported |
| `one_phase_tops` | 63.1 | TOPS | See key and source condition | simulation | directly_reported |
| `write_parallel_devices` | 32 | cell | See key and source condition | measured_chip | directly_reported |
| `reset_pulse` | 125 | ns | See key and source condition | measured_chip | directly_reported |
| `set_pulse` | 250 | ns | See key and source condition | measured_chip | directly_reported |
| `set_trailing_edge` | 50 | ns | See key and source condition | measured_chip | directly_reported |
| `iteration_pulse` | 125 | ns | See key and source condition | measured_chip | directly_reported |
| `verify_read` | 512 | ns | See key and source condition | measured_chip | directly_reported |
| `verify_precharge` | 256 | ns | See key and source condition | measured_chip | directly_reported |
| `max_iterations` | 30 | iteration | See key and source condition | measured_chip | directly_reported |
| `acceptance` | 5 | ADC count | See key and source condition | measured_chip | directly_reported |
| `process` | 14 | nm | See key and source condition | measured_chip | directly_reported |
