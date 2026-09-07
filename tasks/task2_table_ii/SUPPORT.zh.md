# Table II：窗口化 CIM 操作数需求

## 1. 问题、范围与读法

本表回答给定 LLM 矩阵算子、窗口与驻留映射以后，CIM 边界实际需要接收多少 streaming 输入、写入多少 resident 状态。沿用已授权的 Task 0 基线 `6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`。约定文档中的 candidate 字样未由本任务修改。

三层证据分开：官方配置和实现给出张量；本文选择服务边界、驻留角色及调度；脚本按事件计算 payload。ISAAC 提供 resident 矩阵乘向量和输入分段／结果归并的原始依据，本文的 Qwen 映射、任意 r×c tile、BF16 口径及训练副本策略都是分析选择。没有采用硬件速率或器件基线。

主表使用 `logical_operator`。S1–S5 是一个投影矩阵，S6–S7 是一层 attention 的 QK 与 AV 需求之和；S8–S9 是单 microbatch 的梯度组件；S10 是同一线性层一次参数更新周期。各行以 S ID 对应 `data/table_rows.json`，后者连接稳定的 `wl_` ID。所有数据内部以 Byte、OP、有理数保存，RI 的静态分支记录为 `{"status":"infinite"}`。表格以 MiB 显示，必要时按四位小数 ROUND_HALF_UP；RI 用精确分数或可精确表示的短小数。

本轮覆盖 GEMM 内的有用乘加，1 MAC=2 OP。Embedding lookup、bias 加法、SiLU／门控逐元素乘法、Softmax／缩放、RoPE、RMSNorm、残差、优化器计算及状态访问、通信、检查点重计算等在此矩阵服务范围外。它们没有被认定为零代价。注意力概率输入采用 BF16；官方 eager 实现的 softmax 内部提升到 FP32 再转回 query dtype，内部数值处理不另计作当前 CIM streaming payload。训练梯度和临时激活采用本文选定的 BF16 逻辑格式，不是官方训练精度配置，也不验证训练或量化精度。

## 2. 模型结构与证据（D1）

官方原始字节文件在 `configs/qwen7B_config.json`、`configs/qwen14B_config.json`，模型卡在 `sources/official/`。`data/official_models.json` 同时保存完整配置结构和固定 revision。模型参数不是由“7B/14B”名称推算。

| 字段 | Qwen2.5-7B | Qwen2.5-14B |
|---|---:|---:|
| revision | d149729398750b98c0af14eb82c78cfe92750796 | 97e1e76335b7017d8f67c08a19d103c0504298c9 |
| hidden_size h | 3584 | 5120 |
| intermediate_size f | 18944 | 13824 |
| decoder layers | 28 | 48 |
| H_q / H_kv | 28 / 4 | 40 / 8 |
| d=h/H_q | 128 | 128 |
| vocab_size（参数矩阵行数）| 152064 | 152064 |
| tie_word_embeddings | false | false |
| hidden_act / MLP | silu / SwiGLU | silu / SwiGLU |
| serialized torch_dtype | bfloat16 | bfloat16 |
| use_sliding_window / attention_dropout | false / 0 | false / 0 |
| 配置内 transformers_version（元数据）| 4.40.1 | 4.43.1 |

来源：`t2_qwen7b_config`、`t2_qwen14b_config`；技术报告 `t2_qwen_report` 第 2 节和表 1。报告讨论 tokenizer 的常规 token 数；线性层/embedding 的实际参数矩阵取配置 vocab_size=152064。二者描述对象不同，不据报告的 tokenizer 数缩减 LM head。

固定核查实现为 Transformers v4.45.2，源码 commit `53fad641cfdb5105e2470bcf3ef17ea8e25cc300`。发布标签是 annotated tag，记录的是解引用后的 commit，不把 tag object 当源码 commit。`modeling_qwen2.py` 309–327 行给出 head_dim 及 Q/K/V/O；265–276 行为 `down(silu(gate(x))*up(x))`；1089 行定义独立 LM head。Q/K/V 有 bias，O、gate/up/down、LM head 无 bias。配置元数据版本与本任务固定核查代码版本分别保存。

令 k=H_kv d，resident 统一表示为 n_out×n_in：

