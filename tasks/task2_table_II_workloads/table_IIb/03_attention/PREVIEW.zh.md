# Attention：中文结果预览

## 对象与公式

单序列、所选完整/global 因果 GQA；所有计量角色取 1 Byte/element。H_q 为 query 头数，H_kv 为 KV 头数，g=H_q/H_kv；d_QK 与 d_V 为原生头维，L 为本次追加后可见长度。每个 KV head 保存一份唯一逻辑 K/V。

Prefill：空 KV → L。Q_S = H_q[L d_QK + L(L+1)/2]，Q_R = L H_kv(d_QK+d_V)，RI = g[d_QK+(L+1)/2]/(d_QK+d_V)。

Decode：已有 L−1 追加一个 → L。Q_S = H_q(d_QK+L)，Q_R = H_kv(d_QK+d_V)，RI = g(d_QK+L)/(d_QK+d_V)。

QK 的 query 与 AV 的 softmax 后系数分别计入各矩阵阶段，输出不另加。最终有效 KV 容量均为 L H_kv(d_QK+d_V) Byte；Prefill 初始容量为 0，Decode 初始容量为 (L−1)H_kv(d_QK+d_V) Byte。因果三角和仅表示算法有效范围。

## 模型信息

六模型均取固定版本中的完整/global GQA 层，层号从 0 起。

| 模型 | 所选层 | H_q | H_kv | g | d_QK | d_V |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-2B | 3 | 8 | 2 | 4 | 256 | 256 |
| Ministral 3 8B (2512) | 0 | 32 | 8 | 4 | 128 | 128 |
| Qwen3.6-35B-A3B | 3 | 16 | 2 | 8 | 256 | 256 |
| Tencent Hy3 (295B) | 1 | 64 | 8 | 8 | 128 | 128 |
| Ling-1T | 4 | 64 | 8 | 8 | 128 | 128 |
| MiMo-V2.5-Pro | 7 | 128 | 8 | 16 | 192 | 128 |

各模型保留原有上下文设置。Ling-1T 的 L=65536（64K）沿用既定的官方 YaRN factor=4、original_max_position_embeddings=32768、type=yarn，并设置 --max-model-len 131072。MiMo 保留原生 d_QK=192、d_V=128，Value 写入前乘 0.612，所选全局层无 sink。

## 代入结果

两表均以模型为行、追加后可见长度 L 为列，单元格为小数 RI；1K=1024，RI≥1 保留一位小数。

### 预填充（Prefill）

| 模型 | L=1K | L=8K | L=64K |
|---|---:|---:|---:|
| Qwen3.5-2B | 6.0 | 34.0 | 258.0 |
| Ministral 3 8B (2512) | 10.0 | 66.0 | 514.0 |
| Qwen3.6-35B-A3B | 12.0 | 68.0 | 516.0 |
| Tencent Hy3 (295B) | 20.0 | 132.0 | 1028.0 |
| Ling-1T | 20.0 | 132.0 | 1028.0 |
| MiMo-V2.5-Pro | 35.2 | 214.4 | 1648.0 |

### 单步解码（Decode）

| 模型 | L=1K | L=8K | L=64K |
|---|---:|---:|---:|
| Qwen3.5-2B | 10.0 | 66.0 | 514.0 |
| Ministral 3 8B (2512) | 18.0 | 130.0 | 1026.0 |
| Qwen3.6-35B-A3B | 20.0 | 132.0 | 1028.0 |
| Tencent Hy3 (295B) | 36.0 | 260.0 | 2052.0 |
| Ling-1T | 36.0 | 260.0 | 2052.0 |
| MiMo-V2.5-Pro | 60.8 | 419.2 | 3286.4 |

例如，Qwen3.5-2B 在 Prefill、L=1K 时，Q_S=8[1024×256+1024×1025/2]=6,295,552 Byte，Q_R=1024×2×(256+256)=1,048,576 Byte，RI≈6.0。

## 结果说明

固定头维时，RI 随 g 成比例增长。两个 Qwen 模型的头维相同，Qwen3.6 的 g 加倍，RI 也加倍。

RI 均随 L 线性增长；写入窗口则不同：Prefill 从空 KV 建到 L，Decode 只追加一个 token。

Hy3 与 Ling 的头结构相同，RI 相同；MiMo 直接使用原生 192/128 头维。

固定模型来源、精确字节及复算记录见本目录 README 与 data/；数学入口为 Table II(a)。
