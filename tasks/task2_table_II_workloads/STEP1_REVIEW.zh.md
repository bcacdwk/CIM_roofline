# Task II · Step 1 审阅

**Step 1完成，待审阅。** 2026-09-23；本地起点 HEAD 为 `81b7c332c20b9b5be6890256e9cf0d3edab12785`，与用户检查点一致。

六个模型身份、官方 checkpoint 和不可变 revision 已固定；本地结构资料足以进入下一阶段的共享计数方法写作。本轮仅整理证据、配置与矩阵形状，没有生成任何场景 Q_S、Q_R、RI、TeX 主表、器件配对或性能分区。Task I、主论文和归档未修改。研究设计完整保存于 [README](README.md) 与 [study_plan.json](data/study_plan.json)。

## 六模型概览

层号均从 0 起。H 是 hidden size；Q/KV 是头数；d_QK/d_V 是真实每头维度。参数 B 表示十亿，与研究复用参数 B 无关。总量/激活量保留官方标签，不拿它们替代子层矩阵结构。

| 模型（结构卡） | 官方总量 / 激活量 | H；主干层数 | 实际层型与本次层号 | Q/KV；d_QK/d_V | FFN／单路由专家宽度；路由/共享 | 原生发布格式；上下文 |
|---|---|---|---|---|---|---|
| [Qwen3.5-2B](literature/01_qwen35_2b/STRUCTURE.zh.md) | 语言主干 2B / Dense | 2048；24 | 18 DeltaNet + 6 full GQA；取 3 | 8/2；256/256 | Dense 6144 | BF16；262144 |
| [Ministral 3 8B 2512](literature/02_ministral3_8b/STRUCTURE.zh.md) | 语言主干 8.4B / Dense；视觉另约 0.4B | 4096；34 | 全部 full GQA；取 0 | 32/8；128/128 | Dense 14336 | Base BF16；262144，带原生 YaRN/位置缩放 |
| [Qwen3.6-35B-A3B](literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) | 语言主干 35B / 3B | 2048；40 | 30 DeltaNet + 10 full GQA；全部 MoE；取 3 | 16/2；256/256 | 专家 512；256 选 8 + 共享 1×512 | BF16；262144 原生 |
| [Tencent Hy3 295B](literature/04_hy3_295b/STRUCTURE.zh.md) | 295B / 21B；MTP 3.8B 另列 | 4096；80 | 全 GQA；1 Dense + 79 MoE；取 1 | 64/8；128/128 | 专家 1536；192 选 8 + 共享 1×1536 | BF16；262144 |
| [Ling-1T](literature/05_ling_1t/STRUCTURE.zh.md) | 1000B / 报告 51B，模型卡约 50B | 8192；80 | 全 GQA；4 Dense + 76 MoE；取 4 | 64/8；128/128 | 专家 2048；256 选 8 + 共享 1×2048 | BF16；32768，按官方 YaRN 扩展至 131072 |
| [MiMo-V2.5-Pro](literature/06_mimo_v25_pro/STRUCTURE.zh.md) | 1020B / 42B | 6144；70 | 60 SWA + 10 global；1 Dense + 69 MoE；取 7 | 128/8；192/128 | 专家 2048；384 选 8，无共享 | FP8 E4M3 mixed；1048576 |

以上数据由各模型原始 config/model card 及固定实现交叉支持，逐项入口在结构卡与 [models.json](data/models.json) 的 `evidence` 中。Ministral 报告 PDF pp.2–3、Ling 报告 pp.4–5/13–14 的结构表及上下文段落已核对。其余四个模型的主要一手来源是完整官方模型卡、配置与实现；未找到确切版本的独立报告 PDF，未借其它型号配置补字段。

## 版本固定与选择

