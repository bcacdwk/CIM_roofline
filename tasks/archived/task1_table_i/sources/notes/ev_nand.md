# ev_nand

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_nand2021

Location: Published pp.62–64, Sec.II-A/B/C; article text read online; Table 1 image not inspected

Supports: NeuroSim/HSPICE design; 16 outputs, four blocks per 8-bit weight; 3 SSL encode two weight bits and three BL copies encode two input bits.

Does not support: Missing complete phase timing and verified-write/erase service. 303 ns WL setup is not MVM time. Capacity does not imply write parallelism.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `layers` | 32 | layer | See key and source condition | simulation | directly_reported |
| `blocks` | 64 | block | See key and source condition | simulation | directly_reported |
| `bl_per_block` | 13824 | bitline | See key and source condition | simulation | directly_reported |
| `ssl_per_block` | 3 | SSL | See key and source condition | simulation | directly_reported |
| `logical_inputs` | 4608 | element | See key and source condition | simulation | directly_reported |
| `weight_bits` | 8 | bit/element | See key and source condition | simulation | directly_reported |
| `input_bits` | 8 | bit/element | See key and source condition | simulation | directly_reported |
| `wl_setup` | 303 | ns | See key and source condition | simulation | directly_reported |
| `bl_setup` | 12 | ns | See key and source condition | simulation | directly_reported |
| `adc_bits` | 7 | bit/element | See key and source condition | simulation | directly_reported |
| `logic_node` | 32 | nm | See key and source condition | simulation | directly_reported |
