# ISCAS 2027 写作总纲

> 用途：供新的本地写作 Agent 恢复研究主线、建立英文论文项目并逐节写作。本文件是写作约定和版面计划，不是论文正文。
>
> 本轮只完成 **标题、英文摘要、章节骨架和图表版面原型**。Introduction 至 Conclusion 保留有内容的提纲，不一次写成全文。由当前 Agent 亲自写作，不使用 sub-agent。

## 1. 当前状态与依据

仓库：`bcacdwk/CIM_roofline`。本总纲核对的 HEAD 为 `aee989c9e2255df26fda592f4a6f6b64e1a2bedc`；本地有更新时以实际工作区为起点，不回退。

Task I、Task II 的计算和 Task III 的候选图工作均已完成并获认可。现在进入论文整合，不重新选模型、不重做硬件估算、不增加实验分支。旧文件中的“待审阅”是历史记录，不改变本次授权。

**格式按用户要求：4 页技术内容＋第 5 页纯参考文献，IEEE 双栏。** 这是论文篇幅约束；仓库提供的通用模板本身没有写出本届会议的具体页数规则。

模板入口：

- `Conference-LaTeX-template_10-17-19/conference_101719.tex`
- 同目录 `IEEEtran.cls`、`conference_101719.pdf`、`IEEEtran_HOWTO.pdf`

采用模板的 `IEEEtran` conference 模式、纸张尺寸、字体、栏宽和间距。模板明确要求标题及摘要不使用数学公式、符号或脚注；因此公式放进正文，摘要用语言说明。标题不另加副标题。作者、单位和资助暂不填写，不保留模板虚构的人名与单位。

**材料使用层次：**

- `CIM_Roofline_Paper/cim_roofline.tex`：已修订的理论工作稿，用于恢复角色分解、窗口、上界和算例。其“数值分析尚待完成”等历史状态不进入新文稿。
- 当前 Task I/II/III 的汇总、计算约定和数据：作为数值、工作负载和设计讨论的依据。
- 最早的 41 页中文 PDF/旧 TeX：用于理解研究动机与早期组织，不直接恢复其旧标定、旧适配结论和已经撤下的理论推广。

研究结论以当前已认可材料为准。若某句话找不到支持，先留写作标记，不用一般知识或旧数字补齐。

## 2. 标题、文章主张与摘要构思

### 推荐标题

**A Resident-Streaming Roofline Model for Compute-in-Memory**

中文工作译名：面向存内计算的驻留—流式 Roofline 模型。

2026-10-06 用户审阅更新：标题加入 Model，标题字号采用 19.6 pt 以单行排下；关闭英文连字。后续编译诊断已将“连字”与“自动断词”分开：fi/fl 连字保持关闭，正常断词恢复，以免双栏字间距失衡。此项覆盖前述模板字体约定中的标题字号限制。

优先采用这一标题：直接交代研究对象与核心分解，不增加“首次”“统一一切”或架构失效的宣言。文章不限于非易失存储，标题不使用 NVM 概括全部案例。

### 一句话主张

CIM 把一类操作数保存为计算状态，另一类操作数流过该状态完成求值；将工作量与服务能力按 resident 和 streaming 两种角色配对，可以显式分析状态更新的摊销，并把硬件能力转化为可理解的复用要求。

### 摘要：由 Agent 写成一段完整英文，建议 160–190 词

2026-10-06 用户审阅更新：摘要改为从 Roofline 出发，不再从 CIM 的物理特点起笔。现行顺序为：Roofline 是分析 CPU/GPU 的标准工具→CIM 违背了经典 Roofline 的存算分离假设→开门见山提出模型：streaming 与 resident-write 吞吐分别取代计算吞吐与访存带宽→原因是观察到的对称性（分离架构是异质硬件处理同质数据，CIM 是同质硬件处理驻留与流式两类异质数据）→NeuroSim 仿真结合文献提取参数，把十种 CIM 技术放上该 Roofline，并分析主流 LLM 各计算阶段的需求（不写“六个模型”）→结论用成对的 GPU 概念迁移表达：写入速度对应带宽，复用低于临界值时限制吞吐（临界复用跨四个以上数量级）；激活流过整个阵列的速度对应计算吞吐，代表 CIM 真正的计算性能。不加额外收尾句。“单纯提高流式吞吐使转折点右移”放在 IV-B，不进摘要。硬件来源以 Task I README 的 NeuroSim 说明为准；配置含 SRAM 与 gain-cell，不以 NVM 统称。下列 1–6 条中的边界与定量锚点仍然适用，叙事顺序以本条为准。

