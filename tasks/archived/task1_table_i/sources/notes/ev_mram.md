# ev_mram

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_jung2022

Location: PDF p.2 / Nature p.212 Fig.1; PDF p.3 / p.213 Fig.2; Methods PDF pp.7–8, Crossbar array weight update and Operating frequency

Supports: 64 bipolar logical weights written per row in two clocks: left MTJs concurrently, then complementary right MTJs. Same 11.1 MHz evaluation clock includes digital control.

Does not support: Exclude PC/USB/SPI loading, LUT calibration setup and external offset arithmetic; use native TDC output. No write-error-rate/endurance claim added; no independent simultaneous read/write assumption.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 64 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 64 | column | See key and source condition | measured_chip | directly_reported |
| `mtjs_per_weight` | 2 | cell/element | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 1 | bit/element | See key and source condition | measured_chip | directly_reported |
| `weight_bits` | 1 | bit/element | See key and source condition | measured_chip | directly_reported |
| `frequency` | 11.1 | MHz | See key and source condition | measured_chip | directly_reported |
| `row_write_cycles` | 2 | clock | See key and source condition | measured_chip | directly_reported |
| `parallel_weights` | 64 | element | See key and source condition | measured_chip | directly_reported |
| `write_voltage` | 1.5 | V | See key and source condition | measured_chip | directly_reported |
| `tdc_counter_bits` | 4 | bit/element | See key and source condition | measured_chip | directly_reported |
| `max_delay` | 29 | ns | See key and source condition | measured_chip | directly_reported |
| `theoretical_frequency` | 17.2 | MHz | See key and source condition | measured_chip | directly_reported |
| `process` | 28 | nm | See key and source condition | measured_chip | directly_reported |
