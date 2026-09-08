# 证据覆盖矩阵（R1 正文复核）

更新：2026-09-08。除标注“C 待主文”的项目外，以下引用均已检查实际正文中的相关内容。这里的“核心”表示值得用于后续参考情景，不等于无需换算就可填表。页码与边界见 [逐篇审阅](FULLTEXT_REVIEW_R1.md)，所有 ID 在 [目录](LITERATURE_CATALOG.md) 可点击到 PDF。

| 资料组 | 读侧 | 写侧／更新步骤 | 粒度／并行条件 | 外围或求值桥接 | 交叉验证与限制 | 全文可用性 |
|---|---|---|---|---|---|---|
| 00 CMOS | [CMOS-02](LITERATURE_CATALOG.md#CMOS-02) ADC 实测；CMOS-07 SRAM sensing | [CMOS-03](LITERATURE_CATALOG.md#CMOS-03) 动态写模型；[CMOS-07](LITERATURE_CATALOG.md#CMOS-07) clock/WL/port | CMOS-04 同址冲突；CMOS-07 局部配置 | [SACIM-03](LITERATURE_CATALOG.md#SACIM-03) 实际 28 nm DAC/ADC；SDCIM-01/03 数字完整精度 | CMOS-01/05 负载不同；CMOS-06 仅仿真；无公开完整 compiler 库 | 自有 7/7；共享 macro 已有，SACIM-05 C 待主文 |
| SRAM ACIM | SACIM-01/02/03/04 求值与测量 | 普通 SRAM：CMOS-03/07；macro 独立写周期仍需辨认 | SACIM-01 的 core/网络；SACIM-03/04 实际阵列与 ADC 数量 | SACIM-03 28 nm 完整路径；SACIM-04 22 nm R2R 驱动/SAR 内步骤 | SACIM-02/04 为其他工艺；[SACIM-05](LITERATURE_CATALOG.md#SACIM-05) C 补 28 nm 8-bit 共享读出 | 4/5 主文；2022 会议前作仅作版本 |
| SRAM DCIM | SDCIM-01/03 28 nm | SDCIM-01 128-bit 写口；CMOS-03/07 普通写服务 | SDCIM-01/03 多时钟展开、post-sum；SDCIM-02 操作依赖周期 | SDCIM-01/03 数字外围；不能拿单时钟作完整 VMM | SDCIM-02 65 nm 独立算法/电路交叉 | 3/3 主文，另有同篇作者 slides |
| 2D NOR | NOR-01/02/03 存储接口；NOR-04 模拟传播 | NOR-01/02/03 的内置 program/erase/BUSY；NOR-05 write-verify | word/page/sector/buffer 脚注已确认；NOR-04 half-select | NOR-04/05 细调到模拟 CIM 的桥接 | 三家产品，但 NOR-03/04/05 有 SST 生态关联；不能移用 SPI rate | 5/5，datasheet 正式版本齐 |
| 3D NAND | NAND-01 MLC/TLC；NAND-02/03 QLC | NAND-01 program/erase；NAND-03 page-program；SLC 完整更新仍缺 | NAND-02 物理/逻辑 page 与 6-plane；NAND-05 SLC 选择/复制 | NAND-04 RC/HSPICE 模型；NAND-05 实际器件与拟议求值 | Micron、Sandisk/KIOXIA、SK hynix；NAND-04/05 有同器件来源关系 | 5/5；不是完整部件 datasheet 都齐 |
| RRAM | RRAM-01/02/05 完整读流程 | RRAM-01 实际闭环；RRAM-02 脉冲次数；RRAM-04 内部提交；[RRAM-06](LITERATURE_CATALOG.md#RRAM-06) C | RRAM-02 分段/单 cell verify；RRAM-05 binary+空间编码 | RRAM-01/02/05 专用 ADC/感测 | RRAM-03 raw/P&V 可靠性；RRAM-04 慢产品交叉，不强行平均 | 5/6；C 补 page SET/RESET 控制 |
| MRAM | MRAM-01 电阻求和/TDC；MRAM-03/04 普通感测 | MRAM-01 互补行写两步；MRAM-03 自终止；MRAM-05 接口语义 | MRAM-01/03 局部边界；MRAM-02 near-memory 须另列 | MRAM-01 为模拟；[MRAM-06](LITERATURE_CATALOG.md#MRAM-06) C 为 bitcell 数字 | MRAM-02 不再当模拟 CIM；SI 已确认 PUF/普通写路径有别 | 5/6 主文；MRAM-02/06 SI 齐 |
| PCM | PCM-01/02 tile；PCM-03 hybrid SLC/MLC | PCM-01 diagonal selection；PCM-02 row CLT；[PCM-06](LITERATURE_CATALOG.md#PCM-06) C 追溯细节 | PCM-01 diagonal 与 PCM-02 row 并行不同；PCM-03 位串行 | PCM-01/02 ADC/PWM/控制；PCM-03 VSA 四阶段 | IBM 同技术线非独立材料；PCM-04 ScSbTe、PCM-05 GST 条件对照 | 5/6 主文；PCM-04-SI 真缺件 |
| HfO₂ FeRAM | FERAM-02/03/04 感测与恢复 | FERAM-02/03/04 writeback；FERAM-01 两步行更新 | FERAM-03 64 kb；FERAM-04 双层及完整 tRC | FERAM-01 C2FeRAM 机制/模型；FERAM-06 仅 FeCAP 部分 | Sony/SK hynix/Micron 阵列互补；FERAM-05 外延器件条件不同 | 6/6，现有两份 SI 齐 |
| Gain-cell eDRAM | GC-01/02/04/05 | GC-02 WWL 升压；GC-04 粗/精写；GC-05 storage/stationary | GC-02 保持分布/刷新；GC-05 更新与计算重叠模式 | GC-01/04 模拟；GC-05 数字；GC-03 模型桥接 | 65/28/16 nm 不混用；保持终点、允许错误率及状态精度分开 | 5/5 |
| 3D FeNOR/vertical FeFET | FENOR-01/02 器件/小阵列；FENOR-04 阵列逻辑 | FENOR-01/02/04/06 PGM/ERS 偏置与 MW 终点 | FENOR-02 半选/相邻扰动；NOR/AND 拓扑分别记录 | FENOR-01/02/04 的大规模 CIM/外围多为模型 | FENOR-03/04 同包；FENOR-06 与 Zhou 同团队；FENOR-05 仅 FeNAND 对照 | 6/6 文件记录、5 个包；4 个核心来源 |

## 真正剩余的资料缺口

1. 四篇 C 主文及 PCM-04-SI：已明确到题名、DOI、文件目标路径，见 [V2](DOWNLOAD_REQUESTS_V1.md)。没有继续请求已归档附件。
2. 3D NAND SLC 完整 program/erase、plane busy/命令并发：现有 SLC 器件与 burst 模式各有价值，但不足以视为同一个完整产品时序基线；本轮未核实到合适完整公开手册，保留缺口。
3. 通用 28 nm memory compiler 全时序库未公开取得。现有 CMOS-03/07 与实际 28 nm CIM macro 能支持带明示条件的参考情景，不能冠以 foundry 保证值。

## 后续仍需选择的共同条件

- 服务边界：local sub-array、macro、共享转换器/驱动是否包含在内。
- 逻辑尺寸、输入/权重/输出精度；ADC 名义 bit 与有效精度/截断分开。
- ADC/DAC 共享、位串行展开、数字累加及哪些步骤可重叠。
- Flash/PCM/RRAM 的 binary、多级、闭环容差，以及直接更新、先擦再编程或含隐藏 RESET 的模式。
- FeRAM 读后恢复、gain-cell 刷新与 stationary 切换是否占用同一服务资源。
- 统一普通 CMOS 服务的哪些条件，保留哪些介质专用 HV、电流、sense margin、保持/错误率约束。

本轮不为这些条件预先固定最终延时或范围，也不制作 ρ、τ、RI* 占位表。
