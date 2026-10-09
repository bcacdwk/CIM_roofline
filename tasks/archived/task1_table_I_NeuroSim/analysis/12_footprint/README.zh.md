# 原生二元存储密度与 F² 面积补充

本补充比较十类明确参考身份的原生二元存储 cell / 最小重复 tile。原六类已接受的输入和数值逐字段锁定；本轮为原四个缺口补充厂商几何、显式模型和独立文献参考。它不重建 INT8 矩阵面积、宏 PPA、等面积吞吐或三情景性能，也不改论文 Fig.3 与 rho–tau 图。两指标来自同一几何，不能当成两次独立验证。

- [双面板 PNG](output/storage_density_footprint.png) · [SVG](output/storage_density_footprint.svg) · [单页 PDF](output/storage_density_footprint.pdf)
- [权威小输入](geometry_inputs.json) · [原缺口历史](source_history.json) · [原六类锁定](reference_lock.json) · [逐类来源与边界](sources.zh.md) · [完整来源目录 / PDF 哈希](sources.json)
- [主表 CSV](results/footprint_main.csv) · [含 NAND 原层数 / 单层自检 CSV](results/footprint_all_rows.csv) · [完整精度 JSON](results/footprint_results.json)
- [两个新增布局模型输入](model_inputs.json) · [模型代码](geometry_models.py) · [布局/电气边界说明](geometry_model_notes.zh.md) · [粗静态驱动检查](drive_check.json) · [实际NMOS调用记录](primitive_record.json) · [几何/有限诊断结果](results/geometry_model_results.json)
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
| 2D NOR / GF 28SLPe SST ESF3 reference | 0.04 | 1 | 0.04 | 25 | 28* | 51.0204* | 厂商完整 bitcell；独立几何身份 |
| 3D NAND, SLC, 500-layer projection | 0.030 | 500 | 0.000060 | 16666.7 | 20 | 0.150 | 作者几何模型上的用户指定投影 |
| WH-2T1R RRAM, m=1 model | ≈0.685083 | 1 | ≈0.685083 | ≈1.45968 | 28* | ≈873.830* | 原生管尺寸 + 显式重复布局估计 |
| 互补 2T2MTJ IBMD MRAM + latch | ≈2.56 | 1 | ≈2.56 | ≈0.390625 | 40* | ≈1600* | 作者近似 bitcell 估计导出 |
| PCM / 28 nm FD-SOI 1T1R geometry reference | 0.036 | 1 | 0.036 | 27.7778 | 28* | 45.9184* | 文献完整 cell；显式替代几何参考 |
| HZO 1T1C / 130 nm conditional model | ≈5.4145 | 1 | ≈5.4145 | ≈0.184689 | 130* | ≈320.385* | 报告电容 + 公开HV访问管参考模型 |
| GC-04 硅 CMOS 3T1C | 6 | 1 | 6 | 0.166667 | 65* | 1420.12* | 文献完整 cell layout；弃用 MLC 增益 |
| 垂直 AND FeFET / 四层横向 tile | 0.0204 | 4 | 0.0051 | 196.078 | 60 | 1.41667 | 有来源 pitch 的几何模型 |

## 原四个缺口的补充口径

NOR 使用 GF 28SLPe / SST ESF3 的厂商报告完整 bitcell **0.04 µm²**。GF 给出的数值与 Microchip 同日发布的 **<0.05 µm²** 相容，但后者只是上界。本轮每物理元件计1 bit；不把厂商未单列的“SLC专门认证”写成事实。这个明确参考身份不等于原 S29GL/W25Q 服务点的芯片几何。

PCM 先复查原 40 nm PCM-03 三页正文及阵列/芯片图；仅有1T1R拓扑和18 mm²完整test-chip面积，没有相容局部 pitch 或访问管 W/L。现有700/125 µA的RESET/SET预算也缺同工艺单位宽驱动约束，不能据此任意缩小访问管。因此按用户授权选 Palhares 2024 / Arnaud IEDM2018 的 **28 nm FD-SOI 1T1R ePCM 0.036 µm²**独立几何参考，不另造40 nm投影。ST原工艺资料明确二态LRS=1/HRS=0；Palhares后续10状态实验不作为容量因子。这个参考不能与原40 nm吞吐点合并，图中按独立参考纹理和名称标明。

RRAM 保留 WH-2T1R 的原生 **T1 W/L=500/150 nm、T2 W/L=100/30 nm、m=1**。两个独立有接触的NMOS区域、不共用异网扩散；T1由WL控制，T2栅接局部X，非另一个WL。新实际NeuroSim `CalculateGateArea` 调用提供NMOS下层几何，再显式加入长沟道修正、接触/局部X、BL/SL/WL/TBL/GND和body-tie分配。上方RRAM落点边长0.0644 µm是**有条件的容纳假设**，不是测得器件尺寸；0.2/0.4 µm较大落点只作诊断。不使用m=4的30.3%比例、2倍1T1R或默认crosspoint。

