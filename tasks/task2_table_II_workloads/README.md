# Task II：resident–streaming 模型与矩阵工作量

**状态：Step 3已通过；Step 4完成，待用户审阅。** 本轮日期：2026-09-25。

本轮并行分工与数据接口见 [Step 4 协调记录](STEP4_COORDINATION.zh.md)，实际结果及主审阅见 [Step 4 审阅记录](STEP4_REVIEW.zh.md)。Step 3 产物保留为已审阅回归基准。

本任务建立模型无关的驻留端点，以及六个固定 LLM 的真实矩阵阶段需求。重点是操作数角色、状态写入与驻留复用。分析只覆盖语言主干矩阵子层，不进行端到端性能、精度、硬件仿真、完整训练建模或器件适配排名。

## 阅读入口

1. Step 4 分类稿：[QKV](table_IIb/01_qkv_projection/README.md)、[FFN/MoE](table_IIb/02_ffn_moe/README.md)、[Attention](table_IIb/03_attention/README.md)；各自包含中文 TeX/PDF、六模型概览和复算入口。
2. Step 4 汇总：[四行六模型双边界预览](table_IIb/04_crosscheck/PREVIEW.zh.md)、[统一精确 JSON](table_IIb/04_crosscheck/data/results.json) / [CSV](table_IIb/04_crosscheck/data/results.csv)、[独立检查数据](table_IIb/04_crosscheck/data/checks.json)。这是研究底稿，最终英文排版与论文整合留 Step 5。
3. [Step 3 审阅](STEP3_REVIEW.zh.md)、[中文试算 PDF](table_IIb/pilot/output/pilot.zh.pdf) / [TeX](table_IIb/pilot/tex/pilot.zh.tex)、[两模型四行预览](table_IIb/pilot/PREVIEW.md)、[试算与复算入口](table_IIb/pilot/README.md)。
4. [Step 2 审阅原稿](STEP2_REVIEW.zh.md)、[中文共享方法 PDF](shared/output/counting_method.zh.pdf) / [TeX](shared/tex/counting_method.zh.tex) / [共享入口](shared/README.md)。
5. [Table II(a) 英文 PDF](table_IIa/output/table_IIa.pdf) / [独立入口](table_IIa/README.md) / [可复用片段](table_IIa/tex/table_fragment.tex) / [精确数据](table_IIa/data/results.json)。
6. [研究配置](data/study_plan.json) 与 [共享机器约定](shared/data/conventions.json)：固定 B、L、表格设计、精度、双边界、窗口与公式。
7. [模型结构数据](data/models.json)、[来源清单](data/sources.json) 与 [Step 1 审阅原稿](STEP1_REVIEW.zh.md)：已经审阅的固定模型/原始证据。原件中的历史状态及精度待定字段不重写，本轮状态以本 README/研究配置为准，计数精度以共享约定为准。
8. [共同算法资料](literature/00_shared/README.md)。六模型结构卡见下表；`raw/` 是原件，`extracted/` 是派生检索文本。

| 固定列序 | 显示名 | 结构卡与本地资料包 |
|---|---|---|
| 1 | Qwen3.5-2B | [01_qwen35_2b](literature/01_qwen35_2b/STRUCTURE.zh.md) |
| 2 | Ministral 3 8B，2512 | [02_ministral3_8b](literature/02_ministral3_8b/STRUCTURE.zh.md) |
| 3 | Qwen3.6-35B-A3B | [03_qwen36_35b_a3b](literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) |
| 4 | Tencent Hy3，295B | [04_hy3_295b](literature/04_hy3_295b/STRUCTURE.zh.md) |
| 5 | Ling-1T | [05_ling_1t](literature/05_ling_1t/STRUCTURE.zh.md) |
| 6 | MiMo-V2.5-Pro | [06_mimo_v25_pro](literature/06_mimo_v25_pro/STRUCTURE.zh.md) |

## 起点与已完成基线

Step 1 已通过，审阅提交为 `e95de9e213d3dd0db9208459b07ce48152f102c9`。Step 2 已通过，审阅提交为 `2eb7e7c59242c675594537002cc1316131be9226`。Step 3 已通过，审阅提交与本轮 Step 4 起点 HEAD 均为 `e472a0d864b8fb9afb14b0c306217a0e5653e122`，初始工作区干净，不回退。全部修改局限本任务目录；本轮不暂存、提交、推送或重置 Git。Step 2 的起点 `d60bc32ff83f1ab48cae0ffd106ebd9df46940d0` 及审阅原稿作为历史保留。

Step 1 最初检查点为 `81b7c332c20b9b5be6890256e9cf0d3edab12785`，其原审阅记录和原始资料均保留。

