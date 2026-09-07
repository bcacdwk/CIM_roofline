# ev_jia

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_jia2022

Location: PDF pp.5–6 / journal pp.202–203, Figs.7–9; PDF p.9 / p.206 Sec.V-A; PDF p.11 / p.208 Table IV

Supports: Native BPBS mode; four spatial weight columns and four input bit phases; SIMD reconstructs full multibit results; peak 4b chip rate consistent with geometry.

Does not support: No full weight-load timing. 500 MHz is timing-closure target. 28 MB weight buffer is proposed system component, not prototype capacity.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 1152 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 256 | column | See key and source condition | measured_chip | directly_reported |
| `cores` | 16 | core | See key and source condition | measured_chip | directly_reported |
| `adc_rate` | 20 | MS/s | See key and source condition | measured_chip | directly_reported |
| `digital_clock` | 200 | MHz | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 4 | bit/element | See key and source condition | measured_chip | directly_reported |
| `weight_bits` | 4 | bit/element | See key and source condition | measured_chip | directly_reported |
| `adc_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `columns_per_simd` | 4 | column | See key and source condition | measured_chip | directly_reported |
| `peak_chip` | 11.8 | TOPS | See key and source condition | measured_chip | directly_reported |
| `voltage` | 0.8 | V | See key and source condition | measured_chip | directly_reported |
| `process` | 16 | nm | See key and source condition | measured_chip | directly_reported |