FeRAM 采用文献明确的 **130 nm CUB结构及1 µm²有效HZO电容**，方形外形是保持面积的假设；访问端是明确命名的 **Sky130 5 V级NMOS参考，W=1 µm、L=0.5 µm**，不是Sony未公开的原管布局。以5 V WL、2.5 V储存节点作额定域和粗静态可行性检查。电容、电极、访问管及BL/WL/PL/body-tie在分层坐标中重叠/连接，按完整外包络求面积；不是裸电容面积，也不是机械相加或只有 `max(A_access,A_cap)`。不声称DRC/LVS、端点写电流、铁电瞬态或原时序闭合。

新模型均保存紧凑主条件、布局间距+20%的有限条件和少数单变量诊断。它们不是三情景性能或统计误差条；被更大包络遮蔽的变量可使总面积不变，但内部尺寸仍响应。输入、实际primitive记录和输出面积严格绑定，主表不从手填面积绕过模型。

原四条N/A判断及其排除理由完整保留在 [source_history.json](source_history.json)，不倒写为先前已有测量。新增数值的身份、模型假设和证据等级另列；原六类及NAND原层数/单层自检由自动哈希锁保护。

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

来源优先读取仓库现有原文；本轮只导出小型数值、定位、DOI/URL 与 PDF SHA-256，不复制大 PDF/源码树/日志到 OneDrive。四项补充路线和保留的历史判断见[来源说明](sources.zh.md)。直接报告的NOR/PCM面积直接换算；NeuroSim仅为相容CMOS组成和几何链提供计算，不是独立预测所有材料存储密度。

论文 `papers/figures/prepare_hardware_layout.py` 的 Fig.3 数据入口仍为兄弟 NVM 任务 `analysis/11_summary_figures/data/{rho_tau_loglog_circles_validation.json,rho_tau_loglog_circles_points.csv}`；现行 NeuroSim 汇总脚本使用自身 `analysis/data/{ten_case_results,paired_scenario_results}.json`。本轮核对身份、没有更换任一图源；同类名字不能把这些速度点与 NAND500 或本轮 cell/tile 面积合成一套完整硬件配置。

## 复跑与独立复核

在当前任务目录运行。默认入口使用已核验的真实NeuroSim primitive记录，重算两个布局模型并验证A/b绑定，再生成十类结果与图；不会重新运行既有时序：

```sh
/opt/anaconda3/bin/python -B analysis/12_footprint/build_footprint.py
# 不写正式结果的独立复跑（选新的非同步输出目录）：
/opt/anaconda3/bin/python -B analysis/12_footprint/build_footprint.py \
  --output-dir "$HOME/neurosim/runs/footprint-check/results" \
  --figure-dir "$HOME/neurosim/runs/footprint-check/figures"
# 新模型的独立fresh构建：锁定原函数，所有20个几何请求实际执行
python3 -B analysis/12_footprint/run_geometry_primitives.py \
  --run-dir "$HOME/neurosim/runs/footprint-check/primitives"
/opt/anaconda3/bin/python -B analysis/12_footprint/build_footprint.py \
  --primitive-record "$HOME/neurosim/runs/footprint-check/primitives/primitive_record.json" \
  --output-dir "$HOME/neurosim/runs/footprint-check/fresh-results" --no-figures
```

绘图只需 Python 3 + matplotlib；计算可加 `--no-figures`。`build_footprint.py` 验证倒数单位、alpha 回乘、改 F 时绝对密度不变、SLC、互补 bit 和 NAND 单次折叠。本轮独立 reviewer 在非同步目录新编译20个NMOS请求，独立复算两个新增模型的主条件/有限诊断及十类量，检查原源、bit计数、六类锁定和布线边界，不只比对生产CSV。原普通SRAM/1T1R探针保留此前验证记录，本轮没有重复运行。最终 PDF 已实际渲染为 PNG 并检查双面板文字、对数坐标、图例与脚注；渲染文件只在非同步目录保留。

范围检查：原六类输入和结果及NAND诊断逐字段不变；现有十例、30点、rho–tau及历史文件保持本轮保护范围。本轮起始HEAD为 `782921c498750ebc3b2dfaf374daf5668e6614ca`；definition中的 `reference_git_sha=8795902...` 标识最初几何补充的讨论来源，`completion_reference_git_sha` 标识本轮。未写入论文，期间发现的并发论文修改原样保留；详见 [范围检查记录](review/boundary_report.json)。没有 git add、commit 或 push。
