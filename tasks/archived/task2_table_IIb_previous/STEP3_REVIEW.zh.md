# Task II · Step 3 审阅

**Step 2 已通过；Step 3 完成，待审阅。** 2026-09-24。

本轮从干净的当前 HEAD `2eb7e7c59242c675594537002cc1316131be9226` 继续，它也正是用户指定的 Step 2 审阅提交。未回退、提交或推送；修改仅在本任务目录。没有权重下载、模型运行或端到端性能测量，没有启动 Step 4。

## 产物与范围

- [独立中文 PDF](table_IIb/pilot/output/pilot.zh.pdf) / [TeX](table_IIb/pilot/tex/pilot.zh.tex)：9 页，按真实计算、结果解释与方法回查组织。
- [两个主模型四行预览](table_IIb/pilot/PREVIEW.md)：分别显示 ports 和 operator，固定 B/L 顺序。
- [精确 JSON](table_IIb/pilot/data/results.json) / [CSV](table_IIb/pilot/data/results.csv)、[配置与来源哈希](table_IIb/pilot/data/config.json)、[独立检查](table_IIb/pilot/data/checks.json)、[复算入口](table_IIb/pilot/README.md)。

Ministral 3 8B Base 2512 取第 0 层，Qwen3.6-35B-A3B 取第 3 层，均完成 QKV 一个 token、FFN/单专家 B=8/64/512、Prefill 和 Decode 各 L=1024/16384/131072，共各 10 个汇总工况。MiMo-V2.5-Pro 仅取第 7 层 global GQA，完成 L=1024 的 Prefill/Decode 两个工况。主数据共 22 条，分项、双边界、调用数、最终容量与追加切片另存。

## 实际结果与关键解释

下表为 **ports 主口径**精确 RI；B/L 依上述顺序。完整 operator 对照见预览及数据，未混用边界。

| 行 | Ministral 3 8B (2512) | Qwen3.6-35B-A3B |
|---|---|---|
| QKV Projection | ∞ | ∞ |
| FFN / MoE | 1/16, 1/2, 4 | 1/16, 1/2, 4 |
| Attention Prefill | 2177/128, 32897/128, 262273/128 | 2177/64, 32897/64, 262273/64 |
| Attention Decode | 32, 512, 4096 | 64, 1024, 8192 |

1. **静态 QKV 的 ∞ 不能代替需求量检查。** Ministral/Qwen 的局部输入分别为 196608/147456 Byte，调用 1536/1152 次，预驻留权重 24/18 MiB；两者窗口内权重写入均为零。Qwen output gate 单独贡献 65536 Byte 输入、512 次调用和 8 MiB 权重，完整保留。若漏 gate，RI 仍是 ∞，但需求会错。operator 总输入为 4096/2048 Byte，同源分项显式去重。
2. **Dense 与细粒度专家可有相同局部 RI。** 本例 D、F 均整除 128，三矩阵各有 `Q_S=BDF/128`、`Q_R=DF`，汇总为 B/128。Ministral 三矩阵为 168 MiB，Qwen 单专家为 3 MiB；相同 B 下局部输入、写入、tile 数、调用数相差 56 倍。B 只增加服务输入与调用，一次装载、容量和 resident tile 数不变。operator 为 `B(D+F)/(3DF)`，两模型不相同。
3. **两主模型 Attention 的局部输入与调用逐项相同。** `H_q*d_QK` 均为 4096，`H_q*ceil(d_V/128)` 均为 32，两项调用因子也均为 32。Qwen 的每 token KV 写入为 1024 Byte，Ministral 为 2048 Byte，故 Qwen RI 加倍。1K Prefill 两者局部输入均为 35667968 Byte，写入分别 1/2 MiB；1K Decode 输入均为 65536 Byte，写入仅 1024/2048 Byte。
4. **Prefill 与 Decode 的差别来自窗口和状态复用。** Prefill 写入是同 L Decode 的 L 倍，输入是从 1 至 L 的逐步 Decode 输入和。固定三档 L 下，ports 输入比为 `(2L+129)/4`、RI 比为 `(2L+129)/(4L)`，1K 分别为 544.25 和 2177/4096。差量一致性只对应当前逐前缀组织，不是其它执行方式的性能结论。
5. **MiMo 半宽尾片影响有效字节，不删除调用。** 1K Decode：ports `(327680,2560,128)`；operator `(155648,2560,304/5)`。QK 的 2048 次调用中，1024 次接收 128 Byte、1024 次接收 64 Byte；AV 另有 1024 次调用。Prefill：ports `(180420608,2621440,2753/40)`；operator `(92340224,2621440,1409/40)`。最终有效 KV 2.5 MiB、tile 分配 3 MiB；Decode 的 Q_R 仅 2560 Byte。未据半宽片推断服务时间减半，也未修改 Task I。

