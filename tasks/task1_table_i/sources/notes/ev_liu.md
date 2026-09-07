# ev_liu

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_liu2025

Location: PDF pp.3–5 / article pp.2–4, Figs.1–5; PDF pp.7–8 / article pp.6–7, Figs.10–11

Supports: Hybrid 1T1R then 2T2R programming; verified differential state; measured CIM and 16 state tests.

Does not support: Absolute program pulse/verify/control timing absent; speed defined using pulse counts. Table normalization 1.5b x 1.5b cannot serve as native full-precision throughput. 4.31/4.67 speed wording inconsistent across abstract/body; not used for tau.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `rows` | 576 | row | See key and source condition | measured_chip | directly_reported |
| `columns` | 512 | column | See key and source condition | measured_chip | directly_reported |
| `cells_per_weight` | 2 | cell/element | See key and source condition | measured_chip | directly_reported |
| `adc_count` | 64 | ADC | See key and source condition | measured_chip | directly_reported |
| `output_mux` | 8 | cycle | See key and source condition | measured_chip | directly_reported |
| `adc_bits` | 8 | bit/element | See key and source condition | measured_chip | directly_reported |
| `weight_levels` | 16 | level | See key and source condition | measured_chip | directly_reported |
| `tolerance` | 6 | uS | See key and source condition | measured_chip | directly_reported |
| `tested_weights` | 5760 | element | See key and source condition | measured_chip | directly_reported |
| `max_pulses` | 1000 | pulse | See key and source condition | measured_chip | directly_reported |
| `speed_ratio` | 4.67 | ratio | See key and source condition | measured_chip | directly_reported |
| `input_test_parallel_small` | 32 | element | See key and source condition | measured_chip | directly_reported |
| `input_test_parallel_large` | 128 | element | See key and source condition | measured_chip | directly_reported |
