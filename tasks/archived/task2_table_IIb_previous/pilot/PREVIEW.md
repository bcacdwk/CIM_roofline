# Step 3 两模型四行预览

精确 RI；FFN 顺序 B=8,64,512，Attention 顺序 L=1024,16384,131072。QKV 为一个 token。

## ports（主口径）

| Workload | Ministral 3 8B (2512) | Qwen3.6-35B-A3B |
|---|---|---|
| QKV Projection | infinity | infinity |
| FFN / MoE | 1/16, 1/2, 4 | 1/16, 1/2, 4 |
| Attention Prefill | 2177/128, 32897/128, 262273/128 | 2177/64, 32897/64, 262273/64 |
| Attention Decode | 32, 512, 4096 | 64, 1024, 8192 |

## operator（对照口径）

| Workload | Ministral 3 8B (2512) | Qwen3.6-35B-A3B |
|---|---|---|
| QKV Projection | infinity | infinity |
| FFN / MoE | 3/3584, 3/448, 3/56 | 5/768, 5/96, 5/12 |
| Attention Prefill | 1281/128, 16641/128, 131329/128 | 1537/128, 16897/128, 131585/128 |
| Attention Decode | 18, 258, 2050 | 20, 260, 2052 |

原始 Byte、精确分数、分项与容量见 [JSON](data/results.json) / [CSV](data/results.csv)。显示不先取整再求比值。