已阅读 [MODEL_CONVENTIONS](../../docs/MODEL_CONVENTIONS.md)、[Task I 共享基线](../task1_table_I_NVM/analysis/shared_baseline/README.md)、[十例约定](../task1_table_I_NVM/analysis/TEN_CASE_CONVENTIONS.zh.md) 与 [十例审阅](../task1_table_I_NVM/analysis/TEN_CASE_REVIEW.zh.md)。旧稿的 candidate/待审阅标签不推翻用户确认的完成状态。Task I 的十类硬件估算是固定输入：共同 28 nm 外围、128×128 INT8 矩阵乘向量、每次 128 Byte 输入、矩阵 16384 Byte=16 KiB；本轮未更改。

`tasks/archived/task2_table_ii/` 不作为本次模型、计数或结果基线；早期论文也不提供本轮继承的 workload 数字。

## 计量与研究边界

Q_S 是窗口内经过声明 streaming 输入边界并被服务的逻辑操作数字节累计量；Q_R 是窗口内建立、更新或重载可计算 resident 状态的逻辑写入字节累计量。RI=Q_S/Q_R；静态驻留 Q_R=0 时 RI=∞。它们不是 GPU/HBM 流量或驻留容量的同义词。

窗口内初始写入、更新、重载须按实际声明计入；内部编码、位串行、广播、verify、refresh/restore 不自动变成新的逻辑 payload。本轮采用 128×128 tile 接收端累计作为主边界 `ports`，整矩阵阶段的共享输入入口作为对照 `operator`。输出不直接加入本次 Q_S；若成为后续矩阵求值输入，在后次服务计数。Attention 的 query 与 Attention 系数是两次矩阵任务的不同输入。

选择原生完整/全局 GQA 子层，保留原生 Q/K/V、额外门控、FFN 和专家结构。混合线性层、SWA、视觉/音频编码器、MTP、embedding/LM head 均不展开；选择的单层不代表整个模型。模型原生 dtype 与本文参考精度分开记录。本轮把权重、激活、K/V、query 和 Attention 系数设为每元素 1 Byte 的 INT8 逻辑参考，公式仍保留独立角色宽度；这不是六模型 INT8 精度验证。数字部分和与非矩阵处理后重新定标进入下一阶段，不直接把 BF16 需求配 INT8 能力。

## Table II(a)：模型无关的驻留端点

两行固定为：

1. **Weight-static**：权重预驻留，窗口内不写入。
2. **Per-use reloaded**：每次使用前完整写入被分析权重。

“一次使用”按一个输入向量求值定义，第二行不是完整训练 step。resident 矩阵 W 为 N×K，N 是输出维度、K 是输入维度。五列依次是 **(128,128)、(1024,1024)、(4096,4096)、(1024,4096)、(4096,1024)**。它们是逻辑任务形状，不是五种新物理 macro。英文主表每格保留 Q_S、Q_R、RI，本轮已完成。主口径是局部接收端：`Q_S=ceil(N/128)K Byte`，动态 `Q_R=NK Byte`；五形状动态 RI 都为 `1/128`，静态为 ∞。整算子对照保存在中文推导与机器数据中。

## Table II(b)：真实模型的四类推理工况

六列顺序见上表，四行固定为：

1. **QKV Projection**：选中完整 GQA 的模型原生 QKV 投影，权重预驻留，按一个输入 token 的矩阵需求分析；原生额外投影输出在结构卡中保留。
2. **FFN / MoE**：Dense 取一个 FFN，MoE 取一个路由专家的 FFN；一次装载后服务 B 个输入向量，再发生替换。
3. **Attention Prefill**：从本段空 KV 状态开始，建立长度 L 的 KV，完成相应因果 Attention 矩阵任务。
4. **Attention Decode**：已有 L−1 个 token 的 KV，本次追加一个，求值可见长度为 L。

**B={8,64,512}**，表示同一份 FFN/专家权重一次驻留期间实际服务的输入向量总数，不是批次数，也不自动等于全模型全局 batch size。**L={1024,16384,131072} token**，显示为 {1K,16K,128K}，这里 K=1024。B 仅用于 FFN/MoE，L 仅用于 Attention 两行，不做 B×L 全组合扫描。

驻留策略、B、L 是本研究选定工况，不是需要从模型报告验证的部署事实。研究预览优先突出 RI，适用行依既定 B/L 顺序显示三个值；完整 Q_S、Q_R、RI、配置与推导保存在分类底稿及统一机器数据中。

两个子表独立制备、独立编译。Table II(a) 的精确数值与独立英文表格已通过 Step 2 审阅。Step 3 在 `table_IIb/pilot/` 完成 Ministral 3 8B（2512）与 Qwen3.6-35B-A3B 各 10 个汇总工况，MiMo-V2.5-Pro 仅计算 L=1024 的 Prefill/Decode，共 22 条主数据。Step 4 已重新生成六模型共 60 个工况、146 个矩阵分项；pilot 的 22 个工况是其中的回归重叠部分，不额外计为 82 个。

