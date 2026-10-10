# 写作第1轮版面审阅

2026-10-06。标题：**A Resident-Streaming Roofline Model for Compute-in-Memory**。摘要 **189 词**（空白分词，连字符词计一词），单段，无公式、数学符号、引用或脚注。摘要按用户审阅后的叙事重写：Roofline 的地位—CIM 违背存算分离假设—提出新模型及其替换关系—对称性—NeuroSim 估算与 LLM 需求分析—写入速度对应带宽及临界复用跨度—激活流过阵列的速度对应计算吞吐，代表 CIM 真正的计算性能。重写后第一页左栏仍容纳摘要、Index Terms 与引言提纲，五页安排不变。

## 实际五页安排

| 物理页 | 已查看的实际内容与位置 |
|---|---|
| 1 | 标题 19.6 pt、居中单行；左栏 Abstract、Index Terms、I Introduction；右栏上部 Fig.1 用户原图（等比例撑满单栏），下部 II-A 定义及式(1)。正文预留区均有灰框标记。 |
| 2 | 左栏 II-B、核心上界、两个计数算例与单栏 Table I（五矩阵 × 五档有限 U 及 U→∞）；右栏上部 Fig.2 对称双子图及英文计量对应表，下部 II-C 与复用阈值公式。 |
| 3 | Fig.3 通栏在上，Table II 通栏紧随其后；底部左栏 III-A，右栏 III-B。表转置为六模型行、十二个 RI 列，采用三层表头。 |
| 4 | 左栏从 IV-A 与完整 tile 映射关系开始；Fig.4 重画为单栏，置右栏顶部，下接 IV-B、装载时间预算与 V Conclusion。 |
| 5 | **只有 References**，共 21 条，左右栏分别从 [1]、[12] 开始；下部留白供后续扩充。没有正文、占位块、图或表。 |

## 核对与来源

- 数字：Task III `03_reuse_threshold/data/plotted_thresholds.csv` 的典型 U* 最小/最大值为 **1.5950155763 / 38866.8809074**，跨度 **4.3868** 个数量级；STT-MRAM 三个实际点为 **180.7058824 / 132.7407407 / 94.8148148**。只读取现有结果，不重启分析。
- 理论与边界：`CIM_Roofline_Paper/cim_roofline.tex`、Task I `analysis/shared_baseline/README.md`、Task II `table_IIb/04_crosscheck/CONTRACT.zh.md`、Task III `shared/README.zh.md`。保留上界而非实测吞吐、完整装载而非任意 append 的区别。
- Fig.3：原 Task I rho–tau 矢量图原样保存在投稿目录；实际入版另做**纯排版副本**。原画布约 19.94 英寸宽，直接缩入双栏会把 12 pt 标注缩到约 4.3 pt，因此改为纸面 7.5–8.5 pt。全部 30 个坐标、十圆几何、颜色及成对关系沿用原始文件，并验证等尺度对数轴；没有换为 N*rho 轴或生成新数据。按最新审阅将横轴收至 10^-2.15–10^4.15（约 0.00708–14125，两侧各留 0.15 decade），纵轴严格为 10^0–10^3。全部数据点仍在视窗内；圆按新边界裁切，边缘点符号不裁断。图高由约 4.35 in 降至 3.64 in，第三页释放约 18 mm 高度，已重编译并查看。
- Fig.4：按最新审阅重画为 **3.5 × 2.55 in 单栏图**，源矢量 PDF 另存对照。沿用 Task III C 图的 30 个精确横坐标、十类排序、颜色/符号及三情景填充语义；仅在分类行内错开小点以显露重叠。取消右侧数值列，典型值放在对应情景范围旁；横轴保留 1、128、1K、128K 四个参照，范围覆盖全部阈值。行名 6.5 pt、数值和坐标 7–7.5 pt，图面面积比此前裁边后的通栏版减少约 60%，图注同步压缩。已按实际单栏宽度查看，点、数值、行名和图例无裁切。
- Table I / II：分别从 Task II 的 `table_IIa/data/results.json` 与 `table_IIb/04_crosscheck/data/results.json` 选取 25 / 72 个现有有限采样点；精确分数、字节量与显示值保存在两份 `selected_*.csv`。1K=1024，1M=1024²，模型、选层与计数口径保持现行版本。
- 文献：Roofline、Jia 等最近工作、十配置的代表性器件/宏来源、三条共享外围来源，以及六个固定模型配置。共 21 条，均有正文引用；来源入口见 README 和 `.bib` 注释。完整硬件证据链尚未全部放入这版短文引用。

