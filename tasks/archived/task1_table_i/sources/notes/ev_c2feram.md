# ev_c2feram

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_c2feram2023

Location: Accepted manuscript PDF pp.2–3, Figs.3–5; p.3 Fig.6 application simulation

Supports: FeCAP plus plate capacitor and two MOSFETs, measured as discrete components; proposed two-step erase/program and simulated current summation.

Does not support: No fabricated timed CIM macro with ADC; waveform current-MAC is not complete digital MVM throughput. Tiny simulated capacitors not same as discrete measured components.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `write_voltage` | 2 | V | See key and source condition | measured_device | directly_reported |
| `read_vds` | 0.05 | V | See key and source condition | measured_device | directly_reported |
| `cpl_measured` | 470 | pF | See key and source condition | measured_device | directly_reported |
| `cfe_low` | 165 | pF | See key and source condition | measured_device | directly_reported |
| `cfe_high` | 195 | pF | See key and source condition | measured_device | directly_reported |
| `cpl_simulated` | 5 | fF | See key and source condition | simulation | directly_reported |
| `cfe_sim_low` | 3 | fF | See key and source condition | simulation | directly_reported |
| `cfe_sim_high` | 7 | fF | See key and source condition | simulation | directly_reported |
| `read_test_cycles` | 1000000.0 | cycle | See key and source condition | measured_device | directly_reported |
| `on_off_ratio` | 1000.0 | ratio | See key and source condition | measured_device | directly_reported |
| `endurance` | 100000000.0 | cycle | See key and source condition | measured_device | directly_reported |
| `test_area` | 2500 | um2 | > | measured_device | directly_reported |
