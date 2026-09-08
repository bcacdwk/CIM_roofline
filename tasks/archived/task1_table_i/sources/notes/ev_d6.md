# ev_d6

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_d6cim2023

Location: PDF p.1 / proceedings p.413, Sec.II-A and Fig.1; PDF p.3 / p.415, Sec.III; p.4 Fig.10

Supports: Complete 8-bit VMM schedule and measured operating point; ordinary SRAM R/W port.

Does not support: No measured normal-write frequency or ready interval. Fig.10 label 363 MHz differs from text ~360 MHz; use textual 360, not extra precision.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 128 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 128 | column | See key and source condition | measured_chip | directly_reported |
| `weight_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `output_bits` | 23 | bit/element | See key and source condition | measured_chip | directly_reported |
| `cycles` | 64 | clock/MVM | See key and source condition | measured_chip | directly_reported |
| `frequency` | 360 | MHz | See key and source condition | measured_chip | directly_reported |
| `write_bus` | 128 | bit | See key and source condition | measured_chip | directly_reported |
| `voltage` | 1.1 | V | See key and source condition | measured_chip | directly_reported |
| `process` | 28 | nm | See key and source condition | measured_chip | directly_reported |
