# Task III：硬件—负载关系候选图

**当前状态：Task III候选图完成，待用户选图与审阅。** Task I 与 Task II 已经用户验收，本任务不重新审定其参数。

请从[候选图集](review/GALLERY.md)开始，或打开[缩略总览](review/overview.png)、[五页矢量 PDF](review/candidates.pdf)。[组合建议](review/SELECTION.zh.md)区分最直观的 **A＋C** 与设计启示最强的 **C＋E**，没有替用户决定最终两张。

- 用户检查点及本地实际 HEAD：`100c233a2dbdb74ca3894aa96ee39c358e9ebe41`；不回退。
- 开始时已有用户改动：`.DS_Store`；保留。
- 只在本目录写入。原 Task I、Task II、文献、归档及主论文只读；不执行 Git 暂存、提交、推送、重置或分支切换。
- Supervisor 负责共同方法、构图审查、实际图面复核与最终建议；数据、绘图和独立算术复核由子 Agent 执行。

## 候选与接口

| 候选 | 目录 | 回答的问题 |
|---|---|---|
| A | `01_hardware_overlay/` | 参考复用需求与硬件能力在何处平衡？ |
| B | `02_demand_dual/` | 模型绝对需求有多大，显式分块服务如何改变平衡参照？ |
| C | `03_reuse_threshold/` | 一次完整装载需要多少次复用才能达到平衡？ |
| D | `04_normalized_response/` | 随复用增加，两通路参考上界何时饱和？ |
| E | `05_improvement_payoff/` | 改善哪条通路可以提高当前参考上界？ |

共同数据与约定在 `shared/`；最终图集、缩略总览、逐页 PDF、推荐组合及内部审查记录在 `review/`。

主接口为等宽 INT8、原生完整矩阵一次装载的复用次数：
`U*=T_R/Delta_S=N*rho/tau`。`N*rho` 是显式变换的能力坐标，不能称为原始 streaming 输入能力。
具体模型的需求平面只在已明确推导的分块边界下使用有效硬件参照。FFN 多阶段与 Attention append 不套用完整矩阵装载阈值。

最终由用户审阅候选并选择至多两张；本轮不整合主论文。

## 完成情况与复现

五张候选均已生成 PNG、PDF、SVG、独立脚本、绘图精确数据/共享入口、中文说明和英文 caption。已完成实际图面审查及修改；独立复核采用交叉分工，复核者不审自己绘制的图。过程与核验依据见[审查记录](review/REVIEW.zh.md)。

所有图均按 7.16 in 双栏检查。A/B/C/E 高约 4 in，D 高 2.60 in；合并 PDF 保持这些实际尺寸，每张一页。

从仓库根重建全部 Task III 产物：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/build_all.py
```

环境依赖为 Python、numpy、matplotlib、Pillow、pypdfium2。当前环境不含 Poppler，PDF 用 pypdfium2 渲染逐页检查；合并直接导入原始矢量页。各图也可单独运行对应目录的 `build.py`。重建只写本任务目录，不运行 Task I/II 的原生成器。重建后的 PDF QA 状态重置为待图面查看，保留最后一轮人读审查记录供参考。
