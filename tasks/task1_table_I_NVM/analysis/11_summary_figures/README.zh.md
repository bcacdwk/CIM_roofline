# Table I 与原生配置 ρ–τ 图

正式表图从[统一未取整数据](../data/ten_case_results.json)生成，采用十例选定的原生配置、INT8 逻辑 payload 与完整服务边界。表中的 K×N 为输入×输出逻辑元素数；各配置的资源、尺寸和单次工作量不同，图表不表示等面积或相同计算量下的性能排名。

## 正式文件

| 内容 | 预览 | 矢量文件 / 数据 |
|---|---|---|
| Table I，乐观／典型／悲观三情景 | [PNG](output/table_I_three_scenarios.png) | [PDF](output/table_I_three_scenarios.pdf) · [SVG](output/table_I_three_scenarios.svg) |
| 表格可编辑文本 | [Markdown](output/table_I_three_scenarios.md) | [LaTeX](output/table_I_three_scenarios.tex) |
| ρ–τ 图，10 个典型点 | [PNG](output/rho_tau_loglog.png) | [PDF](output/rho_tau_loglog.pdf) · [SVG](output/rho_tau_loglog.svg) |
| ρ–τ 图，30 个成对情景点与圆 | [PNG](output/rho_tau_loglog_circles.png) | [PDF](output/rho_tau_loglog_circles.pdf) · [SVG](output/rho_tau_loglog_circles.svg) |
| 三页合并版：表格、典型图、圆图 | [PDF](output/review_figures.pdf) | — |
| 30 组完整精度表格数据 | [CSV](data/table_scenarios.csv) | [JSON](data/table_scenarios.json) |
| 典型图绘制点与来源 | [CSV](data/rho_tau_loglog_points.csv) | [数值与布局检查](data/rho_tau_loglog_validation.json) |
| 圆图绘制点与来源 | [CSV](data/rho_tau_loglog_circles_points.csv) | [几何与布局检查](data/rho_tau_loglog_circles_validation.json) |

## 数据与服务边界

ρ、τ 使用十进制 MB/s = 10⁶ Byte/s，正文表和图标签一般显示两位有效数字；点坐标及 JSON/CSV 保留计算结果的完整精度。ρ 对应完整输入向量及规定输出的求值服务间隔，τ 对应所选整个 resident 矩阵的有效逻辑容量与完整装载服务时间。表中局部分组大小说明更新组织，不替代完整装载的分子与时间边界。NOR/NAND 包含持续擦除、编程及必要装载成本，Gain-cell 包含周期刷新。

每例三点均为同一原生组织与资源下的可持续成对工程情景；典型不是统计中位数。资源扩展、维护临界点、不可行调度和预擦除有限 burst 均不进入普通三情景。Gain-cell 的慢点也是可持续主情景。3D FeFET 的主身份为 2026 vertical AND FeFET，图中使用技术简称；Gain-cell 保持 GC-04 的 65 nm 3T1C current-programmed dynamic-cascode 路径。完整模式、编码、保持、外围与更新资源由[统一数据](../data/ten_case_results.json)及[各例章节入口](../TEN_CASE_REVIEW.zh.md)保存。

可持续性表示声明时序与维护占用可排程，不替代数值精度资格。NAND偏置编码的名义10bit量化诊断可使弱信号或抵消输出发生符号错误；其点仅为条件近似求值预算，未保证小信号准确度。该限制同时写入正式表脚注、统一结果卡及[机器诊断](../04_nand_3d/data/quantization_diagnostics.json)。PCM共享前端768 ns敏感性与独立长观察、GC提前释放模式均另列，不进入本表或普通圆。

表图的 RI* = ρ/τ 是硬件配置的服务比值。对匹配的 INT8 矩阵，U* = N·RI* = T_R/Δ_S；扩大到算子时必须重新确认完整矩阵装载、输入共享、重放与资源分时，见[公共方法](../shared_baseline/README.md)。图中所有比值标签和参考线均标为 RI*，不代表某一 workload 的 RI。

## 双对数图与圆的含义

横轴为 resident 更新能力 τ，纵轴为 streaming 输入能力 ρ。两个 log₁₀ 轴每个数量级显示长度相同，ρ=τ 参考线为 45°。绘制范围由当前点及圆的完整外界自动计算，并预留标签空间。十类颜色、大典型点、小快慢点、配色细连接线、浅色填充和虚线圆采用共同规则；标签可在点的邻近方向排布，点坐标保持原值。

圆在 `(log₁₀ τ, log₁₀ ρ)` 平面构造。记快、慢点为 a、b，典型点为 p，m=(a+b)/2，d=b−a。圆心是 p 在 a、b 中垂线上的投影：

```text
c = p − [(p−m)·d / (d·d)] d
r = ||a−c|| = ||b−c||
```

这一圆使两个端点位于圆周，并使圆心到典型点的距离最小。十例现行情景的典型点均在各自圆内，半径约为 0.20–0.53 个数量级。几何规则不反向改变任何工程参数。圆仅概括有限成对情景，不是置信区间，也不表示圈内所有读写组合都可实现。

## 复算与检查

从仓库根运行：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NVM/analysis/11_summary_figures/build_figures.py
```

该入口生成正式三情景表、两幅图与三页合并 PDF。[build_loglog.py](build_loglog.py)调用同一完整入口；[build_loglog_circles.py](build_loglog_circles.py)可单独生成圆图及其点数据、验证记录。三个脚本均只写本目录。

构建检查统一导出与原生结果一致，按 `source_mapping` 指针核对全部 30 组数值，并验证原生 payload、完整服务时间、RI* 和 U*。随后执行[独立检查器](../scripts/check_ten_cases.py)的输入驱动阶段与几何检查，不以旧吞吐数值或固定 128×128 分子作为预期答案。

[通用验证](data/validation.json)记录输入、原生结果、共享参数和中央数据的 SHA-256。[典型图检查](data/rho_tau_loglog_validation.json)与[圆图检查](data/rho_tau_loglog_circles_validation.json)验证原始坐标、等对数比例、45° 参考线、完整边框、点与标签入框、技术标签与参考线标签无碰撞，以及全部圆完整可见。[PDF QA](data/pdf_qa.json)绑定正式 PDF 的真实哈希、页数、字体嵌入、文本边界及逐页渲染审查。