按以下逻辑写，不做逐节目录介绍：

1. **问题与物理动机。** 存算耦合并不消除数据服务代价，而是使驻留状态更新与流式求值承担不同角色；只用一个汇总的访存量不容易直接揭示这种差异。
2. **方法。** 提出 resident-streaming Roofline，在指定工作窗口内分别计量两类逻辑字节，并与对应的两路服务能力配对，以 resident intensity 得到简单的两分区吞吐上界。
3. **统一的对象。** 权重装载与复用，以及 KV 的建立与增量更新，可以在相同的角色化计量方法下分析。不要将此写成已经验证完整训练或端到端 LLM 性能。
4. **证据范围。** 文献支持的十个模拟／数字 CIM 原生参考配置，以及六个语言模型中代表性矩阵阶段的精确需求计数。这里的精确性指给定结构和计量约定后的计数，硬件结果仍是有依据的工程估算。
5. **一项定量结果。** 所选原生配置的典型临界复用次数跨越四个以上数量级。可用英文 “typical critical reuse counts span more than four orders of magnitude across the selected native configurations”。依据是约 1.6 至 38,867 次完整输入向量求值／装载；不要把它写成所有器件的普遍范围或实测结果。
6. **落点。** 以驻留复用和更新行为，而非任务名称或单一峰值指标，组织瓶颈判断与设计选择。

摘要保留一个定量锚点即可。不要塞入六个型号、十种器件名称、所有符号或整套扫描参数。用一版主摘要，不同时维护多份竞争版本。

建议关键词：Compute-in-memory; roofline model; resident intensity; data reuse; large language models。

## 3. 全文结构与论证顺序

采用 I–V 一级标题，必要时 A/B/C 二级标题，不继续细分成多层标题。相关工作融入 Introduction 和模型联系段，不单列长综述。

### I. Introduction

目标：让读者先理解“为什么要按操作数角色重新组织 Roofline”。

拟用四个短段落：

- 经典 Roofline 的价值与 CIM 的实际分析问题；结合 Fig. 1 介绍存算分离和存算耦合的差别。
- 核心非对称：建立／更新 resident 状态，与在既定状态上服务 streaming 输入。resident 不固定等于权重，KV 也可承担这一角色。
- 简短承接最接近的已有工作：已有 IMC 写入／计算受限视角，本文的贡献是统一的角色与窗口计量，以及跨配置和负载的解析应用。重点查旧稿列出的 Jia 等工作和 Roofline 原文，不将“首次区分写入和计算”写成贡献。
- 三项贡献：模型与计量；有依据的硬件／负载分析；临界复用及设计解释。用自然文字写，不做长贡献清单。

### II. A Resident-Streaming Roofline

**A. Operand Roles and Counting Boundaries**

- 定义分析窗口、逻辑输入与驻留写入需求，以及同边界服务能力。
- 一次初始装载是否在窗口内、更新／重载如何计数。
- 指出 demand 取决于结构、窗口、精度与映射；不在正文罗列所有实现例外。

**B. Throughput Bound and Residency Intensity**

- 用两路时间下界推导核心 Roofline，给出 resident-bound、streaming-bound 和 ridge。
- Fig. 2 对比经典与新坐标的语义。保留形式上的简洁，不声称经典 Roofline 数学失效。
- 两个短例子：① 对同一次完整 MVM，输入 Byte/s 与有用 OP/s 的计量转换；② 同一逻辑矩阵的预驻留、装载一次后复用，以及每次使用前重载。
- SRAM 示例可采用逻辑 128×128 INT8 的操作数与 OP 计数；不必再次引入旧稿的示意 10 ns，更不能把它当成 Task I 的实测周期。