| 列 | 官方 checkpoint | 固定 revision |
|---|---|---|
| 1 | `Qwen/Qwen3.5-2B` | `15852e8c16360a2fea060d615a32b45270f8a8fc` |
| 2 | `mistralai/Ministral-3-8B-Base-2512` | `d4883f9b36aa2e5d775730d3fdba3d30de51a8ef` |
| 3 | `Qwen/Qwen3.6-35B-A3B` | `995ad96eacd98c81ed38be0c5b274b04031597b0` |
| 4 | `tencent/Hy3` | `a960ebc3da325ba167f069f76c41eb62c9280d22` |
| 5 | `inclusionAI/Ling-1T` | `268f2aa76aa8cf5b36ca33805481cea91133327e` |
| 6 | `XiaomiMiMo/MiMo-V2.5-Pro` | `21d1ecfecd7bd70f31be25ca49d7edd21f003659` |

Ministral 选同一 2512 系列的 Base BF16，因其完整提供原生 params.json、HF text_config 和同系列报告；没有将 2024 年的 Ministral 8B 混入。Hy3 选 2026 年 7 月正式发布的 295B Instruct，不混用 preview。MiMo 选 Pro 后训练版本，不混用非 Pro、V2-Pro 或 Base。两款 Qwen 和 Ling 使用确切指定型号官方版本。

Qwen3.6 的架构类仍称 `Qwen3_5MoeForConditionalGeneration`，这是官方 checkpoint 的事实。两款 Qwen、Ministral、Hy3 共用一份 Transformers commit `2c4914fb939fe9de0d8e7a798af4684d552f18b4` 的静态实现资料，Ling/MiMo 的 remote code 与 checkpoint revision 一起固定。未执行第三方模型代码或加载权重来宣称部署兼容。

## 四类工况的覆盖

下面的层型与矩阵参数来自来源；驻留、B、L 与窗口来自本研究。全表只选真实完整 GQA 子层，不能据此推出所有层都是同一种 Attention。

| 模型 | QKV Projection | FFN / MoE | Attention Prefill 与 Decode | L=1K / 16K / 128K |
|---|---|---|---|---|
| Qwen3.5-2B | 第 3 层，Q+output gate 打包，K/V 分开 | 第 3 层 Dense FFN | K/V 各 2×256，4 个 Q 头共享一组 KV | 均支持，原生配置内 |
| Ministral | 第 0 层，Q/K/V 分开 | 第 0 层 Dense FFN | K/V 各 8×128，组大小 4 | 均支持，保留配置中的 YaRN 和位置缩放 |
| Qwen3.6 | 第 3 层，Q+output gate 打包，K/V 分开 | 第 3 层单路由专家 | K/V 各 2×256，组大小 8 | 均支持，原生配置内 |
| Hy3 | 第 1 层，Q/K/V 分开 | 第 1 层单路由专家 | K/V 各 8×128，组大小 8 | 均支持，checkpoint 为 256K |
| Ling | 第 4 层，融合 QKV | 第 4 层单路由专家 | K/V 各 8×128，组大小 8 | 前两档原生；128K 须官方 YaRN factor=4 + 运行端长度配置 |
| MiMo Pro | 第 7 层 global，融合 QKV | 第 7 层单路由专家 | K=8×192、V=8×128，组大小 16 | 均支持，Pro checkpoint 声明 1M |

结构卡给出实际 Q/K/V、额外 output gate、输出投影和 gate/up/down 的 N×K 形状；同时列出单专家、激活路由集合、全部路由专家与共享专家的三矩阵元素数。它们没有转换为字节，没有引入 B/L 情景数值。MoE 主行的对象已经固定为单路由专家，不能自动再乘 top-k 或专家总数。

## 需要保留的结构差异与缺口

