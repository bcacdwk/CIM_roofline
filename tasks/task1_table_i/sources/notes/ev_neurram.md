# ev_neurram

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_neurram2022

Location: PDF p.3 Fig.2h; Methods PDF pp.10–11 and 14–15; PDF p.28 Extended Data Table 1

Supports: 128-input, 256-output logical per-core forward MVM after differential-row mapping. Source 256x256 logical characterization uses two cores, not one. Complete precision includes neuron integration and output conversion.

Does not support: Analog unquantized targets, not a 4-bit resident codebook; 4-bit weight label in comparison reflects software-equivalent accuracy. External-control programming interval unreported.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 256 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 256 | column | See key and source condition | measured_chip | directly_reported |
| `cores` | 48 | core | See key and source condition | measured_chip | directly_reported |
| `cells_per_weight` | 2 | cell/element | See key and source condition | measured_chip | directly_reported |
| `input_bits` | 4 | bit/element | See key and source condition | measured_chip | directly_reported |
| `output_bits` | 6 | bit/element | See key and source condition | measured_chip | directly_reported |
| `latency` | 3.9 | us | See key and source condition | measured_chip | directly_reported |
| `program_pulse` | 1 | us | See key and source condition | measured_chip | directly_reported |
| `verify_min` | 1 | us | See key and source condition | measured_chip | directly_reported |
| `verify_max` | 10 | us | See key and source condition | measured_chip | directly_reported |
| `pulse_mean` | 8.52 | pulse | See key and source condition | measured_chip | directly_reported |
| `acceptance` | 1 | uS | See key and source condition | measured_chip | directly_reported |
| `timeout_reversals` | 30 | reversal | See key and source condition | measured_chip | directly_reported |
| `program_passes` | 3 | pass | See key and source condition | measured_chip | directly_reported |
| `wait_before_inference` | 30 | minute | See key and source condition | measured_chip | directly_reported |
| `process` | 130 | nm | See key and source condition | measured_chip | directly_reported |