## 视觉与编译检查

采用原模板 `IEEEtran` conference、Letter，正文保持 10 pt；按用户授权将标题从 24 pt 改为 19.6 pt，加入 Model 后以单行排下。20 pt 实测宽 524.955 pt，19.6 pt 约 514.456 pt，小于可用栏宽 516 pt。关闭 fi/fl/ff 等英文连字；最新编译修复恢复正常断词，并启用标准 microtype 微排版；未改字体家族、页边距、栏宽或页码。作者/单位/资助未填。PDFium 按 **144 dpi** 渲染并逐页查看最终五页：图表清晰、无文字遮挡或出界，四幅图和表均留在前四页，未发现缺字、未解析引用或公式越栏。LaTeX 无 Overfull、无未定义引用；恢复正常断词并修复草稿通栏容器后，正文 Underfull 已消除；仅参考文献 [5] 长型号列表保留一条提示。逐页确认无出界、遮挡或图表漂移。

## 后续只需关注的空间问题

1. **第三页仍需控制篇幅。** 收紧 Fig.3 视窗后，主图与表、图注合计约占正文高度六成，较上一版多出约 18 mm 正文空间。完整写作宜把部分 III-A 的服务假设前移到第二页末，并精简两图图注；不继续缩图。当前未把全部 workload 公式另起四个公式块，避免只为公式占位挤出正文。
2. **第四页已释放空间。** Fig.4 放入右栏顶部，左栏可以直接展开 IV-A；后续正文可利用左栏下部空间，不必再让两栏都从通栏图下方起笔。
3. **第一、二页还有组织余地。** Introduction 和模型说明扩写后可重新分配 Fig.1/2 的高度；现在的灰框是预留空间，不是最终段落长度承诺。作者信息尚未填写，首屏空间仍需复核。

`\layoutdraftfalse` 可整体关闭预留框和临时分页，恢复常规浮动。已另行编译关闭开关的自然流版本，确认预留框消失、标准浮动可用；该检查 PDF 仅在忽略的 build/ 中。英文 Outline 明确保留为待改写内容。本轮在骨架处停止。

工作区说明：本轮只写 `papers/`。最终检查另见仓库根 `.DS_Store` 与 `2026.9.23 CIM Roofline 邵瀚雍.pptx` 有并行工作区变化，本轮未写入、暂存或回退这些文件。

**写作第1轮完成，待审阅。**

## 编译警告核查与处理

重新强制编译并对照当前源文件，原设置产生 26 条 `Underfull \hbox`，没有 `LaTeX Font Warning`、缺字、未定义引用或 Overfull。

- **不是缺字体。** `ot1ptm.fd` 明确把 `bx` 映射到 `b`（`ssub`），日志中的 `Font Info: ... bx ... not available ... b ... tried instead` 是字体包正常配置。正文正体、粗体、斜体和粗斜体的 URW Times `.pfb` 均存在，最终编译实际嵌入这些字体，不需要另装字体。
- **实际应修复的是排版。** 上次把“关闭连字”同时做成了禁止自动断词；`hyphenat[none]` 将两个断词惩罚设为 10000，双栏两端对齐因此拉大字间距。现保留 `\DisableLigatures[f]`，恢复正常断词，并启用 microtype 的标准 protrusion/expansion。
- **修复两个草稿容器提示。** `paperwidefigure` / `paperwidetable` 在 minipage 前后显式结束段落、取消首行缩进，避免空的欠满行；自然浮动分支保持不变。
- **结果：26 → 3 → 1。** 容器修复加正常断词后为 3 条，启用微排版后只剩参考文献 [5] Infineon 型号列表的一条 Underfull（生成 `.bbl` 的第 47–50 行）。该条表示字间距偏宽，未缺字、越栏或截断；保留原始书目信息，暂留这条可见提示，最终书目定稿时再调整。

