# 共享计数方法

**Step 2完成，待审阅。** 主参考为 `WS128-INT8-semantic-banks-v1`。

- [中文方法 PDF](output/counting_method.zh.pdf) / [TeX](tex/counting_method.zh.tex)：按“前提—公式—例子—结论”逐节审阅。
- [机器约定](data/conventions.json)：双边界、精度、驻留窗口、语义矩阵分块、GQA 与 append 方向、全部符号模板。
- [精确计算器](scripts/counting.py)：Python 标准库与 Fraction；只接收维度，不读取六模型做批量求值。
- [独立检查](scripts/check_counting.py) / [合成检查数据](data/synthetic_checks.json)：闭式、独立分块求和、显式输入/写入事件枚举。
- [PDF 核验记录](data/pdf_qa.json)。

`ports` 是主口径：所有 128×128 tile 的有效输入接收累计。`operator` 是对照口径：整矩阵阶段入口，同源并行分支输入去重，串行阶段的下一次输入重新计入。分项 `operator` 数据包含各矩阵独立入口；QKV 和 FFN 汇总会显式扣除共享输入的重叠。`ports` 接收端不同，直接累计。

所有角色在本参考均为 1 Byte/element INT8；输入、FFN 中间激活、query、Attention 系数、各类权重、K/V 的宽度仍为独立参数。原生 BF16/FP8 和长上下文条件继续从 Step 1 原件读取。这里不验证 INT8 准确率，不估计非矩阵数字处理的执行时间。

每个语义矩阵有自己的分块网格，不跨 Q/G/K/V 或 gate/up 合并尾块。源码融合不改变此规则。驻留空间足够，无容量触发的重载；输入维部分和在数字域累加。有效尾块形状、调用次数与逻辑写片段保留，不能用有效字节比例推断完整服务时间。

Attention 采用逐 token 的因果前缀：先 append，再求值全部 query heads。K resident 为 `i × d_QK`，V resident 为 `d_V × i`；追加分别是行与列。GQA 每个 KV head 仅存一份状态。精确求和包含 `L(L+1)/2` 和 `sum ceil(i/T)`；并检验与逐步 Decode 的累计/差分一致。

从仓库根检查并独立编译两个 PDF：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/shared/scripts/build.sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/shared/scripts/render_pdfs.py
```

默认检查不写数值数据。明确改动公式或共同参考后，需要先分别运行 `check_counting.py --emit`、`generate_IIa.py --emit` 刷新派生文件，再构建并重新查看 PDF。`build/`、`tmp/` 局部忽略；最终 PDF、TeX、JSON 和脚本保留。

**Table II(b) 只有符号模板及合成检查，六模型正式数值未开始。**
