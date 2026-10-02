# Table II：共同记号、计数与显示约定

2026-10-02：按用户审阅意见，由主 Agent 亲自统一 II(a)/II(b) 的复用记号、扫描与小数显示。本轮原位更新，没有新增归档或版本目录。已有三稿的结构提取与公式保持，模型原件、Task I 和主论文保持不动。

## 1. 共同输入

相对任务根 `tasks/task2_table_II_workloads/`：

- `table_IIa/tex/table_IIa.tex`、`table_IIa/data/config.json`：前置中文数学讨论。
- `data/models.json`、`data/sources.json`、六模型的固定原始配置/实现和结构卡。
- `table_IIb/04_crosscheck/data/conventions.json`：当前扫描、精确数据接口；`data/model_inputs.json`：原生参数提要（相对本目录）。
- `scripts/format_results.py`：只负责数量后缀与小数显示，不参与需求计算。

## 2. 统一记号和边界

**U 为复用次数（reuse count）：一份权重完整装载后累计服务的输入向量数，包含首次使用。** 可跨多个 batch 或请求累计，不等于 batch size、批次数或序列长度。一般投影将这些向量按行记为 X[U,K]，W[N,K]，Y=XWᵀ[U,N]；这不是一次执行的排程要求。N 为输出维，K 为输入维；D 为隐藏维，F 为 FFN／单专家中间宽度。

全部计量角色取 1 Byte/element。矩阵阶段入口处，同阶段并行分支的共同源输入只计一次；后续阶段的新输入另计。当前输出不直接加进 Q_S。Q_R 是窗口内实际新增/装载状态的累计有效字节，初末有效容量分别保留。无需硬件分块、接收端重复、分配容量或求值调用数；原生头维 128/192 等不变。

U→∞ 是固定一次装载的无界复用极限：Q_S 与 RI 无界增长，Q_R 仍为有限权重大小。它不是无限 batch 或一个零写入的有限窗口。

## 3. 固定场景与公式

| 对象 | 当前扫描 | 公式与窗口 |
|---|---|---|
| II(a) 五种矩阵 | U=1、128、1K、16K、128K、1M、∞ | Q_S=UK，Q_R=NK，RI=U/N |
| QKV 六模型 | U=1、1K、128K、1M、∞ | Q_S=UD，Q_R=D N_proj，RI=U/N_proj；Q、可选 G、K、V 完整装载一次，不含 O 投影 |
| FFN／单专家六模型 | U=1、16、128、1K、16K | Q_S=U(D+F)，Q_R=3DF，RI=U(D+F)/(3DF)；gate/up/down 各装载一次 |
| Attention Prefill | L=1K、8K、64K | Q_S=H_q[L d_QK+L(L+1)/2]，Q_R=L H_kv(d_QK+d_V) |
| Attention Decode | L=1K、8K、64K | Q_S=H_q(d_QK+L)，Q_R=H_kv(d_QK+d_V) |

数量后缀 **1K=1024、1M=1024²**，机器配置保存原始整数。直立 K/M 后缀与斜体矩阵输入维度 K 区分。

QKV：N_proj=H_q d_QK+D_g+H_kv(d_QK+d_V)。各分项独立输入均为 UD，汇总扣除 (m−1)UD。

FFN：gate/up 为 F×D，down 为 D×F。X[U,D]，Z=SiLU(XW_gᵀ)⊙(XW_uᵀ)，Y=ZW_dᵀ。分项输入 UD、UD、UF，汇总扣除 UD。不乘 top-k、专家总数、共享专家或层数。实际替换策略影响 U；不能只凭专家大小断言实际替换频率。

Attention：g=H_q/H_kv，每 KV head 一份唯一 K/V。有效前缀 i 的 K 为 i×d_QK，V 为 d_V×i；streaming 输入为每 query head 的 d_QK 维 query 和 i 维 AV 系数。历史 K/V 是 resident 操作数，不重复计入 Q_S。Prefill 的三角和来自有效系数 1+…+L；每个 token 的 KV 只新增一次，总写入是 L 份新状态，不是所有历史前缀重复写入。Decode 从 L−1 追加一份后对 L 求值。MiMo 原生 192/128；Ling 的 64K 沿用先前固定的官方扩展配置。

II(a) 为30个有限工况、5个极限格。II(b) 为90个有限工况、6个极限格、262条组件记录；QKV24+6、FFN30、Attention36。归档仅作独立回归，不增加主表场景。

## 4. 精确计算与显示

主计数用 Python 整数和 Fraction，不依赖权重下载或模型执行。JSON/CSV 保留原始 Byte、精确 RI 和符号 infinity。PDF/Markdown 的 RI≥1 保留一位小数；0<RI<1 保留三位有效数字，使用普通小数形式。显示用 Decimal、ROUND_HALF_UP，不能把显示值回写精确字段。

主生成器可直接按原生维度使用闭式。独立检查从原始配置重新读尺寸，按矩阵行、源输入身份或有效前缀累计；不能调用主生成器作为唯一预期值。大范围只保存计数/区间，不生成大矩阵或海量事件。

## 5. 统一文件和正文

三个分类目录统一为 `README.md`、`PREVIEW.zh.md`、`DELIVERY.json`；`data/{config,results,checks,pdf_qa}.json`、`data/results.csv`；`tex/report.zh.tex`、两份 `*.generated.tex`；`output/report.zh.pdf`；`scripts/{generate.py,check.py,build.sh,render.py}`。第四目录管理共同约定、合并与复核。

正文四节：**对象与公式 → 模型信息 → 代入结果 → 结果说明**。统一引用 `template/preamble.tex`；模型/结果表用全宽 tabularx，首列 p{0.32\linewidth}，其余列居中。模型表用 ModelTableSetup，结果表用 ResultTableSetup；结果单元格为小数，不再显示精确分数。来源/版本/检查细节放 README 和机器数据，不在正文机械展开六遍。

默认 generate/check 只读比较，--emit 才刷新。所有 PDF 编译后渲染、逐页查看，随后更新 QA 和 DELIVERY。主 Agent 本轮亲自修改并验证；内部通过不代表用户已审阅通过。不执行 Git 暂存、提交、推送、重置或切分支。
