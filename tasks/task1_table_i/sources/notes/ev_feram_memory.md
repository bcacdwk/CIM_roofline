# ev_feram_memory

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_feram_datasheet

Location: Manufacturer datasheet 002-10175 Rev.*A pp.1,9–10,12–13,19; accessed PDF text online

Supports: Formal ordinary F-RAM storage timing; random full-word rewrite bandwidth can be calculated; minimum cycle includes required control/precharge constraints.

Does not support: Not CIM; native storage bandwidth is not tau for C2FeRAM or any FeFET. Page-mode timing cannot replace random-word cycle.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `word_bits` | 16 | bit | See key and source condition | reference_scenario | directly_reported |
| `words` | 65536 | word | See key and source condition | reference_scenario | directly_reported |
| `random_write_cycle` | 90 | ns | See key and source condition | reference_scenario | directly_reported |
| `low_voltage_write_cycle` | 105 | ns | See key and source condition | reference_scenario | directly_reported |
| `page_write_cycle` | 40 | ns | See key and source condition | reference_scenario | directly_reported |
| `voltage_min` | 2.7 | V | See key and source condition | reference_scenario | directly_reported |
| `voltage_max` | 3.6 | V | See key and source condition | reference_scenario | directly_reported |