**C. From Resident Intensity to Reuse**

- 定义 U：一次装载后累计服务的输入向量数，包含首次使用，可跨 batch／请求。
- 给出一般矩阵的需求和 U/N 关系，说明 U→∞ 与预驻留窗口的关系。
- 引出临界复用 U*，并预告原生硬件与算子阶段需通过相同服务边界对应。

### III. Hardware and Workload Characterization

**A. Memory-Based Reference Configurations**

- 十个原生参考配置、两路完整服务、三组成对工程情景；简述来源和公共外围假设。
- 当前不同案例保留原生 K、N、资源与更新组织，不能退回“全部为同一 128×128、等面积的 28 nm 芯片”的表述。
- Fig. 3 展示原始 rho–tau 分布。正文说明绝对能力与能力比例是不同信息。

**B. Inference Matrix Workloads**

- 六模型是结构实例库，分析 QKV、单 Dense FFN／路由专家、GQA Prefill 和 Decode 的矩阵阶段。
- 紧凑表格展示代表性 RI，正文用少量公式解释 U、矩阵形状、GQA 共享与 L 的作用。
- 历史 KV 是 resident；Attention 的 streaming 输入是 query 与后续 AV 系数。Prefill 新增每个 token 的 KV 一次，Decode 只新增当前一份。

### IV. Reuse Requirements and Design Implications

**A. Critical Reuse Across Configurations**

- Fig. 4 使用 Task III 的 C 图，展示完整原生矩阵装载的 U* 及成对情景。
- 给出一段已经推导过的代表性算子映射：完整 tile 一次装载后服务相同 U 时，组件数量在两侧时间平衡中抵消。来源为 Task III 的 B 图底稿，不需要保留 B 图本身。
- 用典型阈值跨度和一个情景跨界例子解释图，不逐一点评十种介质。

**B. Design Implications**

- 依据目标 U 反推可接受的完整装载服务时间，而不是只说“提高写入带宽”。
- 较低 U* 不等于较高性能：必须同时查看流式能力。
- Projection 的驻留策略与 Attention 的状态增长不同；不把完整装载阈值未经转换用于所有 KV append。
- 默认不新增提升曲线。GC-04 同资源控制对照仅作备用短例，版面需要时再决定；本轮不增加其图或重新仿真。

### V. Conclusion

约一短段：角色化计量使驻留更新与流式求值的匹配可视化，并提供复用层面的设计要求。只总结已建立的分析能力，不再提出新的通道理论或新实验承诺。

### 全文需要传递的三层认识

**解释：** 长期驻留为何能摊销装载，而动态更新必须显式计入。

**纠偏：** 模型总参数量、阶段名称和单一峰值不足以决定当前工作点；较小的 ridge 或复用阈值也不是综合性能排名。

**指导：** 从具体状态和复用次数出发，检查服务平衡并反推所需能力。

## 4. 正文的核心计量与可引用结果

以下内容用于写作核对，不要求全部变成独立公式块。

### 4.1 基本定义

- Q_S：窗口内经过所声明 streaming 输入边界的逻辑字节。
- Q_R：窗口内建立、更新或重载 resident 状态的逻辑写入字节，不是一般意义上的容量。
- rho、tau：与两组需求使用相同边界、配置和精度的服务能力。
- RI=Q_S/Q_R；Q_S>0、Q_R=0 的静态分支取 RI=∞。
- T 是完成窗口工作的时间；P=Q_S/T 是相应输入服务吞吐。

核心式：

```text
T >= max(Q_S/rho, Q_R/tau)
P <= min(rho, tau*RI)
RI* = rho/tau
```

这是上界。是否接近它由共享资源与执行组织决定；不需要假定已经证明两路独立峰值可同时实现。

### 4.2 一次装载与复用

对 W[N,K]，一次装载后服务 U 个输入向量：

