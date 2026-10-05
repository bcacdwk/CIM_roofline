# Table I 与 rho–tau 图

正式表图读取[三情景完整精度数据](../data/paired_scenario_results.json)，并逐值核对其中十个 reference 与[典型配置权威数据](../data/ten_case_results.json)一致。三情景是同一组织和资源下，由有来源的服务参数组成并实际重跑的 optimistic / reference / pessimistic 成对条件；每个点的 ρ 与 τ 来自同一情景的完整求值和完整装载服务。

| 内容 | 预览 | 矢量文件 / 数据 |
|---|---|---|
| Table I，十例三情景 | [PNG](output/table_I_three_scenarios.png) | [PDF](output/table_I_three_scenarios.pdf) · [SVG](output/table_I_three_scenarios.svg) |
| 表格可编辑文本 | [Markdown](output/table_I.md) | [LaTeX](output/table_I.tex) |
| rho–tau 图，十个典型点 | [PNG](output/rho_tau_loglog.png) | [PDF](output/rho_tau_loglog.pdf) · [SVG](output/rho_tau_loglog.svg) |
| rho–tau 图，30 个成对情景点与圆 | [PNG](output/rho_tau_loglog_circles.png) | [PDF](output/rho_tau_loglog_circles.pdf) · [SVG](output/rho_tau_loglog_circles.svg) |
| 三页合并版：表格、典型图、圆图 | [PDF](output/table_I.pdf) | — |
| 30 组完整精度与参数来源 | [CSV](data/table_I.csv) | [JSON](data/table_I.json) |
| 实际典型点与布局检查 | [CSV](data/rho_tau_loglog_points.csv) | [检查](data/rho_tau_loglog_validation.json) |
| 实际成对点与圆几何检查 | [CSV](data/rho_tau_loglog_circles_points.csv) | [检查](data/rho_tau_loglog_circles_validation.json) |

配色、显示名、字体、表格条纹与典型列底色、大小圆点、连接线、虚线圆和标签排布直接沿用原 NVM 图表样式。图中 RRAM 是 WH-2T1R，3D FeFET 是垂直 AND FeFET；Gain-cell 是易失性 GC-04 eDRAM。脚本不读取 NVM 性能数据。

横轴为 resident 能力 τ，纵轴为 streaming 能力 ρ，均使用十进制 MB/s = 10⁶ Byte/s。两个 log₁₀ 轴每个数量级长度相同，ρ=τ / RI*=1 为 45° 参考线；坐标范围包含原始点、完整圆和标签。表图显示约两位有效数字，数据和绘制坐标保留完整精度。RI* 是服务比值，U* 是匹配完整矩阵与完整输入向量的服务交叉点，不是实际 workload 复用次数。

大点为典型，小点为乐观/悲观，细线从典型点连接到对应端点；标签避让只调整文字位置。重合端点保持原位，可能遮叠，但不会抖动或虚造范围。两个能力都采用维护后的有效间隔；GC 的 raw 单次服务与长期有效服务间隔分开保存，不能用 raw 时间覆盖有效两率。

## 圆的几何与含义

圆在 `(log₁₀ τ, log₁₀ ρ)` 空间中构造。令乐观、悲观、典型点分别为 a、b、p，`m=(a+b)/2`、`d=b−a`。沿用原模板的最近圆心规则：

```text
c = p − [(p−m)·d / (d·d)] d
r = ||a−c|| = ||b−c||
```

圆心是 p 在 a、b 中垂线上的投影，使两端点落在圆周并最小化圆心至典型点的距离。程序另行核验典型点在圆内。若 `a=b`，等距约束自动成立，延拓为 `c=p`、`r=||a−p||`；三点全重合时半径为零，只保留原坐标点，不画人为可见半径。若非退化圆不能包含典型点，生成器报错，不改变工程参数或点坐标。

情景与圆仅概括有限成对工程条件，不是统计置信区间、同一芯片 PVT 保证或所有实现的严格边界；圆内读写组合未必可实现。未变化、受模型条件限制或重合的服务预算不代表不确定性为零。实际变动参数与未覆盖条件见[方法说明](../METHOD.zh.md)及每行 `scenario_parameters`；逻辑规模、资源及精度条件不同，不构成等面积或等工作量排名。

## 重绘与检查

从仓库根运行：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NeuroSim/analysis/11_summary_figures/build_figures.py
```

该命令生成三情景表、两幅图及三页合并 PDF。`build_loglog.py` 和 `build_loglog_circles.py` 都可调用同一完整入口。只读取现行数据，不编译 NeuroSim，不访问 archive 或兄弟 NVM 的性能数据。独立预览可加：

```sh
--source <paired_scenario_results.json> --reference <ten_case_results.json> --output-root <非同步本地目录>
```

生成器核对 30 组 payload、raw/effective、ρ/τ、RI*/U* 的恒等式与十个典型点逐值一致性；验证等对数比例、45° 参考线、原始点坐标、完整圆和标签边界，并拒绝不可行情景进入普通圆图。[验证摘要](data/validation.json)绑定两份权威数据的 SHA-256。[PDF 验证摘要](data/pdf_qa.json)绑定正式 PDF 的哈希、页数、字体和真实逐页渲染结果；中间图像、文字边界明细与长过程记录保存在非同步运行区。
