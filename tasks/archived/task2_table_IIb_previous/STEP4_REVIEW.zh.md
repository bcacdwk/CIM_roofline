# Task II · Step 4 审阅

**Step 3 已通过；Step 4 完成，待用户审阅。** 2026-09-25。三类交付、Agent D 独立复核和主 Agent 内部验收均已完成；不代表用户已通过 Step 4。

本轮从干净的当前 HEAD `e472a0d864b8fb9afb14b0c306217a0e5653e122` 开始，它也是 Step 3 审阅提交。主 Agent 实际启动三个计算子 Agent 并行工作；首个任务交付后释放并发名额，启动第四位独立复核 Agent。共享版本始终为 `WS128-INT8-semantic-banks-v1`。没有 Git 暂存、提交、推送、重置或分支切换。

## 实际分工与交付入口

| Agent | 独占目录与入口 | 工况 | 当前交付 |
|---|---|---:|---|
| A：`/root/qkv` | [QKV README](table_IIb/01_qkv_projection/README.md)、[PDF](table_IIb/01_qkv_projection/output/pdf/qkv.zh.pdf)、[TeX](table_IIb/01_qkv_projection/tex/qkv.zh.tex) | 6 | revision 2，4 页 |
| B：`/root/ffn` | [FFN/MoE README](table_IIb/02_ffn_moe/README.md)、[PDF](table_IIb/02_ffn_moe/output/ffn_moe.zh.pdf)、[TeX](table_IIb/02_ffn_moe/tex/ffn_moe.zh.tex) | 18 | revision 2，4 页 |
| C：`/root/attention` | [Attention README](table_IIb/03_attention/README.md)、[PDF](table_IIb/03_attention/output/attention.zh.pdf)、[TeX](table_IIb/03_attention/tex/attention.zh.tex) | 36 | revision 1，8 页 |
| D：`/root/crosscheck` | [复核报告](table_IIb/04_crosscheck/REVIEW.zh.md)、[README](table_IIb/04_crosscheck/README.md) | 60 独立复核与汇总 | revision 1，内部通过 |

各计算目录提供六模型概览、精确 JSON/CSV、来源配置、计算与独立检查、PDF QA 和锁定哈希的 DELIVERY。目录外只读，主 Agent 只维护状态、协调与本审阅记录，没有接管三类计算程序或详细推导。共同接口和交付/修订过程见 [STEP4_COORDINATION.zh.md](STEP4_COORDINATION.zh.md)。

统一入口：[精确 JSON](table_IIb/04_crosscheck/data/results.json) / [CSV](table_IIb/04_crosscheck/data/results.csv)、[四行六模型双边界预览](table_IIb/04_crosscheck/PREVIEW.zh.md)、[独立检查记录](table_IIb/04_crosscheck/data/checks.json)。JSON 保留完整分项、直方图、上下文条件与来源追踪；CSV 有 412 条数据行及 1 行表头、30 列。该预览是 Step 4 研究入口，不是 Step 5 的最终英文论文表格。

## 覆盖与口径

固定模型顺序为 Qwen3.5-2B、Ministral 3 8B Base 2512、Qwen3.6-35B-A3B、Tencent Hy3、Ling-1T、MiMo-V2.5-Pro；所选零起点层号为 3、0、3、1、4、7。

QKV 每模型一个 token；FFN 每模型 B=8/64/512；Attention 每模型 Prefill/Decode 各 L=1024/16384/131072，合计 **60 个唯一汇总工况**。其下共有 20 个 QKV、54 个 FFN、72 个 Attention 矩阵分项实例，共 146 项。pilot 的 22 条是这 60 条中的重叠部分，没有新增成 82 条。

三类主流程均从已审阅模型入口重新生成，未复制 pilot 条目；ports 与 operator 的精确 Q_S、Q_R、RI 分别保存。分角色 1 Byte、独立语义矩阵、GQA 唯一状态与逐前缀组织均未变化。operator 的 QKV 同源输入和 FFN gate/up 输入显式去重，down 与 AV 新输入继续收费。累计写入、有效容量与完整逻辑 tile 槽位分开记录。

## 六模型最重要的实际结果

### QKV：同为静态端点，规模并不相同

六模型 ports 输入依次为 **81920、196608、147456、327680、655360、1302528 Byte**；权重有效/分配容量依次 **10、24、18、40、80、159 MiB**，调用数依次 **640、1536、1152、2560、5120、10176**。窗口内写入均为零，所以两个边界 RI 均为 ∞；并非没有权重状态或所有需求相同。

两款 Qwen 的 output gate 完整保留，分别贡献 32768/65536 Byte 局部输入和 4/8 MiB 权重。Hy3 的 Q 是 8192×4096，不能按 hidden size 默认为方阵。Ling 与 Hy3 投影输出宽度相同，但输入 D 翻倍，因此需求和容量也翻倍。MiMo 的投影两轴都整除 128；其 Attention 的 192 维输入尾片不能搬到 QKV 再做每头填充。

### FFN：六模型局部 RI 相同，分项仍有价值

六组 D、F 均整除 128，三矩阵各装载一次且角色等宽，所以 ports 汇总 RI 均为 **B/128 = 1/16、1/2、4**。三矩阵容量依固定模型序为 **36、168、3、18、48、36 MiB**。B 增大只提高输入累计与求值调用，不提高本驻留期的一次装载量或状态容量。

