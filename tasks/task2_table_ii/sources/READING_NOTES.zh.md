# 原始资料阅读笔记与映射界限

## 模型仓库和版本

通过发布者 Qwen 的 Hugging Face API 读取模型仓库 SHA，再以该完整 SHA 下载 config.json、README.md 与 LICENSE。两仓库的 SHA、原始配置、源文件校验和分别保存在场景配置、data/official_models.json、manifest.json。API 原始响应作为当日快照保存，其中 sha 和 safetensors.total 用于核对；下载量、点赞等动态元数据不参与计数。没有下载任何权重文件。

7B 的 intermediate_size=18944，14B 为 13824；分别有 28/48 层与 28/40 query heads。因此不能把 14B 的所有矩阵看成 7B 的统一倍数。两者 head_dim 都由 hidden_size/num_attention_heads 得到 128。模型卡和报告的 GQA heads、层数、untied embedding 与配置一致。

技术报告第 2 节讲 tokenizer 的常规 token 与控制 token；本任务 LM head 使用 config 的 vocab_size=152064，避免混淆 tokenizer 语义计数与 padded 参数矩阵行数。这不是需要修改 Task 0 的模型定义冲突。

## 固定实现中的尺寸和语义

Transformers v4.45.2 的 tag object 为 `cba5c4a6fcd0f6b73bf591505337ccf08ded3550`，解引用 commit 为 `53fad641cfdb5105e2470bcf3ef17ea8e25cc300`；保存的源码来自后者。模型配置中的 transformers_version 字段仍保留原值，未把它冒充本任务使用的源码版本。

- `Qwen2MLP`（265–276）：两个 hidden→intermediate Linear、一个 intermediate→hidden Linear，三个 bias=False；SiLU 应用于 gate，再与 up 输出逐元素乘。
- `Qwen2Attention`（309–327）：d=h/Hq；Q/K/V 为有 bias 的独立投影；O 无 bias。349–357 的 reshape 区分 query 与 KV heads。
- 365–370：先把新增 K/V 放进 cache，再 repeat_kv；repeat_kv 280–289 是 query-group 对应的软件展开，不是 CIM 必需复制状态。
- 372–380：先 query×keyᵀ，加入 mask，softmax 用 FP32 并转换回 query dtype，再概率×value。
- 100–116：causal mask 使用 cache_position，并保留当前 token。configuration_qwen2.py 160–161 在 use_sliding_window=False 时把实际 sliding_window 置为 None。原配置虽保留一个 sliding_window 数字，所选语义仍为 full causal。
- 1089：LM head 为 hidden→vocab_size，bias=False；两个模型 tie_word_embeddings=False。

源码可选择 eager、SDPA 或 FlashAttention 后端，配置本身没有唯一固定执行后端。本文逐可见前缀 CIM 服务由我们选择；它在数学上实现 causal attention，但不声称逐前缀调度是该 eager Python 实现的实际 GPU 执行。`verify_exports.py` 使用 AST 读原始 Linear 构造函数，独立检验目录形状。

## Attention / GQA / 融合的原始依据

Vaswani 等的式 (1) 给出两次矩阵乘，3.2.3 说明 causal 包括当前位置。Ainslie 等的 Fig. 2 与 2.2 节给出每组 query heads 共用一组 K/V。本文用 g=Hq/Hkv 将 query head 映射到唯一的 KV head；不同 batch 请求仍各自保存 KV。

FlashAttention Algorithm 1（PDF p. 5）以 K/V 块和 Q 块组织计算，维持 online softmax 的统计量并更新输出；第 3 节讨论 fusion 和 HBM IO。本表的 Q_S 是 CIM 求值接收的逻辑操作数，不是这个 HBM 层级的 IO。原文用于确认 AV 的逻辑系数输入不强制整张注意力矩阵外部物化，没有继承其 IO 公式作为本表 payload。

## CIM 原始映射依据与本文选择

ISAAC 作者稿 PDF p. 3 Fig. 1 / Sec. III 给出 resident conductance 与输入电压实现点积和矩阵乘向量；pp. 6–7 Sec. VI 的执行例子将逻辑问题分到多个 crossbar，输入的前后段送到对应多个阵列，最后做 shift-and-add / output-register 归并。

本任务只据此采用“resident 矩阵、输入分段、各接收阵列服务和必要归并”的概念。ISAAC 原文物理 row/column 方向按其输入线和输出线命名，本文 resident 统一以 n_out×n_in 表达，二者轴名不能机械对照。这里 r/c 是逻辑输出／输入维度，不从 ISAAC 的物理尺寸、cell bits 或 bit-serial 周期直接抄来。BF16、任意矩形 tile、KV append、训练 W 转置副本和临时 X 都是本文声明的参考选择；没有声称 ISAAC 实现这些场景。

## 训练原始代码链

PyTorch v2.4.1 commit `ee1b6804381c57161c477caa380a840a84167676`。Linear.cpp 96/111 行是 input @ weight.t()；derivatives.yaml 1172–1175 的 mm 梯度路由到 FunctionsManual.cpp。后者 1415–1451 给出 grad @ mat2ᵀ 与 mat1ᵀ @ grad（实数情形）。对 weight.t() 再用链式法则便得到 dX=dY W、dW=dYᵀX。

上述代码支持数学梯度关系，不支持任何默认免费 CIM 转置能力。维护 W/Wᵀ 两布局及每 microbatch 临时 Xᵀ 是本文调度；在事件中分别计末尾更新和临时建立，并用小矩阵有限差分与索引计数交叉检查。

## 资料提交策略

公开模型配置、模型卡与必要源代码保存原文，并附所下载的 Apache-2.0 / PyTorch LICENSE。论文全文及其本地提取文本统一放在默认忽略的 `local-only/`，不依赖其是否可以再次公开分发；可提交的 manifest、上述阅读笔记和推导包含完整可引用定位。所有计数复现仅需已保留的配置与代码；全文可按固定 URL 另外恢复。
