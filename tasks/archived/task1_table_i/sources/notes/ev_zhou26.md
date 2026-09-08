# ev_zhou26

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_zhou2026

Location: PDF p.2 Figs.2–5; PDF p.3 Figs.7–11 and Table 1; p.1 narrative

Supports: Optimized SL-HZO/O-poor cell has +/-2V20ns and >1e12 cycles. Fabricated 4x32x32, explicitly shown error-free patterns cover 4x16x16. Vw/3 disturb scheme, read gate -0.5V.

Does not support: 20 ns read-disturb pulse is not full read/ADC interval. No CIM MVM. Layer-scaled read latency and 256-layer density are TCAD/SPICE estimates. Parallel-write scale and array programming schedule not reported; no temperature specified for endurance/retention.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `layers` | 4 | layer | See key and source condition | measured_device | directly_reported |
| `fabricated_rows` | 32 | row | See key and source condition | measured_device | directly_reported |
| `fabricated_columns` | 32 | column | See key and source condition | measured_device | directly_reported |
| `pattern_rows` | 16 | row | See key and source condition | measured_device | directly_reported |
| `pattern_columns` | 16 | column | See key and source condition | measured_device | directly_reported |
| `channel_length` | 50 | nm | See key and source condition | measured_device | directly_reported |
| `channel_width` | 20 | nm | See key and source condition | measured_device | directly_reported |
| `vertical_pitch` | 40 | nm | See key and source condition | measured_device | directly_reported |
| `program_voltage` | 2 | V | See key and source condition | measured_device | directly_reported |
| `erase_voltage` | -2 | V | See key and source condition | measured_device | directly_reported |
| `program_pulse` | 20 | ns | See key and source condition | measured_device | directly_reported |
| `erase_pulse` | 20 | ns | See key and source condition | measured_device | directly_reported |
| `raw_delay_upper` | 100 | ns | See key and source condition | measured_device | directly_reported |
| `read_gate` | -0.5 | V | See key and source condition | measured_device | directly_reported |
| `read_disturb_pulse` | 20 | ns | See key and source condition | measured_device | directly_reported |
| `endurance_lower` | 1000000000000.0 | cycle | See key and source condition | measured_device | directly_reported |
| `disturb_cycles` | 1000000000.0 | cycle | See key and source condition | measured_device | directly_reported |
| `retention_measured` | 3000 | s | See key and source condition | measured_device | directly_reported |
| `halfselect_O_pulse` | 0.1 | s | See key and source condition | measured_device | directly_reported |
| `highdensity_sim_layers` | 256 | layer | See key and source condition | simulation | directly_reported |
| `highdensity_sim` | 8.37 | Gb/mm2 | See key and source condition | simulation | directly_reported |
