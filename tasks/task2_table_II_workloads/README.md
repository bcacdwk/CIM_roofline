# Task II：resident–streaming 模型与矩阵工作量

**状态：Step 1完成，待审阅。** 本轮日期：2026-09-23。

本任务建立模型无关的驻留端点，以及六个固定 LLM 的真实矩阵阶段需求。重点是操作数角色、状态写入与驻留复用。分析只覆盖语言主干矩阵子层，不进行端到端性能、精度、硬件仿真、完整训练建模或器件适配排名。

## 阅读入口

1. [Step 1 中文审阅](STEP1_REVIEW.zh.md)：六模型概览、工况覆盖、来源差异及下一阶段问题。
2. [研究配置](data/study_plan.json)：固定 B、L、两个子表的行列、窗口与五阶段状态。
3. [模型结构数据](data/models.json)：六个固定 checkpoint/revision，配置键与实现定位，原生矩阵、缓存、专家及上下文条件。
4. [来源清单](data/sources.json)：下载 URL/DOI、发布日期或明确缺省原因、revision、获取时间、本地路径、SHA-256。
5. [共同算法与实现资料](literature/00_shared/README.md)。每个模型的中文结构卡见下表；`raw/` 保存原始文件，`extracted/` 是便于检索的派生文本，不冒充原件。

| 固定列序 | 显示名 | 结构卡与本地资料包 |
|---|---|---|
| 1 | Qwen3.5-2B | [01_qwen35_2b](literature/01_qwen35_2b/STRUCTURE.zh.md) |
| 2 | Ministral 3 8B，2512 | [02_ministral3_8b](literature/02_ministral3_8b/STRUCTURE.zh.md) |
| 3 | Qwen3.6-35B-A3B | [03_qwen36_35b_a3b](literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) |
| 4 | Tencent Hy3，295B | [04_hy3_295b](literature/04_hy3_295b/STRUCTURE.zh.md) |
| 5 | Ling-1T | [05_ling_1t](literature/05_ling_1t/STRUCTURE.zh.md) |
| 6 | MiMo-V2.5-Pro | [06_mimo_v25_pro](literature/06_mimo_v25_pro/STRUCTURE.zh.md) |

## 起点与已完成基线

用户给出的检查点与实际本地起点 HEAD 均为 `81b7c332c20b9b5be6890256e9cf0d3edab12785`，不回退。起点已有 `.DS_Store` 和 `2026.9.23 CIM Roofline 邵瀚雅.pptx` 修改，本轮未处理这些文件。全部交付位于本任务目录，不暂存、提交、推送或重置 Git。

已阅读 [MODEL_CONVENTIONS](../../docs/MODEL_CONVENTIONS.md)、[Task I 共享基线](../task1_table_I_NVM/analysis/shared_baseline/README.md)、[十例约定](../task1_table_I_NVM/analysis/TEN_CASE_CONVENTIONS.zh.md) 与 [十例审阅](../task1_table_I_NVM/analysis/TEN_CASE_REVIEW.zh.md)。旧稿的 candidate/待审阅标签不推翻用户确认的完成状态。Task I 的十类硬件估算是固定输入：共同 28 nm 外围、128×128 INT8 矩阵乘向量、每次 128 Byte 输入、矩阵 16384 Byte=16 KiB；本轮未更改。

`tasks/archived/task2_table_ii/` 不作为本次模型、计数或结果基线；早期论文也不提供本轮继承的 workload 数字。

## 计量与研究边界

Q_S 是窗口内经过声明 streaming 输入边界并被服务的逻辑操作数字节累计量；Q_R 是窗口内建立、更新或重载可计算 resident 状态的逻辑写入字节累计量。RI=Q_S/Q_R；静态驻留 Q_R=0 时 RI=∞。它们不是 GPU/HBM 流量或驻留容量的同义词。

窗口内初始写入、更新、重载须按实际声明计入；内部编码、位串行、广播、verify、refresh/restore 不自动变成新的逻辑 payload。独立接收端口、映射重放和输入复用的边界留到 Step 2 明确。输出不直接加入本次 Q_S；若成为后续矩阵求值输入，在后次服务计数。Attention 的 query 与 Attention 系数是两次矩阵任务的不同输入。