不使用 `\hbadness=10000`、全局 `\sloppy` 或警告过滤来隐藏问题。字体 Info 无需修复或屏蔽。最终 `latexmk -g -pdf` 通过，PDF 仍为五页；按 144 dpi 逐页查看，单行标题、正文图表与纯参考文献页保持正确。

## 图标签与 MRAM 类型核对

Fig.4 行名从 7.5 pt 调为 6.5 pt，左侧标签区从 1.01 in 收至 0.67 in；图宽/高仍为 3.5 × 2.55 in，实际数据绘图区由 2.44 in 增至 2.78 in（约 +14%）。Fig.3 与 Fig.4 共同采用 eDRAM、FeRAM、3D FeNOR、STT-MRAM，已同步正文中的 STT-MRAM 算例。

类型依据：Task I `analysis/06_mram/README.md` 与 `notes/evidence.zh.md` 指向 MRAM-06 的原生互补 bank 路径；本地 `MRAM-06_2025_LosslessParallelSpintronicCIM.pdf` 第 1 页摘要及第 2 页正文均明确是 40-nm spin-transfer torque / STT-MRAM。稿件的该配置引用已从另一电阻求和宏更正为对应的 MRAM-06：Nature Electronics 8, 1046–1058 (2025)，DOI 10.1038/s41928-025-01479-y。

3D FeNOR 为本文统一技术标签；原始文献的 FeFET 题名和来源文件名按出版信息保留，未改动 Task 数据或旧图原件。重新生成两张投稿图、编译并查看第 3–5 页，全部数据点和数值保留，左侧标签无裁切；PDF 仍为五页、参考文献仍为 21 条，没有新增编译警告。

## Fig.1 原图接入

采用用户提供的 `figures/Fig1.png`，以 `\includegraphics[width=\linewidth]` 替换原占位框，保持 3198 × 1697 原图比例和透明背景，未重绘或裁切。第一页右栏内撑满宽度，图注同步改为正式的 A/W 操作数角色描述。重新编译并查看第一页，透明背景在 PDF 中正常显示为纸面白色，图像无溢出；PDF 仍为五页，第五页仅参考文献。

## Fig.4 中 128 参照线的语义

已核对当前 30 个情景：Fig.4 使用各配置原生 N（16、32、64、128 或 240），不是统一 128×128 假设。相同逻辑字节宽度下 RI=U/N，而服务平衡要求 RI*=rho/tau，因此 U*=N RI*；RI=1 只表示逻辑字节量相等。SRAM ACIM 的 N=128、典型 U*=1.595；STT-MRAM 的 N=32、典型 U*=132.741。

128 来自先前选定的复用示例，适合解释 STT-MRAM 三个实际情景的跨界，不是所有配置的统一分界。已取消该竖线的加粗，所有复用参照线采用同样的浅灰样式；右上角加入 Native W[N,K]、U*=N RI*、U=128: example，图注强调各行原生尺寸及参照线的示例含义。该修改未更改任何点或阈值，重新编译仍为五页。

## Fig.2：原生 TikZ 双子图

已参考中文理论稿的经典与 resident-streaming 两张示意图，合成同一个 TikZ 绘图入口 `figures/roofline_comparison_diagram.tex`，由参数化宏生成左右 a/b，无需导出图片再拼接。单栏宽 252 pt、高 157 pt；两边轴长、拐点、曲线和标注位置一致。

曲线采用 1.6 pt，坐标轴 0.65 pt，辅助虚线 0.55 pt；紫色斜段/青色水平段对应两种约束。文字为局部 DejaVu Sans（6.5–7.4 pt），与 Python 图的字体家族一致；希腊字母通过 LGR 编码使用 DejaVu Sans 斜体，正文及正文数学字体保持原设置。图中包含两轴单位、斜率、上限、脊点和两个受限区域；图注明确为独立线性标度的上界示意，几何一致不代表能力数值相同。

已按 144 dpi 查看第二页整体，并放大检查图内标注；无文字、曲线或图注重叠。全文仍为五页，Fig.2 位于第二页右栏顶部，四图均为实际内容。编译仍仅有此前参考文献 [5] 的一条 Underfull，没有新增字体、缺字、引用或越栏警告。

## Table I / II 重排

