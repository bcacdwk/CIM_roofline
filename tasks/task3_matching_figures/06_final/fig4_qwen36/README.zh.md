# Fig.4：Qwen3.6-35B-A3B 六条负载竖线版

基线：`f98cb74d936f58d1b8eda33bc1a7384e02d00abb`。

本目录是 Fig.4 的可复现制图包。2026-10-10 按用户要求沿用本包代码和 CSV，仅优化单栏图的字体、标注及留白，并通过论文已有的图片路径重新插图。**本任务未写入任何 `.tex`**，`fig:critical-reuse` label 保持原样；未更新论文图注或正文。工作期间检测到 `papers/sections/model.tex` 被并行更新，予以保留，最终编译基于当时最新文件。拟用图注另存于 [caption.en.md](caption.en.md)。没有重新计数、tile 换算、仿真或远程仓库写操作。

## 输出

- `figures/Qwen36_six_lines_shared_SI_single.{png,svg,pdf}`：当前单栏版，3.50 × 3.08 in。十行硬件 reference SI* 和三个原生情景的 min–max 段；六条 workload SI 竖线。正文标注约 7.15–7.7 pt，模型标题 8.6 pt；方向提示/图例 7 pt。
- `figures/Qwen36_six_lines_SI_rho_double.{png,svg,pdf}`：包内原双栏备选，7.16 × 3.15 in，本次未重绘或插入论文。同样六条竖线；纵轴保留原生流式上限 rho。
- `papers/figures/critical_reuse_single.{pdf,png,svg}`（相对仓库根）：单栏图的相同文件副本；PDF 文件名沿用现有 `includegraphics`，不改 TeX 即可替换 Fig.4。

所有图均为黑色坐标轴。硬件颜色沿用论文指定配色；负载竖线统一灰色，避免再引入一套分类颜色。PNG 为360 dpi，SVG保留文字，PDF嵌入字体。本次使用 pypdfium2 渲染论文和单独图文件，按实际单栏尺寸目视检查。

## 选择的六点

全部来自 Table II 的已有格子，不插值，不反推新的 U/L，不移动 SI。

| 负载 | 工况 | 精确 SI | SI 小数 |
|---|---|---|---:|
| MoE，单个 routed expert | U=16 | 5/384 | 0.013020833333333334 |
| QKV | U=1K | 1/9 | 0.1111111111111111 |
| MoE，单个 routed expert | U=1K | 5/6 | 0.8333333333333334 |
| Prefill | L=1K | 1537/128 | 12.0078125 |
| QKV | U=1M | 1024/9 | 113.77777777777777 |
| Decode | L=64K | 1028 | 1028 |

相邻间隔约为0.931、0.875、1.159、0.977和0.956个数量级。这是既有工况自然产生的间隔，不是等间距坐标回填。六点覆盖约五个数量级，并保留四类阶段。

本轮是**单模型、跨工况的示例**，不再代表上一轮六模型范围，也不代表统一的高复用/长上下文主组或实际流量的典型分布。

Prefill L=8K 的 SI=8705/128=68.0078125，和 QKV U=1M 的 SI=113.77777777777777 相差约1.673倍。为避免堆在同一区，主版本先用 Prefill L=1K，补足 SI≈10 这一档。它也恰好提供3D NAND参考点附近的真实平衡例子。没有把 L=8K 的数据挪到 L=1K 的位置。

标签采用“负载名称 / U或L工况”两行。现有六点不需要上下错层；脚本包含双层标签避碰逻辑，只调整文字的纵向位置，不改变任何数据横坐标。

## 读图方向

左下角写的是：

> Hardware relative to each line:
> ← streaming | resident →

这里的左、右是**硬件点相对每条负载竖线的位置**。硬件 SI* < 负载 SI 时在左侧，对应 streaming 侧；SI* > SI 时在右侧，对应 resident 侧；相等时为平衡。不存在对所有负载共用的一条左右分界。

单栏硬件段覆盖三个真实原生情景，不是统计误差。二维连线只连接真实配对情景，不表示连续可达域或工作负载吞吐需求。低 SI* 不表示绝对速度、面积或能效更优。