| 算子 | resident 形状 | 7B | 14B |
|---|---|---|---|
| Q / O | h×h | 3584×3584 | 5120×5120 |
| K / V | k×h | 512×3584 | 1024×5120 |
| gate / up | f×h | 18944×3584 | 13824×5120 |
| down | h×f | 3584×18944 | 5120×13824 |
| LM head | vocab_size×h | 152064×3584 | 152064×5120 |

目录 `data/operator_catalog.json` 逐项分开，记录层实例次数、bias 和来源。Embedding 虽有 vocab_size×h 参数表，其 lookup 没有按稠密 GEMM 计数；输出 head 若选择 prefill 全 token logits，其 U=B L，若只要末 token logits则须改 U，数据明确选前一种目录场景。这里没有把目录中所有可选工作相加为一个“模型唯一需求”。

源码 AST 解析独立核对所有 Linear 构造函数的输入／输出参数与 bias；再将目录矩阵、bias、embedding 和 RMSNorm 参数相加，与官方仓库元数据中的总参数数核对，结果见 `output/export_audit.json`。无需下载权重。

## 3. 通用线性求值与窗口（D2）

采用 Y=X Wᵀ，X∈R^(U×n)，W∈R^(m×n)，Y∈R^(U×m)。这里 m=n_out、n=n_in，U 是窗口内由同一矩阵状态服务的向量数。独立 projection 每次各自接收 X；不能在各投影相加时又只算一份 X。

事件 G1_LO：写入 m n 个 W 元素一次；对 u=1…U 接收 n 个 X 元素；完成 U m n 次有效 MAC。

\[
Q_S=Unb_S,\quad Q_R=mnb_R,\quad M=2Umn,\quad RI=\frac{Ub_S}{mb_R}.
\]

G0_LO：初始 W 已驻留，窗口结束 W 不变，因此 Q_R=0、Q_S>0、RI=∞，但完整驻留容量仍为 mn b_R。初始装载排除有明确的窗口依据。

G2_LO：E 次实际 placement，epoch e 服务 U_e 个向量，ΣU_e=U。每个 epoch 结束后为执行其他算子而逐出当前矩阵，下个 epoch 重装。于是 Q_R=E mn b_R，Q_S=Unb_S，RI=Ub_S/(E m b_R)。默认例子是 2048 个向量分成四组 512；装载一次加三次重载，共四次实际写入。它是具体调度策略，不是所有 prefill 的必然行为。

Decode 线性投影每请求本轮处理一个 token，U=B；prefill 处理 N 个新 token，U=BN。这只定义向量工作量，是否装载权重另由 G0/G1/G2 决定。batch 的请求共享模型 W，因此从 B=1 到 B=8 不要求重写八份 W。完整重复同一含装载的工作模式 k 次时，Q_S、Q_R 和 M 均乘 k，RI 不变；仅扩大 U 并保持一份 resident 则提高 RI。这是两种不同窗口。

精度保持独立：b_S、b_R、b_Q、b_K、b_V、b_A、b_X、b_dY 各按角色定义。主场景均为 BF16/2 Byte。支撑数据固定 INT8 输入，比较 INT8 与 INT4 权重：仅将 b_R 从 1 变成 1/2，Q_R 减半、Q_S 和 M 不变、RI 加倍。`Fraction` 保留例如 3 个 INT4 元素=3/2 Byte；物理打包、位切片及 padding 不在此处冒充有效 payload。BF16 与 INT16 不因字节相同而兼容。

融合对照 F1_LO 将 Q/K/V（或 gate/up）按输出行拼成一个 resident 矩阵，一次接收 X。这时 Q_R、M 等于各矩阵之和，Q_S 则分别是独立投影总输入的 1/3 或 1/2。输入共享发生在扩大后的服务边界内。这是有不同容量、输出要求的另一映射；主表始终使用独立投影。

## 4. 从 logical_operator 到 tile_port（D2）

tile 的逻辑输出行为 r，输入列为 c，二者为任意正整数。设输出分块有效行数 m_i=min(r,m−ir)，输入分块有效列数 n_j=min(c,n−jc)。主遍历在每个 epoch 内按输出块 i、输入块 j 顺序，装入 W_ij 后服务该 epoch 的全部 U_e 个对应输入片段，再产生部分和并进入下一 tile。G1_TP 可用一个临时 tile 与外部输入／部分和工作区；G0_TP 必须已保留所有 tile。不能以一个 tile 容量声称整个静态矩阵都已驻留。