用户已确认正文直接编号 Table I、Table II，不使用 a/b。Table I 放在第二页 II-C 后，单栏：左列依次为 128×128、1024×1024、4096×4096、1024×4096、4096×1024，U 列为 128、1K、16K、128K、1M。表注集中说明 Q_S=UK、Q_R=NK、RI=U/N，以及逻辑形状不等于物理 tile。相同 N 对应相同 RI 是 K 抵消的结果。

Table II 位于第三页 Fig.3 下方，跨双栏。第一层为 Weight projections / Attention；第二层为 QKV (U)、FFN/MoE (U)、Prefill (L)、Decode (L)；第三层分别为 1K/128K/1M、16/1K/16K、1K/8K/64K、1K/8K/64K。六个模型作行；补齐 Hy3 (295B)、Ling-1T (1000B)、MiMo-V2.5-Pro (1020B)。Ministral 3 8B 保留官方型号名；固定来源另记录其语言主干为 8.4B。用户明确选择沿用现有 QKV，不扩展 O，因此该组表头与表注保持 QKV（含适用 gate，不含 O）。

两表均使用正常 8 pt 表格字号，无 resizebox 或字体压缩。25+72=97 个值逐一核对原始 JSON 的 Q_S、Q_R、RI 精确分数；显示沿用现有 Decimal/ROUND_HALF_UP 规则。重新编译并逐页查看，五页结构、四图位置与第五页纯参考文献保持正确；没有新增编译警告，仍只有既有参考文献 [5] 的 Underfull。

## Table I 增补无界复用列

最右侧加入 U→∞，五种矩阵的 RI 均为 ∞；25 个有限值与字号（8 pt）保持原样，新增五格直接来自原始结果的 limit 记录。表注说明 Q_R=NK 仍有限，未与零写入窗口混同。单栏内正常放下，无缩放、无新增越栏提示；重新编译并查看第二页，全文仍为五页。

## 2026-10-07：Fig.2 合并英文计量对应表

依据中文稿的“Roofline 计量对应”表，在 Fig.2 的 a/b 曲线下方增加单栏英文对应表，与曲线共享一个 Figure 编号。新增 Decomposition 一行：GPU 为 Hardware resources，CIM 为 Data roles。Workload 行采用 OP, Byte 与 Q_S, Q_R；相应 AI 与纵轴表达式也改用 OP/Byte、OP/T。图注说明 OP 和 Byte 分别表示操作次数和搬运字节数。

保留 Service rates、Intensity、Vertical axis、Upper bound、Left regime、Right regime、Ridge 各行。服务率明确列 π [OP/s]、β [Byte/s]，以及 ρ,τ [Byte/s]；其他表格行不另列单位，AI/RI 仅给定义式。表中文字为 DejaVu Sans 7.2 pt，沿用同文件的希腊字母字体；并未栅格化或整体缩小。

为保留清晰字号，Table I 移到第二页左栏原正文预留区；Fig.2 组合图仍位于第二页右栏顶部，II-C 接在其后。两张正式数值表仍编号 Table I、Table II，没有新增 Table III。已查看第二页整页及组合图放大图，无表格换行溢出或元素重叠；全文五页，参考文献页保持纯参考文献，无新增编译警告。

## Fig.2 上方曲线进一步压缩

四个 bound 标签已移入各自图内：Memory/Resident-bound 位于左侧三角形内，Compute/Streaming-bound 位于右侧水平上限下方。两边共用相同几何，略加宽三角形以容纳原 6.5 pt 标签，未缩小文字。横轴删除全称，AI、RI 及单位置于右端下方，与 ridge 标注同一水平行；ridge 比值与单位均使用上下分式。

曲线部分由 252×157 pt 缩为 252×129 pt，节省 28 pt（约 9.8 mm）高度；下方计量对应表保持原样。重新编译并查看第二页整页及放大图，标签均在图内，没有压线、重叠或裁切；全文仍为五页，无新增编译警告。

## 2026-10-10：Section II 重组精修

基于 HEAD `f98cb74`（261010_0030）。只改 `sections/model.tex` 与本记录；Abstract、Introduction、图表文件及其他章节未改。

