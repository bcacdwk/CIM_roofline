# ev_zhou25

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_zhou2025

Location: PDF p.2 Figs.2–6; PDF p.3 Fig.12 and Table 1; PDF p.1 narrative

Supports: Fabricated 8x8x3 structure, single-cell switching/endurance; read-after-write delay; Fig.12b measured four one-bit multiplication states.

Does not support: Array-wide parallel write number and complete CIM cycle not given; Fig.12a hybrid bonded CIM is proposed and Fig.12c accuracy simulated. Fig.6a uses -3.5V and layer endurance uses +/-4/3V 60ns, separate from fastest-mode conditions; endurance temperature not specified.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `layers` | 3 | layer | See key and source condition | measured_device | directly_reported |
| `rows` | 8 | row | See key and source condition | measured_device | directly_reported |
| `columns` | 8 | column | See key and source condition | measured_device | directly_reported |
| `channel_length` | 100 | nm | See key and source condition | measured_device | directly_reported |
| `channel_width` | 70 | nm | See key and source condition | measured_device | directly_reported |
| `program_voltage` | 4.25 | V | See key and source condition | measured_device | directly_reported |
| `erase_voltage` | -3.25 | V | See key and source condition | measured_device | directly_reported |
| `program_pulse` | 50 | ns | See key and source condition | measured_device | directly_reported |
| `erase_pulse` | 50 | ns | See key and source condition | measured_device | directly_reported |
| `raw_delay_upper` | 100 | ns | See key and source condition | measured_device | directly_reported |
| `read_vds` | 0.1 | V | See key and source condition | measured_device | directly_reported |
| `endurance_lower` | 100000000000.0 | cycle | See key and source condition | measured_device | directly_reported |
| `endurance_window_end` | 0.3 | V | See key and source condition | measured_device | directly_reported |
| `retention_measured` | 4000 | s | See key and source condition | measured_device | directly_reported |
| `layer_test_program_voltage` | 4 | V | See key and source condition | measured_device | directly_reported |
| `layer_test_erase_voltage` | -3 | V | See key and source condition | measured_device | directly_reported |
| `layer_test_pulse` | 60 | ns | See key and source condition | measured_device | directly_reported |
