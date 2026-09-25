# Step 4 · Agent D 独立复核报告

2026-09-25。基准 HEAD／已通过的 Step 3：`e472a0d864b8fb9afb14b0c306217a0e5653e122`。**60 个汇总、146 个分项全部通过；22 条 pilot 重叠工况无既有语义字段差异。** 未发现需要修正三份上游数据或共享方法的问题。本报告是内部复核交付，最终研究状态由主 Agent 记录；不视为用户已审阅，不开展 Step 5 英文表格。

## 最终交付锁与范围

只验收主 Agent 明确发出 READY 通知的版本；修订中的文稿不作为最终交付验收。A/B 的 revision 1→2 是代表性数字代入／文字修订，results 哈希未变；本次全量验收重新检查了最终 revision 2 的完整文件清单。

| 责任目录 | 最终版本 | 汇总／分项 | results SHA-256 |
|---|---:|---:|---|
| `01_qkv_projection` | 2 | 6／20 | `c342f0781f396df3d18d6bfcc94bdef95c3846f9985a8ca0e038297f0ef69a27` |
| `02_ffn_moe` | 2 | 18／54 | `5fc920987cd169108e39c72b5c844d0217b504dedffb8f9fbfce8f0ce40a4e8b` |
| `03_attention` | 1 | 36／72 | `7f552ac50508897407e7856c96221a3a73e2ac28ff5629b512a9f35736875107` |

完整 DELIVERY 哈希、revision、所有清单项及对应 SHA-256 位于 [config.json](data/config.json)，明确 READY 通知锁位于 [ready_sources.json](data/ready_sources.json)。A、B、C 的 manifest 外层结构／路径基准不同，逐份按其 `path_base` 解析，未把这类包装差异当成数值差异。统一 schema 不更改原结果内容。

固定口径为 `WS128-INT8-semantic-banks-v1`：128×128，所有角色 1 Byte，ports 主边界、operator 对照，独立语义矩阵，原生 Hq/Hkv/dQK/dV，每 KV head 一份 K/V，逐因果前缀。矩阵子层不扩张为整模型。六模型、零基层号3/0/3/1/4/7、checkpoint revision、B=8/64/512 与 L=1024/16384/131072 均核对。

## 独立 oracle 怎样形成

[crosscheck.py](scripts/crosscheck.py) 只用 Python 标准库；**不导入生产 counting.py、三个生成器或 pilot 生成器形成预期值**。读取这些生成结果仅作被比较对象。所用维度重新从六份原始 config 的语言配置提取，选层由 full/global 与 Dense/MoE 配置规则推导，再与 models.json 对照；固定实现只读核验 Qwen Q/G 切片、Ministral 同宽 V、Hy3 原生 head_dim、Ling 融合 QKV、MiMo 非等宽投影和 cache 交接。原始来源的既有50份哈希另由 Step 1 回归核验。

矩阵 oracle 显式构造各独立语义矩阵的有效 tile 矩形 `(n_i,k_j)`。每个 receiver／向量的 streaming 加 `k_j`，每次完整装载加 `n_i*k_j`，每次调用计1；有效容量用矩形面积求和，分配容量用实际 tile 数×16384。operator 用输入身份集合去重：Q/K/V/G 都是同一 `x`；FFN gate/up 共用 `x`，down 为新的 `z`。因此独立分项的 operator 不可直接相加，去重量单独核对。所有 RI 重新由对应边界的精确总字节求商，未平均分项比值。

Attention 采用与生产前缀闭式不同的**反向组织**：每个序列 tile 在第一次出现后，经历一次有效长度增长，再持续参与后续查询；对 tile 的生存期和每种有效 N×K 形状累计调用。AV 输入的序列元素 j 参与 L−j+1 个后续前缀，逐元素参与次数累计；Decode 只取最终可见状态的一次求值。由调用形状直方图的 `有效输入宽度×调用数` 求 Q_S，不使用生产 `sum_ceil_prefix`。保留 dQK=192 的128/64尾片，不能按填充宽256收取 streaming 字节，也不能删除半宽调用。

K 行追加的 `[1,k_j]`、V 列追加的 `[n_i,1]`、每 token／窗口切片次数和写入字节单独生成。最终布局按 Hkv 份状态构造，初始布局按 Prefill 0 或 Decode L−1 构造。全部 Attention result 字段，包括有效 tile 直方图、调用形状直方图、按输入宽度归类的调用数、初态容量与最终容量，均与 oracle 精确一致。

全量 `result` 递归比较覆盖 **29,122 个叶字段**，严格要求键集合相同，无忽略的新增结果字段；数值类型、整数、分数、无穷／null 同时核对。case_id 完整且唯一，模型／行／B/L 顺序与 study_plan 一致，case_id 后缀与实际 B/L 一致。以上计数是字段覆盖量，不把它解释为29,122项相互独立的数学证明。

## 重点结论与可回查数字

**两款 Qwen 的 Attention output gate 均保留。** Qwen3.5 的 Q/G 各2048×2048，G 独立贡献 ports Q_S=32768 Byte、256调用、4 MiB容量；Qwen3.6 的 Q/G 各4096×2048，G 为65536 Byte、512调用、8 MiB。两者 QKV 总 ports Q_S 分别81920／147456 Byte，总调用640／1152，预驻留容量10／18 MiB；Q_R 都是0，RI 都为∞。只看∞会掩盖漏 gate 的错误。

