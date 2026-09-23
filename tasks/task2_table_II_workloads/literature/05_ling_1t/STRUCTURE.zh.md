# Ling-1T：结构卡

**状态：Step 1完成，待审阅。** 矩阵均按 W=(输出维度 N, 输入维度 K)，层号从 0 起。

## 身份与选择

- 官方仓库：[inclusionAI/Ling-1T](https://huggingface.co/inclusionAI/Ling-1T/tree/268f2aa76aa8cf5b36ca33805481cea91133327e)。
- checkpoint：`Ling-1T`；revision：`268f2aa76aa8cf5b36ca33805481cea91133327e`。
- 发布日期：2025年10月；精确公开发布日期未单独核实，不拿仓库创建日替代；所取 revision 日期：2026-04-13T11:45:13.000Z。
- 原始 [配置](raw/config.json)、[模型卡](raw/README.md)、[仓库元数据](raw/hf_metadata.json)；[完整来源清单](../../data/sources.json)记录 URL、日期、revision 与 SHA-256。
- 总参数标签 1000B；激活标签 51B。口径：报告 Table 1 为 1000B/51B，模型卡约写 50B 激活。

本次为 Ling 2.0 系列的 `inclusionAI/Ling-1T` 非思考 Instruct，未使用 Ring-1T 或 Ling-2.5/2.6。80 层全 GQA；0–3 层 Dense 宽 18432，4–79 层 MoE，选第 4 层。每层 256 个路由专家选 8，另一个宽 2048 的共享专家。QKV 在 `query_key_value` 中融合，按 Q=64、K=8、V=8 个 128 维头切分。

报告 PDF p.5 Table 1 给出 1000B/51B；模型卡约写 1T/50B，保留为报告值与宣传取整值，不据此反推矩阵。报告 p.4 对系列写“8、16 或 32 个 KV 头”，未逐模型分配且与所取配置有疑义；明确的 `num_key_value_heads=8` 和代码 `repeat_kv` 为本 checkpoint 的入口，不按系列顺序猜 32。

报告 p.4 与 `rotary_dim=64` 描述部分 RoPE，但所存 remote code 使用 `partial_rotary_factor`（配置缺少该键，局部回退为 1），未消费 `rotary_dim`。本轮不裁定所有运行后端的旋转语义完全一致；这一问题不改变完整 K=128 的矩阵/缓存维度。报告 p.5/13 另有训练 MTP depth=1；所取 config 未提供 `num_nextn_predict_layers`，configuration 文件默认 0，不能凭报告给该推理入口补一层。

原始最大长度 32768，`rope_scaling=null`。官方模型卡 238–250 行给出 **YaRN factor=4，original_max_position_embeddings=32768，type=yarn**，并要求设置运行端 `--max-model-len`；本研究 128K 对应 131072。配置原件未改写；该支持是有条件的官方入口，未运行模型或验证长上下文质量。

## 关键结构与原始定位

| 项目 | 固定值 | 依据 |
|---|---|---|
| hidden size / 主干层数 | 8192 / 80 | `hidden_size / num_hidden_layers` |
| 本次实际层 | 第 4 层；完整因果 GQA | 配置层型及实现 decoder layer |
| Q heads / KV heads / 共享组大小 | 64 / 8 / 8 | `num_attention_heads / num_key_value_heads`；`repeat_kv` |
| QK / V 每头维度 | 128 / 128 | `head_dim` 与 attention 构造 |
| FFN / 单路由专家宽度 | 2048 | `moe_intermediate_size` |
| 路由专家总数 / top-k / 共享专家 | 256 / 8 / 1 | 原始配置专家键；MoE 构造 |

## 投影与 FFN 矩阵

| 矩阵 | W 的形状 N×K |
|---|---|
| Q（逻辑部分） | 8192×8192 |
| K | 1024×8192 |
| V | 1024×8192 |
| Attention 输出投影（为完整结构记录，非 QKV 行） | 8192×8192 |
| 原生融合 QKV | 10240×8192 |
| 所选 FFN／单专家 gate | 2048×8192 |
| 所选 FFN／单专家 up | 2048×8192 |
| 所选 FFN／单专家 down | 8192×2048 |
| 共享专家 gate（另列，非本行主对象） | 2048×8192 |
| 共享专家 up（另列，非本行主对象） | 2048×8192 |
| 共享专家 down（另列，非本行主对象） | 8192×2048 |
| 路由 gate（区别于 SwiGLU gate） | 256×8192 |

gate/up/down 参数元素合计：单个所选 FFN／专家 **50,331,648**。 同一 MoE 层激活路由专家集合为 **402,653,184**，全部路由专家为 **12,884,901,888**，共享专家另有 **50,331,648**。 这里只是三矩阵元素数，不含路由、范数、Attention、embedding 或 MTP，也不是 Byte 或场景工作量。

这些形状由固定配置与线性层构造导出，未下载权重核验每个张量。所取实现的融合/堆叠不自动决定后续 CIM 输入接收次数。

## KV 与四类工况入口

- QKV Projection：使用所选完整 GQA 的原生投影，一个输入 token；权重预驻留为本研究约定。
- FFN / MoE：一个路由专家的 SwiGLU FFN，一次装载服务 B={8,64,512} 个向量；top-k 和全部专家数仅记录结构，不能作为主行的隐式倍数。
- Attention Prefill/Decode：K 逻辑缓存 `[sequence_batch,8,tokens,128]`；V 为 `[sequence_batch,8,tokens,128]`。`sequence_batch` 是维度标签，不是研究参数 B。
- 缓存保存处理后的 K 与 V：K 已经过 QK 归一化和 RoPE；V 为值投影结果。缓存更新发生于 GQA 扩展之前；每份 KV 对应 8 个 query heads，共享不是额外持久副本。
- Prefill 从本段空 KV 建到 L 并完成因果矩阵任务；Decode 从 L−1 追加 1、可见 L。物理分页、复制、宏映射和非矩阵算子边界留 Step 2。
- 三个 L：1024、16384、131072。原始配置最大长度 32768。128K 需上述官方 YaRN 与运行端长度设置；1K、16K 不需该扩展。

## 精度与证据入口

checkpoint 声明 BF16，router_dtype=fp32；报告的 FP8 训练不表示该产物全部为 FP8。尚未选定后续 streaming、resident、KV 与 Attention 系数的逻辑精度；不把原生 BF16/FP8 直接配 Task I 的 INT8 能力。

[固定实现：modeling_bailing_moe_v2.py](raw/modeling_bailing_moe_v2.py)；核心定位：`BailingMoeV2Attention` 与 `BailingMoeV2MLP / BailingMoeV2SparseMoeBlock`。下面列出本地行号，便于直接复核：

- `modeling_bailing_moe_v2.py:86`：`MoEV2CausalLMOutputWithPast`。
- `modeling_bailing_moe_v2.py:271`：`BailingMoeV2MLP`。
- `modeling_bailing_moe_v2.py:351`：`BailingMoeV2SparseMoeBlock`。
- `modeling_bailing_moe_v2.py:441`：`BailingMoeV2Attention`。
- `modeling_bailing_moe_v2.py:565`：`BailingMoeV2FlashAttention2`。
- `modeling_bailing_moe_v2.py:770`：`BailingMoeV2SdpaAttention`。
- `modeling_bailing_moe_v2.py:941`：`BailingMoeV2DecoderLayer`。

[技术报告 PDF](raw/2510.22115v2.pdf)：pp.4–5 §2/Table 1，pp.13–14 上下文与 MTP；[可搜索提取文本](extracted/2510.22115v2.txt)。

共同算法资料见 [共享资料入口](../00_shared/README.md)。结构差异、条件和未决项也同步在 [models.json](../../data/models.json)。
