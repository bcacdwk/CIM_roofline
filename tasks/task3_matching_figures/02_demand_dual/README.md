# 候选 B：QKV 逻辑需求平面与原生 tile 平衡参照

**目标双栏：7.16 × 4.30 in；字号 7.3–11 pt。** 图面为英文，PNG 240 dpi；PDF/SVG 保留矢量。已完成第一轮 supervisor 审阅与版面修改，待用户选图与审阅。

- [PNG](output/figure.png) · [PDF](output/figure.pdf) · [SVG](output/figure.svg)
- [英文 caption](caption.en.md) · [精确绘图数据](plotted_data.json) · [数值检查](validation.json)
- 共同只读入口：[data.json](../shared/data.json)、[计量接口](../shared/README.zh.md)。不修改或运行 Task I/II 的生成器。

## 回答的问题与读法

在真实模型的逻辑 Byte 平面上，一次权重装载与累计输入的大小如何变化？同一个硬件的平衡参照需要怎样转换，才能和该逻辑需求同边界比较？

两个面板共享对数坐标；黑点为四个已认可的 QKV 状态，竖线连接同一完整权重装载随 U 增长的轨迹。不同模型保留真实 Q_R 水平位置。三条彩色射线对应典型 SRAM ACIM、3D FeFET、2D NOR；射线上方为 streaming-bound、下方为 resident-bound（这里指两类累计组件服务的相对负担）。彩色空心符号只辨认射线的介质身份，不表示额外硬件情景点。无限复用延续竖直轨迹到无界 Q_S，没有被编码为一个很大的有限点。

## 选点与映射

使用 Qwen3.5-2B（D=2048、N_proj=5120，含输出 gate）和 MiMo-V2.5-Pro（D=6144、N_proj=27136），原扫描 U=1/1K/128K/1M。它们是已认可 QKV 中大小差异明显且可完整整除 128 的两种模型。保留全部四个现行有限状态，避免为预期结论新造 U。硬件子集跨度覆盖低阈值、中阈值及较高装载摊销要求，均是原生 K=N=128，只显示 reference 典型情景。

共同数据已完成如下有限映射，不把原始 RI* 直接贴在模型逻辑坐标上。Q/G/K/V 沿输出维拼接，同一阶段输入共享扣除保持原定义。一个原生 128×128 engine 逐 tile 完整装载、服务 U 次，再处理下一 tile；m_K=D/128、m_N=N_proj/128，总 tile 数 M=m_Km_N。逻辑 Q_S=UD、Q_R=DN_proj，原生累计输入=m_N Q_S。因此两条组件累计时间是 M U Δ_S 和 M T_R，得到：

```text
rho_eff = rho/m_N       tau_eff = tau
RI*_eff = RI*/m_N = U*/N_proj
Q_S = RI*_eff Q_R       (each model has its own rays)
```

Qwen 的 m_K/m_N/M 为 16/40/640，MiMo 为 48/212/10176。没有 padding。跨 tile 归约、切换、上游搬运和完整输出存储未进入参考；不保证容量/时序/精度，也不把两路 max 时间当作真实顺序任务的墙钟时间。此范围集中在共同方法与 caption 中，不在图面堆长说明。

## 可以支持的观察

1. 相同 U 下，MiMo 的 resident 装载为 159 MiB，对比 Qwen 的 10 MiB，是 15.9 倍；累计逻辑输入是 3 倍。只比较 RI 会隐藏这些绝对量差异。
2. MiMo 的射线斜率为 Qwen 的 1/5.3；模型尺寸改变有效 RI*。在明确的完整 tile 服务映射下，两边同一 U 相对射线的位置仍由相同的原生 U* 决定。这说明更低的算子 RI 不能单独证明更不适配某器件。
3. U=1K 时两个模型均已跨过典型 ACIM 与 FeFET 参照，而 NOR 的累计 resident 装载服务仍占主导；到 U=128K 跨过典型 NOR 参照。该结论仅涉及所画真实典型点，不外推到 NOR 的 long 情景，也不构成绝对吞吐排名。

相对候选 A，本图增加具体模型、绝对字节及输入重放映射，代价是只覆盖两个 QKV 阶段和三个原生同形硬件。与只画 U* 的候选 C 不同，本图保留工作负载大小。

## 复现和检查

从仓库根执行：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/02_demand_dual/build.py
```

脚本只从共享接口读数，保存 8 个原始逻辑需求点、6 条有效射线和 24 个硬件—状态判定；逐一验证逻辑射线比值、U/U* 和累计组件时间比值相同，并核对 18 个阈值及其邻域。`plotted_data.json` 保存共享文件哈希与来源指针，`validation.json` 保存验证结果。

第一轮自查已查看实际 PNG，修正了最低 U 标签与坐标轴接触及 SRAM 射线符号落在显示范围外的问题。点的位置不变；所有有限状态保留。图需要按 7.16 in 双栏宽使用，不建议缩为单栏。
