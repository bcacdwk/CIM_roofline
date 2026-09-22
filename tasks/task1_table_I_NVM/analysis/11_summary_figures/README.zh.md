# Table I 与最终 ρ–τ 图

本目录的正式交付为三情景汇总表和最终双对数图，下表只列正式文件。十例原始分析与估算数据未改动。

旧文件清理尚未完成：自动审批拒绝了批量删除，也拒绝了限定到单个临时 PNG 的删除，仅返回 `blocked by policy`。因此临时 A/B/C/D、比较图、旧 loglog、loglogcompact、线性散点图及其旧脚本和记录目前仍在；它们不属于下面的正式交付。新的复现入口只生成最终图。

## 交付文件

| 内容 | 预览 | 矢量文件 / 数据 |
|---|---|---|
| 最终 ρ–τ 图，10 个典型点 | [PNG](output/rho_tau_loglog.png) | [PDF](output/rho_tau_loglog.pdf) · [SVG](output/rho_tau_loglog.svg) |
| Table I，短／典型／长三情景 | [PNG](output/table_I_three_scenarios.png) | [PDF](output/table_I_three_scenarios.pdf) · [SVG](output/table_I_three_scenarios.svg) |
| 表格可编辑文本 | [Markdown](output/table_I_three_scenarios.md) | [LaTeX](output/table_I_three_scenarios.tex) |
| 两页合并版：表格＋最终图 | [PDF](output/review_figures.pdf) | — |
| 最终图的完整精度点与来源 | [CSV](data/rho_tau_loglog_points.csv) | [数值与布局检查](data/rho_tau_loglog_validation.json) |
| 表格的 30 组完整精度数据 | [CSV](data/table_scenarios.csv) | [JSON](data/table_scenarios.json) |

## 最终图

- 横轴：**Resident throughput τ [MB/s]**，范围 0.0011–6000。
- 纵轴：**Streaming throughput ρ [MB/s]**，范围 0.04–60。
- 两轴均为双对数，每个数量级的显示长度相同；绘图区宽高约 2.12:1，ρ=τ 参考线严格为 45°。
- 保留 10 个推荐参考点；点下方依次标技术名和 `RI = 数值`，无文字指示线。图中的 RI 指原分析的 **RI*=ρ/τ**，显示四位有效数字，不是实际工作负载的 Q_S/Q_R。
- 名称和 RI 共两行。两个 SRAM 点的 τ 相同且位置相近，其标签按上／下点顺序排在点对下方；点坐标未移动。
- 中间等能力线与标注加粗；RI=10⁻²、10² 两条辅助线及文字增强对比；四边框完整。图下方不放注释小字。

标题为 “Typical streaming and resident throughput”，副标题为 “Ten CIM reference designs · RI = ρ/τ”。这些数值沿用文献支持的参考设计：Gain-cell 计入周期刷新，3D FeFET 指 2026 vertical AND 主模式；NAND 使用持续重写。十类中包含易失性的 SRAM 和 Gain-cell 参照。

## 汇总表口径

表格三大列组为短预算、典型／参考、长预算，每组并列 ρ、τ、RI*；典型列组以浅蓝底和粗体突出。ρ、τ 使用十进制 MB/s=10⁶ Byte/s。典型指原推荐参考点，不是统计中位数。

三组数值是成对工程情景，不是独立读写极值组合或统计置信区间。Gain-cell 长情景以 † 单列为刷新压力点，α=3.93%，不并入普通条件范围。NOR/NAND 的 τ 对应完整 16 KiB 重写；其余技术沿用各例声明的局部更新形状。各案例的模式和来源见 [Markdown 表](output/table_I_three_scenarios.md)。

## 复现与核对

从仓库根运行：

```powershell
python -X utf8 tasks/task1_table_I_NVM/analysis/11_summary_figures/build_figures.py
```

[build_figures.py](build_figures.py)负责数据核对、汇总表和合并 PDF；[build_loglog.py](build_loglog.py)负责最终图。直接运行后者也会重建这两份最终交付，不再生成旧版图。

脚本读取[统一未取整数据](../data/ten_case_results.json)，用现有适配器核对全部原生结果，并按各例 JSON 指针核对 30 组情景。Windows/POSIX 路径分隔符仅在比较时规范化，原文件不改写；另用既有独立阶段算式复核 10 个典型点。

[通用验证记录](data/validation.json)保留来源文件 SHA-256；[最终图验证](data/rho_tau_loglog_validation.json)检查全部 10 点、RI=ρ/τ、相同对数比例、45° 参考线、四边框、标签完整入框且互不重叠、不遮住点。[PDF 检查](data/pdf_qa.json)核对页数、文字边界及字体嵌入。PNG 已人工查看。
