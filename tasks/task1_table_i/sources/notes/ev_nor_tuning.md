# ev_nor_tuning

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_nor_tuning2016

Location: PDF p.1 abstract and procedure; PDF p.2 Figs.2–6

Supports: Original 180 nm ESF1 tuning experiment, alternating program/erase and measured feedback, no global erase required.

Does not support: Separate 10x10 array, not 2017 classifier timing. Pulse totals do not include read/algorithm overhead or specify SET/erase counts. Do not transplant to main NOR row.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `tested_cells` | 100 | cell | See key and source condition | measured_chip | directly_reported |
| `program_pulse` | 100 | us | See key and source condition | measured_chip | directly_reported |
| `erase_pulse` | 2.5 | ms | See key and source condition | measured_chip | directly_reported |
| `pulses_3percent` | 10 | pulse | See key and source condition | measured_chip | directly_reported |
| `pulses_point3percent` | 35 | pulse | See key and source condition | measured_chip | directly_reported |
