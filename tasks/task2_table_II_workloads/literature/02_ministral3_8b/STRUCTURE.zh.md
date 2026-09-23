# Ministral 3 8B (2512)：结构卡

**状态：Step 1完成，待审阅。** 矩阵均按 W=(输出维度 N, 输入维度 K)，层号从 0 起。

## 身份与选择

- 官方仓库：[mistralai/Ministral-3-8B-Base-2512](https://huggingface.co/mistralai/Ministral-3-8B-Base-2512/tree/d4883f9b36aa2e5d775730d3fdba3d30de51a8ef)。
- checkpoint：`Ministral-3-8B-Base-2512`；revision：`d4883f9b36aa2e5d775730d3fdba3d30de51a8ef`。
- 发布日期：2025-12-02；所取 revision 日期：2026-01-15T11:17:01.000Z。
- 原始 [配置](raw/config.json)、[模型卡](raw/README.md)、[仓库元数据](raw/hf_metadata.json)；[完整来源清单](../../data/sources.json)记录 URL、日期、revision 与 SHA-256。
- 总参数标签 8.4B；激活标签 不另定义（Dense）。口径：语言主干 8.4B，模型卡另列视觉编码器约 0.4B。

选择官方 `Ministral-3-8B-Base-2512`：与用户指定的 2025 年 12 月系列一致，原生 BF16、`params.json` 和 HF `text_config` 均齐全。Base、Instruct、Reasoning 的行为不同；本任务只研究矩阵结构，不以 Base 替代模型效果评估。模型卡报告语言主干 8.4B，另有约 0.4B 视觉编码器；报告用系列名 8B，二者不是参数统计矛盾。

34 层均为完整 GQA + Dense SwiGLU；`sliding_window=null`。原生 `params.json` 中 `dim/n_layers/hidden_dim/n_heads/n_kv_heads/head_dim` 与 HF 配置对应。`v_head_dim=null` 是原生参数格式中未启用特殊 V 维度，并非 V 宽度为零；实现中 V 与 QK 都取 `head_dim=128`。

128K 落在官方 256K 支持范围内，但应保留 checkpoint 自带的 YaRN（factor=16，original=16384，beta_fast=32、beta_slow=1、mscale=mscale_all_dim=1）以及 `llama_4_scaling_beta=0.1` 的位置相关 query/温度缩放。已保存在原始配置，不把“16K 原始位置长度”误记成最终最大上下文。报告 PDF pp.2–3，Table 1 与 §2 是核心依据。

## 关键结构与原始定位

| 项目 | 固定值 | 依据 |
|---|---|---|
| hidden size / 主干层数 | 4096 / 34 | `text_config.hidden_size / num_hidden_layers` |
| 本次实际层 | 第 0 层；完整因果 GQA | 配置层型及实现 decoder layer |
| Q heads / KV heads / 共享组大小 | 32 / 8 / 4 | `text_config.num_attention_heads / num_key_value_heads`；`repeat_kv` |
| QK / V 每头维度 | 128 / 128 | `text_config.head_dim` 与 attention 构造 |
| FFN / 单路由专家宽度 | 14336 | `text_config.intermediate_size` |
| 路由专家总数 / top-k / 共享专家 | 0 / 0 / 0 | 原始配置专家键；MoE 构造 |

## 投影与 FFN 矩阵

| 矩阵 | W 的形状 N×K |
|---|---|
| Q（逻辑部分） | 4096×4096 |
| K | 1024×4096 |
| V | 1024×4096 |
| Attention 输出投影（为完整结构记录，非 QKV 行） | 4096×4096 |
| 所选 FFN／单专家 gate | 14336×4096 |
| 所选 FFN／单专家 up | 14336×4096 |
| 所选 FFN／单专家 down | 4096×14336 |

gate/up/down 参数元素合计：单个所选 FFN／专家 **176,160,768**。 这里只是三矩阵元素数，不含路由、范数、Attention、embedding 或 MTP，也不是 Byte 或场景工作量。

这些形状由固定配置与线性层构造导出，未下载权重核验每个张量。所取实现的融合/堆叠不自动决定后续 CIM 输入接收次数。

## KV 与四类工况入口

- QKV Projection：使用所选完整 GQA 的原生投影，一个输入 token；权重预驻留为本研究约定。
- FFN / MoE：一个 Dense SwiGLU FFN，一次装载服务 B={8,64,512} 个向量；top-k 和全部专家数仅记录结构，不能作为主行的隐式倍数。
- Attention Prefill/Decode：K 逻辑缓存 `[sequence_batch,8,tokens,128]`；V 为 `[sequence_batch,8,tokens,128]`。`sequence_batch` 是维度标签，不是研究参数 B。
- 缓存保存处理后的 K 与 V：K 已经过 RoPE；V 为值投影结果。缓存更新发生于 GQA 扩展之前；每份 KV 对应 4 个 query heads，共享不是额外持久副本。
- Prefill 从本段空 KV 建到 L 并完成因果矩阵任务；Decode 从 L−1 追加 1、可见 L。物理分页、复制、宏映射和非矩阵算子边界留 Step 2。
- 三个 L：1024、16384、131072。原始配置最大长度 262144。三个 L 均有官方配置/模型卡支持；保留上述原生上下文设置。

## 精度与证据入口

所取 Base 为 BF16；Instruct FP8 是另一个发布产物。尚未选定后续 streaming、resident、KV 与 Attention 系数的逻辑精度；不把原生 BF16/FP8 直接配 Task I 的 INT8 能力。

[固定实现：modeling_ministral3.py](../00_shared/raw/transformers/modeling_ministral3.py)；核心定位：`Ministral3Attention` 与 `Ministral3MLP`。下面列出本地行号，便于直接复核：

- `modeling_ministral3.py:111`：`Ministral3Attention`。
- `modeling_ministral3.py:176`：`Ministral3MLP`。
- `modeling_ministral3.py:213`：`Ministral3DecoderLayer`。

[技术报告 PDF](raw/2601.08584v1.pdf)：pp.2–3 §2/Table 1；[可搜索提取文本](extracted/2601.08584v1.txt)。[原生 params.json](raw/params.json) 与 HF 配置互证。

共同算法资料见 [共享资料入口](../00_shared/README.md)。结构差异、条件和未决项也同步在 [models.json](../../data/models.json)。
