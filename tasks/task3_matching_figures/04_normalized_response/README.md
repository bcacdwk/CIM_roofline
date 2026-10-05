# D：复用增加后的归一化参考上界

已完成绘图 Agent 自查、supervisor 退修和独立数值复核，待用户选图与审阅。采用跨双栏 **7.16 × 2.60 in**，三面板共享 log U 与线性归一化纵轴；字体 6.8–10 pt。输出不自动裁边改变物理尺寸。

- [PNG 预览](output/figure.png) · [矢量 PDF](output/figure.pdf) · [SVG](output/figure.svg)
- [英文 caption](caption.en.md)
- 精确扫描点：[scan_points.csv](data/scan_points.csv)；完整解析曲线采样：[curve_points.csv](data/curve_points.csv)；[阈值邻域检查](data/validation.json)
- 共同入口：[shared/data.json](../shared/data.json) 的 `hardware` 与 `table_IIa_finite`，以及只读 [interface.py](../shared/interface.py)、[style.py](../shared/style.py)。

## 问题与读法

复用增长到什么程度，两通路参考上界才达到该硬件自身的 streaming 上界？每个面板选 Task I 典型成对情景，绘制 `P_bound/rho=min(1,U/U*)`；平台归一化为 1，**不是实测利用率**。面板内同时给出原生输入 streaming 上界 rho，避免把相同平台误读成相同绝对吞吐。虚线和空心符号是精确临界值 U*；实心符号为原 Table II(a) 有限扫描档位。

选择 MRAM、3D NAND、2D NOR，是为了覆盖约 10²、10³、10⁴ 次临界复用，以及 U=128 附近、1K 与 16K 之间、16K 与 128K 之间的不同转折位置。不是依据综合性能排名选优，也没有隐藏某情景来获得更理想的曲线；本候选统一使用典型 pair，三 paired scenario 的差异由候选 C 承载。

扫描来自 `W[128,128]` 的 `U=1,128,1K,16K,128K,1M`，对应 `N128/K128/U{1,128,1024,16384,131072,1048576}`。仅 2D NOR 与该算子形状相同；MRAM（原生 K=256,N=32）与 NAND（K=4608,N=240）保留自身完整服务，只迁移同一个 U，**不把 W[128,128] 的 RI 直接套到不同硬件形状**。全图不涉及 Attention append 或多阶段 FFN。U 是一次完整装载后累计服务的向量数，包含首次使用；1K=1024，1M=1024²。

## 支持的观察

1. MRAM 典型 U*=132.74074074074073，U=128 已达到参考 streaming ceiling 的 96.43%，但仍为 resident-bound；与 C 中同一真实点分类一致。
2. NAND 典型 U*=2839.2847701745545，U=1K 时仅约 36.07% 的归一化参考上界，到原扫描点 U=16K 已饱和。NOR 典型 U*=38866.880907372404，在 U=16K 时约 42.15%，到 U=128K 才达到扫描中的平台。
3. 平台后进一步增加 U 不提高这个模型中的两通路参考上界。MRAM、NAND、NOR 的绝对 rho 分别是 316.04938271604937、6.828082861630561、24.19659735349716 MB/s；归一化平台不能用于绝对吞吐排名。

与 C 相比，本图展示从低复用到平台的收益曲线；与 A 搭配时，A 提供绝对能力尺度，D 提供归一化收益与饱和位置。连续曲线是由既有硬件点导出的解析响应，并非新增硬件情景或拟合实测数据。

## 复现与自查

从仓库根运行：

```sh
PYTHONDONTWRITEBYTECODE=1 python tasks/task3_matching_figures/04_normalized_response/build.py
```

只写本目录；原 Task I/II 与 shared 只读。在每个 U* 的 0.999×、1×、1.001× 处检查响应分别为 0.999、1、1，以及 resident、balanced、streaming 分类。已查看实际 PNG；首版 NOR 文字横穿曲线，第二版将 NAND/NOR 数值移至左侧空区。Supervisor 首轮审阅后，将副标题修为“Filled: Table II(a) U scan · Open: balance U*”，避免空心临界点被误认作原扫描点。所有原有限 U 扫描点保留至 1M，未截断关键状态。另用 PDFium 在 144 dpi 渲染 [paper_review.png](output/paper_review.png)，核对 PDF 与 PNG 一致，并核验 PDF 页面为 7.16 × 2.60 in。