\[
Q_R^{TP}=E\sum_{i,j}m_i n_j b_R=E mn b_R,
\quad Q_S^{TP}=\sum_{e,i,j}U_e n_jb_S
=\lceil m/r\rceil Unb_S,
\quad M^{TP}=2Umn.
\]

每个有效权重在每次 placement 中恰好写一次。输入列划分的 Σ_j n_j=n，只是把输入切段；输出分块的每个接收端各需一份，故乘 ceil(m/r)。**不再无条件乘 ceil(n/c)。** n/c 影响端口分段调用数、部分和归并和利用率，r 则直接改变 streaming 接收累计量。

边界 tile 只传有效元素，无效槽由内部生成零或禁用。全矩阵的固定槽数为 ceil(m/r)ceil(n/c)rc；这是逻辑槽容量，不是有效 payload，也不是物理 cell 数。若硬件要求外部补零、整块改写、不同重放或不能归并部分和，Task 3 必须实例化不同事件。对于不丢弃部分结果的顺序映射，最多需要 U m 个外部累加元素；容量与格式由后续实现决定，其处理成本属于完整输出服务条件。

独立枚举使用 m=5、n=7、U=3、r=3、c=4：35 个不同权重索引各写一次；每个 (u,k) 输入索引恰好在两个输出块接收；固定槽为 48，13 个无效槽不增加有效写入。INT8 输入／INT4 resident 的精确结果与全部索引列表在 `data/independent_enumeration.json`。

## 5. Attention：因果前缀、GQA 与 KV append（D3）

记 B 为请求数，H_q 为 query heads，H_kv 为 KV heads，g=H_q/H_kv，d 为 head dimension。每请求开始已有 C 个历史 KV，本窗口新增 N 个 token。第 j 个新 token 的**append 后**可见长度 t_j=C+j（j=1…N），包括它自己；最终长度 L_v=C+N。主 decode 场景是 N=1、C=L_v−1，L_v 取 2048 或 8192；prefill 从空 KV 开始，C=0、N 取 2048 或 8192。所有请求具有相同声明长度且没有 padding。

`t2_attention` 式 (1) 定义 softmax(QKᵀ/√d)V，第 3.2.3 节说明 causal 包括当前位置；`t2_gqa` 第 2.2 节／图 2 定义组内共享 K/V。对应官方代码先 reshape、RoPE、cache update，再 repeat_kv 和两个 matmul。repeat_kv 的软件扩展不强制本文维护 H_q 份 KV。主映射每 KV head 维护一份 K 和一份 Vᵀ：K 的 resident 方向是 t_j×d，Vᵀ 是 d×t_j，后者写入新增列。这里两份指两种不同张量，不是把同一 K 或 V 再复制两遍。

令 D 为每种 KV 布局的额外驻留副本数，主参考 D=1。存在副本时把组内 query 工作分配到这些副本，不重复计算 query，因此写入、容量乘 D，Q_S 与 M 不乘 D。脚本接受 1≤D≤g；不同副本可服务不等数量 query heads。组内共享可串行调度，不假定获得并行吞吐。

### 5.1 QKᵀ 单独求值

对每个请求、每个 query head 和新 token j，streaming 是长度 d 的 q_j，resident 是所属 KV head 的 K_≤t_j（t_j×d）。输出是 t_j 个分数，组内 g 个 query heads使用同一当前 resident 前缀。

\[
Q_{S,QK}=BH_qNd b_Q,\quad
Q_{R,K}=BH_{kv}DNdb_K,\quad
M_{QK}=2BH_qd\sum_{j=1}^N t_j.
\]

写入只涵盖新增 K；decode 旧历史在初始状态中已明确驻留。K 已包含 RoPE 变换；RoPE 计算在边界外。

### 5.2 AV 单独求值

streaming 是第 j 行有效概率 a_j（长度 t_j），resident 是所属 KV head 的 Vᵀ（d×t_j），输出 d 维加权结果。

\[
Q_{S,AV}=BH_q b_A\sum_{j=1}^N t_j,\quad
Q_{R,V}=BH_{kv}DNdb_V,\quad
M_{AV}=2BH_qd\sum_{j=1}^N t_j.
\]

