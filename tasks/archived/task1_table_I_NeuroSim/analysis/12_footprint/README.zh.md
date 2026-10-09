# 原生二元存储密度与 F² 面积补充

本补充只比较当前十类参考身份的原生二元存储 cell / 最小重复 tile；六类有可追溯几何，四类保留 N/A。它不重建 INT8 矩阵面积、宏 PPA、等面积吞吐或三情景性能，也不改论文 Fig.3 与 rho–tau 图。两指标来自同一几何，不能当成两次独立验证。

- [双面板 PNG](output/storage_density_footprint.png) · [SVG](output/storage_density_footprint.svg) · [单页 PDF](output/storage_density_footprint.pdf)
- [权威小输入](geometry_inputs.json) · [逐类来源与缺口](sources.zh.md) · [完整来源目录 / PDF 哈希](sources.json)
- [主表 CSV](results/footprint_main.csv) · [含 NAND 原层数 / 单层自检 CSV](results/footprint_all_rows.csv) · [完整精度 JSON](results/footprint_results.json)
- [NeuroSim 面积链审查](neurosim_area_audit.zh.md) · [实际编译探针记录](neurosim_probe_results.json) · [CIM 映射 metadata](mapping_metadata.json) · [独立复核](review.zh.md)

## 同一面积、两个指标

重复 unit 的二维投影面积为 `A_xy [µm²]`，独立存储位数为 `b`：

```text
a_bit = A_xy / b                         [µm²/bit]
D = 1 / a_bit                           [Mbit/mm²，十进制]
alpha = a_bit / (F_mem_nm / 1000)²       [F_mem²/bit]
```

由于 1 mm² = 10⁶ µm²、1 Mbit = 10⁶ bit，`D` 数值恰为 `a_bit` 的倒数。固定几何仅改 F 时，D 必须不变，只有 alpha 改变。代码保留 50 位 Decimal 计算串及完整浮点 JSON；这些是计算精度，不表示来源几何有如此多有效数字。图上仅显示约三位有效数字。

边界含所选 unit 内必需访问管、位内电路、单元接触与局部布线；排除宏级 ADC、数字归约、泵、I/O、全局控制及阵列边缘。D6CIM 使用含局部共享 NOR/隔离与分布式压缩器的完整重复 tile，39 µm 的另一个 HCA/BFA 条带不计入。SRAM ACIM 的 MOM、GC 的存储电容已在报告的投影中，不重复相加。裸 MTJ、电极、沟道或 FeCAP 面积不能替代完整 bitcell。

所有可独立编程元件最多计 1 bit。MRAM 的强制互补 2T2MTJ + latch unit 为 **1 个独立 bit**；GC 的一个原生 3T1C 为 1 bit，其上层伪差分配对另留 metadata。INT8 位平面、NAND 正负编码、复制与参考页不进入本轮原生 cell 密度；因此主图既不是现有实现的有效权重密度，也不是完整芯片密度。

## 十类结果

`*` 为名义工艺节点归一化；NAND 与 FeFET 使用有明确方向的物理 half-pitch。右图不构成统一严格 half-pitch 排名。两图都不以无证据参数补齐十柱。

| 参考身份 / 原生 unit | A_xy [µm²] | b [bit] | a_bit [µm²/bit] | D [Mbit/mm²] | F_mem [nm] | alpha [F_mem²/bit] | 来源质量 |
|---|---:|---:|---:|---:|---:|---:|---|
| SRAM ACIM / 9T1C | 0.994 | 1 | 0.994 | 1.006 | 28* | 1267.86* | 文献完整 cell 几何 |
| SRAM DCIM / 8 列×128 行 tile | 582.4 | 1024 | 0.56875 | 1.758 | 28* | 725.446* | 文献尺寸导出；含重复局部逻辑 |
| 2D NOR | N/A | 1 | N/A | N/A | N/A | N/A | 缺匹配身份的完整 cell 与 F |
| 3D NAND, SLC, 500-layer projection | 0.030 | 500 | 0.000060 | 16666.7 | 20 | 0.150 | 作者几何模型上的用户指定投影 |
| WH-2T1R RRAM, m=1 | N/A | 1 | N/A | N/A | 28* | N/A | 缺 m=1 完整重复布局面积 |
| 互补 2T2MTJ IBMD MRAM + latch | ≈2.56 | 1 | ≈2.56 | ≈0.390625 | 40* | ≈1600* | 作者近似 bitcell 估计导出 |
| SLC voltage-mode 1T1R PCM | N/A | 1 | N/A | N/A | 40* | N/A | 未报告匹配完整 cell 面积 |
| HZO 1T1C FeRAM | N/A | 1 | N/A | N/A | N/A | N/A | 仅电容面积不足以闭合投影 |
| GC-04 硅 CMOS 3T1C | 6 | 1 | 6 | 0.166667 | 65* | 1420.12* | 文献完整 cell layout；弃用 MLC 增益 |
| 垂直 AND FeFET / 四层横向 tile | 0.0204 | 4 | 0.0051 | 196.078 | 60 | 1.41667 | 有来源 pitch 的几何模型 |