Qwen3.5 的 D/F=2048/6144 与 MiMo 的 6144/2048 互换，使 ports 及 operator 汇总需求都相同；但 gate/up 和 down 的 operator 分项互换，共享输入扣除不同。例如 B=64，前者独立入口为 128/128/384 KiB、扣除 128 KiB，后者为 384/384/128 KiB、扣除 384 KiB，汇总均为 512 KiB。相同总 RI 不能替代组件需求，也不能由 Dense/MoE 标签推定差异。

### Attention：共享比例、维度与状态规模共同决定结果

ports RI 分为三组：Qwen3.5/Ministral 相同；Qwen3.6/Hy3/Ling 相同；MiMo 另成一组。三档 Decode RI 分别为 **32/512/4096**、**64/1024/8192**、**128/2048/16384**。相同 RI 的组内仍可有两倍的输入、写入、容量和调用规模差别。

Hy3 与 Ling 的 H_q/H_kv/d_QK/d_V 完全相同，所选单层 Attention 的两边界数值均相同；Ling 的 128K 工况仍明确要求官方 YaRN factor=4、original=32768、type=yarn 与运行端长度 131072，不改原始配置。Qwen 的 d_V=256 使 AV 的 ports 输入有两组输出 tile 接收；operator 不含这一重放，因此能区分部分相同 ports RI 的模型。

MiMo 全局第 7 层保留 QK/V=192/128。1K Decode 的 QK 2048 次调用中，1024 次输入 128 Byte，1024 次输入 64 Byte；AV 另有 1024 次调用。128K 最终有效 KV 为 320 MiB、完整槽位为 384 MiB，Decode 本次写入仍仅 2560 Byte。半宽尾片降低有效 payload，不消除调用，更不自动缩短完整服务时间。

Prefill 是当前逐前缀组织的累计窗口，Decode 是单次追加窗口；差量关系只对同组织下的字节和调用成立，不对 RI 做相减，也不推广为所有实现的性能结论。结果不用于单 macro 延迟、器件排名或端到端性能预测。

## 主 Agent 亲审与修订

主 Agent 亲读三份完整 TeX、六模型概览与相关来源，抽查 Hy3 原生 Q 投影构造、Ling 融合/共享/官方扩展、MiMo cache update；查看三份最终 PDF 的全部 **16 页**渲染图，并亲自运行各目录 generate/check 默认只读入口，全部通过。

发现并落实的文稿问题有两项：A/B 第一版已有通式和结果，但缺少连续数字代入链；已要求责任 Agent 补 Qwen3.6 的代表例，使矩阵、tile、分项字节、去重、调用和 RI 连续可读。A 还将本地容量符号 M 改为 C_R，避免与理论约定的有用 OP 符号混淆。修订后仍为 4/4 页，已重新编译渲染并亲审；数值数据和计算源码哈希不变。

没有发现需要更改 Step 1 参数、Step 2 方法或 Step 3 pilot 的问题。各类独立检查分别从原始配置与真实 tile/输入身份或 tile 存活期得到预期值，没有把生产函数返回值当作独立验证。主 Agent 随后亲读 D 的完整报告、独立程序和统一预览，确认覆盖与结论一致；D 预览中“每 head”已明确为“每 KV head 一份 K/V”，科学数据不变。

## 独立复核、复现与停止条件

D 最终锁定 **A2/B2/C1**，52 个上游清单项哈希通过；统一数据逐条保留原目录、results 路径/哈希、DELIVERY revision/hash、case_id 和 JSON Pointer。独立 oracle 从原始配置重提维度，显式切 tile、按输入身份去重，对 Attention 反向累计序列 tile 存活期与元素参与次数，不导入生产计数函数或上游生成器形成预期值。

- **60 个汇总、146 个分项全覆盖且唯一**；模型、行、B/L 顺序及版本、层号、精度和窗口一致。29,122 个 result 叶字段精确一致，包括双边界需求、容量、调用、追加和直方图；这是覆盖计数，不是把每个字段当成独立数学证明。
- **22 个 pilot 重叠工况的 3,787 个既有叶字段完全一致，差异为空**。Attention 正式数据新增初始布局、调用形状直方图、每 token 追加与上下文诊断；新增字段也独立检查，未覆盖 pilot 消除差异。
- **5 项既有只读回归全通过**：Step 1 六模型与 50 份原始来源；Step 2 的 28 项合成记录及 Table II(a) 10 格双边界；pilot 的生成一致性和独立检查。历史 PDF 未重编。
- 固定 HEAD 未改变、暂存区为空。全仓已有 tracked 文件仅任务 README/study_plan 的授权状态更新；其科学输入子集相对 HEAD 不变。原始资料、models、shared、pilot、Table II(a)、Task I 与主论文保持不变。

从仓库根执行最终统一复核及交付哈希检查：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/crosscheck.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/verify_delivery.py
```

三份分类 PDF 已分别成功编译，最终 4/4/8 页均经责任 Agent 与主 Agent 逐页查看。统一精确数据、只读复算与保护检查通过；没有未解决的数值差异、来源缺口或共享方法修改建议。

**具备在用户审阅通过后进入 Step 5 的条件。** Step 5 可进行最终英文 Table II(b) 的版面提炼与论文整合；本轮没有开展它，也没有增加场景、器件匹配或性能分区。实际硬件聚合资源、更新粒度与数字交接仍是后续使用需求数据时必须保持的适用条件，不是本轮计数阻塞。

**本轮到 Step 4 内部验收为止，等待用户审阅。**