概率在进入 AV 时计一次。QK 输出不另加一笔 Q_S；AV 输出也不加入本次 Q_S。实现需要得到全前缀归一化概率，但可只保留一行概率或采用专门融合策略；这里的逻辑输入需求没有要求完整 N×L_v 注意力矩阵在外部 DRAM 物化。

### 5.3 汇总与精确因果求和

\[
T=\sum_{j=1}^N(C+j)=NC+\frac{N(N+1)}2,
\]
\[
Q_S=BH_q(Nd b_Q+Tb_A),\quad
Q_R=BH_{kv}DN d(b_K+b_V),\quad
M=4BH_qdT.
\]

这是两个组件的需求汇总，RI 从合计 Q_S/Q_R 重新计算；不对 head 或组件 RI 做算术平均。完整结束 KV 容量为 BH_kv D L_v d(b_K+b_V)，对 decode 常常远大于新增写入量。

同为 2 Byte 时：

\[
RI^{LO}=\frac{g}{2D}\left[1+\frac{C+(N+1)/2}{d}\right].
\]

Prefill 空历史精确使用 N(N+1)/2，不替换为 N²/2。Decode N=1 则使用 L_v=C+1，RI=g(d+L_v)/(2Dd)。B 同时乘输入与每会话私有 KV 写入，所以在该等长窗口中消去；H_q 控制 query／概率输入与有效运算，H_kv 控制 KV 写入和容量。其关系不同于 batch 共享模型权重。

### 5.4 Attention 的 tile 方向

固定 tile 坐标，历史 tile 保留，新 token 仅更新新增 K 行与 Vᵀ 列，即使它们落在已有的边界 tile 内，也不重写整块。每个 j 完成 QK、归一化和 AV 后才进入下一个前缀。

K 的输出行是可见 token 轴，输入列是 d 轴，故每个 query 需要 d ceil(t_j/r) 个输入元素；Vᵀ 的输出行是 d 轴，输入列是可见 token 轴，每行概率需要 t_j ceil(d/r) 个输入元素。

\[
Q_S^{TP}=BH_q\left[d b_Q\sum_{j=1}^{N}\lceil(C+j)/r\rceil
+ b_A\lceil d/r\rceil T\right].
\]

有效 Q_R 与 M 在无重载／无额外副本时保持不变。c 的分段不是额外输入元素倍数：QK 分段调用数为 BH_q ceil(d/c)Σceil(t_j/r)，AV 为 BH_q ceil(d/r)Σceil(t_j/c)。两方向的固定槽总数分别按最终 L_v×d、d×L_v 计算，已写入容量字段。全部 KV tile 须容纳；若容量不足并重载，必须新增写入事件。

用于快速精确实例化，若 x=kr+s，0≤s<r，则 F(x)=Σ_(t=1)^x ceil(t/r)=r k(k+1)/2+s(k+1)；窗口和为 F(C+N)−F(C)。独立枚举没有调用该公式，而是逐请求、head、token、矩阵索引和接收 tile 遍历。r、c 参数通过 `generate.py --tile R C` 输入；128×128、192×160 只是随数据提供的例子。

### 5.5 有效三角项与其他执行形式

主参考逐前缀服务，因此执行 MAC 就是有效三角 MAC，外部不发送被 mask 项或无效 padding。对照“先完整矩形、后 mask”：每个 query 对全部 L_v 个 K 求值，AV 再接收 L_v 个概率（未来项为外部发送的零）。其 QK 的逻辑 query 元素仍是 Nd，但 AV 是 NL_v；执行矩阵 OP 为 4BH_qdNL_v，有用 OP 仍是 4BH_qdT；tile 版还会使 QK 接收端数量按 L_v 增加。若零由内部生成并跳过对应服务，它又是不同映射。

`t2_flashattention` 第 3 节／Algorithm 1 的分块在线 softmax 和 kernel fusion另有重放与部分结果更新顺序。本文只用原文支持“无需外部物化整个注意力矩阵”和区分 IO 边界，没有将其 HBM 访问公式套给本表。保留 QK、AV 分项是后续能力配对的必要接口。

## 6. 线性层训练及一次更新周期（D4）

