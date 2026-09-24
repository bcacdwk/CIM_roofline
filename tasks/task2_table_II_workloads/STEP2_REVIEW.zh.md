# Task II · Step 2 审阅

**Step 1已通过；Step 2完成，待审阅。** 2026-09-24。

Step 1 审阅提交为 `e95de9e213d3dd0db9208459b07ce48152f102c9`；实际从干净的 `d60bc32ff83f1ab48cae0ffd106ebd9df46940d0` 继续，未回退。六模型结构/来源原件与 Task I、主论文、理论约定均保持不变；本轮不提交、不推送。

## 两项主要产物

1. [中文方法 PDF](shared/output/counting_method.zh.pdf) / [TeX](shared/tex/counting_method.zh.tex)：9 页，依次说明精度和接口、双边界与分块、通用端点、QKV、FFN、Attention 布局、Prefill/Decode 闭式及独立核验。
2. [Table II(a) 英文 PDF](table_IIa/output/table_IIa.pdf) / [独立入口](table_IIa/tex/table_IIa.tex) / [生成表格片段](table_IIa/tex/table_fragment.tex)：1 页，英文两行五列，每格完整保留 Q_S、Q_R、RI。

配套：[共享机器约定](shared/data/conventions.json)、[Table II(a) 精确数据](table_IIa/data/results.json)、[合成检查](shared/data/synthetic_checks.json)、[PDF 核验](shared/data/pdf_qa.json)。Table II(b) 六模型正式数值没有开始。

## 已落实的主参考

- **精度**：被分析的输入与 resident 数值均为 INT8 逻辑参考，每元素 1 Byte。权重、激活、中间 down 输入、K/V、query 和 Attention 系数分别保留字节宽度参数。部分和在数字域累加，适用的非矩阵处理后重定标到下一角色。Step 1 的 BF16/FP8 是原生事实，未被覆盖；没有模型精度验证。
- **主边界 `ports`**：所有 128×128 tile 实际接收端的有效输入累计。同源广播进入不同 tile/不同求值调用，分别累计；bit-plane、ADC、verify、restore 不新增逻辑 payload。
- **对照边界 `operator`**：整矩阵阶段入口。同一阶段的 Q/G/K/V 或 gate/up 可共享上游源输入；串行 down/AV 输入仍在下一阶段入口计数。这不是整个模型或 FFN 的外部唯一 I/O。分项独立矩阵入口不能未经去重就相加，机器数据保留了去掉的共享重叠量。
- **映射**：每个语义矩阵独立按输出/输入维分块，不跨分支合并尾块。融合源码按语义切片后遵循同样映射；两款 Qwen 的额外 output gate 被完整计入。每个 tile 在声明驻留期只按真实装载次数收费，假定有足够驻留空间。
- **Attention**：每个 KV head 一份 K/V，由 GQA 组内 query heads 共享。K 以 `i×d_QK` 驻留、序列沿输出行增长；V 以 `d_V×i` 驻留、序列沿输入列增长。逐 token 先追加再求值因果前缀。逻辑行/列 append 不补成整 tile 重写，也不宣称各种介质能以相同效率承接。

## Table II(a) 结果

每个窗口一个输入向量，主边界 `Q_S=ceil(N/128)K Byte`。静态行所有格 `Q_R=0, RI=∞`；动态行完整装载一次。

| 形状 N×K | 主边界 Q_S | 动态 Q_R | 动态 RI | tile 求值次数 |
|---|---:|---:|---:|---:|
| 128×128 | 128 Byte | 16 KiB | 1/128 | 1 |
| 1024×1024 | 8 KiB | 1 MiB | 1/128 | 64 |
| 4096×4096 | 128 KiB | 16 MiB | 1/128 | 1024 |
| 1024×4096 | 32 KiB | 4 MiB | 1/128 | 256 |
| 4096×1024 | 32 KiB | 4 MiB | 1/128 | 256 |

所有 N 为 128 的整数倍，因此主口径动态 RI 均精确等于 `0.0078125`。需求比例相同不表示需求规模或运行时间相同。整算子对照的动态 RI 依次为 `1/128, 1/1024, 1/4096, 1/1024, 1/4096`，没有混入英文主表的三元组。

## 四个模板的分析入口

| 模板 | 窗口与核心规则 | 中文稿 |
|---|---|---|
| QKV Projection | 一个 token、权重预驻留；Q、可选 output gate、K、V 分项；同一语义 bank 规则处理融合与独立投影 | §4 |
| FFN / MoE | 单 Dense FFN 或单路由专家；gate/up/down 各装载一次，服务 B 向量；同源 gate/up 与新 down 输入分别交代 | §5 |
| Attention Prefill | 空 KV 开始，逐前缀建立并求值；保留 `L(L+1)/2` 和 `Σ ceil(i/T)` 的精确闭式 | §6–7 |
| Attention Decode | 从 L−1 追加一个，在可见 L 上求值；仅追加元素进入 Q_R | §6–7 |

各模板分项和汇总均给 Q_S、Q_R 与求 RI 的规则；汇总先累计字节，再求比值。B={8,64,512}、L={1024,16384,131072} 及模型顺序未改，不做 B×L 扫描，不乘模型层数、top-k、全部专家或共享专家。

## 验证结果

28 条检查记录全部通过，主要采用三种互相独立的方式：闭式公式、按有效 tile/前缀循环求和、按输入身份/接收端/写入元素显式枚举。枚举实现未调用闭式函数生成预期值。

- 矩形与尾块：包含 `5×7` 配 `3×2` 测试 tile，以及 `129×130` 等真实 128 边界；保存有效形状与调用次数。
- 窗口：静态、装载一次服务多向量、每次使用重载均分别验证；不同角色字节宽度及分数宽度也做合成检查。
- QKV/FFN：额外 output gate、融合后的语义切片规则、gate/up 的上游共享与独立接收端，以及 down 的中间输入通过检查。
- Attention：GQA 组大小、不等宽 QK/V、L=1、跨 tile 边界和 K/V 唯一状态通过检查；增加 query heads 不增加 KV 写入。
- 同一前缀规则下，逐 token Decode 累计与 Prefill 完全相等；`Prefill(L)−Prefill(L−1)=Decode(L)` 对两套 Q_S、Q_R 和调用次数分别成立，不对 RI 做差。
- Table II(a) 全部 10 格、两种边界由独立 tile 求和复算。英文片段、中文数值表与 JSON 由同一生成脚本输出。

合成 GQA 例 `H_q=4,H_kv=2,d_QK=3,d_V=5,L=7,tile=3×2`：Prefill 主口径 `(Q_S,Q_R)=(368,112) Byte`，Decode 为 `(92,16) Byte`；Prefill 从 6 到 7 的差量正是该 Decode。所有例子均为方法检查，不是六模型正式结果。

两份 PDF 均已独立编译、渲染并逐页检查。最终日志无溢出、缺字或未定义引用；具体页数、哈希和核验范围见 PDF 记录。

## 真正需要审阅的选择与停止点

共同参考已明确采用 **INT8 分角色接口、独立语义矩阵 bank、逐前缀因果组织**。需要讨论的是这三个方法选择是否作为后续主参考，而不是重新选择模型、B、L 或重做硬件。

原生模型准确率、数字衔接时间与具体介质 append 可行性均不在本轮验证范围；相关边界已集中说明。当前没有阻止后续代入的公式缺口。

**到此停止，等待审阅；不进入 Step 3。**