选择原生完整/全局 GQA 子层，保留原生 Q/K/V、额外门控、FFN 和专家结构。混合线性层、SWA、视觉/音频编码器、MTP、embedding/LM head 均不展开；选择的单层不代表整个模型。模型原生 dtype 与未来 CIM 参考精度分别记录，streaming、resident、KV、Attention 系数精度尚未选定，不能直接把 BF16 需求配 Task I 的 INT8 能力。

## Table II(a)：模型无关的驻留端点

两行固定为：

1. **Weight-static**：权重预驻留，窗口内不写入。
2. **Per-use reloaded**：每次使用前完整写入被分析权重。

“一次使用”按一个输入向量求值定义，第二行不是完整训练 step。resident 矩阵 W 为 N×K，N 是输出维度、K 是输入维度。五列依次是 **(128,128)、(1024,1024)、(4096,4096)、(1024,4096)、(4096,1024)**。它们是逻辑任务形状，不是五种新物理 macro。最终每格保留 Q_S、Q_R、RI。

## Table II(b)：真实模型的四类推理工况

六列顺序见上表，四行固定为：

1. **QKV Projection**：选中完整 GQA 的模型原生 QKV 投影，权重预驻留，按一个输入 token 的矩阵需求分析；原生额外投影输出在结构卡中保留。
2. **FFN / MoE**：Dense 取一个 FFN，MoE 取一个路由专家的 FFN；一次装载后服务 B 个输入向量，再发生替换。
3. **Attention Prefill**：从本段空 KV 状态开始，建立长度 L 的 KV，完成相应因果 Attention 矩阵任务。
4. **Attention Decode**：已有 L−1 个 token 的 KV，本次追加一个，求值可见长度为 L。

**B={8,64,512}**，表示同一份 FFN/专家权重一次驻留期间实际服务的输入向量总数，不是批次数，也不自动等于全模型全局 batch size。**L={1024,16384,131072} token**，显示为 {1K,16K,128K}，这里 K=1024。B 仅用于 FFN/MoE，L 仅用于 Attention 两行，不做 B×L 全组合扫描。

驻留策略、B、L 是本研究选定工况，不是需要从模型报告验证的部署事实。主表优先突出 RI，适用行依既定 B/L 顺序显示三个值；完整 Q_S、Q_R、RI、配置与推导后续保存在底稿/机器数据中。

两个子表后续独立制备、独立编译。本轮仅记录设计，没有场景 Q_S/Q_R/RI 数值或最终 TeX 表格。

## 五阶段与后续目录

| 阶段 | 内容 | 状态 |
|---|---|---|
| Step 1 | 固定六模型、结构参数及本地资料 | **完成，待审阅** |
| Step 2 | 共享方法与通用驻留端点 | 未启动 |
| Step 3 | 少量真实模型试算 | 未启动 |
| Step 4 | 分类并行分析 | 未启动 |
| Step 5 | 统一复核与英文表格 | 未启动 |

未来 `shared/` 保存统一计数方法；`table_IIa/`、`table_IIb/` 各保存自己的推导、程序和独立 TeX/PDF。当前未创建这些目录中的空正文或占位结果。`literature/00_shared/` 的共同原始资料只存一份，模型卡以相对路径引用。

## 本地可用性与检查

六个版本的模型卡、配置及必要实现均已保存；Ministral 和 Ling 的确切技术报告全文已下载，另有三份共同算法论文。其它四个模型未找到确切版本的独立报告，已用官方完整模型卡/说明、配置、实现组成主要证据；没有把摘要当作全文核对。没有下载权重、安装/执行模型或运行第三方代码。

`.gitignore` 只在本任务局部保护未经明确再分发授权的论文全文及其提取文本、官网全文快照；它们已在本机可读。新 checkout 不含这些忽略文件时，可按 `sources.json` 的固定版本 URL 补取。GQA 论文为 CC BY 4.0，保留原始署名及许可证元数据。模型卡声明许可证和实现文件头的许可证分别保留，不据模型权重许可证推定所有网页可再发布。

运行轻量检查（Python 标准库，无网络、不加载模型；本机使用已可用的 Anaconda Python）：

```sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/scripts/check_step1.py
```

检查源文件哈希、JSON/配置键、六列与固定扫描参数、层型、矩阵形状、专家元素数及必要本地路径。检查记录见 [step1_validation.json](data/step1_validation.json)。PDF 的全文可提取性与结构相关页目视检查另记录其中；未声称逐页审读与本研究无关的 benchmark/训练章节。

**停止点：等待用户审阅；不启动 Step 2。**