令 X∈R^(U×n)、W∈R^(m×n)、dY∈R^(U×m)。由 PyTorch 固定版本 Linear.cpp 的 XWᵀ，以及 `derivatives.yaml` 的 mm 梯度路由、`FunctionsManual.cpp` 1415–1451 行的两个矩阵梯度，按链式法则得到：

\[
Y=XW^T,\qquad dX=dY W,\qquad dW=dY^T X.
\]

三者输出依次为 U×m、U×n、m×n；每一项 M=2Umn。测试另对一个标量损失 ⟨XWᵀ,dY⟩ 中每个 X、W 元素做中心有限差分，不以再次抄写公式充当独立核对。

| 组件 | resident (n_out×n_in) | streaming（向量次数×长度）| 本组件 Q_R | Q_S（LO）|
|---|---|---|---|---|
| forward | W: m×n | X: U×n | 0（预驻留）| Un b_X |
| dX | Wᵀ: n×m | dY: U×m | 0（预驻留转置布局）| Um b_dY |
| dW 主映射 | Xᵀ: n×U | dYᵀ: m×U | Un b_X | Um b_dY |
| dW 对照 | dYᵀ: m×U | Xᵀ: n×U | Um b_dY | Un b_X |

主映射中 n_out=n、n_in=U，向量次数是 m，服务输出恰为 dW（m×n）；对照输出为 dWᵀ（n×m），归置转回 dW 在声明的输出处理范围内。两种角色分配给出相同有用 M，但 resident 规模和 streaming payload 不同。对照没有进入主周期汇总。

转置能力不默认免费：T1 明确维护 W、Wᵀ 两套布局，每套权重数均为 mn；每周期末两套各写一次新参数。若目标硬件允许同一 W 的反向求值，可另计单布局更新；若必须在 dX 前重装 Wᵀ，则应按每次发生时间新增写入。主参考没有把这些方案混在一起。

### 6.1 窗口首尾和事件顺序

开始：W 与 Wᵀ 已包含本次更新前的参数；临时区可覆盖，外部梯度累加器已初始化。对 microbatch a=1…A：

1. forward 用当前 W 服务 X_a。
2. dX 用 Wᵀ 服务 dY_a。
3. 向临时区写入 X_aᵀ，服务 dY_aᵀ 求 dW_a。
4. 将 dW_a 在边界外累加为本次参数更新的梯度；不把 dW 输出再计一份输入或 resident 写入。
5. 第 A 个 microbatch 完成后，在边界外生成新参数，并分别更新 W、Wᵀ 各一次。临时 X 可丢弃；窗口结束的两套权重正是下一周期的初始 resident。

因此不是“每次训练 forward 都更新参数”，也不是“初始装载加末尾更新同时重复收取”。冷启动若把两套 W 装载纳入窗口，可另外加 2mn b_W；本表的重复更新周期排除了该窗口外初始装载。

\[
Q_{S,cycle}^{LO}=A U(n b_X+2m b_{dY}),
\quad Q_{R,cycle}=AUnb_X+2mnb_W,
\quad M_{cycle}=6AUmn.
\]

临时 X 写入随 A 增长；权重更新次数每周期保持两次，故每 microbatch 的更新写入摊销为 2mn b_W/A。相同总 microbatch 工作比较时，A=16 的一次周期只更新两套权重一次，而 16 个 A=1 周期会更新 16 次，后者不是同样的参数更新语义。主场景 microbatch B=1、L=2048，U=2048，A=1、16；这些是分析场景，不是官方训练设置。

tile 版本分别应用真实 resident 方向：forward 输入乘 ceil(m/r)，dX 与主映射 dW 输入乘 ceil(n/r)。所以

\[
Q_{S,cycle}^{TP}=A U[n b_X\lceil m/r\rceil+2m b_{dY}\lceil n/r\rceil].
\]

两套权重的全部 tile 保留，临时 X 可逐 tile 装入并服务；Q_R 仍按有效写入事件累计。模型权重区加完整临时状态的 LO 容量为 2mn b_W+Un b_X。TP 最小驻留容量可将临时 X 改为一个有效 tile；外部输入、梯度累加器、优化器空间另需安排。周期组件使用不同 resident 和输入维度，Q_S/Q_R 汇总用于描述需求，不宣称存在一个已校准的统一训练 ρ。

