# 几何来源与边界

完整文献标题、作者、DOI/URL、原仓库路径及 PDF SHA-256 见 [sources.json](sources.json)。页码均为 PDF 页码。已有来源 PDF 只读；抽取文本和渲染留在非同步区。原始几何、口径与逐例限制也直接写入 [geometry_inputs.json](geometry_inputs.json)。

| 身份 | 来源 / 原始量 | 主图选择与限制 |
|---|---|---|
| SRAM ACIM | [SACIM-03](https://doi.org/10.1109/tcsii.2023.3234620) p3 SecIII: 0.994 µm², 28 nm CMOS；p2 SecII-B: 1.33 fF MOM 在 cell 上方 | 完整 9T1C bitcell，b=1。电容已包含在投影内，不额外相加。 |
| SRAM DCIM | [SDCIM-01](https://doi.org/10.1109/ESSCIRC59616.2023.10268725) p3 Fig8: 91 µm 横向×6.4 µm 纵向、8 列×128 行；SecIII: 28 nm | A=582.4 µm² / 1024 bit。含重复局部 NOR、隔离及 15:4 压缩器；不含另一个 39 µm HCA/BFA 条带。图示尺寸估计，不称精确 layout extraction。0.379 µm² 裸核省略共享局部电路，仅作背景。 |
| 2D NOR / GF28 ESF3 reference | [GF官方2023-09-27](https://gf.com/news-and-events/news/globalfoundries-and-microchip-announce-microchips-28nm-superflash-embedded-flash-memory-solution-in-production/): ESF3完整bitcell 0.04 µm²；[Microchip同日公告](https://www.microchip.com/en-us/about/news-releases/corporate/globalfoundries-microchip-announce-microchips-28nm-superflash): <0.05 µm² | 采用GF明确值；不把Microchip上界当精确面积。GF28SLPe名义F=28nm。按本轮binary-use计1bit，无MLC增益；与原S29GL/W25Q吞吐身份分开。 |
| 3D NAND | [NAND-04](https://doi.org/10.1109/JXCDC.2021.3093772) p2 SecII-A / Fig1: BL pitch 40 nm、SSL pitch 0.75 µm、13824×32×3 cell；[NAND-05](https://doi.org/10.1109/IEDM19573.2019.8993652) p1: 实验 16 层 SLC | 采用前者作者 32 层模型的横向几何，A=0.030 µm²、每层 1 bit；保存32层行，主图仅把b改500。前者对后者层数的引用差异明确保留。无侧壁二次计bit，不含 staircase / 阵列边界。 |
| WH-2T1R RRAM model | [RRAM-05](https://doi.org/10.1109/jssc.2023.3280357) p3 Fig4给T1 W/L=500/150nm、T2 W/L=100/30nm和准确端网；锁定NeuroSim原几何函数及常数 | 本轮用m=1真实W/L建两个独立有接触的NMOS区域，再加local X/BL/SL/WL/TBL/GND及body-tie分配，得到条件估计。RRAM上方落点.0644um是工程容纳假设，另查.2/.4um；不是m=4比例折算或默认1T1R。完整参数、来源/假设及坐标见model_inputs和model results。 |
| MRAM | [MRAM-06](https://doi.org/10.1038/s41928-025-01479-y) 补充材料 p10: 自身 IBMD 约 1600F²；主文 p2 Fig2: 互补 2T2MTJ + latch，原生 40 nm | A≈1600×0.040²=2.56 µm²，b=1。作者近似模型归类为工程估计；共享 tail 不重复添加。不能用补充 p11 对比旧设计的约1200F²，也不能把两互补MTJ算2bit。 |
| PCM / 28 nm 1T1R geometry reference | [Palhares2024](https://doi.org/10.1038/s44335-024-00008-y) p2 Results/Fig1: 0.036 µm²/bit、28nm FD-SOI 1T1R；[Arnaud IEDM2018](https://doi.org/10.1109/IEDM.2018.8614595)，ST官方报告slide11/27/28给完整cell和二态LRS1/HRS0 | 原PCM-03 40nm信息缺局部pitch、访问W/L及相容单位宽驱动约束，不能闭合40nm模型。按信息充分性选择已授权28nm参考，F必须28nm；后续10状态实验不增容量，不另加selector、不贴到40nm。 |
| HZO FeRAM model | [Okuno JEDS](https://doi.org/10.1109/JEDS.2021.3129279) p2给130nm、CUB和0.4/.6/.8/1um²电容；公开Sky130 nfet_g5v0d10v5参考及规则 | 选1um²有效电容，方形外形是假设；访问W1/L.5um、5V WL/2.5V存储节点是条件参考，不是Sony测得完整cell。按跨层坐标保留电极/BL/WL/PL/bodytie，NMOS几何由实际原函数+长L/接触修正；F130为名义node。仅额定域/粗静态检查，不做瞬态或DRC认证。 |
| GC-04 eDRAM | [GC-04](https://doi.org/10.1109/jssc.2023.3339887) p6 SecIII-A / Fig8: 65 nm、完整3T1C layout 6 µm²、10 fF MOM在metal4–7 | 一个硅CMOS 3T1C取1bit；不采用原文3bit MLC对应2 µm²/bit的容量增益。上层伪差分配对仅metadata；不换成IGZO或1T1C DRAM。 |
| 垂直 AND FeFET | [FENOR-02](https://vlsi26.mapyourshow.com/8_0/sessions/session-details.cfm?ScheduleID=251) p3 Fig11b,c: X pitch120 nm、Y pitch170 nm、split BL/SL；p1/p2 Fig2: 四层 | A=0.0204 µm²，4层×每层1独立bit，a=0.0051。为TCAD/SPICE模型pitch的cell-grid估计；不是实测layout提取、0.001 µm²沟道面积或256层headline密度。保留4层，不扩500；不加第二个侧壁bit。 |

F_mem 分开记录：ACIM/NOR/DCIM/RRAM/PCM 28、MRAM 40、FeRAM 130、GC 65 nm 均标名义节点并在右图加 `*`；NAND 20 nm 是 BL 方向 pitch/2，FeFET 60 nm 是 X 方向 pitch/2，正交 pitch 已保留在绝对几何中。膜厚、垂直层距和 MTJ 直径不作为平面 F。两类 F 定义不能冒充严格统一 half-pitch 比较。

证据分级：ACIM、GC及厂商NOR为报告完整cell几何；D6CIM、MRAM、FeFET与本轮RRAM/FeRAM为有边界的模型/尺寸估计；PCM为显式公开几何proxy；NAND500用独立投影纹理。原四条N/A判断保留在source_history，不倒写为原来已测得完整cell。未取得量产500层SLC完整宏或性能验证，也未做完整阵列 overhead 估算；没有添加任意折扣。

NOR/PCM补充来源均已核对原厂/作者页面：GF明确bitcell；Microchip技术页说明SuperFlash为split-gate NOR。Palhares论文p2先介绍物理1T1R与面积，再讨论MLC；其2025年更正DOI10.1038/s44335-025-00019-3仅补Data Availability，无面积修改。ST作者官方IEDM2018报告将0.036 µm²标在含WL/SL/BL、GST/heater的完整cell，并展示1/0二态。所有下载PDF只保留本地，规范目录只存小型源定位和哈希。
