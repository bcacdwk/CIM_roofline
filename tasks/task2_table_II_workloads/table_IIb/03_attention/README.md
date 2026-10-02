# Attention：算子级输入复用与 RI

2026-10-02 主 Agent 修订，待用户审阅。以当前 Table II(a) 的 `RI=Q_S/Q_R`、每元素 1 Byte 为数学入口，按共同合同分析固定六模型所选完整/global 因果 GQA 层。本文仅含 QK 与 AV 两个矩阵阶段。

- [中文 PDF](output/report.zh.pdf)、[正文 TeX](tex/report.zh.tex)、[中文结果预览](PREVIEW.zh.md)。
- [配置与来源](data/config.json)、[精确 JSON](data/results.json)、[CSV](data/results.csv)、[独立检查](data/checks.json)、[逐页 PDF 检查](data/pdf_qa.json)。
- 共同约定：[合同](../04_crosscheck/CONTRACT.zh.md)、[机器接口](../04_crosscheck/data/conventions.json)。

## 窗口、公式与分项

`L` 为追加后可见长度，单序列。每个 KV head 保存一份唯一逻辑 K/V，由 `g=H_q/H_kv` 个 query heads 共享。原生维度 `H_q,H_kv,d_QK,d_V` 不变。所有角色均固定 1 Byte/element，原生 dtype 仅作来源记录。

| 窗口 | QK 输入 Q_S | AV 输入 Q_S | 新 K 写入 Q_R | 新 V 写入 Q_R | 汇总 RI |
|---|---|---|---|---|---|
| Prefill：空 KV → L | H_q L d_QK | H_q L(L+1)/2 | L H_kv d_QK | L H_kv d_V | g[d_QK+(L+1)/2]/(d_QK+d_V) |
| Decode：已有 L−1，追加一个 → L | H_q d_QK | H_q L | H_kv d_QK | H_kv d_V | g(d_QK+L)/(d_QK+d_V) |

QK 的 query 和 AV 的 softmax 后系数是不同矩阵阶段的输入，分别计入；当前输出不直接加入 Q_S。因果三角和只描述算法有效范围。Q_R 是当前窗口中新状态的累计写入量。两个窗口的最终有效 KV 容量均为 `L H_kv(d_QK+d_V)`；Prefill 初始容量为 0，Decode 初始容量为 `(L−1)H_kv(d_QK+d_V)`。数据中的 `shape_N_K` 是最终可见长度下、每份唯一状态矩阵的形状：QK 为 `[L,d_QK]`，AV 为 `[d_V,L]`；`state_copies=H_kv`。

## 固定模型与证据

模型顺序、完整 revision、零起点所选层及来源 SHA-256 均固定于 `data/config.json`。源文件路径相对任务根 `tasks/task2_table_II_workloads/`；原始 URL 与实现 revision 由该任务根的 `data/sources.json` 追踪。计数直接使用以下头结构，未从模型总参数标签反推维度。

| 模型 | 所选层 | H_q / H_kv | d_QK / d_V | 结构证据 |
|---|---:|---:|---:|---|
| Qwen3.5-2B | 3 | 8 / 2 | 256 / 256 | [结构卡](../../literature/01_qwen35_2b/STRUCTURE.zh.md) |
| Ministral 3 8B (2512) | 0 | 32 / 8 | 128 / 128 | [结构卡](../../literature/02_ministral3_8b/STRUCTURE.zh.md) |
| Qwen3.6-35B-A3B | 3 | 16 / 2 | 256 / 256 | [结构卡](../../literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) |
| Tencent Hy3 (295B) | 1 | 64 / 8 | 128 / 128 | [结构卡](../../literature/04_hy3_295b/STRUCTURE.zh.md) |
| Ling-1T | 4 | 64 / 8 | 128 / 128 | [结构卡](../../literature/05_ling_1t/STRUCTURE.zh.md) |
| MiMo-V2.5-Pro | 7 | 128 / 8 | 192 / 128 | [结构卡](../../literature/06_mimo_v25_pro/STRUCTURE.zh.md) |

每模型分别取 Prefill、Decode 的 `L=1K,8K,64K`（1K=1024），共 36 个有限工况。Ling-1T 的 64K 沿用既定官方模型卡中的 YaRN 条件：`factor=4`、`original_max_position_embeddings=32768`、`type=yarn`，并设 `--max-model-len 131072`；原始配置不改。Ministral 保留配置已有的 YaRN 与位置相关 query 缩放。MiMo 保留原生 192/128 头维，Value 写入前乘 0.612；所选全局层无 sink，不额外增加 KV token。Qwen 两模型的 output gate 不增加 query head 或 KV 状态。

## 复算、编译与检查

从仓库根运行，默认生成器和检查器仅比较文件；显式 `--emit` 才刷新机器结果。

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/render.py
```

需要更新时，依次运行 `generate.py --emit` 和 `check.py --emit`，再编译、渲染并目检每一页。`render.py` 只生成检查图，不自动声明视觉通过。PDF 目检结果与文件哈希写入 `data/pdf_qa.json`，交付状态为 `ready_for_review`，不代表用户已审阅。

主生成器独立实现原生维度闭式。检查器另从原始配置读取头数和头维，对每个有效前缀累计 query 输入宽度、系数长度和新增 KV 行宽；使用 O(L+H_q+H_kv) 时间及常数工作内存。仅在四个小型结构上显式枚举输入与状态元素身份，核对两个阶段和初末状态；另查 L=1 时 Prefill/Decode 相等。全过程使用整数或精确分数，不构建 L×L 矩阵。

第二条回归路径只读归档 `tasks/archived/task2_table_IIb_previous/03_attention/data/results.json` 的 operator 字段。原有36个工况作为历史回归单独按前缀复算，其中12个1K工况与新主表重合；16K/128K仅用于回归，不额外计为当前场景。当前36个工况均另行独立复算。归档代码不执行，旧生产计数 API 不导入。来源哈希、严格接口、固定行序和 108 行 CSV 一并检查；细节置于 `data/checks.json`。

三角和只出现在有效系数输入的累计；每个 token 的 K/V 只新增一次。历史 K/V 是 resident 操作数，不再当作 streaming 输入重复计入 Q_S。PDF/预览使用小数 RI，精确分数仍保留在 JSON/CSV。