## 7. 每一主表行的实际代入

以下内容由 `scripts/generate.py` 从同一事件记录插入，独立副本也在 `data/table_substitutions.zh.md`。S3 配对值顺序为 7B/14B；S10 为 A=1/16。

<!-- BEGIN GENERATED SUBSTITUTIONS -->

### S1
- `wl_7b_k_decode_b1_static_lo`；映射 `G0_LO`。
- 窗口：`{"B": 1, "tokens_per_request": 1, "U": 1, "model_weight_shared_across_batch": true}`。
- Q_R = 0；Q_S = 7168；M = 3670016 OP；RI = ∞。
- 写入／输入事件：
  - /X：stream_input，形状 [3584]，次数 1，3584 元素 × 2 Byte = 7168 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。

### S2
- `wl_7b_k_decode_b1_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 1, "tokens_per_request": 1, "U": 1, "model_weight_shared_across_batch": true}`。
- Q_R = 3670016；Q_S = 7168；M = 3670016 OP；RI = 1/512。
- 写入／输入事件：
  - /W：resident_write，形状 [512, 3584]，次数 1，1835008 元素 × 2 Byte = 3670016 Byte。
  - /X：stream_input，形状 [3584]，次数 1，3584 元素 × 2 Byte = 7168 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。

### S3
- `wl_7b_k_decode_b8_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 8, "tokens_per_request": 1, "U": 8, "model_weight_shared_across_batch": true}`。
- Q_R = 3670016；Q_S = 57344；M = 29360128 OP；RI = 1/64。
- 写入／输入事件：
  - /W：resident_write，形状 [512, 3584]，次数 1，1835008 元素 × 2 Byte = 3670016 Byte。
  - /X：stream_input，形状 [3584]，次数 8，28672 元素 × 2 Byte = 57344 Byte。
- 完整 resident 容量：3670016 Byte；详见该记录的 capacity 和 components。
- `wl_14b_k_decode_b8_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 8, "tokens_per_request": 1, "U": 8, "model_weight_shared_across_batch": true}`。
- Q_R = 10485760；Q_S = 81920；M = 83886080 OP；RI = 1/128。
- 写入／输入事件：
  - /W：resident_write，形状 [1024, 5120]，次数 1，5242880 元素 × 2 Byte = 10485760 Byte。
  - /X：stream_input，形状 [5120]，次数 8，40960 元素 × 2 Byte = 81920 Byte。
- 完整 resident 容量：10485760 Byte；详见该记录的 capacity 和 components。

### S4
- `wl_7b_gate_prefill_b1_l2048_load_lo`；映射 `G1_LO`。
- 窗口：`{"B": 1, "N_new": 2048, "U": 2048, "lm_head_policy": "all processed tokens if this operator is selected"}`。
- Q_R = 135790592；Q_S = 14680064；M = 278099132416 OP；RI = 4/37。
- 写入／输入事件：
  - /W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - /X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

### S5
- `wl_7b_gate_reload_b1_l2048_e4_lo`；映射 `G2_LO`。
- 窗口：`{"B": 1, "U": 2048, "epoch_vectors": [512, 512, 512, 512], "eviction_cause": "evict this operator between token chunks to schedule other operators in a shared resident region"}`。
- Q_R = 543162368；Q_S = 14680064；M = 278099132416 OP；RI = 1/37。
- 写入／输入事件：
  - /W：resident_write，形状 [18944, 3584]，次数 4，271581184 元素 × 2 Byte = 543162368 Byte。
  - /X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

### S6
- `wl_7b_attn_prefill_b1_l2048_lo`；映射 `A1_LO`。
- 窗口：`{"B": 1, "C_before_append": 0, "N_new": 2048, "L_visible_final": 2048, "layer_instances": 1}`。
- Q_R = 4194304；Q_S = 132177920；M = 30079451136 OP；RI = 16135/512。
- 写入／输入事件：
  - /K：resident_write，形状 [2048, 128]，次数 4，1048576 元素 × 2 Byte = 2097152 Byte。
  - /query：stream_input，形状 [128]，次数 57344，7340032 元素 × 2 Byte = 14680064 Byte。
  - /V_transposed：resident_write，形状 [128, 2048]，次数 4，1048576 元素 × 2 Byte = 2097152 Byte。
  - /attention_probability：stream_input，形状 ['C+j']，次数 57344，58748928 元素 × 2 Byte = 117497856 Byte。