```text
Q_S = U*K*b_S
Q_R = N*K*b_R
RI = U*b_S/(N*b_R)
```

相同完整矩阵服务下：

```text
rho = K*b_S/Delta_S
 tau = N*K*b_R/T_R
 U* = T_R/Delta_S = (N*b_R/b_S)*RI*
```

Task II 参考的所有计量角色为 1 Byte，因此上述关系化为 RI=U/N、U*=N RI*。

U→∞ 保留有限的一次写入，是无界复用极限；预驻留的有限窗口可另有 Q_R=0。不要把两者写成完全相同的工作窗口。

### 4.3 当前 workload 公式

采用现行矩阵阶段入口：共同源输入在同阶段只计一次，不同阶段的新输入再计。D、F、各 head 维度来自固定模型资料。

| 对象                   | Q_S                    | Q_R              |
| ---------------------- | ---------------------- | ---------------- |
| QKV，含适用的额外 gate | U D                    | D N_proj         |
| 单 FFN／单路由专家     | U(D+F)                 | 3DF              |
| GQA Prefill            | H_q[L d_QK + L(L+1)/2] | L H_kv(d_QK+d_V) |
| GQA Decode             | H_q(d_QK+L)            | H_kv(d_QK+d_V)   |

N_proj 包括 Q、可选 G、K、V 的真实输出宽度。FFN 的 gate/up 共享输入，down 的中间输入另计；单专家不乘 top-k、全部专家或共享专家。保留 d_QK 与 d_V 的区别。

同一 L 下，在现行因果窗口计数中，Decode/Prefill 的 RI 之比为：

```text
(d_QK+L) / [d_QK+(L+1)/2]
```

长前缀时趋近 2。这是需求比关系，不是速度比。

### 4.4 适合正文和摘要的结果锚点

- 所选原生配置的典型 U*：约 1.6 至 38,867；这是十个参考配置的典型值跨度，不是某个材料的固有常数。
- STT-MRAM 在 U=128 时，三个实际情景的 U* 约为 181、133、95，说明典型点和稳健跨界判断不同。
- NOR 的 U=128K 超过典型阈值，却低于 long 情景约 254K；需要时与 STT-MRAM 例二选一，避免挤满正文。
- U、真实矩阵形状与原生 GQA 共享解释需求变化；不从模型总参数数目直接推断 RI。

原始精度与小数显示分别保留，写作数值从机器数据读取。源结果是工程估算和解析计数，不称为新测量、芯片实证加速或完整网络验证。

## 5. 图表取舍、来源与拟定编号

最新图标签约定：eDRAM、FeRAM、3D FeNOR、STT-MRAM；论文图文统一用名，文献原题和原始来源文件名保持出版信息。Fig.4 行名采用 6.5 pt，收窄左侧标签区以扩大数据绘图区。

Fig.2 最新状态：已使用原生 TikZ 在单栏内左右并列绘制 a/b，由同一宏保证几何对齐，DejaVu Sans 字体与 Python 图保持同族，直接随论文编译。

**当前目标为 4 幅图＋2 张表。** 正文编号直接为 Table I（单栏基础复用表）和 Table II（通栏真实模型表），不使用 a/b；Task 中的研究阶段编号保留为来源入口。

| 编号／label                       | 任务                                                                          | 位置与宽度建议                              | 当前状态                                                |
| --------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------- |
| Fig. 1`fig:operand-roles`       | 存算分离与存算耦合中的 resident/streaming 路径；说明为何换分解方式            | 第1页，单栏，优先放在引言后部邻近位置       | 未绘制。本轮只用明确占位框，用户之后单独讨论            |
| Fig. 2`fig:roofline-comparison` | 经典 Roofline 与 resident-streaming Roofline 并列；附极简的量、单位、分区对应 | 第2页，简单示意优先单栏；太拥挤时改为浅通栏 | 本轮保留面板与对应信息占位，不展开制图任务              |
| Fig. 3`fig:hardware-capacities` | Task I 原始 rho–tau 能力图，十个原生配置与成对情景                           | 第3页，跨双栏                               | 已有矢量图，保留原始坐标，不换成 Task III A 的 N*rho 轴 |
| Table I `tab:reuse-intensity` | 五种逻辑矩阵 × 五档有限 U 及 U→∞ 的 RI | 第2页 II-C 后，单栏 | 选取现有 Task II(a) 数据 |
| Table II `tab:workload-intensity` | 六模型 × 十二个 RI 列 | 第3页，跨双栏 | 选取现有 Task II(b) 数据；QKV 不含 O |
| Fig. 4`fig:critical-reuse`      | Task III 的 C：完整装载临界复用 U*                                            | 第4页，单栏（右栏顶部）                               | 已有矢量图，作为主要设计解释图                          |