- **额外门控**：两款 Qwen 的原生 q_proj 产出 query 与同宽 output gate。Qwen3.5 是 4096×2048，Qwen3.6 是 8192×2048；不能用纯 Q 投影矩阵替代，也不能把 gate 当新 KV 状态。
- **投影维度独立于 H**：Hy3 的 Q 宽度为 8192，而 H=4096；Qwen3.6 的 Q 宽度 4096，而 H=2048。MiMo QK=192、V=128，融合 QKV 为 27136×6144。配置里的 head_dim 具有决定性，不能一律用 H/头数。
- **全局与滑窗层型**：MiMo 的全局层是 `[0,7,15,23,31,39,47,55,62,69]`；6:1 是总层数比例，非均匀周期。全局层没有 attention sink bias；SWA 才有，不为所选全局层额外添加虚拟 KV token。
- **Ling 来源差异**：报告的 51B 激活与模型卡约 50B 分别保留。报告系列文字提到 8/16/32 KV heads，却没有可靠逐模型对应；checkpoint 与代码明确使用 8。`rotary_dim=64`/报告部分 RoPE 与 remote code 的 `partial_rotary_factor` 路径未完全对齐，保留实现问题，不私改原始配置；QK/V 完整维度仍能确定。128K 官方 YaRN 配方已在本地，不是无条件原生支持。
- **MTP**：训练报告/模型卡和轻量推理实现可能呈现不同 MTP 入口，特别是 Ling 与 MiMo。本轮已记录差异并排除 MTP，不把它们加进主干层数或场景需求。MiMo 的公开总参数标签是否含全部 MTP 张量未做权重普查，不用它反推子层。
- **精度**：Ling 的 FP8 训练声明不等于 BF16 checkpoint 已全部存为 FP8；MiMo 的 `torch_dtype=bfloat16` 也不否定其 `quantization_config` 所声明的 FP8 mixed。各模型的实际 KV/输入精度由后端决定，本轮保持未来计量精度为未定，不全部默认同一 dtype。
- **非结构性缺省**：Ling-1T 的精确公开发布日期未单独锁定；保留官方仓库创建时间、所取 revision 时间及技术报告版本日期。配置/代码文件未独立标明发表日时，来源清单保留 null 并说明，未把仓库创建时间当发布日。

上述剩余问题不构成六个所选矩阵子层的结构缺失；没有用另一型号补配置。当前无必需资料下载失败，**无需用户补充下载**。若后续要做完整运行复现，则应另核对 Ling 的 RoPE 后端语义、运行库兼容性与被排除的 MTP 路径；这些不扩展为本轮仿真任务。

## 下一阶段仅需决定的少数问题

1. 分别声明 streaming 输入、权重、K/V 与 Attention 系数的逻辑精度，并说明与 Task I INT8 参考条件的关系；保留原生格式供追溯。
2. 固定所分析服务边界、融合矩阵与独立输入接收端口、GQA 共享/重放的映射规则。原生 Qwen output gate 结构已固定，Step 2 需要交代它与非矩阵算子的边界，不能悄悄删除。
3. 固定因果 Prefill 中有效前缀矩阵的求值/驻留组织、KV 建立与 Decode append 的方向及窗口，避免把遮罩后的无效区、缓存容量和真正写入混为一谈。

不再讨论模型排名、不扫描 B×L、不改六模型或三个 L、不引入完整训练 step。

## 文件与核验

- 原始来源索引：[sources.json](data/sources.json)；结构数据：[models.json](data/models.json)；六份中文结构卡见概览第一列。
- 六份原始 config 完整保留，前三个模型的 nested text_config 未裁剪；Ministral 原生 params.json 同时保存。所有下载均有哈希和获取日期。
- 5 份 PDF（2 份模型报告 + 3 份共同算法论文）共 99 页，全部能打开并抽取非空文本；已目视核对关键结构/定义页，未声称审读全部无关章节。
- 许可不明确的全文与派生文本已用本任务 `.gitignore` 排除公开 Git 分发，文件仍在本地；其它机器可按固定来源补取。没有只交摘要链接。
- [轻量检查](scripts/check_step1.py) 校验配置键、形状、层型、来源哈希与文件路径；结果在 [step1_validation.json](data/step1_validation.json)。

**本轮到此停止，等待用户审阅。**
