# Table I 与 rho–tau 图

正式表图仅从[统一完整精度数据](../data/ten_case_results.json)读取十例参考配置，使用与原 NVM 总结图一致的十类配色、显示名、字体、表格条纹与典型列底色、圆点、参考线和标签布局规则。图中 RRAM 对应 WH-2T1R，3D FeFET 对应垂直 AND FeFET；Gain-cell 是易失性 GC-04 eDRAM。

| 内容 | 预览 | 矢量文件 / 数据 |
|---|---|---|
| Table I，十例典型配置 | [PNG](output/table_I_typical.png) | [PDF](output/table_I_typical.pdf) · [SVG](output/table_I_typical.svg) |
| 表格可编辑文本 | [Markdown](output/table_I.md) | [LaTeX](output/table_I.tex) |
| rho–tau 双对数图，十个典型点 | [PNG](output/rho_tau_loglog.png) | [PDF](output/rho_tau_loglog.pdf) · [SVG](output/rho_tau_loglog.svg) |
| 两页合并版：表格、典型图 | [PDF](output/table_I.pdf) | — |
| 完整精度表格数据 | [CSV](data/table_I.csv) | [JSON](data/table_I.json) |
| 实际绘制点与布局检查 | [CSV](data/rho_tau_loglog_points.csv) | [检查](data/rho_tau_loglog_validation.json) |

横轴是 resident 更新能力 τ，纵轴是 streaming 输入能力 ρ，单位均为十进制 MB/s = 10⁶ Byte/s。两个 log₁₀ 轴每个数量级长度相同，ρ=τ / RI*=1 为 45° 参考线；坐标范围由完整精度数据自适应确定。颜色和标签定位沿用原模板，标签可避让，点坐标不变。显示约两位有效数字，RI* 是服务比值；U* 是匹配完整求值/装载边界的服务交叉点，不是实际 workload 复用次数。

表和图使用维护后的有效能力。GC 的 raw 时间与长期有效服务间隔分别导出，不能以 raw 时间覆盖有效两率。内部位平面、参考页、读验及刷新不增加逻辑 payload。具体来源类别、数值精度与未完整建模条件见[方法说明](../METHOD.zh.md)。这些配置的规模与资源不同，不能作等面积或等工作量排名。

所选评估没有与自身配置相容且完整可追溯的成对范围，因此只生成典型表与典型点图，不生成三情景圆图。

从仓库根只重绘：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NeuroSim/analysis/11_summary_figures/build_figures.py
```

该命令只读取现行统一数据，写本目录的正式 `output/` 与小型派生 `data/`；不编译 NeuroSim，不访问 archive 或兄弟 NVM 的性能数据。`build_loglog.py` 是同一完整入口的兼容快捷命令。独立预览可加 `--source <统一数据.json> --output-root <非同步本地目录>`，中间构建、PDF 渲染与审查截图均留本地区。

生成器核验十例 payload、raw/effective、ρ/τ、RI*/U* 的恒等式，并检查双轴等比例、45° 参考线、点坐标、标签和边框。数据 SHA-256 保存在[数据检查](data/validation.json)。[PDF 检查](data/pdf_qa.json)记录正式 PDF 的哈希、页数、字体嵌入与真实逐页渲染；合并 PDF 的页数为两页。