- 完整 resident 容量：4194304 Byte；详见该记录的 capacity 和 components。

### S7
- `wl_7b_attn_decode_b8_v8192_lo`；映射 `A1_LO`。
- 窗口：`{"B": 8, "C_before_append": 8191, "N_new": 1, "L_visible_final": 8192, "layer_instances": 1}`。
- Q_R = 16384；Q_S = 3727360；M = 939524096 OP；RI = 455/2。
- 写入／输入事件：
  - /K：resident_write，形状 [1, 128]，次数 32，4096 元素 × 2 Byte = 8192 Byte。
  - /query：stream_input，形状 [128]，次数 224，28672 元素 × 2 Byte = 57344 Byte。
  - /V_transposed：resident_write，形状 [128, 1]，次数 32，4096 元素 × 2 Byte = 8192 Byte。
  - /attention_probability：stream_input，形状 ['C+j']，次数 224，1835008 元素 × 2 Byte = 3670016 Byte。
- 完整 resident 容量：134217728 Byte；详见该记录的 capacity 和 components。

### S8
- `wl_7b_train_gate_u2048_a1_lo_dx`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 0；Q_S = 77594624；M = 278099132416 OP；RI = ∞。
- 写入／输入事件：
  - /dY：stream_input，形状 [18944]，次数 2048，38797312 元素 × 2 Byte = 77594624 Byte。
- 完整 resident 容量：135790592 Byte；详见该记录的 capacity 和 components。

### S9
- `wl_7b_train_gate_u2048_a1_lo_dw`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 14680064；Q_S = 77594624；M = 278099132416 OP；RI = 37/7。
- 写入／输入事件：
  - /X_transposed：resident_write，形状 [3584, 2048]，次数 1，7340032 元素 × 2 Byte = 14680064 Byte。
  - /dY_transposed：stream_input，形状 [2048]，次数 18944，38797312 元素 × 2 Byte = 77594624 Byte。
- 完整 resident 容量：14680064 Byte；详见该记录的 capacity 和 components。

### S10
- `wl_7b_train_gate_u2048_a1_lo`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 1, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 286261248；Q_S = 169869312；M = 834297397248 OP；RI = 54/91。
- 写入／输入事件：
  - forward/X：stream_input，形状 [3584]，次数 2048，7340032 元素 × 2 Byte = 14680064 Byte。
  - dX/dY：stream_input，形状 [18944]，次数 2048，38797312 元素 × 2 Byte = 77594624 Byte。
  - dW/X_transposed：resident_write，形状 [3584, 2048]，次数 1，7340032 元素 × 2 Byte = 14680064 Byte。
  - dW/dY_transposed：stream_input，形状 [2048]，次数 18944，38797312 元素 × 2 Byte = 77594624 Byte。
  - end_update/W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - end_update/W_transposed：resident_write，形状 [3584, 18944]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
- 完整 resident 容量：286261248 Byte；详见该记录的 capacity 和 components。
- `wl_7b_train_gate_u2048_a16_lo`；映射 `T1_LO`。
- 窗口：`{"microbatch_B": 1, "tokens": 2048, "U_per_microbatch": 2048, "A": 16, "parameter_updates": 1, "component_counts": "each child GEMM is one microbatch; parent events multiply by A"}`。
- Q_R = 506462208；Q_S = 2717908992；M = 13348758355968 OP；RI = 864/161。
- 写入／输入事件：
  - forward/X：stream_input，形状 [3584]，次数 32768，117440512 元素 × 2 Byte = 234881024 Byte。
  - dX/dY：stream_input，形状 [18944]，次数 32768，620756992 元素 × 2 Byte = 1241513984 Byte。
  - dW/X_transposed：resident_write，形状 [3584, 2048]，次数 16，117440512 元素 × 2 Byte = 234881024 Byte。
  - dW/dY_transposed：stream_input，形状 [2048]，次数 303104，620756992 元素 × 2 Byte = 1241513984 Byte。
  - end_update/W：resident_write，形状 [18944, 3584]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
  - end_update/W_transposed：resident_write，形状 [3584, 18944]，次数 1，67895296 元素 × 2 Byte = 135790592 Byte。