- 结构：保留 A/B/C。A 为 Workload Demands and Hardware Throughputs（窗口 → Q_S/Q_R → ρ/τ → SI、P → 计量原则与边界）；B 为 Throughput Bound and Roofline Interpretation（时间下界推导 → ridge 含义与分区 → 可达性一次 → Fig.2 对应 → OP/s 换算）；C 为 From Streaming Intensity to Reuse（负载侧 SI=Ub_S/(Nb_R) → Table I → 三种驻留策略文字化 → Δ_S、T_R 与 U*=T_R/Δ_S → P/ρ≤min(1,U/U*)）。
- 公式标签：删除 `eq:windows`（三策略表改为文字）与 `eq:op-conversion`（换算改为行内）；新增 `eq:reuse-bound`；`eq:roofline` 等其余标签保留。全文无悬空引用；Section IV 公式顺延为 (8)–(11)。
- 版面：草稿模式下 Section II 从第 2 页左栏约 35% 处开始，Fig.2 仍由 `\draftcolumnbreak` 置于第 2 页右栏顶部（断点在式 (1) 段落之后，左栏约余 2 行）；Table I 位于第 3 页左栏底部；本节止于第 3 页右栏约 60%。若 Introduction 长度再变，需重调该断点。
- 页数：仍为 7 页，与检查点相同。原因是 Introduction 已延伸到第 2 页，而 III 前的 `\draftspread`、IV 前的 `\draftpagebreak` 仍按旧五页安排强制换页（第 3 页右栏下部、第 5 页大部空白）。在 build/ 中临时副本核查：改为自然浮动或仅去掉 IV 前 `\draftpagebreak` 均为 6 页；未修改源文件。
- 编译：`make` 与 `latexmk -g` 通过，无 Overfull/Underfull、未定义引用。本轮期间 `figures/critical_reuse_single.*` 被并行更新（非本轮修改），当前 PDF 中 Fig.4 图体已换新，原图注尚未同步。

## 2026-10-10 下午：Section II 逐句精简

基于 HEAD `edc4022`（261010_1400），开始时工作区无改动。只改 `sections/model.tex` 与本记录；`layout_fixed.tex` 锚点、图表与其他章节未动。

- 精简前（实际 PDF，6 页）：Section II 自第 2 页左栏约 28% 起，止于第 4 页左栏 Table II 下约 24 行。精简后：止于第 3 页右栏约 13 行（Fig.3 下方），末句为 “so insufficient reuse caps the throughput at a fraction U/U* of the streaming ceiling.”；III 紧随其后，全文仍为 6 页。
- 词数（正文词，行内数学计一个单元，独立公式与标题不计）：1257 → 711，净减 546。
- 公式：ρ=Kb_S/Δ_S、τ=NKb_R/T_R 改为行内，删除 `eq:matrix-services`；其余标签保留，无悬空引用。II 现为式 (1)–(6)，Section IV 顺延为 (7)–(10)。
- 固定对象核对：Fig.2 第 2 页右栏上部、Table I 第 2 页右栏下部、Fig.3 第 3 页顶部、Table II 第 4 页顶部，均未移动。

## 2026-10-10 傍晚：Section II 补强建模理由

基于 HEAD `fe32627`（261010_1445），开始时工作区无改动。只改 `sections/model.tex` 与本记录。

- II-A：首段改为“一份驻留状态支撑多次求值、建立状态另有服务需求 → 明确窗口、分别统计”；补 Q_S 代表已完成规定计算与输出的工作、可与 resident 写入直接比较；窗口写入正面定义（可预驻留，但窗口内必需写入全部计入，值不变的重载也计）；“Each demand is served by its own throughput” 改为 “We characterize the two services by their corresponding throughputs”。
- II-B：ridge 改为需求率解释：达到 streaming ceiling 需平均 resident 写入率 ρ/SI，等于 τ 处即 ridge。
- II-C：开头限定为一次完整装载后复用的矩阵；U* 改用“每次输入摊销的装载时间 T_R/U 等于 Δ_S”解释；U* 限定为两路服务平衡所需复用。
- 公式、标签、计量口径未变；编译无警告。Section II 仍止于第 3 页右栏（约 17 行处，较上轮多约 4 行），固定对象未移动，全文 6 页。
