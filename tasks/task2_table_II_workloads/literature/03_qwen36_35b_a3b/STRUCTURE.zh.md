# Qwen3.6-35B-A3B：结构卡

**状态：Step 1完成，待审阅。** 矩阵均按 W=(输出维度 N, 输入维度 K)，层号从 0 起。

## 身份与选择

- 官方仓库：[Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B/tree/995ad96eacd98c81ed38be0c5b274b04031597b0)。
- checkpoint：`Qwen3.6-35B-A3B`；revision：`995ad96eacd98c81ed38be0c5b274b04031597b0`。
- 发布日期：2026-04-16；所取 revision 日期：2026-04-24T02:53:42.000Z。
- 原始 [配置](raw/config.json)、[模型卡](raw/README.md)、[仓库元数据](raw/hf_metadata.json)；[完整来源清单](../../data/sources.json)记录 URL、日期、revision 与 SHA-256。
- 总参数标签 35B；激活标签 3B。口径：语言主干总量/激活量的官方取整标签。

这是官方 Qwen3.6 checkpoint。其 `model_type=qwen3_5_moe`、`architectures=Qwen3_5MoeForConditionalGeneration` 是官方实现复用；没有拿 Qwen3.5-35B-A3B 的配置补齐。40 层为 30 个 Gated DeltaNet + 10 个完整 GQA，完整层零起点 `[3,7,11,15,19,23,27,31,35,39]`；每层配 MoE。选第 3 层。

Q 真正宽度 16×256=4096，大于 hidden size 2048。原生 `q_proj` 还输出等宽 output gate，故实际矩阵为 8192×2048。K/V 各 2×256=512。每个路由专家宽 512，256 选 8；另有宽 512 的共享专家及一个 1×2048 的共享专家输出门。共享专家不是路由专家编号中的第 257 个，不加入本表的“单路由专家”对象。

一个训练相关 MTP 层的配置存在，但本轮只固定 40 层语言主干。

## 关键结构与原始定位

| 项目 | 固定值 | 依据 |
|---|---|---|
| hidden size / 主干层数 | 2048 / 40 | `text_config.hidden_size / num_hidden_layers` |
| 本次实际层 | 第 3 层；完整因果 GQA | 配置层型及实现 decoder layer |
| Q heads / KV heads / 共享组大小 | 16 / 2 / 8 | `text_config.num_attention_heads / num_key_value_heads`；`repeat_kv` |
| QK / V 每头维度 | 256 / 256 | `text_config.head_dim` 与 attention 构造 |
| FFN / 单路由专家宽度 | 512 | `text_config.moe_intermediate_size` |
| 路由专家总数 / top-k / 共享专家 | 256 / 8 / 1 | 原始配置专家键；MoE 构造 |

## 投影与 FFN 矩阵

| 矩阵 | W 的形状 N×K |
|---|---|
| Q（逻辑部分） | 4096×2048 |
| K | 512×2048 |
| V | 512×2048 |
| Attention 输出投影（为完整结构记录，非 QKV 行） | 2048×4096 |
| 额外 output gate（逻辑部分） | 4096×2048 |
| 原生 q_proj，Q 与 gate 打包 | 8192×2048 |
| 所选 FFN／单专家 gate | 512×2048 |
| 所选 FFN／单专家 up | 512×2048 |
| 所选 FFN／单专家 down | 2048×512 |
| 共享专家 gate（另列，非本行主对象） | 512×2048 |
| 共享专家 up（另列，非本行主对象） | 512×2048 |
| 共享专家 down（另列，非本行主对象） | 2048×512 |
| 路由 gate（区别于 SwiGLU gate） | 256×2048 |
| 共享专家 output gate | 1×2048 |

gate/up/down 参数元素合计：单个所选 FFN／专家 **3,145,728**。 同一 MoE 层激活路由专家集合为 **25,165,824**，全部路由专家为 **805,306,368**，共享专家另有 **3,145,728**。 这里只是三矩阵元素数，不含路由、范数、Attention、embedding 或 MTP，也不是 Byte 或场景工作量。

这些形状由固定配置与线性层构造导出，未下载权重核验每个张量。所取实现的融合/堆叠不自动决定后续 CIM 输入接收次数。

## KV 与四类工况入口

- QKV Projection：使用所选完整 GQA 的原生投影，保留 Q 旁的 output gate，一个输入 token；权重预驻留为本研究约定。
- FFN / MoE：一个路由专家的 SwiGLU FFN，一次装载服务 B={8,64,512} 个向量；top-k 和全部专家数仅记录结构，不能作为主行的隐式倍数。
- Attention Prefill/Decode：K 逻辑缓存 `[sequence_batch,2,tokens,256]`；V 为 `[sequence_batch,2,tokens,256]`。`sequence_batch` 是维度标签，不是研究参数 B。
- 缓存保存处理后的 K 与 V：K 已经过 QK 归一化和 RoPE；V 为值投影结果。缓存更新发生于 GQA 扩展之前；每份 KV 对应 8 个 query heads，共享不是额外持久副本。
- Prefill 从本段空 KV 建到 L 并完成因果矩阵任务；Decode 从 L−1 追加 1、可见 L。物理分页、复制、宏映射和非矩阵算子边界留 Step 2。
- 三个 L：1024、16384、131072。原始配置最大长度 262144。三个 L 均有官方配置/模型卡支持；保留上述原生上下文设置。

## 精度与证据入口

语言配置声明 BF16；被排除的线性递归状态声明 float32。尚未选定后续 streaming、resident、KV 与 Attention 系数的逻辑精度；不把原生 BF16/FP8 直接配 Task I 的 INT8 能力。

[固定实现：modeling_qwen3_5_moe.py](../00_shared/raw/transformers/modeling_qwen3_5_moe.py)；核心定位：`Qwen3_5MoeAttention` 与 `Qwen3_5MoeExperts / Qwen3_5MoeSparseMoeBlock`。下面列出本地行号，便于直接复核：

- `modeling_qwen3_5_moe.py:751`：`Qwen3_5MoeAttention`。
- `modeling_qwen3_5_moe.py:828`：`Qwen3_5MoeMLP`。
- `modeling_qwen3_5_moe.py:845`：`Qwen3_5MoeExperts`。
- `modeling_qwen3_5_moe.py:904`：`Qwen3_5MoeSparseMoeBlock`。
- `modeling_qwen3_5_moe.py:947`：`Qwen3_5MoeDecoderLayer`。

未找到属于此确切版本的独立技术报告 PDF；本卡依据完整官方模型卡、固定配置与实现，不以其它型号报告补结构。

共同算法资料见 [共享资料入口](../00_shared/README.md)。结构差异、条件和未决项也同步在 [models.json](../../data/models.json)。
