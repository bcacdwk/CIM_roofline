# 六模型 FFN / 单路由专家概览

固定模型顺序；每窗口完整装载 gate/up/down 一次，B=8,64,512 为同一权重实际服务的向量数。所有 Byte 与分数均精确。

| 模型 | 层（零起点） | 对象 | D | F | Q_R / 容量 (Byte) | resident tiles |
|---|---:|---|---:|---:|---:|---:|
| Qwen3.5-2B | 3 | Dense | 2048 | 6144 | 37,748,736 | 2,304 |
| Ministral 3 8B (2512) | 0 | Dense | 4096 | 14336 | 176,160,768 | 10,752 |
| Qwen3.6-35B-A3B | 3 | 单专家 | 2048 | 512 | 3,145,728 | 192 |
| Tencent Hy3 (295B) | 1 | 单专家 | 4096 | 1536 | 18,874,368 | 1,152 |
| Ling-1T | 4 | 单专家 | 8192 | 2048 | 50,331,648 | 3,072 |
| MiMo-V2.5-Pro | 7 | 单专家 | 6144 | 2048 | 37,748,736 | 2,304 |

ports RI 六模型均为 **1/16, 1/2, 4**；Q_S、调用数随 B 线性增加，Q_R、容量、resident tiles 不变。

| 模型 | operator RI，B=8 | B=64 | B=512 |
|---|---:|---:|---:|
| Qwen3.5-2B | 1/576 | 1/72 | 1/9 |
| Ministral 3 8B (2512) | 3/3584 | 3/448 | 3/56 |
| Qwen3.6-35B-A3B | 5/768 | 5/96 | 5/12 |
| Tencent Hy3 (295B) | 11/4608 | 11/576 | 11/72 |
| Ling-1T | 5/3072 | 5/384 | 5/48 |
| MiMo-V2.5-Pro | 1/576 | 1/72 | 1/9 |

六组 D、F 均整除 128，每项 ports Q_S=BDF/128、Q_R=DF，故总 RI=B/128。operator 汇总从三独立入口扣除 BD，保留 down 的新输入 BF，RI=B(D+F)/(3DF)。Qwen3.5 与 MiMo 的 D/F 互换，ports 和汇总 operator 全部相同；独立 gate/up 与 down 的 operator 输入互换，共享扣除量不同。

精确 18 工况与 54 分项见 [JSON](data/results.json) / [CSV](data/results.csv)；来源见 [config.json](data/config.json)，复算见 [checks.json](data/checks.json)。