试算支持保持 Step 1 提取和共享方法 `WS128-INT8-semantic-banks-v1`。两主模型 FFN 的局部 RI 同为 B/128，但容量与总局部需求相差 56 倍；同 L Attention 的局部输入和调用恰好相同，Qwen 的 KV 写入为一半，RI 为两倍。MiMo 保留 192=128+64 的输入尾片，区分有效字节与完整调用。全部原始 Byte、精确分数、分项、容量和追加形状见 [试算数据](table_IIb/pilot/data/results.json)，方法适用条件与最小映射对照见 [Step 3 审阅](STEP3_REVIEW.zh.md)。

六模型实例化保留这些结论：FFN ports RI 全部为 B/128，容量依序为 36/168/3/18/48/36 MiB；QKV 全部 RI=∞，但 ports 输入为 80/192/144/320/640/1272 KiB。Attention 的 ports RI 有相同组，operator 可呈现不同入口复用；Hy3 与 Ling 的选中 Attention 头结构相同，两个边界结果也相同。Ling 128K 的官方扩展条件与 MiMo 不等宽 head、尾片、有效/分配容量区别仍明确保留。

## 五阶段与后续目录

| 阶段 | 内容 | 状态 |
|---|---|---|
| Step 1 | 固定六模型、结构参数及本地资料 | 已通过（e95de9e） |
| Step 2 | 共享方法与通用驻留端点 | 已通过（2eb7e7c） |
| Step 3 | 少量真实模型试算 | 已通过（e472a0d） |
| Step 4 | 分类并行分析 | **完成，待用户审阅** |
| Step 5 | 统一复核与英文表格 | 未启动 |

`shared/` 已保存统一计数方法、符号模板和轻量检查；`table_IIa/` 已保存精确数据、片段及独立 TeX/PDF。`table_IIb/pilot/` 保存已审阅试算材料；本轮分类任务分别在 `table_IIb/01_qkv_projection/`、`02_ffn_moe/`、`03_attention/`，独立复核与统一汇总在 `04_crosscheck/`。`literature/00_shared/` 的共同原始资料只存一份，模型卡以相对路径引用。

## 本地可用性与检查

六个版本的模型卡、配置及必要实现均已保存；Ministral 和 Ling 的确切技术报告全文已下载，另有三份共同算法论文。其它四个模型未找到确切版本的独立报告，已用官方完整模型卡/说明、配置、实现组成主要证据；没有把摘要当作全文核对。没有下载权重、安装/执行模型或运行第三方代码。

`.gitignore` 只在本任务局部保护未经明确再分发授权的论文全文及其提取文本、官网全文快照；它们已在本机可读。新 checkout 不含这些忽略文件时，可按 `sources.json` 的固定版本 URL 补取。GQA 论文为 CC BY 4.0，保留原始署名及许可证元数据。模型卡声明许可证和实现文件头的许可证分别保留，不据模型权重许可证推定所有网页可再发布。

Step 2 检查与独立编译（数值检查只需 Python 标准库，PDF 需 XeLaTeX；本机已有工具）：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/shared/scripts/build.sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/shared/scripts/render_pdfs.py
```

闭式公式、独立 tile/前缀求和和显式输入/写入事件枚举全部通过；结果见 [synthetic_checks.json](shared/data/synthetic_checks.json)。中文方法 9 页与英文表格 1 页均已渲染并逐页目视检查，见 [PDF 核验](shared/data/pdf_qa.json)。最终 TeX/PDF/JSON 保留，构建及页面渲染中间文件局部忽略。

原始资料仍可运行 `scripts/check_step1.py` 验证。Step 1 的 [原核验记录](data/step1_validation.json) 作为历史保留；本轮未更改其模型/来源原件，也未借本轮状态更新重写已审阅的数据。

Step 3 复算、独立检查与编译：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/pilot/scripts/build.sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/pilot/scripts/render.py
```

22 个主工况、12 个真实 head 边界点、7 个主长度前缀差量与原始结构审计通过。9 页试算 PDF 已逐页查看，见 [核验记录](table_IIb/pilot/data/pdf_qa.json)。原始资料、Step 1/2 计数文件和 Table II(a) 未改；旧文件中的历史状态不覆盖本 README 与研究配置的当前状态。

Step 4 的三类计算与独立检查分别见各分类 README；统一复核入口（默认只读）为：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/crosscheck.py
```

统一数据保持原子任务字段与来源哈希/JSON 位置，不手工改写汇总数字。三份分类 PDF 共 16 页已由主 Agent 亲读并逐页查看；D 的 60 工况独立复核、22 条 pilot 回归与最终交付哈希均已通过。共享方法、模型原件、pilot、Table II(a)、Task I 和主论文不改。

**停止点：Step 4 完成并通过内部复核，待用户审阅；无明确阻塞，具备审阅通过后进入 Step 5 的条件。本轮未启动 Step 5。**