**Hy3 的 Q 输出宽为64×128=8192，而 hidden size 为4096。** 独立读取原始 config 和 `HYV3Attention.q_proj` 后构造 Q=8192×4096，K/V各1024×4096。结果 ports Q_S=327680 Byte，2560调用，40 MiB有效／分配容量。未强制 Q 宽等于 D，也未强制 GQA-8。

**全部 FFN／单专家的 ports RI 相同，需求量仍不同。** 所选 D、F 都整除128，三项有效 tile 求和给出 B/128，因此三档 RI 均1/16、1/2、4。六模型权重容量依次36、168、3、18、48、36 MiB。operator 保留 gate/up共享 x 和 down新 z，RI 依 D/F变化；Qwen3.5 与 MiMo 的 D/F 对调恰好给出相同汇总，但分项的方向、布局和各自输入宽度不同。未乘 top-k、总路由专家、共享专家或层数。

**Ling 的128K保留官方条件。** 原始 config 仍为 max_position_embeddings=32768、rope_scaling=null。官方 README 的 YaRN 范例是 factor=4、original_max_position_embeddings=32768、type=yarn；运行端还须通过 `--max-model-len` 设置所需131072长度。两条 Ling 128K结果及预览都明确条件，没有把未修改的原始配置说成无条件支持128K。来源：`literature/05_ling_1t/raw/README.md`第238–250行。

**MiMo 的192/128只改变有效字节与布局，不删除调用。** 第7层 global GQA 的1K Decode：ports `(Q_S,Q_R,RI)=(327680,2560,128)`，operator `(155648,2560,304/5)`。QK有2048调用，其中1024次接收128 Byte、1024次接收64 Byte；AV另1024调用，总3072。1K Prefill ports为 `(180420608,2621440,2753/40)`，operator为 `(92340224,2621440,1409/40)`，总调用1769472。最终有效KV为2621440 Byte、分配3145728 Byte、192 tiles，Decode窗口只写2560 Byte。保持每KV head一份，未把 repeat_kv 的广播变成持久复制。MiMo原生Value scale=0.612、无global sink只作为数字交接与结构条件，未添加到矩阵payload。

## 与 pilot 的逐字段比较

22 条重叠由 **2 QKV + 6 FFN + 14 Attention** 组成；比较 pilot 每条 case 的全部既有键和叶值，包括身份、revision、层、B/L、双边界Q_S/Q_R/RI/calls、tile_layout、有效／分配容量、初末KV、append切片和次数、GQA信息、前缀统计。**3,787个既有叶字段完全一致，差异列表全部为空**，详见 [checks.json](data/checks.json)。没有覆盖或重新生成 pilot。

Attention正式数据在pilot字段之外增加初始布局/容量、有效形状调用直方图、每token append信息、context条件和configuration等诊断；它们通过独立oracle或原始配置检查。统一数据另增加trace。这些是有明确含义的附加信息，不是对pilot既有字段的改写。

## 统一产物与保护检查

[results.json](data/results.json) 收录60条记录，每条保留上游原目录、results路径与SHA-256、DELIVERY revision/hash、case_id、数组索引和JSON Pointer。顺序固定为模型优先，再四行及各自B/L。JSON保留精确整数／有理数／符号无穷；没有浮点近似作为主数据。

[results.csv](data/results.csv) 有 **412条数据行+1行表头**：`(60汇总+146分项)×2边界`。30列包括身份与窗口、component/boundary、Q_S/Q_R/RI/调用、矩阵维度与copies、三项容量、operator去重、初末状态、append和来源追踪；完整直方图仍在JSON。双边界四行六模型的精确RI见 [PREVIEW.zh.md](PREVIEW.zh.md)。未另造PDF，也未重写三份中文底稿。

已运行的5项适用既有默认只读回归全部通过：

| 入口 | 结果 |
|---|---|
| `scripts/check_step1.py` | 六模型结构、50份原始来源哈希、126处本地链接通过 |
| `shared/scripts/check_counting.py` | 28项合成记录、独立分块／事件核验通过 |
| `shared/scripts/generate_IIa.py` | 10格、两个边界精确一致 |
| `table_IIb/pilot/scripts/generate.py` | 22工况及6份既有生成物一致 |
| `table_IIb/pilot/scripts/check.py` | 22独立工况、12真实head边界点、7前缀差量等通过 |

回归均设置 `PYTHONDONTWRITEBYTECODE=1`；未执行任何会重编旧PDF的build。整个仓库相对固定HEAD的tracked变更只允许主Agent负责的任务README与study_plan；原始来源、models、shared、II(a)、pilot、Task I、主论文均无tracked变化，暂存区为空。study_plan比较的是定义、模型/行顺序、B/L、选择规则、精度参考和Task I等科学输入，不依赖阶段状态整文件SHA，因此主Agent正常收尾不会使数据过期。

后续上游DELIVERY／数据变化会触发哈希失败，必须先取得新READY通知并重验。当前无数值阻塞、无共享方法修改建议；本结论限于已经声明的逻辑映射，不推定真实介质append效率、精度保持或整模型性能。
