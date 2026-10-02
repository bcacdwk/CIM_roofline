# Task II：算子级输入复用与模型工作负载

**2026-10-02：用户认可前三份中文稿的结构与计算；主 Agent 按新意见统一 U、扫描和小数结果，修订待用户审阅。** 当前目标是比较原生模型矩阵和不同工作负载的 RI，不引入硬件分块或器件性能。

## 当前入口

- [Table II(a)](table_IIa/README.md)：一次权重装载、U 次向量服务，RI=U/N；五种矩阵 × U=1/128/1K/16K/128K/1M/∞。
- Table II(b) 当前只使用下面四个目录。此前三个 Agent 已完成初稿，本轮由主 Agent 亲自修订，均按同一模板组织。

| 目录 | 职责 |
|---|---|
| [01_qkv_projection](table_IIb/01_qkv_projection/README.md) | [中文PDF](table_IIb/01_qkv_projection/output/report.zh.pdf)：QKV与原生额外gate；一次装载与U扫描 |
| [02_ffn_moe](table_IIb/02_ffn_moe/README.md) | [中文PDF](table_IIb/02_ffn_moe/output/report.zh.pdf)：单FFN／单专家；一次装载累计服务U个向量 |
| [03_attention](table_IIb/03_attention/README.md) | [中文PDF](table_IIb/03_attention/output/report.zh.pdf)：原生完整/global GQA的Prefill与Decode |
| [04_crosscheck](table_IIb/04_crosscheck/README.md) | 统一约定、中文模板、格式接口、合并与复核 |

[共同合同](table_IIb/04_crosscheck/CONTRACT.zh.md) 已固定记号、计数边界、公式、文件名和中文正文顺序。三个正文均按“对象与公式—模型信息—代入结果—结果说明”组织，使用同一排版入口。

## 计数口径

一般投影为 X[U,K]×Wᵀ[K,N]→Y[U,N]。输入、权重及相关中间矩阵输入均按1 Byte/element计数；U 为复用次数（reuse count），是一次装载后累计服务的向量数，包含首次使用；可跨多个 batch/请求。

复合工作负载统一使用**矩阵阶段入口**：同阶段并行分支共享源输入只计一次，不同阶段的新输入再计。FFN 计 x 与 down 输入 z，Attention 计 query 与注意力系数。Q_R 是当前窗口建立/追加/装载驻留状态的有效字节累计，初末有效容量另列。

本轮原生矩阵、层号、checkpoint 与精度来源不变；不使用 tile、分配容量或接收端重复系数形成主结果，不预测运行时间。

## 固定工况

- QKV：用户确认改为完整权重装载一次，U=1、1K、128K、1M，另列 U→∞ 极限。保留 Q、可选 gate、K、V，不含输出投影。
- FFN/MoE：U=1、16、128、1K、16K；Dense 取单 FFN，MoE 取单路由专家，不乘 top-k、专家总数、共享专家或层数。
- Attention：Prefill 与 Decode 各 L=1K、8K、64K。每 KV head 一份 K/V；Prefill 空状态建立到 L，Decode 从 L−1 追加一个后求值。保留 MiMo 原生不等宽维度与 Ling 64K 的已固定官方扩展条件。

1K=1024、1M=1024²。PDF/预览的 RI≥1 保留一位小数，RI<1 保留三位有效数字；JSON/CSV 保留精确值。

合计90个有限工况、6个QKV极限格，全部已复算；统一目录包含精确数据、预览和主审阅记录。无穷是极限标记，不是有限批次的零写入记录。

## 原始模型资料

模型顺序、revision 与结构入口见 [models.json](data/models.json)、[sources.json](data/sources.json)；本轮研究配置见 [study_plan.json](data/study_plan.json)。

| 固定顺序 | 模型与结构卡 | 所选层（零起点） |
|---|---|---:|
| 1 | [Qwen3.5-2B](literature/01_qwen35_2b/STRUCTURE.zh.md) | 3 |
| 2 | [Ministral 3 8B Base 2512](literature/02_ministral3_8b/STRUCTURE.zh.md) | 0 |
| 3 | [Qwen3.6-35B-A3B](literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) | 3 |
| 4 | [Tencent Hy3](literature/04_hy3_295b/STRUCTURE.zh.md) | 1 |
| 5 | [Ling-1T](literature/05_ling_1t/STRUCTURE.zh.md) | 4 |
| 6 | [MiMo-V2.5-Pro](literature/06_mimo_v25_pro/STRUCTURE.zh.md) | 7 |

本地原始资料足够使用，无需下载权重或运行模型。结构卡的旧状态文字属于原提取记录，当前工作以本 README 和共同合同为准。

## 旧材料

旧三类稿件、pilot、旧复核汇总及 Step 3/4 审阅记录已整体移入 [archived](../archived/task2_table_IIb_previous/README.md)，不再作为当前表格入口。旧operator数值用于迁移核对；旧ports口径不进入新正文。`shared/` 的旧映射方法是历史材料，不定义此次重写。

当前不做 Step 5 论文整合，不修改 Task I、理论约定、模型原件；II(a) 的记号、扫描与中文表述按本轮授权更新。所有 Git 暂存、提交、推送、重置和分支切换均由用户处理。
