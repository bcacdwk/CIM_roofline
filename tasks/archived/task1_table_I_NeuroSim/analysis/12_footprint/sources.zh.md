# 几何来源与缺口

完整文献标题、作者、DOI/URL、原仓库路径及 PDF SHA-256 见 [sources.json](sources.json)。页码均为 PDF 页码。已有来源 PDF 只读；抽取文本和渲染留在非同步区。原始几何、口径与逐例限制也直接写入 [geometry_inputs.json](geometry_inputs.json)。

| 身份 | 来源 / 原始量 | 主图选择与限制 |
|---|---|---|
| SRAM ACIM | [SACIM-03](https://doi.org/10.1109/tcsii.2023.3234620) p3 SecIII: 0.994 µm², 28 nm CMOS；p2 SecII-B: 1.33 fF MOM 在 cell 上方 | 完整 9T1C bitcell，b=1。电容已包含在投影内，不额外相加。 |
| SRAM DCIM | [SDCIM-01](https://doi.org/10.1109/ESSCIRC59616.2023.10268725) p3 Fig8: 91 µm 横向×6.4 µm 纵向、8 列×128 行；SecIII: 28 nm | A=582.4 µm² / 1024 bit。含重复局部 NOR、隔离及 15:4 压缩器；不含另一个 39 µm HCA/BFA 条带。图示尺寸估计，不称精确 layout extraction。0.379 µm² 裸核省略共享局部电路，仅作背景。 |
| 2D NOR | NOR-01、NOR-02 商用手册给服务预算；[NOR-05](https://web.ece.ucsb.edu/~strukov/papers/2016/DRCflash2016.pdf) p1 的约 1.5 µm² 属改造后的 analog-tunable 180 nm ESF1 | 所选二元 NOR 缺匹配完整 cell/tile 和平面 F，N/A。不能把异身份模拟调谐单元或整 die 密度替代。 |
| 3D NAND | [NAND-04](https://doi.org/10.1109/JXCDC.2021.3093772) p2 SecII-A / Fig1: BL pitch 40 nm、SSL pitch 0.75 µm、13824×32×3 cell；[NAND-05](https://doi.org/10.1109/IEDM19573.2019.8993652) p1: 实验 16 层 SLC | 采用前者作者 32 层模型的横向几何，A=0.030 µm²、每层 1 bit；保存32层行，主图仅把b改500。前者对后者层数的引用差异明确保留。无侧壁二次计bit，不含 staircase / 阵列边界。 |
| WH-2T1R RRAM | [RRAM-05](https://doi.org/10.1109/jssc.2023.3280357) p3 Fig4: m=4 布局和相对 30.3% 开销，T1 W/L=500/150 nm、T2 W/L=100/30 nm | 这些是管尺寸而非 cell pitch；缺当前 m=1 完整 unit 绝对面积，N/A。不得按晶体管数线性换算或套 1T1R。F=28 nm 仅名义节点，仍因缺面积而 alpha=N/A。 |
| MRAM | [MRAM-06](https://doi.org/10.1038/s41928-025-01479-y) 补充材料 p10: 自身 IBMD 约 1600F²；主文 p2 Fig2: 互补 2T2MTJ + latch，原生 40 nm | A≈1600×0.040²=2.56 µm²，b=1。作者近似模型归类为工程估计；共享 tail 不重复添加。不能用补充 p11 对比旧设计的约1200F²，也不能把两互补MTJ算2bit。 |
| PCM | [PCM-03](https://doi.org/10.1109/isscc42614.2022.9731670) p1/p2 Fig11.3.2: 40 nm 1T1R 与 hybrid SLC/MLC 架构 | 只取SLC，但匹配完整存储cell面积未报告，N/A。不能用电极/加热器面积或宏容量密度替代。40 nm 是名义节点。 |
| HZO FeRAM | [FERAM-03](https://doi.org/10.1109/vlsitechnology18217.2020.9265063) p1 Fig5-7: 电容0.4–1.0 µm²，位于访问管上方；[FERAM-02](https://doi.org/10.1109/iedm19574.2021.9720545) p1: 1X nm | 完整1T1C投影与准确F未闭合，N/A。电容面积非bitcell；重叠不能机械相加；1X不猜成某一整数，5 nm膜厚不作F。 |
| GC-04 eDRAM | [GC-04](https://doi.org/10.1109/jssc.2023.3339887) p6 SecIII-A / Fig8: 65 nm、完整3T1C layout 6 µm²、10 fF MOM在metal4–7 | 一个硅CMOS 3T1C取1bit；不采用原文3bit MLC对应2 µm²/bit的容量增益。上层伪差分配对仅metadata；不换成IGZO或1T1C DRAM。 |
| 垂直 AND FeFET | [FENOR-02](https://vlsi26.mapyourshow.com/8_0/sessions/session-details.cfm?ScheduleID=251) p3 Fig11b,c: X pitch120 nm、Y pitch170 nm、split BL/SL；p1/p2 Fig2: 四层 | A=0.0204 µm²，4层×每层1独立bit，a=0.0051。为TCAD/SPICE模型pitch的cell-grid估计；不是实测layout提取、0.001 µm²沟道面积或256层headline密度。保留4层，不扩500；不加第二个侧壁bit。 |

F_mem 分开记录：ACIM 28、DCIM 28、MRAM 40、GC 65 nm 均保守标名义节点并在右图加 `*`；NAND 20 nm 是 BL 方向 pitch/2，FeFET 60 nm 是 X 方向 pitch/2，正交 pitch 已保留在绝对几何中。膜厚、垂直层距和 MTJ 直径不作为平面 F。两类 F 定义不能冒充严格统一 half-pitch 比较。

证据分级：ACIM、GC 为文献完整 cell 几何；D6CIM、MRAM、FeFET 为有边界的模型/尺寸几何估计；NAND500 用独立投影纹理。四个缺口经过现有原文及定向补查仍缺匹配完整 unit，不填默认数。未取得量产500层SLC完整宏或性能验证，也未做完整阵列 overhead 估算；没有添加任意折扣。
