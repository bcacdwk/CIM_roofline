# Step 3：真实模型试算

**完成，待审阅。** 固定共享方法 `WS128-INT8-semantic-banks-v1`；起点 HEAD 和 Step 2 审阅提交均为 `2eb7e7c59242c675594537002cc1316131be9226`。

本目录仅计算 Ministral 3 8B（2512，第 0 层）、Qwen3.6-35B-A3B（第 3 层）各 10 个工况，以及 MiMo-V2.5-Pro 第 7 层 global GQA 的 L=1024 Prefill/Decode 两个定点。L=1/127/128/129 仅用于检查，不增加主表场景。没有计算其余模型或启动 Step 4。

- [中文研究稿 PDF](output/pilot.zh.pdf) / [独立 TeX](tex/pilot.zh.tex)：真实结构、四类代入、比例解释、MiMo 尾块、独立回查和一个最小映射对照。
- [两模型四行预览](PREVIEW.md)：ports 主口径与 operator 对照各自显示；固定 B/L 顺序，精确 RI。
- [完整 JSON](data/results.json) / [平铺 CSV](data/results.csv)：两边界各自的 Q_S、Q_R、RI；所有矩阵分项；容量、tile、调用、追加记录。
- [输入快照与版本](data/config.json)：固定模型 revision、层号、参数、原件和共享方法 SHA-256；以 models.json 为主计算入口，原始配置由独立检查再提取。
- [独立检查](data/checks.json)：22 主工况、12 个真实 head 边界点、7 个主长度差量；原始证据定位与输入宽度调用分布。
- [PDF 核验](data/pdf_qa.json)；[Step 3 审阅](../../STEP3_REVIEW.zh.md)。

四行窗口是独立研究场景。ports 分项可相加；operator 的 QKV 同源输入和 FFN gate/up 同源输入须去重，去掉的重叠量另存。输出不重复计入；down 和 AV 输入保留。MoE 为单路由专家，不乘 top-k、全部或共享专家。

Byte 数据与分数不取整。JSON 非整数分数用 `{numerator, denominator}`，无穷用字符串 `infinity`；CSV 精确分数用 `a/b`。调用数仅随 ports 记录，operator 的空调用字段不表示无计算。`capacity.valid_resident_bytes` 为窗口最终有效状态；`allocated_tile_bytes` 是 128×128 完整逻辑 tile 的槽位容量，非物理编码面积/容量；两者与累计 Q_R 分开。Attention 的 `append.logical_slice_write_events` 是逻辑切片数，不是介质写事务数。

主计算调用共享闭式；独立检查对原始配置建立真实矩阵切片，对 Attention 按绝对 token tile 存活期倒序汇总，小长度再枚举 receiver/input/write 身份。独立预期值不调用共享公式。128K 不分配 Attention 矩阵或大事件清单。

从仓库根执行（数值仅依赖 Python 标准库，编译需 XeLaTeX/latexmk/ctex；渲染需 pypdfium2）：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/pilot/scripts/build.sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/pilot/scripts/render.py
```

只复算，无需 TeX：

```sh
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/pilot/scripts/generate.py
/opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/pilot/scripts/check.py
```

修改输入或计算后，先给这两个 Python 命令依次加 `--emit` 刷新数据，再构建、渲染和逐页检查。默认不覆盖数据。PDF QA 记录只能在检查最终页面后更新。`build/` 与 `tmp/` 局部忽略，最终数据、源码和 PDF 保留。

Step 1/2 无需修正；Table II(a)、共享版本、原始资料和 Task I 保持。后续可沿用组件需求检查资源聚合与更新粒度，不能把总 RI 直接转换成单 macro 时间或器件排名。