## Step 1/2 的判断：保持

没有发现需要修正的提取、公式或实现错误；共享版本继续为 `WS128-INT8-semantic-banks-v1`，Table II(a) 数据/PDF 无变化。这个判断有具体依据：

- 原始配置抽查：Ministral HF text_config 与 params.json 对应；V 的 null 特殊维度由固定实现明确回落到 128。Qwen 第 3 层 full GQA、16/2 heads、256 维、额外 gate 和宽 512 专家均得到配置与源码支持。MiMo 第 7 层 global、192/128、Value 缩放 0.612 与无全局 sink 均一致。
- 原生融合交接：Qwen q_proj 按 head 打包 Q/G，切片后恰好覆盖 8192 行且互不重叠；gate/up 打包后仍按两个语义矩阵计数，down 的中间输入保留。源码的输出 gate、SwiGLU gate、路由 gate 和共享专家 gate 没有混为一个对象。
- KV 共享与方向：固定实现先更新未扩展 KV，再供 GQA 求值。参考 K 为 token 行、V 为 token 列，每 KV head 一份。K/V 建立与 append 不混入预驻留投影权重的 Q_R；scores 不另计输入，softmax 系数在 AV 入口计一次。
- 独立复算：22 条主工况的分项与汇总、两边界精确字节/RI/调用数一致。真实矩阵以 tile 切片复算；Attention 以 tile 生存期反向累加，不拿同一个闭式生成预期值。三种真实 head 在 L=1/127/128/129 的 12 个检查点枚举接收和追加身份；7 个主长度再检查 Prefill 差量。

原始 Step 1 配置、实现快照、结构卡、models.json 未改。旧审阅稿及共享文件的当时状态作为历史保留；当前研究状态在 README 与 study_plan.json 更新。

## 映射能支撑什么

足够驻留空间、独立语义矩阵分块、逐前缀因果组织，可以完整描述这 22 个参考工况。相同比例是该合理参考的结果，不是必须制造差异的失败；容量与总需求不能由 RI 推定。

只做了一个最小映射对照：Qwen 1K Decode 若持久复制 KV 至每个 query head，保持输入和调用相同，写入从 1024 增至 8192 Byte、容量从 1 增至 8 MiB，ports RI 从 64 降至 8；operator 从 20 降至 5/2。它说明 GQA 的需求优势依赖共享状态组织，没有替换主参考，也没有宣称复制的并行性能收益。

后续可使用现有分项检查聚合资源、K 行/V 列更新粒度和半宽尾块。实际硬件容量、追加效率、数字衔接时间与并行调度仍需对应实现，不能把总 RI 直接套单 macro 吞吐或据此给器件排名。本轮未扩张设计空间、重做硬件或修改理论边界。

## 复算、编译和停止点

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/pilot/scripts/build.sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/pilot/scripts/render.py
```

主计算/独立检查均通过；Step 1 的 50 份来源哈希与六模型结构只读回查通过，Step 2 的 28 项合成检查、Table II(a) 10 格双边界数据一致性通过。独立中文 PDF 已编译并逐页渲染核验，具体记录见 [pdf_qa.json](table_IIb/pilot/data/pdf_qa.json)。

**无明确阻塞；具备在 Step 3 审阅通过后进入 Step 4 的条件。本轮停在 Step 3，不开展剩余模型或并行分工。**
