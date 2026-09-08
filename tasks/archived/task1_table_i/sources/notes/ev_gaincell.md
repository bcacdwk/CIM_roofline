# ev_gaincell

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_gaincell2022

Location: PDF p.1 / p.112 dataflow; PDF p.2 / p.113 Figs.2 and 7

Supports: One 27-input MAV group with eight parallel weight slices and four 2-bit input phases; 16-bit combiner output.

Does not support: Macro engine replication/layout not fully specified. Do not infer 8 simultaneous independent groups solely from rounded 22 GOPS. Normal-write width, cycle and refresh duty missing. Access-time-based rate is a scheduled nominal capability, not an external-port throughput test.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `capacity` | 32 | Kibit | See key and source condition | measured_chip | directly_reported |
| `dot_inputs` | 27 | element | See key and source condition | measured_chip | directly_reported |
| `weight_slices` | 8 | slice | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `weight_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `input_bits_per_phase` | 2 | bit/element | See key and source condition | measured_chip | directly_reported |
| `phase_time` | 5 | ns | See key and source condition | measured_chip | directly_reported |
| `full_access` | 20 | ns | See key and source condition | measured_chip | directly_reported |
| `output_bits` | 16 | bit/element | See key and source condition | measured_chip | directly_reported |
| `gops` | 22 | GOPS | See key and source condition | measured_chip | directly_reported |
| `process` | 65 | nm | See key and source condition | measured_chip | directly_reported |
| `voltage` | 1 | V | See key and source condition | measured_chip | directly_reported |