### 5.1 已采用的图

Fig. 3：
`tasks/task1_table_I_NVM/analysis/11_summary_figures/output/rho_tau_loglog_circles.pdf`

数据入口：
`tasks/task1_table_I_NVM/analysis/data/ten_case_results.json`
`tasks/task1_table_I_NVM/analysis/11_summary_figures/data/rho_tau_loglog_circles_points.csv`

保留 rho、tau 的真实坐标、单位和三组成对情景；RI*=1 是硬件比值参照，不是对任意 workload 的分区线。圆只概括有限情景。

Fig. 4：
`tasks/task3_matching_figures/03_reuse_threshold/output/figure.pdf`

数据入口：
`tasks/task3_matching_figures/03_reuse_threshold/data/plotted_thresholds.csv`
`tasks/task3_matching_figures/shared/data.json`

C 图原版为 7.16×4.05 in，不可不加判断地直接缩成单栏。 用户后续审阅已要求重画单栏版：当前稿采用 3.5×2.55 in 版式，取消独立数值列并将典型值标在点旁，原始数据与选图方向不变。主文中的紧凑排版可以在后续仅调整标题、留白和标注，但不能挪动数据点或压扁坐标。此轮先看实际入版效果，记录需要的排版精简。

两张主分析图保持一致的介质颜色和简称。优先使用矢量 PDF；不要用整个研究报告页的截图替代图。

### 5.2 当前两表方案（用户最新确认）

**Table I：单栏基础复用表。** 五行逻辑形状为 128×128、1024×1024、4096×4096、1024×4096、4096×1024，形状不使用 1K/4K 缩写。U 列为 128、1K、16K、128K、1M，最右另加 U→∞ 极限列。该极限下 Q_R=NK 仍是一次有限写入，不改成零。采用现行一次完整装载口径，格内显示 RI；Q_S=UK、Q_R=NK、RI=U/N 集中放表注。端点区别已在模型章节的三个窗口算例中说明，不恢复历史 B 记号或旧两端点表。

**Table II：跨双栏模型表。** 六个模型作行：Qwen3.5-2B、Ministral 3 8B、Qwen3.6-35B-A3B、Hy3 (295B)、Ling-1T (1000B)、MiMo-V2.5-Pro (1020B)。三层表头如下：

- Weight projections：QKV（U=1K/128K/1M）、FFN/MoE（U=16/1K/16K）。
- Attention：Prefill、Decode（各 L=1K/8K/64K）。

用户已明确选择沿用现有 QKV（含适用额外 gate，不含 O）；不将原 QKV 数值改名为 QKVO。每格仅列一个 RI，共 72 个现有有限工况。FFN/MoE 仍是一个 dense FFN 或一个 routed expert，Attention 保持原生 GQA 和现行 KV 窗口。

两表均采用 8 pt 正常表格字号，矩阵形状写全，U/L 使用 1K=1024、1M=1024² 的后缀。显示规则沿用 Task II，不将显示小数回写精确值。源数据为 `table_IIa/data/results.json` 与 `table_IIb/04_crosscheck/data/results.json`；只选取和重排数据，不重启 Task 分析。

当前入口为 `papers/tables/reuse_intensity.tex`、`workload_intensity.tex`；`prepare_tables.py` 负责只读选数与输出，两份 selected CSV 保留完整精度与来源 case_id。

