# C：完整装载的临界复用次数

已完成绘图 Agent 自查、supervisor 图面审阅和独立数值复核，待用户选图与审阅。采用跨双栏 **7.16 × 4.05 in**；字体 7–10 pt，输出不自动裁边改变物理尺寸。

- [PNG 预览](output/figure.png) · [矢量 PDF](output/figure.pdf) · [SVG](output/figure.svg)
- [英文 caption](caption.en.md)
- 精确值：[plotted_thresholds.csv](data/plotted_thresholds.csv)；[数值检查](data/validation.json)
- 共同数据入口：[shared/data.json](../shared/data.json) 的 `hardware` 和 `selected_workloads`；构图仅调用只读 [interface.py](../shared/interface.py) 与 [style.py](../shared/style.py)。完整来源链保留在 CSV 与 shared source index。

## 问题与读法

一次完整装载需要服务多少输入向量，resident 通路上界才不再低于 streaming 通路上界？行按典型 U* 升序排列以便读图，不是性能排序。每行是 Task I 一个原生配置，横轴 `U*=T_R/Delta_S=N*rho/tau`，不是原始 RI*。在该原生完整矩阵服务里，实际 U 小于本行阈值为 resident-bound，大于阈值为 streaming-bound；等于阈值则平衡。U* 保留连续解析阈值；真实整数复用达到或超过该阈值需使用满足 U≥U* 的整数，跨界判断不先舍入阈值。

三点都来自 Task I 原有成对情景，连线仅连接这些点的最小与最大横坐标，不代表连续可实现配置、概率范围或任意组合。大实心点为典型值，小空心为 short，小浅色实心为 long；小点在分类行内上下偏移以显露重叠数据，横坐标不移动。各介质的颜色、符号统一引用 shared。short / long 指原情景，**不保证临界复用单调排列**。

竖虚线来自 Table II(a) `W[128,128]` 的 `U=1,128,1024,131072` 四个已认可状态。对应 case ID 为 `N128/K128/U1`、`N128/K128/U128`、`N128/K128/U1024`、`N128/K128/U131072`。它们覆盖首次使用、中等复用与高复用；1K=1024，1M=1024²。仅原生 K=N=128 的硬件与这张矩阵形状直接一致，其余行的 U 是将同一复用次数用到各硬件原生完整矩阵的参照，**不声称已经完成 W[128,128] 到所有硬件的部署映射**。U→∞ 作为极限留在说明中，不赋予有限对数坐标。

## 支持的观察

1. 典型临界复用从 SRAM ACIM 的 1.595 到 2D NOR 的 38,866.881，摊销要求跨多个数量级；这是原生配置的复用阈值差异，不是综合产品排名。
2. MRAM 的 U=128 处不能用圆或区间中心替代真实情景判断。short、reference、long 的 U* 分别为 180.7058823529412、132.74074074074073、94.81481481481481，分类依次为 resident、resident、streaming。典型 U/U*=0.9642857142857144，确实仍在 resident-bound 一侧。
3. 2D NOR 的 U=128K 高于典型阈值、低于 long 情景阈值 253,826.0056657224；相同复用档位也可能因成对情景变化而跨界。短/长服务情景不能各自挑最有利 rho 与 tau 再拼接。

与能力图搭配，这张图直接把“能力比值”翻译为“需复用多少次”；绝对吞吐大小仍由能力图承载。

## 复现与自查

从仓库根运行：

```sh
PYTHONDONTWRITEBYTECODE=1 python tasks/task3_matching_figures/03_reuse_threshold/build.py
```

只写本目录；原 Task I/II 与 shared 只读。精确数据验证 `U*=T_R/Delta_S`，并对全部 30 个实际点在 4 个参考 U 下分类。已查看实际 PNG；首版底部轴标与来源文字拥挤，第二版调整底部空间后消除重叠。PDF 保留目标物理尺寸，PNG 240 dpi。另用 PDFium 在 144 dpi 渲染 [paper_review.png](output/paper_review.png)，核对 PDF 与 PNG 一致，并核验 PDF 页面为 7.16 × 4.05 in。
