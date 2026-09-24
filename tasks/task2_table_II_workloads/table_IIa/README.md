# Table II(a)：通用驻留端点

**Step 2完成，待审阅。**

- [独立英文 PDF](output/table_IIa.pdf) / [独立 TeX 入口](tex/table_IIa.tex)。
- [可复用表格片段](tex/table_fragment.tex)：英文两行五列，每格包含 Q_S、Q_R、RI；由脚本生成，主口径为 `ports`。
- [完整精确数据](data/results.json)：两行 × 五种形状，同时保留 `ports` 与 `operator`，不在同一三元组中混用。
- [中文推导](../shared/output/counting_method.zh.pdf)：第 2–3 节；[TeX](../shared/tex/counting_method.zh.tex)。
- [生成脚本](../shared/scripts/generate_IIa.py)：同时生成 JSON、英文片段及中文数值表。

一个窗口对应一个输入向量。Weight-static 的窗口内写入为零；Per-use reloaded 在求值前完整写入矩阵一次。INT8 输入/resident 均为 1 Byte/element。主参考按 128×128 tile 接收端累计：

`Q_S = ceil(N/128) × K Byte`，动态 `Q_R = N × K Byte`。

五个固定形状的 N 都整除 128，故动态 RI 均为精确 `1/128`；静态均为 ∞。矩形两个方向的主口径需求相同是这套映射的结果，不人为增加差异。整矩阵对照口径是 `Q_S=K Byte`，动态 `RI=1/N`，仅在机器数据与中文说明中另列。

表格片段需要 `booktabs`、`tabularx`、`array`，不包含 documentclass、导言区或固定表编号；独立入口设置表号 II(a)。未来可直接在论文中 `input` 片段并按论文规则编号。

共同构建：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/shared/scripts/build.sh
```

只编译本表（可独立进行）：

```sh
cd tasks/task2_table_II_workloads/table_IIa
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build tex/table_IIa.tex
cp build/table_IIa.pdf output/table_IIa.pdf
```

本目录不包含模型专属结果或器件性能预测。
