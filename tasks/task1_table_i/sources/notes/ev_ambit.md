# ev_ambit

Generated from `data/extractions.json`; edit that JSON to correct facts.

Sources: t1_ambit2017

Location: PDF pp.7–8, Fig.8 and Sec.5.3; PDF p.10 Table 3

Supports: SPICE-based optimized AAP; full AND sequence has four AAPs; modeled system uses 8 KB rows.

Does not support: No full integer-MVM schedule; AAP or Boolean row throughput is not rho; rank row width cannot be assigned to every physical chip automatically.

Extraction: text and original figure labels read. Values are text or explicit figure labels; no continuous-curve digitization is used.

| Key | Original value | Unit | Relation | Result origin | Derivation |
|---|---:|---|---|---|---|
| `aap` | 49 | ns | See key and source condition | simulation | directly_reported |
| `and_aaps` | 4 | operation | See key and source condition | simulation | directly_reported |
| `row_bytes` | 8192 | Byte | See key and source condition | simulation | directly_reported |
| `rows_per_subarray_typical_low` | 512 | row | See key and source condition | simulation | directly_reported |
| `rows_per_subarray_typical_high` | 1024 | row | See key and source condition | simulation | directly_reported |
