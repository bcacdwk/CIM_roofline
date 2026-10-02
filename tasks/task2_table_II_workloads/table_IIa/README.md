# Table II(a)：一次装载与复用次数 U

2026-10-02：主 Agent 按用户审阅意见改为中文前置讨论，统一 U、扫描档位与小数显示；数学公式与计数边界保持。修订待用户审阅。

- [中文 PDF](output/table_IIa.pdf)、[TeX](tex/table_IIa.tex)、[表格片段](tex/table_fragment.tex)、[中文预览](PREVIEW.zh.md)。
- [配置](data/config.json)、[精确 JSON](data/results.json) / [CSV](data/results.csv)、[独立检查](data/checks.json)、[逐页 QA](data/pdf_qa.json)。
- 既有 [历史快照](history/ports_v1/README.md) 和 [来源记录](data/rewrite_provenance.json) 保持原样，本轮不新增归档。

U 为复用次数（reuse count）：一次完整权重装载后累计服务的输入向量数，包含首次使用，可以跨 batch 或请求。X[U,K] 是累计向量的行矩阵表示，不要求一次执行 U 行。W[N,K]，Y=XWᵀ；等宽 1 Byte 时，**Q_S=UK、Q_R=NK、RI=U/N**。Q_S 不含本阶段输出或 resident 操作数的重复读取。

五种原有矩阵形状不变；七列为 **U=1、128、1K、16K、128K、1M、∞**。1K=1024，1M=1024²。共30个有限工况、5个极限格。U→∞ 仍有有限的一次权重写入；不是无限 batch，也不将 Q_R 设成零。

所有字节用 Python 整数计算，比例用 Fraction 精确计算。PDF/预览中 RI≥1 保留一位小数，RI<1 保留三位有效数字；显示用 Decimal、ROUND_HALF_UP。原始精确分数留在 JSON/CSV，显示不能作为后续计算输入。

从仓库根复算；前两条默认只读，--emit 才刷新结果和检查记录：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIa/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIa/scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIa/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIa/scripts/render.py
```

独立检查按输入行与权重行计数，并用小规模元素身份枚举核对非整齐尺寸与不同字节宽度；极限单独验证固定正写入和正输入增长。所有 PDF 渲染后逐页目检，再记录 QA。当前正文共用 II(b) 的排版文件，显示函数位于任务根 `scripts/format_results.py`；计数公式不依赖 II(b) 的模型参数。