## NAND 500 层假设

NAND-04 的作者模型给出 BL pitch 40 nm、SSL pitch 0.75 µm、`13824 BL × 32 WL × 3 SSL` 个物理存储 cell。因此一 BL×SSL 横向 tile 为 `A_xy=0.040×0.750=0.030 µm²`，每层一个独立 SLC 元件；不能再因 SGVC 侧壁/柱形状多算一个 bit。`F_mem=20 nm` 是 BL 方向 half-pitch，不是 32 nm 外围 CMOS 节点。

| 计算行 | 有效存储层 / b | a_bit [µm²/bit] | D [Mbit/mm²] | alpha |
|---|---:|---:|---:|---:|
| 单层代数自检 | 1 | 0.030 | 33.3333 | 75 |
| 文献作者模型 L0 | 32 | 0.0009375 | 1066.667 | 2.34375 |
| 主图用户投影 | 500 | 0.000060 | 16666.667 | 0.150 |

从原 32 层到 500 层只用 `a_500=a_32×32/500` 一次；实现中保持 A_xy、F 和每层独立元件数不变，仅将 b=32 改为 500。不是把已折叠的 a_32 再除以 500。500 指有效可存数据的层，不含 dummy/selector，也不是封装叠 die。层数不同是两个配置行，不是误差上下界。

原 NAND-04 模型的 32 层不可称为被引芯片实测层数：NAND-05 原实验实际写明 **16 层**。本轮明确以 NAND-04 的 32 层模型为 L0，保留这个来源差异。500 层仅是固定横向几何的 cell-grid 线性密度投影，不预测 staircase 增长、阵列边界、良率、保持、电流、时序、工艺可制造性，也不添加任意折扣。主图不声称是已验证量产 SLC 典型器件，亦不证明现有 NAND CIM 吞吐可以在该配置保持。FeFET 仍保留自身有据的四层，没有一起扩到 500 层。

## 来源与现有图的关系

来源优先读取仓库现有原文；本轮只导出小型数值、定位、DOI/URL 与 PDF SHA-256，不复制大 PDF/源码树/日志到 OneDrive。四个缺口和排除替代值逐项见[来源说明](sources.zh.md)。NeuroSim 只实际验证普通 SRAM 与常规 1T1R 的相容面积链；不是独立预测所有材料存储密度。

论文 `papers/figures/prepare_hardware_layout.py` 的 Fig.3 数据入口仍为兄弟 NVM 任务 `analysis/11_summary_figures/data/{rho_tau_loglog_circles_validation.json,rho_tau_loglog_circles_points.csv}`；现行 NeuroSim 汇总脚本使用自身 `analysis/data/{ten_case_results,paired_scenario_results}.json`。本轮核对身份、没有更换任一图源；同类名字不能把这些速度点与 NAND500 或本轮 cell/tile 面积合成一套完整硬件配置。

## 复跑与独立复核

在当前任务目录运行，仅重新算几何与绘图：

```sh
/opt/anaconda3/bin/python -B analysis/12_footprint/build_footprint.py
# 不写正式结果的独立复跑（选新的非同步输出目录）：
/opt/anaconda3/bin/python -B analysis/12_footprint/build_footprint.py \
  --output-dir "$HOME/neurosim/runs/footprint-check/results" \
  --figure-dir "$HOME/neurosim/runs/footprint-check/figures"
# 面积探针：每例新源副本、新编译，不运行现有时序
python3 -B analysis/12_footprint/run_neurosim_probes.py \
  --run-dir "$HOME/neurosim/runs/footprint-check/probes"
```

绘图只需 Python 3 + matplotlib；计算可加 `--no-figures`。`build_footprint.py` 验证倒数单位、alpha 回乘、改 F 时绝对密度不变、SLC、互补 bit 和 NAND 单次折叠。独立 reviewer 从原论文重新提取数值，在自己的非同步目录重新计算并新编译探针，既检查输入身份又比较结果，不只比对生产 CSV。最终 PDF 已实际渲染为 PNG 并检查双面板文字、对数坐标、图例与脚注；渲染文件只在非同步目录保留。

范围检查：1462 个受保护现有任务文件（十例、30 点、rho–tau、历史归档等）逐字节不变，HEAD 保持讨论基线且无 staged 内容。本轮未写入论文；运行期间发现论文有并发修改，按原样保留，故不宣称论文逐字节不变。清单见 [范围检查记录](review/boundary_report.json)。未经授权没有 git add、commit 或 push。