例如 Prefill L=1K 的 SI=12.0078125 与3D NAND reference SI*=11.830353209060647 很接近，强度比约1.015；另外两个原生情景的阈值高于该负载SI，因此会改变限制侧。这种近临界位置是原始数据，不应为了视觉分离而移动。

## 英文图注建议：单栏版

参见 [caption.en.md](caption.en.md)，已简要写明原生硬件服务比与模型级逻辑需求的参考对照、未作完整部署映射校正，以及低 SI* 不代表更高绝对速度。按用户最后的“不改 tex”要求，该建议没有写入论文，原 U* 图注和直接相关旧正文仍保留。

## 英文图注建议：二维版

**Native CIM balance requirements and selected operating points of Qwen3.6-35B-A3B.** Dashed vertical lines mark raw workload SI at the labeled U or L; MoE counts one routed expert. Colored filled/hollow points show reference/paired alternative native configurations. Hardware to the left/right of each workload line is on its streaming/resident side; equality marks balance. The vertical coordinate is the native streaming ceiling rho in decimal MB/s, not a workload throughput requirement. Native hardware service ratios are compared with model-level logical demands without full deployment-mapping correction.

## 数据与来源

- `data/plotted_thresholds.csv`：完整30个原生硬件情景。基线原路径：`tasks/task3_matching_figures/03_reuse_threshold/data/plotted_thresholds.csv`。
- `data/rho_tau_loglog_circles_points.csv`：当前 Fig.3a 的 NVM 任务入口，原路径：`tasks/task1_table_I_NVM/analysis/11_summary_figures/data/rho_tau_loglog_circles_points.csv`。没有使用 archived NeuroSim 吞吐数据或 Fig.3b 密度数据。
- `data/selected_workloads.csv`：当前 Table II 的72个精确有限格。基线原路径：`papers/tables/selected_workloads.csv`。
- `data/selected_six_points.csv`：六条竖线的条件、精确分数、SI、Q_S、Q_R和来源 case ID。
- `data/qwen36_all_table_II_points.csv`：该模型在当前 Table II 中的12个点，附选中标记。
- `data/six_point_comparisons.csv`：六点×十硬件×三情景的180条比较。SI/SI* 仅作为强度比，不是实测性能或概率。
- `qa/validation.json`：输入 Git blob SHA、Fig.3a 全30行逐项一致、数据坐标保持、标签避碰和画布边界检查。

SI 与历史字段 RI 含义相同；SI=Q_S/Q_R，SI*=rho/tau。1K=1024，1M=1024²。QKV 包含已计入的 gate，不含 O projection；MoE 不乘专家总数或 top-k；Prefill 从空缓存建立至 L，Decode 追加一个 token 后对长度 L 求值。无需重新计数、硬件分块校正或新仿真。

## 复现

Python 3.10+，依赖 Matplotlib、NumPy：

```bash
python -m pip install -r requirements.txt
python plot_qwen36.py
```

默认仅生成选中的单栏版。`--variant double` / `--variant both` 可显式选择包内其他输出；本次只运行 single。也可 `python plot_qwen36.py --output-dir another_folder`。

从仓库根重绘、通过现有文件名重新插图并编译论文：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/06_final/fig4_qwen36/plot_qwen36.py --variant single --install-paper
make -C papers
```

脚本不联网、不写远程仓库；校验原始输入、核对六个已选工况、输出原有数据摘要和单栏 PNG/SVG/PDF。`--install-paper` 只复制图片文件，不写任何 `.tex`。输入 CSV 的哈希、参考点/范围、标签两两避碰、标签对硬件点及范围的避碰、画布边界均有断言检查。此次全部六份 CSV 的内容哈希保持不变。

替换前已有本地改动的论文 PDF 和旧 Fig.4 已保存在 `qa/before_20261010/`。本次编译与排版复核记录见 [qa/paper_review.zh.md](qa/paper_review.zh.md)。论文原 `prepare_reuse_layout.py` 仍生成旧 U* 图，未修改或运行；重绘本次新图应使用上述本包脚本。
