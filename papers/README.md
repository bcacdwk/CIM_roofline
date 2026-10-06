# ISCAS 2027 paper — writing round 1

**A Resident-Streaming Roofline Model for Compute-in-Memory**

当前是四页技术内容加一页参考文献的英文骨架，不是已完成的正文。入口为 `main.tex`，PDF 为 `output/manuscript_skeleton.pdf`；逐页检查见 `notes/layout_review.zh.md`。总纲保存于 `PAPER_BRIEF.zh.md`，标题按最新审阅意见更新。

## 编译

在本目录执行：

```sh
make
```

需要标准 TeX Live 中的 `latexmk`、`pdflatex`、`bibtex`、`microtype` 和 `IEEEtran.bst`。编译中间文件只写 `build/`，最终 PDF 复制到 `output/`。不运行任何 Task 分析脚本。

`main.tex` 中的 `\layoutdrafttrue` 控制正文预留框、概念图占位框、临时分栏分页与参考文献换栏。改成 `\layoutdraftfalse` 后恢复常规 `figure` / `figure*` / `table*` 浮动；英文 Outline 仍保留供逐节改写，五页安排不再强制。作者、单位、资助均留空。`IEEEtran.cls` 与提供模板逐字节相同。按用户授权，标题在 `main.tex` 单独设为 19.6 pt，完整排成一行；通过 `microtype` 关闭 fi/fl/ff 等英文连字，同时启用标准微排版。行末自动断词已恢复正常，避免双栏两端对齐产生过大的字间距；连字与断词是独立设置。

## 文件入口

- `sections/abstract.tex`：唯一主摘要与 Index Terms。
- `sections/`：正文按 section 分为 `introduction.tex`、`model.tex`、`characterization.tex`、`implications.tex`、`conclusion.tex`；每个 section 内直接包含其 subsection、相关图表入口及草稿版面预留，不再按 subsection 拆文件。
- `figures/*.tex`：四幅图的独立版面入口与图注。
- `tables/workload_intensity.tex`：四行六模型的精简表；`selected_workloads.csv` 保存采用的 36 个现有采样点、精确 RI 与显示值。
- `references.bib`：21 个明确选择并在骨架中引用的条目，无全库导入或 `\nocite{*}`。

## 图表来源

所有来源路径均相对仓库根；旧论文、Task 和模板原件保持只读。

| 稿件入口 | 来源与处理 |
|---|---|
| Fig.1 | 用户提供的 `figures/Fig1.png`（3198 × 1697，透明背景），按 `\linewidth` 等比例撑满第一页右栏，替换原占位框。 |
| Fig.2 | 文字说明占位框，概念图待绘制。 |
| `figures/hardware_capacities.pdf` | Task I `analysis/11_summary_figures/output/rho_tau_loglog_circles.pdf` 的原样矢量副本。 |
| `figures/hardware_capacities_paper.pdf` | Fig.3 实际采用的投稿排版版。`prepare_hardware_layout.py` 只读取 Task I 的 `rho_tau_loglog_circles_points.csv` 与 `rho_tau_loglog_circles_validation.json`；保留全部 30 个点、十个圆的已保存几何、等尺度对数轴、配色及情景配对。按用户审阅收紧视窗：横轴为 10^-2.15 至 10^4.15（两侧各留 0.15 decade），纵轴为 1 至 1000；并调整字号、标注位置、留白与线/点显示尺寸。原研究图标题和脚注并入论文图注。 |
| `figures/critical_reuse.pdf` | Task III `03_reuse_threshold/output/figure.pdf` 的原样矢量副本，保留作来源对照。 |
| `figures/critical_reuse_single.pdf` | Fig.4 当前采用的 3.5 × 2.55 in 单栏重排版，放在第四页右栏顶部。`prepare_reuse_layout.py` 只读 Task III `plotted_thresholds.csv` 与共同样式；保留十类配置的全部 30 个阈值、配色和情景标记，典型值直接标在情景点旁。右上角标明原生矩阵关系 `U*=N RI*`；128 仅为示例复用次数，各行 N 沿用自身配置。 |
| Table I | Task II `table_IIb/04_crosscheck/data/results.json`；QKV/FFN 取 U=1024，attention 取 L=1024/65536。沿用现有 `ri_decimal` 显示规则，不生成新工况。 |

Fig.3/4 的显示名称统一由 `figures/figure_labels.py` 管理：eDRAM、FeRAM、3D FeNOR、STT-MRAM。Fig.4 行名字号为 6.5 pt，左侧标签区由 1.01 in 缩为 0.67 in，数据绘图区增加约 14%。STT 类型据已认可原生来源 MRAM-06 核实；文献引用同步对应该宏。原始文献题名和来源文件名按原文保留。

如需重做版式，在仓库根运行 `python papers/figures/prepare_hardware_layout.py`（Fig.3）或 `python papers/figures/prepare_reuse_layout.py`（Fig.4），需要 matplotlib/numpy。两者只读现有数据，只写投稿目录；正常 LaTeX 编译直接使用已保存的矢量 PDF。

文献的定向来源为旧理论稿的 Roofline 条目、Task I `source_manifest.json` 与共享 `.bib`、Task II `data/models.json` / `data/sources.json` 及固定的本地模型配置。各条目在 `.bib` 注释中保留原始文件入口；未从记忆补齐缺失卷期页码。

状态：**写作第1轮完成，待审阅**。未启动新实验或 sub-agent，未进行 Git 暂存、提交或推送。
