# MiMo-V2.5-Pro：结构卡

**状态：Step 1完成，待审阅。** 矩阵均按 W=(输出维度 N, 输入维度 K)，层号从 0 起。

## 身份与选择

- 官方仓库：[XiaomiMiMo/MiMo-V2.5-Pro](https://huggingface.co/XiaomiMiMo/MiMo-V2.5-Pro/tree/21d1ecfecd7bd70f31be25ca49d7edd21f003659)。
- checkpoint：`MiMo-V2.5-Pro`；revision：`21d1ecfecd7bd70f31be25ca49d7edd21f003659`。
- 发布日期：2026-04-27；所取 revision 日期：2026-07-09T04:20:08.000Z。
- 原始 [配置](raw/config.json)、[模型卡](raw/README.md)、[仓库元数据](raw/hf_metadata.json)；[完整来源清单](../../data/sources.json)记录 URL、日期、revision 与 SHA-256。
- 总参数标签 1020B；激活标签 42B。口径：模型卡总量/激活量标签；未通过张量普查核对是否包含全部 MTP。

选 `XiaomiMiMo/MiMo-V2.5-Pro` 后训练版本，官方声明 1.02T/42B、1M 上下文。不能混用非 Pro 的 310B/48 层或 Base 的 256K 声明。70 层中 10 个全局 GQA、60 个 SWA，滑窗为 128；第 0 层 Dense 宽 16384，其余 69 层为 MoE。完整 GQA 的零起点为 `[0,7,15,23,31,39,47,55,62,69]`，**6:1 是总层数比例，非处处相同的循环**。选第 7 层，能同时对应完整 GQA 和路由专家。

128 个 Q 头、8 个 KV 头，QK head_dim=192，V head_dim=128。Q/K/V 实际宽度为 24576/1536/1024，原生 `fused_qkv` 矩阵为 27136×6144；输出投影输入宽度为 128×128=16384。Value 在缓存写入之前乘 0.612。全局层 `add_full_attention_sink_bias=false`，学习 sink 只属于被排除的 SWA；不能为全局层额外造一个 KV token。

384 个路由专家选 8，单专家宽 2048，`n_shared_experts=null` 且实现无共享专家分支。模型卡描述 3 个 MTP 模块，所取轻量 remote code 仅构建 70 个主干层，未独立核对 MTP 张量布局，且 MTP 不在本研究范围。

checkpoint 原生是 **FP8 E4M3 mixed**，动态激活量化、128×128 权重块缩放，`ignored_layers` 排除 o_proj；`torch_dtype=bfloat16` 不能解读为所有权重 BF16。训练原生 32K 与发布 checkpoint 的 1048576 最大位置长度是不同概念。官方 Pro 模型卡和该配置已提供 128K 支持入口，无需在本轮另造扩展参数。

## 关键结构与原始定位

| 项目 | 固定值 | 依据 |
|---|---|---|
| hidden size / 主干层数 | 6144 / 70 | `hidden_size / num_hidden_layers` |
| 本次实际层 | 第 7 层；完整因果 GQA | 配置层型及实现 decoder layer |
| Q heads / KV heads / 共享组大小 | 128 / 8 / 16 | `num_attention_heads / num_key_value_heads`；`repeat_kv` |
| QK / V 每头维度 | 192 / 128 | `head_dim`、`v_head_dim` |
| FFN / 单路由专家宽度 | 2048 | `moe_intermediate_size` |
| 路由专家总数 / top-k / 共享专家 | 384 / 8 / 0 | 原始配置专家键；MoE 构造 |

## 投影与 FFN 矩阵

| 矩阵 | W 的形状 N×K |
|---|---|
| Q（逻辑部分） | 24576×6144 |
| K | 1536×6144 |
| V | 1024×6144 |
| Attention 输出投影（为完整结构记录，非 QKV 行） | 6144×16384 |
| 原生融合 QKV | 27136×6144 |
| 所选 FFN／单专家 gate | 2048×6144 |
| 所选 FFN／单专家 up | 2048×6144 |
| 所选 FFN／单专家 down | 6144×2048 |
| 路由 gate（区别于 SwiGLU gate） | 384×6144 |

gate/up/down 参数元素合计：单个所选 FFN／专家 **37,748,736**。 同一 MoE 层激活路由专家集合为 **301,989,888**，全部路由专家为 **14,495,514,624**，共享专家另有 **0**。 这里只是三矩阵元素数，不含路由、范数、Attention、embedding 或 MTP，也不是 Byte 或场景工作量。

这些形状由固定配置与线性层构造导出，未下载权重核验每个张量。所取实现的融合/堆叠不自动决定后续 CIM 输入接收次数。

## KV 与四类工况入口

- QKV Projection：使用所选完整 GQA 的原生投影，一个输入 token；权重预驻留为本研究约定。
- FFN / MoE：一个路由专家的 SwiGLU FFN，一次装载服务 B={8,64,512} 个向量；top-k 和全部专家数仅记录结构，不能作为主行的隐式倍数。
- Attention Prefill/Decode：K 逻辑缓存 `[sequence_batch,8,tokens,192]`；V 为 `[sequence_batch,8,tokens,128]`。`sequence_batch` 是维度标签，不是研究参数 B。
- 缓存保存处理后的 K 与 V：K 已经过部分 RoPE；V 已乘 0.612。缓存更新发生于 GQA 扩展之前；每份 KV 对应 16 个 query heads，共享不是额外持久副本。
- Prefill 从本段空 KV 建到 L 并完成因果矩阵任务；Decode 从 L−1 追加 1、可见 L。物理分页、复制、宏映射和非矩阵算子边界留 Step 2。
- 三个 L：1024、16384、131072。原始配置最大长度 1048576。三个 L 均有官方配置/模型卡支持；保留上述原生上下文设置。

## 精度与证据入口

FP8 E4M3 分块权重配动态激活量化；torch_dtype=BF16 为默认浮点类型，ignored_layers 将 o_proj 排除在 FP8 之外。尚未选定后续 streaming、resident、KV 与 Attention 系数的逻辑精度；不把原生 BF16/FP8 直接配 Task I 的 INT8 能力。

[固定实现：modeling_mimo_v2.py](raw/modeling_mimo_v2.py)；核心定位：`MiMoV2Attention` 与 `MiMoV2MLP / MiMoV2MoE`。下面列出本地行号，便于直接复核：

- `modeling_mimo_v2.py:115`：`MiMoV2MLP`。
- `modeling_mimo_v2.py:130`：`MiMoV2MoEGate`。
- `modeling_mimo_v2.py:182`：`MiMoV2MoE`。
- `modeling_mimo_v2.py:215`：`MiMoV2Attention`。
- `modeling_mimo_v2.py:389`：`MiMoV2DecoderLayer`。

未找到属于此确切版本的独立技术报告 PDF；本卡依据完整官方模型卡、固定配置与实现，不以其它型号报告补结构。

共同算法资料见 [共享资料入口](../00_shared/README.md)。结构差异、条件和未决项也同步在 [models.json](../../data/models.json)。
