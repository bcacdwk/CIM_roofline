# ev_edram

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_edram2021

Location: PDF pp.1–3, Figs.16.2.2–16.2.7

Supports: 65 nm 1T1C eDRAM prototype; dataflow includes input DAC, weight fetch, MAV, pooling and SAR ADC.

Does not support: 10 ns two-cycle MAV stage is not a complete input-to-output service interval. 4 MHz measured / 200 MHz simulation are explicitly distinct in Fig.16.2.7.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `capacity` | 16 | Kibit | See key and source condition | measured_chip | directly_reported |
| `measured_clock` | 4 | MHz | See key and source condition | measured_chip | directly_reported |
| `simulated_clock` | 200 | MHz | See key and source condition | simulation | directly_reported |
| `mav_stage` | 10 | ns | See key and source condition | simulation | directly_reported |
| `precision` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
