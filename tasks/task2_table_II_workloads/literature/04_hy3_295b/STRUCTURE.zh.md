# Tencent Hy3 (295B)：结构卡

**状态：Step 1完成，待审阅。** 矩阵均按 W=(输出维度 N, 输入维度 K)，层号从 0 起。

## 身份与选择

- 官方仓库：[tencent/Hy3](https://huggingface.co/tencent/Hy3/tree/a960ebc3da325ba167f069f76c41eb62c9280d22)。
- checkpoint：`Hy3`；revision：`a960ebc3da325ba167f069f76c41eb62c9280d22`。
- 发布日期：2026-07-06；所取 revision 日期：2026-07-20T07:01:39.000Z。
- 原始 [配置](raw/config.json)、[模型卡](raw/README.md)、[仓库元数据](raw/hf_metadata.json)；[完整来源清单](../../data/sources.json)记录 URL、日期、revision 与 SHA-256。
- 总参数标签 295B；激活标签 21B。口径：主干 295B，MTP 参数 3.8B 另列。

选 2026-07-06 正式发布的 `tencent/Hy3` BF16 Instruct，未选 preview 或 FP8 分支。官方模型卡分别给出主干 295B、激活 21B、MTP 3.8B；80 个主干层外另列 1 个 MTP。本轮不把 MTP 数量加入 80 层。

所有主干层为完整 GQA。第 0 层是宽 13312 的 Dense FFN，第 1–79 层是 MoE；本次取第 1 层，192 个路由专家选 8，另有一个同宽 1536 的共享专家。注意 `hidden_size=4096` 并不能推出 Q head_dim=64：明确配置 `head_dim=128`，64 个 Q 头的投影宽度为 8192。

[官方转换代码](raw/convert_ckpt_to_outer.py) 112–122、207–234 行表明原 checkpoint 的逐专家 gate/up/down 可在 HF 装载路径中堆叠为 `gate_up_proj/down_proj`；这只是存储表示，不改变单专家三矩阵。共享专家键从 `shared_mlp` 映射到 `shared_experts`。共享上游实现配置的默认上下文是 131072，而此 checkpoint 明确覆盖为 262144，应使用后者。

## 关键结构与原始定位

| 项目 | 固定值 | 依据 |
|---|---|---|
| hidden size / 主干层数 | 4096 / 80 | `hidden_size / num_hidden_layers` |
| 本次实际层 | 第 1 层；完整因果 GQA | 配置层型及实现 decoder layer |
| Q heads / KV heads / 共享组大小 | 64 / 8 / 8 | `num_attention_heads / num_key_value_heads`；`repeat_kv` |
| QK / V 每头维度 | 128 / 128 | `head_dim` 与 attention 构造 |
| FFN / 单路由专家宽度 | 1536 | `moe_intermediate_size` |
| 路由专家总数 / top-k / 共享专家 | 192 / 8 / 1 | 原始配置专家键；MoE 构造 |

## 投影与 FFN 矩阵

| 矩阵 | W 的形状 N×K |
|---|---|
| Q（逻辑部分） | 8192×4096 |
| K | 1024×4096 |
| V | 1024×4096 |
| Attention 输出投影（为完整结构记录，非 QKV 行） | 4096×8192 |
| 所选 FFN／单专家 gate | 1536×4096 |
| 所选 FFN／单专家 up | 1536×4096 |
| 所选 FFN／单专家 down | 4096×1536 |
| 共享专家 gate（另列，非本行主对象） | 1536×4096 |
| 共享专家 up（另列，非本行主对象） | 1536×4096 |
| 共享专家 down（另列，非本行主对象） | 4096×1536 |
| 路由 gate（区别于 SwiGLU gate） | 192×4096 |

gate/up/down 参数元素合计：单个所选 FFN／专家 **18,874,368**。 同一 MoE 层激活路由专家集合为 **150,994,944**，全部路由专家为 **3,623,878,656**，共享专家另有 **18,874,368**。 这里只是三矩阵元素数，不含路由、范数、Attention、embedding 或 MTP，也不是 Byte 或场景工作量。

这些形状由固定配置与线性层构造导出，未下载权重核验每个张量。所取实现的融合/堆叠不自动决定后续 CIM 输入接收次数。

## KV 与四类工况入口

- QKV Projection：使用所选完整 GQA 的原生投影，一个输入 token；权重预驻留为本研究约定。
- FFN / MoE：一个路由专家的 SwiGLU FFN，一次装载服务 B={8,64,512} 个向量；top-k 和全部专家数仅记录结构，不能作为主行的隐式倍数。
- Attention Prefill/Decode：K 逻辑缓存 `[sequence_batch,8,tokens,128]`；V 为 `[sequence_batch,8,tokens,128]`。`sequence_batch` 是维度标签，不是研究参数 B。
- 缓存保存处理后的 K 与 V：K 已经过 QK 归一化和 RoPE；V 为值投影结果。缓存更新发生于 GQA 扩展之前；每份 KV 对应 8 个 query heads，共享不是额外持久副本。
- Prefill 从本段空 KV 建到 L 并完成因果矩阵任务；Decode 从 L−1 追加 1、可见 L。物理分页、复制、宏映射和非矩阵算子边界留 Step 2。
- 三个 L：1024、16384、131072。原始配置最大长度 262144。三个 L 均有官方配置/模型卡支持；保留上述原生上下文设置。

## 精度与证据入口

模型卡/配置声明 BF16；lm_head 的 FP32 标记不决定 KV 精度。尚未选定后续 streaming、resident、KV 与 Attention 系数的逻辑精度；不把原生 BF16/FP8 直接配 Task I 的 INT8 能力。

[固定实现：modeling_hy_v3.py](../00_shared/raw/transformers/modeling_hy_v3.py)；核心定位：`HYV3Attention` 与 `HYV3Experts / HYV3MoE`。下面列出本地行号，便于直接复核：

- `modeling_hy_v3.py:123`：`HYV3MLP`。
- `modeling_hy_v3.py:210`：`HYV3Attention`。
- `modeling_hy_v3.py:311`：`HYV3Experts`。
- `modeling_hy_v3.py:350`：`HYV3MoE`。
- `modeling_hy_v3.py:379`：`HYV3DecoderLayer`。

未找到属于此确切版本的独立技术报告 PDF；本卡依据完整官方模型卡、固定配置与实现，不以其它型号报告补结构。

共同算法资料见 [共享资料入口](../00_shared/README.md)。结构差异、条件和未决项也同步在 [models.json](../../data/models.json)。