### 5.3 不进入本轮主文的内容

Task III A、B、D、E 不作为额外图；B 的同边界映射推导可进入 IV-A。PD 融合、一般通道分解、时间／空间复杂度推广、完整训练、精度仿真与新的能力倍率实验不进入这篇四页短文。GC-04 控制对照暂不占图位。

## 6. 四页正文的版面草案

下面是内容预算，不是通过负间距强行实现的硬排版。大图保持可读性，正文留出解释空间。

| 物理页 | 主要内容                                                 | 图表安排                                                                              |
| ------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 1      | 标题、Abstract、Index Terms；Introduction；开始 II-A     | Fig. 1 单栏。不要用通栏大示意图挤掉首屏动机                                           |
| 2      | II-A/B/C：定义、上界、两个短例、U与U*；必要时衔接III开头 | Fig. 2 单栏；II-C 后放单栏 Table I                               |
| 3      | III-A/B：硬件估算方式、能力分布、真实推理矩阵需求        | Fig. 3 通栏为主视觉；Table II 紧凑通栏。安排两者与双栏文字的先后，不能让整页只剩图表 |
| 4      | IV-A/B：同边界连接、C图、两三条定量设计认识；V结论       | Fig. 4 单栏；余下为双栏解释与结论。若工作负载表漂移至本页，必须重新核对整体空间       |
| 5      | References                                               | 仅参考文献，无正文、图、表或附录                                                      |

粗略文字预算：摘要160–190词；I约330–420词；II约650–800词；III约400–550词；IV约300–430词；V约60–90词。它用于防止某节失控，不要求逐项凑字。

两幅分析图各占其所在页的大约三分之一到略少于一半。小表占用应明显少于主图。原图若在目标尺寸下字太小，先记录需要重排标注，而不是整体压缩到不可读。末两页图表总量尽量控制在约半幅正文面积附近。

利用正常 `figure`/`figure*`、`table*` 浮动，标题、图注和正文按模板处理。通栏对象通常需提前安排；不要把任务文件编号当成最终浮动顺序。

初版用 layout-draft 开关呈现五页骨架：用明确的内容占位块预留未来段落空间，可临时控制分页，但不通过改页码伪造“第5页”。这些分页与占位辅助应能整体关闭，不变成最终稿的排版依赖。

**第5页检查必须按真实PDF页序进行。** 进入References前处理完正文浮动体；不能因为已有 `clearpage` 就假定所有图都留在前四页。References 不平衡或未占满页面不影响本轮骨架验收。

## 7. 文献与主张的衔接

最终采用 IEEE 引用样式；参考文献全部在第5页，页1–4仍正常放引用标记。

优先覆盖：Roofline原文和最接近的IMC分析；实际支撑所选配置的核心器件／外围来源；六模型的正式报告、固定配置或实现；必要的GQA依据。一般预计二十余条，具体以真实支撑需求决定，不把55份资料库全文照单加入。

来源条目从已核对的文献目录、Bib信息和模型来源清单提取；不要凭记忆补作者、题名、页码或 DOI。首轮只插入已核对的候选条目及对应引用锚点。若用 `nocite` 为骨架预览参考页，只限明确选定的候选集合并在草稿模式中管理。

一手来源支撑事实，我们的程序和推导支撑派生结果。文稿用 literature-grounded estimates、analytical counts、reference configurations 等准确表述，不把软件自检写成实测验证。不要声称已有补充材料、公开数据链接或完整可复现实验包，除非这些已经实际准备并由用户决定发布。

### 需要保持的语言分寸

保留“从硬件功能分解到操作数角色分解”的主线，但采用当前已修订表述。不恢复“CIM没有计算时间”“经典Roofline所有前提失效”“首次区分IMC写入与计算”，也不恢复旧版对FeNOR、RRAM、NAND或训练/decode的普遍适配结论。

把边界说明集中在定义、方法和图注。其余正文直接讲问题、公式、数据和解释，不反复插入防御性段落。

## 8. 本轮写作任务与交付

