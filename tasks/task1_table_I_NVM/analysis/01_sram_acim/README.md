# SRAM ACIM：二进制电荷域展开与普通 SRAM 更新

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

阅读：[中文PDF](output/sram_acim.pdf) · [独立TeX入口](tex/sram_acim.tex) · [章节正文](tex/01_sram_acim.tex) · [证据表](notes/evidence.zh.md) · [方法与手算](notes/method_review.zh.md)。输入在[data/inputs.json](data/inputs.json)，完整计数、阶段、结果和敏感性在[data/results.json](data/results.json)。

128×128 INT8矩阵采用8个binary SRAM权重平面，1bit输入逐位展开。R0每次16输出、8平面并行，共64次求值、64转换批、8192标量转换、128重构拍。保持共同ACIM近似部分和合同，输出24-bit容器；不是精确整数或原四位宏的直接重标。

|情景|Δ_S(ns)|Δ_R(ns)|ρ(GB/s)|τ(GB/s)|RI*|
|---|---:|---:|---:|---:|---:|
|短|1540|2.2|0.08312|7.273|0.01143|
|参考|3210|5|0.03988|3.2|0.01246|
|长|7700|10|0.01662|1.6|0.01039|

B_S=128Byte、B_R=16Byte；GB为10^9Byte。普通写具备128个实际BL驱动，完成同步周期2.2/5/10ns与SRAM DCIM沿用同一CMOS-07/03跨实现证据标准；完整写槽已覆盖本地控制，R4不再叠加2T_D。整矩阵1024批串行聚合，参考5.12µs。

前端reset/input/array合并预算10/20/50ns锚定SACIM-03的128行4b完整宏10ns量级，未称独立实测cell延迟。原文0.9V与1.2V表述差异保留。参考前端和ADC各1280ns，占比各39.9%；固定外围扫前端10/20/50ns，ρ变为0.04981/0.03988/0.02495GB/s，显示前端不确定性。64真实写驱动对照使τ减半。成对ridge相近不代表普遍稳健。

复现（仓库根）：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NVM/analysis/01_sram_acim/scripts/check_sram_acim.py
sh tasks/task1_table_I_NVM/analysis/01_sram_acim/scripts/build.sh
```

输入变更后显式刷新：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NVM/analysis/01_sram_acim/scripts/check_sram_acim.py --emit
```

7项检查通过；XeLaTeX/ctex/Fandol构建5页，并逐页视觉检查。默认复算只读；build先检查已生成文件再构建。共享JSON及API、证据PDF哈希已记录并核验。本目录之外无写入修改；build/tmp/cache本地忽略。

待主审的实质边界：9T1C从原HCA/4b Flash改为独立列SAR，需要真实隔离、局部缓冲与校准；原4b误差不能证明8有效位整体精度。128写驱动从48bit 8T/eFlash锚点移植至9T1C内6T是有限工程预算，需后续电路验证；现有交付不冒称实测配对。`notes/method_review.zh.md`逐项说明桥接、排除项、手算及源码检查覆盖。
