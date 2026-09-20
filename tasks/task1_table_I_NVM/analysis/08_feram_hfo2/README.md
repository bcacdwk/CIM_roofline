# HfO₂系二元1T1C FeRAM：已有读码复用的局部数字CIM

当前统一入口：[十例复核](../TEN_CASE_REVIEW.zh.md) · [结果JSON](../data/ten_case_results.json) · [结果CSV](../data/ten_case_results.csv)。PDF首页结果卡与这些导出由统一适配器生成；本例原始未取整结果仍在 `data/results.json`。摘要统一十进制MB/s，情景分类见统一复核。


当前结论见[十例统一复核](../TEN_CASE_REVIEW.zh.md)。本轮确认原D0的4096-bit读码寄存器可以跨八个输入bit保持，已改为默认调度；真实破坏读的整行恢复保留。

阅读[独立中文PDF](output/feram_hfo2.pdf)及[可复用章节](tex/08_feram_hfo2.tex)。主模式是实测HZO 1T1C存储机制支持的二元局部数字CIM参考组织，不是原文已测CIM宏。32片×32行×128bit只映射一份16 KiB矩阵；4096个SA及本地驱动并行读恢复32条完整行，已有4096-bit读码寄存器随后供八个输入bit只读计算。每向量物理读32轮、数字计算256轮，无第二份同容量锁存或新增捕获拍。

参考点：B_S=128 Byte，Δ_S=4.810 μs，ρ=26.611 MB/s；B_R=16 Byte，Δ_R=150 ns，τ=106.667 MB/s；RI*=0.24948。摘要采用十进制MB/s（10⁶ Byte/s）。16 Byte事务更新一条128-bit物理行，对应一个逻辑输入行中16个相邻且对齐的INT8输出权重；1024次满行事务覆盖16 KiB矩阵，耗时153.6 μs，τ不变。更小部分行更新需要保留其余内容，不能直接沿用满行吞吐。

短/参考/长是三组**成对条件工程情景**：ρ=12.877–68.817 MB/s、τ=53.333–307.692 MB/s、RI*=0.22366–0.24948。不是完整物理不确定性范围。固定参考外围、感测和驱动，仅改变14/50/100 ns保持窗口的独立对照保存在数据和正文；读恢复与两相外部写使用同一个保持参数。

旧逐输入bit重读保留为同硬件调度对照：Δ_S=29.450 μs、ρ=4.346 MB/s、RI*=0.040747，τ不变。主模式ρ及ridge提高6.123倍，来自已有读码保持与循环次序；恢复覆盖从每cell每向量八次变为一次。主模式restore占streaming的33.26%。已有读窗口含捕获和恢复；没有定时刷新项，因此在活动服务窗口假设下原始占用与维护后间隔相同。

数据与依据：

- [证据及工程桥接](notes/evidence.zh.md)：原PDF页/图、14 ns write原值的覆盖范围、完整周期、寄存器生命周期、两相BL/PL更新与非破坏读边界。
- [输入JSON](data/inputs.json)：模式、映射、资源、成对窗口、独立敏感性、阶段覆盖及原PDF/共享哈希。
- [结果JSON](data/results.json)：推荐与成对结果、逐输入bit重读对照、固定外围保持对照、分项占用与矩阵聚合。
- [独立编译入口](tex/feram_hfo2.tex)、[复算脚本](scripts/check_feram.py)、[构建](scripts/build.sh)、[逐页渲染](scripts/render_pdf.py)。

在本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_feram.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改输入后显式刷新派生数据：

```sh
/opt/anaconda3/bin/python scripts/check_feram.py --emit
```

脚本导入共享API，检查来源/共享文件哈希、逻辑映射、两极性目标写、完整行恢复、阶段求和、有效payload、整矩阵聚合和生成文件同步。原文14 ns是write latency；本设计每极性主动保留14/50/100 ns，不称原测量需要两倍14 ns。20/40/80 ns专用建立关闭及4096bit同时恢复驱动为工程选择；C2FeRAM只作机制对照，寿命不混入瞬时τ。