新建独立投稿目录：`papers/`。本文件建议保存为其中的 `PAPER_BRIEF.zh.md`。

推荐最小结构：

```text
papers/
  PAPER_BRIEF.zh.md
  README.md
  main.tex
  IEEEtran.cls                 # 如需本地复制，来自用户模板且保持不改
  references.bib
  sections/
    abstract.tex
    introduction.tex
    model.tex
    characterization.tex
    implications.tex
    conclusion.tex
  figures/                     # 已选图的投稿副本或受控引用
  tables/
  notes/layout_review.zh.md
  output/manuscript_skeleton.pdf
```

内部文件组织可简化；不创建重复的写作管理系统。图的来源与生成版本在README记录，不覆盖原Task产物。

当前 Agent 亲自完成：

1. 按上传模板建立能编译的英文IEEE项目，去掉模板示例内容。
2. 写成标题、单段Abstract和Index Terms的第一版。
3. 建立I–V及A/B/C骨架。各小节用两三句可见的英文写作提纲，明确“要讲什么、用什么依据、指向哪个图表”；详细说明可放TeX注释或中文笔记。不要写成完整Introduction和正文。
4. 核心公式可提前排入，以便测试行宽和数学版面。Fig.1/2清楚占位；Fig.3/4先引入已有矢量图；工作负载表只做精简形态原型，数据取自当前JSON。
5. 产生真实五页的带占位版面原型，前四页展示未来技术内容布局，第五页仅References。可见标识“Outline / figure pending”等，不用无意义假文或伪装成完成稿的填充段落。
6. 渲染并逐页查看PDF，检查真实页数、通栏位置、引用、图表可读性和漂移。用简短中文记录实际页面安排、摘要字数与后续最需要调整的一两处空间问题。

作者暂不处理，Fig.1的具体绘制另行讨论。不要为凑足四页而偷偷写完整篇论文；五页骨架用可关闭的占位实现，正文成熟度如实标明。

所有写入限于新投稿目录。旧论文、Task I/II/III、文献和模板原件保持不动。用户统一处理Git，不暂存、提交或推送。

完成状态：**写作第1轮——标题/摘要与五页骨架完成，待用户审阅。** 到这里停止，后续再逐节撰写和制备概念图。

## 9. 关键资料索引（均为仓库相对路径）

| ID | 入口                                                                         | 主要用途                              |
| -- | ---------------------------------------------------------------------------- | ------------------------------------- |
| S0 | `Conference-LaTeX-template_10-17-19/conference_101719.tex`                 | 用户提供的IEEE排版模板及标题/摘要要求 |
| S1 | `CIM_Roofline_Paper/cim_roofline.tex`                                      | 修订后的理论主线与两个算例            |
| S2 | `tasks/task1_table_I_NVM/analysis/shared_baseline/README.md`               | 原生服务定义、两路估算与Task I/II接口 |
| S3 | `tasks/task1_table_I_NVM/analysis/TEN_CASE_REVIEW.zh.md`                   | 当前实现选择、可引用数值与资格说明    |
| S4 | `tasks/task1_table_I_NVM/analysis/11_summary_figures/README.zh.md`         | 原始能力图的语义、来源和文件          |
| S5 | `tasks/task2_table_II_workloads/table_IIb/04_crosscheck/CONTRACT.zh.md`    | 最新U、计量边界、工况和公式           |
| S6 | `tasks/task2_table_II_workloads/table_IIb/04_crosscheck/data/results.json` | 现行精确workload计数                  |
| S7 | `tasks/task2_table_II_workloads/data/models.json`、`data/sources.json`   | 六模型的固定版本、结构与来源          |
| S8 | `tasks/task3_matching_figures/shared/README.zh.md`                         | U*接口和代表性QKV同边界映射           |
| S9 | `tasks/task3_matching_figures/03_reuse_threshold/README.md`                | 已选C图、阈值范围与情景跨界           |

以这些定向入口恢复状态即可，不重新通读全部底层文献。本总纲中的标题、章节、选图与版面是本轮写作方案；事实与数字回到对应原始结果核对。
