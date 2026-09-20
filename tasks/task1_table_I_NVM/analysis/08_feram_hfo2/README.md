# HfO₂系FeRAM局部数字CIM参考估算

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

阅读 [独立中文PDF](output/feram_hfo2.pdf)（5页）及 [正文TeX](tex/08_feram_hfo2.tex)。主模式为实测HZO 1T1C存储机制支持的参考数字CIM组织，包含整激活行破坏读恢复；不声称原文已测该CIM宏。

参考点：128 Byte输入服务29.450 μs；16 Byte局部行更新150 ns；ρ=0.00434635 GB/s、τ=0.106667 GB/s、RI*=0.0407470。整16384 Byte矩阵更新153.6 μs。成对短/参考/长ridge范围0.0369187–0.0407470；这不是统计材料界。

32片×32行×128bit只映射一份矩阵。每轮32条行共4096bit并行感测和恢复，R0每向量256轮；单外部更新域写一条128bit行。恢复占参考streaming的43.46%。跨8个输入bit复用的4096bit权重锁存对照使读轮数256→32，另计32拍捕获，ΔS降到4.970 μs，ρ及ridge提高5.93倍。

阅读数据与依据：

- [证据及工程桥接](notes/evidence.zh.md)：原PDF页/图/条件、14ns写原值覆盖范围、185ns完整周期、两相BL/PL更新、C2非破坏读与漏电维护界限。
- [输入JSON](data/inputs.json)：模式、映射、资源、配对介质预算、阶段覆盖、原PDF与共享哈希。
- [统一结果JSON](data/results.json)：操作次数、B_S/B_R、Δ_S/Δ_R、ρ/τ/ridge、分项占用、聚合与复用对照。
- [独立编译入口](tex/feram_hfo2.tex)，[只读复算](scripts/check_feram.py)，[构建](scripts/build.sh)，[逐页渲染](scripts/render_pdf.py)。

在本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_feram.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

只在修改输入后显式刷新派生数据：

```sh
/opt/anaconda3/bin/python scripts/check_feram.py --emit
```

脚本导入共享API，不复制吞吐公式或共同外围常数。检查覆盖原PDF/共享文件哈希、逻辑映射、两极性目标写、完整行恢复、数据与时间单位、成对结果和整矩阵聚合。XeLaTeX/ctex/Fandol已构建；5页全部渲染目视检查，无溢出或缺字。build/tmp/缓存由本地.gitignore排除。

主审关注：14ns原值是write latency，本文把14/50/100ns保守分配给每极性相位，不称原文单相脉冲；20/40/80ns开关行专用预算以及4096bit同时恢复驱动能力是显式工程假设。C2FeRAM仅作机制对照，不为缺乏保持时间的fF节点编造刷新率。寿命单列，不混入瞬时τ。