- 完整 resident 容量：286261248 Byte；详见该记录的 capacity 和 components。

<!-- END GENERATED SUBSTITUTIONS -->

## 8. 参数变化与可解释观察

S1、S2 的矩阵与输入相同，改变的只是窗口内是否建立 W；静态分支不意味着所需容量为零。S2、S3 显示同一份 W 服务更多 batch 向量如何增加输入复用。S4 的真实 gate 是强矩形；它与 K 投影的 n_out 不同，即便 U 相同也不会自动有相同 RI。S5 固定有效算子工作及总 U，四次 placement 增加 Q_R，RI 是单次 placement 的四分之一。

7B 与 14B 的中间宽度 f 并不随模型名称单调增加；实际层数、hidden width 和 heads 也变化。完整目录及总参数核对比名称近似可靠。7B 主 attention 的 g=7，14B 的 g=5，写入按 H_kv 而求值按 H_q 增长。主 batch 等长 attention 汇总的 RI 与 B 无关，但两个 payload 和 KV 容量都乘 B。

Prefill 中概率系数的有效输入是精确三角和；decode 只写一个新增 K/V，却接收全部可见概率前缀。tile 的 K 输出分割随上下文跨 r 的边界递增，Vᵀ 的输出分割取决于 d；两者的输入重复不能都用一个历史 RI≈L/(2d) 替代。`data/parameter_comparisons.md` 由脚本显示 LO 与两种 tile、两模型、2048/8192、非对称精度及副本的精确值。

训练 dW 使临时激活进入 resident 角色，因而单独摊销权重更新不能描述整个周期。A 增大降低每个 microbatch 的权重更新写入，但仍持续发生临时激活写入。对照 dW 角色交换保留相同 M，却改变 Q_S、Q_R，体现边界和角色对 RI 的决定作用。

## 9. Task 3 的配对接口

`data/task3_demands.json` 是离线需求导出，包含与 `data/demands.json` 相同的完整记录；二者通过生成脚本同步。每条保留 model/revision、工作窗口、mapping_id、boundary_kind、形状、实际格式、首尾状态、事件与精确 Q_S/Q_R/M/RI、容量及 component IDs。形状 `C+j` 配有 j 的区间与 C；attention 汇总不能替代其 QK/AV 组件。

配对时应选择一个 leaf 服务模式，或证明多个组件可以用相同能力归约后再组合。周期 parent events 已乘 A，子 GEMM 是每 microbatch；绝不同时相加 parent 与 children。形状目录 ID 以 `_shape` 结尾，是算子元数据，不是已实例化的需求。

检查真实支持的格式（尤其 BF16 与整数格式）、logical 输入／写入边界、逻辑 r/c 与位切片之间的转换、固定槽利用率、所需全容量／副本、K 行与 V 列 append 粒度、静态权重保留、临时区调度、完整精度输出与部分和归并、输入重放与实际重载。若任何前提不成立，先修改映射参数和事件重算，再匹配服务能力。总模型唯一字节数不与某个单 macro 原生速率直接相除。

## 10. 可供论文改写的说明（中文）

表 II 将 LLM 矩阵计算的需求限定在明确的工作窗口和驻留策略内。对于线性投影，同一份权重能够服务的 token 向量数决定一次装载的复用程度：预驻留且不更新时没有窗口内写入，低批次 decode 的装载则由少量向量分担；prefill 可提高复用，但调度逐出会重新引入写入。Attention 的 resident 状态是请求专属的 KV，组内 query heads 共享它们。因果 prefill 从空状态逐步建立 KV，概率输入按可见前缀精确求和；decode 只追加当前 token 的 K、V，却仍需服务整个可见上下文。训练进一步改变操作数角色：输入梯度需要所声明的转置权重布局，权重梯度可使激活成为临时 resident。梯度累积降低每个 microbatch 的参数更新频率，但没有消除临时激活写入。上述需求也随服务边界改变：逻辑矩阵内部共享的输入，在输出分块后的多个 tile 接收端须分别计数。因此，表中保留组件、精度和映射参数，以便在后续分析中按兼容的服务模式重新实例化，而不将模型结构压缩为一个脱离执行约定的固定强度。
