"""R0 curated source selections. No throughput data or parameter estimation."""

GROUPS = [
    ('00_cmos_periphery', '00 — 28 nm CMOS 外围参考资料',
     '共同参考需要分别覆盖转换、输入驱动、局部感测／mux 和数字求值。这里组合官方 IP 产品资料、实际 28 nm 原始电路论文及两篇共享 CIM macro 来源；商业 IP 公布的采样率不等于给定 CIM 负载下的建立时间。公开 memory compiler 的完整时序库仍缺，不采用来源不明的商业 compiler 手册镜像。'),
    ('01_sram_acim', '01 — SRAM ACIM',
     '用不同团队的电荷域／电容阵列 macro 核查完整多位求值、ADC 使用方式和局部边界。共享 CMOS-03／04 补普通 SRAM 读写基础；不同工艺的 macro 只作结构与量级交叉参考，不能直接冠以统一 28 nm 的性能。'),
    ('02_sram_dcim', '02 — SRAM DCIM',
     '数字求值需区分单个时钟、位串行步骤和完整精度输出。D6CIM、动态逻辑 macro 与可重构数字 macro 提供互补实现，共享 CMOS-03／04 解释普通写入与读写冲突；未要求单篇同时闭合两路吞吐。'),
    ('03_nor_2d', '03 — 2D NOR Flash',
     '三家厂商的存储资料提供编程、擦除、busy 和操作粒度定义，两篇早期原始 NOR 模拟计算论文连接普通存储与精细电导调谐。普通存储时序可以支撑更新依据，但 SPI／并行封装输出速度和模拟 CIM 求值不是同一边界。'),
    ('04_nand_3d', '04 — 3D NAND Flash',
     'Micron 的 MLC／TLC 技术资料与 SK hynix、KIOXIA 的 QLC 原始芯片论文分开登记状态模式；后两篇桥接资料解释 NAND 串、字线选择与 CIM 求值。重点保留页／块／plane／die 的层级差异，未用 SSD 带宽代表阵列；SLC 专用工作模式的直接候选仍是缺口。'),
    ('05_rram', '05 — RRAM',
     '厂商 ReRAM datasheet 和 Weebit／CEA-Leti 原始测量补普通写入与器件条件；三种 CIM 实现补差分编码、读出和编程策略。比较时必须保留 binary／multi-level、单脉冲／闭环完成的区别，不能把厂家 SPI 时钟当作 cell 切换时间。'),
    ('06_mram', '06 — MRAM',
     'Jung 的电阻求和与 Chiu 的集成 spintronic macro 提供求值桥接，1T1MTJ／2T2MTJ 存储 macro 和 Everspin STT 产品资料补读写服务。器件机制、互补单元和自终止写入需分别保留；这里没有把不同 MTJ／感测实现混为单一实测芯片。'),
    ('07_pcm', '07 — PCM',
     '两种 IBM 多核／多 tile 实验和 TSMC 的 SLC／MLC macro 用于局部求值与并行写入，ST 合作器件测量及 Sc-Sb-Te 原始论文补材料与写入终点差异。SET、RESET、模拟精度与完整编程过程分别核查；两个 IBM 芯片是不同实验，但不是完全独立的工艺团队交叉证据。'),
    ('08_feram_hfo2', '08 — FeRAM（HfO₂-based）',
     '仅将实际 HfO₂ 系电容存储／相关阵列作为主体：C2FeRAM 桥接、Sony／SK hynix／Micron 阵列、共掺杂 hafnia 器件和 FeCAP–memristor 集成研究互补。破坏性读／恢复、极化判读与模拟状态的完成条件留待全文审阅；传统 PZT 商用 F-RAM 不占核心候选。'),
    ('09_gain_cell_edram', '09 — Gain-cell eDRAM',
     '硅 gain-cell 实测存储、2T1C／3T1C CIM 和 oxide gain-cell 设计依据共同覆盖读写端口、保持和刷新。bulk、FD-SOI、氧化物通道和不同状态精度分开标注，普通 1T1C DRAM 不进入这一组。'),
    ('10_fenor_3d', '10 — 3D FeNOR／vertical FeFET',
     '两篇指定 Zhou 原稿原位复制，并补 Feng 的 BEOL 3D FeNOR、POSTECH 三维 FeFET 及直接相关栅堆栈研究。Feng 会议／期刊两项保守合为一个资料包，Zhou 系列显式记录同团队关系；2026 原稿正文写明 AND-type，不因类别简称 FeNOR 改写其结构。')
]

# Shared sources retain one master PDF and stable ID.
SHARED = {
    '00_cmos_periphery': ['SDCIM-01', 'SACIM-03'],
    '01_sram_acim': ['CMOS-03', 'CMOS-04'],
    '02_sram_dcim': ['CMOS-03', 'CMOS-04'],
}

SOURCES = []
def add(sid, group, year, short, roles, level, priority, purpose, **kw):
    SOURCES.append(dict(source_id=sid, group=group, year=year, short_title=short,
                        roles=roles.split('；'), evidence_level=level, priority=priority,
                        purpose=purpose, **kw))

add('CMOS-01','00_cmos_periphery',None,'IGADACT01C_v002','28 nm 外围服务；输入驱动；DAC 转换服务','外围电路／IP 产品规格','P1',
    '官方具体 DAC IP 简表确认真实 28 nm 工艺、分辨率、转换率、输出电流及 compliance 条件；为统一输入服务提供出发点。缺指定容性负载的 settling 和详细接口时序，不足以单独定最终延时。',
    title='IGADACT01C — 28nm HPM 1.8V/0.9V 10bit 300MHz Current Steering DAC [3ch]', authors=['Global Unichip Corporation (GUC)'], venue='官方 Product Brief，v002（未署发行日期）', publication_date=None,
    official_url='https://www.guc-asic.com/en/solutions/IPPortfolio/MixedSignalFront-EndIP',
    access_urls=['https://www.guc-asic.com/upload/2025_07_01/4_20250701210629mn8737Faf18.pdf'],
    document_id='IGADACT01C_Product_Brief_v002',
    process_class='直接的 28 nm 证据（官方 IP 明确 HPM 工艺）',
    identity_note='两页原文未署发行日期；URL 的 2025-07-01 是上传路径，不能作为发表年。文件名用 undated。另有 2022Q3 产品总览索引作为版本线索，不再请求内容较粗的总览。',
    confirmed_content='已核验官方两页 PDF 的产品编号、文档编号、工艺、输出条件和转换服务类别；详细负载建立指标未公开。')
add('CMOS-02','00_cmos_periphery',2021,'AsynchronousSAR','28 nm 外围服务；ADC 转换；输入建立','外围电路（实测 ADC）','P1',
    '核查 SAR 转换／采样节拍、分辨率与有效精度、输入与参考建立条件；同一设计的 timing-protection 说明如何防止把内部 SAR 步骤误作完整服务。',
    doi='10.3390/electronics10222856', process_class='直接的 28 nm 证据',
    access_urls=['https://dr.ntu.edu.sg/server/api/core/bitstreams/803899ac-0885-46c7-af0a-9106d5013c97/content'],
    confirmed_content='已看机构公开正式 PDF 的题名、摘要和架构／measurement 小节；确有实测转换器、时序保护及精度评价。未决定其与 CIM 输入条件的适配。')
add('CMOS-03','00_cmos_periphery',2012,'SRAM_Assist','28 nm 外围服务；读写时序；负载与驱动条件','器件／SRAM 局部电路（建模与仿真）','P1',
    '读写 assist、WL 脉冲与 bitline 负载条件共同约束普通 SRAM 写入估计；可作为显式条件的参考设计依据，不能宣称其仿真假设是量产 compiler 保证值。',
    doi='10.1109/TCSII.2012.2231015', process_class='直接的 28 nm 证据（模型条件）',
    access_urls=['https://people.eecs.berkeley.edu/~krste/papers/zimmer-ieeetcasII-2012.pdf','https://citeseerx.ist.psu.edu/document?doi=8d786312b6f1a1727b8d26304236576dcc1f3f12&repid=rep1&type=pdf'],
    older_reason='直接公开 28 nm 局部 SRAM 的负载与 assist 时序建模条件，仍适用于基础方法核查。',
    identity_note='DOI 登记与作者发表页一致；网页可读原文片段，作者 PDF 返回 404、CiteSeerX 连接超时。',request_rank=3)
add('CMOS-04','00_cmos_periphery',2011,'DualPort_SRAM','28 nm 外围服务；局部读写；操作粒度与冲突','阵列／局部 macro','P1',
    '独立核查双口 SRAM 的局部读写边界、感测与 write-read disturb 条件；补仅有 assist 仿真而无实际 macro 的不足。双口机制不能无条件代表单口 SRAM。',
    doi='10.1109/JSSC.2011.2164021', process_class='直接的 28 nm 证据',
    older_reason='实测 28 nm SRAM 基础 macro；保留用于普通读写服务和端口冲突核查。', request_rank=4)
add('CMOS-05','00_cmos_periphery',2025,'Interleaved_DAC','28 nm 外围服务；DAC／驱动；采样与建立的区别','外围电路（DAC 原始设计，实测属性待主文核查）','P1',
    '核查真实 28 nm 电流舵 DAC 的分辨率、输出方式、各子 DAC 节拍及负载条件，补 IP 简表缺少的电路机制。高带宽四路交织输出不是单个 CIM 字线驱动的直接替代；是否包含可用阶跃建立指标待全文判断。',
    doi='10.1109/TCSII.2024.3518084', process_class='直接的 28 nm 证据（CIM 负载适配未确认）',
    publication_note='期刊卷期为 2025-02；DOI 字符串含 2024，不将其当作最终卷期年份。', request_rank=5)
add('CMOS-06','00_cmos_periphery',2025,'ReconfigurableSAR','28 nm 外围服务；ADC 精度与节拍；独立模型交叉核查','外围电路（28 nm 后仿真，非实测）','P2',
    '补第二团队的 28 nm 单通道 SAR；可核查分辨率改变如何影响完整转换服务和输入带宽。不能只凭最高采样率假设 CIM 精度与驱动已经满足。',
    doi='10.1587/elex.22.20250220', process_class='直接的 28 nm 模型／后仿真条件，不是实测芯片',
    access_urls=['https://www.jstage.jst.go.jp/article/elex/advpub/0/advpub_22.20250220/_pdf'],
    version='J-STAGE advance publication（公开日期 2025-05-07；期刊登记 2025-06-25）',
    confirmed_content='已核验公开接受版封面与正文题名、作者；第 4 节明确 Simulation results，比较表标注 post-layout。仅作电路模型交叉核查；具体输入负载／精度适配留待 R1。')

add('SACIM-01','01_sram_acim',2022,'Scalable_IMC','完整多位求值；操作粒度与局部并行度；CIM 求值桥接','阵列／局部 macro 及整芯片','P1',
    '分清位相位、ADC 和数字重构，寻找输入 payload 对应的完整求值边界；可用普通 SRAM 写入描述补接口线索。', old='t1_jia2022',
    process_class='其他工艺的量级交叉参考（65 nm）', confirmed_content='原 PDF 的阵列、ADC、BPBS SIMD 与测量章节已初筛；完整求值结构可用，普通权重写入服务仍待补。')
add('SACIM-02','01_sram_acim',2025,'PICO_RAM','CIM 求值桥接；输入 DAC／ADC 共享；完整多位求值','阵列／局部 macro','P1',
    '补原位多位电荷计算及 DAC／MAC／ADC 复用同组电容的实现，检查输入方式与精度条件；与 Jia 的位串行路径互补。',
    doi='10.1109/JSSC.2024.3422826', process_class='其他工艺的量级交叉参考（65 nm）',
    access_urls=['https://arxiv.org/abs/2407.12829','https://arxiv.org/pdf/2407.12829'],
    version='作者 arXiv 接受稿；首次公开 2024-07，期刊卷期 2025-01',
    confirmed_content='已核验作者全文题名、原位电容计算与测试 macro；接受稿足够做 R0，不重复请求正式版。')
add('SACIM-03','01_sram_acim',2023,'Hierarchical_Attenuator','28 nm 外围服务；CIM 求值桥接；ADC 与局部读出','局部 macro 电路设计；公开 2022 前作为仿真','P2',
    '28 nm 9T1C 电荷域 macro 连接阵列、权重电容衰减器与 flash ADC，补独立 ADC 无法说明的 CIM 读出条件。稀疏性优化的模式与完整精度节拍需全文确认。',
    doi='10.1109/TCSII.2023.3234620', process_class='直接的 28 nm 设计依据；已得前作是仿真，不宣称两版均实测',request_rank=6)
add('SACIM-04','01_sram_acim',2023,'C2C_ChargeDomain','CIM 求值桥接；完整多位求值；独立结构交叉核查','阵列／局部 macro','P2',
    'Intel C-2C ladder 的完整 8-bit 电荷域 MAC 补独立团队证据，核查位并行输入、求值粒度与输出精度。22 nm 节拍不直接作为 28 nm 基线。',
    doi='10.1109/JSSC.2022.3232601',process_class='其他工艺的量级交叉参考（22 nm FinFET）',
    access_urls=['https://rdorrance.com/publications/','https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10008405'])

add('SDCIM-01','02_sram_dcim',2023,'D6CIM','28 nm 外围服务；数字累加／位串行；普通写入粒度','阵列／局部 macro','P1',
    '区分数字时钟与完整精度 VMM；普通写口宽度可提供后续参考写入情景的粒度依据。写周期仍需共同 SRAM 条件或扩展版确认。',old='t1_d6cim2023',
    process_class='直接的 28 nm 证据',confirmed_content='原会议全文已核验宏结构、位串行调度、普通写端口与测量章节。2026 期刊扩展版只作版本线索，不重复计数或立即请求。')
add('SDCIM-02','02_sram_dcim',2023,'BitReconfigurable_CIM','数字求值与控制；操作粒度；独立量级交叉核查','阵列／局部 macro','P2',
    '可编程加法及位串行乘法提供独立实现，检查不同运算的完整服务粒度；65 nm 实测只支持结构和量级交叉核查。',
    doi='10.1109/TCSII.2023.3257058',process_class='其他工艺的量级交叉参考（65 nm）',
    access_urls=['https://repository.sutd.edu.sg/esploro/outputs/journalArticle/A-Digital-Bit-Reconfigurable-Versatile-Compute-In-Memory-Macro/9912748209846'])
add('SDCIM-03','02_sram_dcim',2022,'DynamicLogic_INT8','28 nm 外围服务；数字求值与控制；完整精度输出','阵列／局部 macro','P1',
    '动态逻辑 ADC-less 28 nm macro 与 D6CIM 互补，核查预充／求值步骤、精度及数字控制节拍；不能把介绍段的通用 SRAM 速度当作本 macro 完整求值。',
    doi='10.1109/ISSCC42614.2022.9731545',process_class='直接的 28 nm 证据',
    access_urls=['https://scholars.duke.edu/publication/1519651','https://www.icacworkshop.cn/2022/slides/ICAC_2022_14.3_Yan_Bonan.pdf'],request_rank=7)

add('NOR-01','03_nor_2d',2024,'GL_S_MIRRORBIT_Military','读侧时间尺度；编程／擦除周期；字／buffer／sector 粒度','整芯片存储规格，含局部操作定义','P2',
    'Infineon GL-S 并行 NOR 提供 random/page read、write-buffer、sector erase 和完成状态定义，补串行 NOR 之外的独立厂家依据。MirrorBit 的物理存储与模拟权重精度不混同。',
    title='S29GL01GS, S29GL512S, S29GL256S, S29GL128S — 128 Mb / 256 Mb / 512 Mb / 1 Gb GL-S MIRRORBIT Flash, Parallel, 3.0 V, Military',
    authors=['Infineon Technologies'],venue='厂商 datasheet，002-18741 Rev. *E',publication_date='2024-09-04',
    official_url='https://www.infineon.com/part/S29GL512S11DHB013',
    access_urls=['https://www.infineon.com/dgdl/Infineon-S29GL01GS_S29GL512S_S29GL256S_S29GL128S_128_Mb_256_Mb_512_Mb_1_Gb_GL-S_MIRRORBIT_Flash_Parallel_3-DataSheet-v06_00-EN.pdf?fileId=8ac78c8c7d0d8da4017d0ee99af9726b'],
    document_id='002-18741 Rev. *E，2024-09-04；官方 URL v06_00-EN',state_mode='数字 NOR／MirrorBit，军规产品条件；非模拟精度声明',
    identity_note='官方 106 页 PDF 网页正文页 1 核验题名、文号、日期；直接下载为空。该链接实为军规版，不能当普通商规版本；保留其操作定义，温度／寿命／时序必须随产品条件。',request_rank=8)
add('NOR-02','03_nor_2d',2019,'W25Q128JV_RevG','编程／擦除周期；操作粒度；接口与内部 busy 区分','整芯片存储规格','P1',
    'Winbond 普通 NOR 的 page program、sector/block/chip erase 与 busy 状态可支撑完整更新步骤；串行读频率仅为接口定义。',
    title='W25Q128JV — 3V 128M-BIT Serial Flash Memory with Dual/Quad SPI',authors=['Winbond Electronics'],venue='厂商 datasheet，Revision G',publication_date='2019-04-08',
    official_url='https://www.winbond.com/hq/support/documentation/?__locale=en&pno=W25Q128JV',
    access_urls=['https://www.winbond.com/resource-files/w25q128jv%20revg%2004082019%20plus.pdf'],document_id='W25Q128JV Rev. G，2019-04-08',
    older_reason='具体修订的完整 datasheet，操作定义清楚；门户另列 2025 更新，R0 不把二者混为同一版本。',state_mode='普通数字 NOR（未作多级模拟精度假设）',
    confirmed_content='公开 PDF 封面修订／日期与身份一致；目录、program／erase 指令和 AC timing 表已定位。')
add('NOR-03','03_nor_2d',2022,'SST26VF064B_RevK','编程／擦除周期；操作粒度；独立量级交叉核查','整芯片存储规格','P1',
    'Microchip SuperFlash 家族补不同 NOR 工艺／擦除方式的独立产品基线，核对 page program、擦除及 ready 条件，不从串行接口估 cell 速度。',
    title='SST26VF064B/SST26VF064BA — 2.5V/3.0V 64-Mbit Serial Quad I/O (SQI) Flash Memory',authors=['Microchip Technology'],venue='厂商 datasheet，DS20005119K',
    official_url='https://www.microchip.com/en-us/product/SST26VF064B',
    access_urls=['https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/SST26VF064B-SST26VF064BA-2-5V-3-0V-64-Mbit-Serial-Quad-IO--SQI--Flash-Memory-20005119K.pdf'],
    document_id='DS20005119K，March 2022',publication_date='2022-03',state_mode='普通数字 SuperFlash NOR',confirmed_content='已核验正式 PDF；第 67 页 revision history 确认 K 版为 March 2022，目录包含写入／擦除过程和 AC 规格。')
add('NOR-04','03_nor_2d',2017,'EmbeddedNOR_Classifier','CIM 求值桥接；输入驱动与输出边界；阵列结构','阵列与两层网络实验','P2',
    '实际嵌入式 NOR 模拟分类器连接浮栅阵列、门电压输入和模拟输出；提供估算结构，不能把整个分类任务延迟视作一个局部 MVM。',old='t1_nor2017',
    older_reason='直接基于 embedded NOR 的原始 CIM 实验，可连接厂商普通存储能力与模拟读出。',
    state_mode='模拟调谐浮栅权重',family='ucsb_esf1',confirmed_content='原论文题名、ESF1 阵列和输入／输出结构已初筛；普通数字 NOR 与其模拟调谐不是同一写入终点。')
add('NOR-05','03_nor_2d',2016,'NOR_ModelBased_Tuning','写入／编程周期；擦除与更新方式；精度与 verify','器件／小阵列','P1',
    '反馈调谐论文补完整模拟状态建立方法与擦除作用，保留目标误差、脉冲和反馈过程的区分。与 NOR-04 同 ESF1 技术路线，不当作独立团队验证。',old='t1_nor_tuning2016',
    older_reason='原始模拟 NOR 精细调谐方法，直接补普通 datasheet 无法描述的权重更新过程。',state_mode='模拟多级调谐',family='ucsb_esf1',
    confirmed_content='已有作者全文显示小阵列调谐、编程与擦除脉冲及反馈算法；不在 R0 组合成总写入时间。')

add('NAND-01','04_nand_3d',2016,'Micron_3DNAND','读侧时间尺度；编程／擦除周期；页／块／plane 粒度','厂商器件／die 规格简表','P1',
    '官方表分别列 2b/c MLC 和 3b/c TLC 的 tR、tPROG、tBERS、页块与 plane 组织，可为完整普通存储操作提供粗粒度依据。是技术简表，详细约束仍需后续 datasheet 核查。',
    title='Micron 3D NAND Flash Memory Technology',authors=['Micron Technology'],venue='厂商技术产品简表，02/16',publication_date='2016-02',document_id='3d-nand-flyer.pdf，02/16',
    official_url='https://www.micron.com/products/storage/nand-flash/3d-nand/part-catalog',
    access_urls=['https://assets.micron.com/adobe/assets/urn%3Aaaid%3Aaem%3A3e6db2c4-d096-425e-91f4-1355e5262cc3/renditions/original/as/3d-nand-flyer.pdf'],
    older_reason='厂商直接列出页／块／plane 和完整操作时间定义；成熟 NAND 基础来源，不是 2026 新产品参数。',state_mode='MLC 2b/c；TLC 3b/c（分列）',
    identity_note='官方 PDF 网页索引可读产品表，页脚 ©2016／02/16 已确认；本地 curl 返回 Request Rejected HTML。',request_rank=1)
add('NAND-02','04_nand_3d',2026,'KIOXIA_6Plane_QLC','编程周期；plane 并行条件；独立产品交叉核查','阵列／die 与整芯片','P1',
    'KIOXIA 第十代 QLC 原始芯片资料补 plane 并行与写入组织；题名 write throughput 仍需全文区分内部编程与 die 级数据路径。',
    doi='10.1109/ISSCC49663.2026.11409136',state_mode='QLC 4b/c；6-plane',
    access_urls=['https://www.kioxia.com/ja-jp/rd/technology/topics/topics-92.html'],request_rank=10)
add('NAND-03','04_nand_3d',2025,'SKhynix_321Layer_QLC','编程周期；操作粒度与局部并行度；独立量级交叉核查','阵列／die 与整芯片','P1',
    'SK hynix 321 层 QLC 实际芯片补独立厂商依据，核对编程步骤、页／plane 组织及吞吐定义。其题名数值不能被旧稿误记为 KIOXIA 或 TLC。',
    doi='10.1109/ISSCC49661.2025.10904748',state_mode='QLC 4b/c（不是 TLC）',request_rank=11)
add('NAND-04','04_nand_3d',2021,'NAND_Codesign','CIM 求值桥接；字线／位线与重构；局部阵列边界','阵列／外围与系统仿真','P1',
    '解释 NAND 物理组织如何映射 CIM、外围共享与必要求值阶段；补商品页读与电流求和之间的估算桥梁。原始参数表图像必须补齐。',old='t1_nand2021',
    state_mode='CIM 选定阈值态／权重编码，不能自动等同商品 TLC 页模式',request_rank=9,
    identity_note='复用前轮原文网页线索；前轮 Table 1 原图未取得，本轮没有将它升级为已核实全文。')
add('NAND-05','04_nand_3d',2019,'3DNAND_nvCIM','CIM 求值桥接；局部并行组织；NAND 结构依据','阵列／局部 macro','P2',
    '产业团队原始 nvCIM 研究补 block／string 组织与输入读出映射，连接 NAND-04 所引用硬件；是否包含编程条件尚需全文。',old='t1_lue2019',
    older_reason='直接 NAND CIM 原始硬件／结构桥接，是后续 codesign 的关键来源。',state_mode='nvCIM 阈值／操作模式待全文确认')

add('RRAM-01','05_rram',2022,'NeuRRAM','CIM 求值桥接；闭环编程；状态精度与验证','阵列／局部 macro 及整芯片','P1',
    '器件目标电导、差分映射、program/verify 与读出结构为多级 RRAM 参考设计提供互补依据；外控测量与集成外围估计须分开。',old='t1_neurram2022',state_mode='模拟多级、差分权重',
    confirmed_content='本地正式正文含 Methods 与 Extended Data；已初筛编程、核结构和求值章节。')
add('RRAM-02','05_rram',2025,'HybridProgramming','28 nm 读出；写入／编程方式；操作粒度','阵列／局部 macro','P1',
    '实际 28 nm macro 的混合编程、差分校验和 ADC 共享可连接器件与统一外围；相对编程改进不等于已公开绝对写入时长。',old='t1_liu2025',state_mode='多级／2T2R 差分',
    process_class='直接的 28 nm 证据（专用 RRAM 外围）',confirmed_content='已核验正式 PDF 与编程／共享结构；是否足够确定绝对服务间隔留待 R1。')
add('RRAM-03','05_rram',2022,'Weebit_28nm','器件编程条件；binary 存储；独立产业交叉核查','器件／测试阵列','P2',
    'Weebit／CEA-Leti 28 nm ReRAM 实测提供与 CIM 团队不同的操作／可靠性条件；初筛确认不只有宣传页，后续检查时序与写入终点是否充分。',
    doi='10.1109/IMW52921.2022.9779293',state_mode='数字存储；多级适用性未主张',
    access_urls=['https://www.weebit-nano.com/wp-content/uploads/2022/06/IMW2022_Weebit_High-temperature-stability-embedded-ReRAM-or-RRAM-for-2x-nm-node-and-beyond.pdf'],
    version='Weebit 厂商托管作者接受稿，前附 IEEE 作者转载声明',
    confirmed_content='厂商公开作者稿含论文正文、工艺和阵列测量；封面为转载说明，实际题名在后续页。')
add('RRAM-04','05_rram',2016,'MB85AS4MT','普通写入完成；操作粒度；存储时序定义','整芯片存储规格','P2',
    '少见公开商用 ReRAM datasheet，提供 write-buffer 与内部写入／busy 语义；只能交叉核查普通存储完整事务，不能拿 SPI 频率替代 RRAM cell 读出。',
    title='MB85AS4MT — Memory ReRAM 4M (512 K × 8) Bit SPI',authors=['Fujitsu Semiconductor'],venue='厂商 datasheet，DS501-00045-1v0-E',publication_date='2016-12',document_id='DS501-00045-1v0-E，2016.12',
    official_url='https://www.fujitsu.com/global/documents/products/devices/semiconductor/memory/reram/MB85AS4MT-DS501-00045-1v0-E.pdf',
    access_urls=['https://download.mikroe.com/documents/datasheets/MB85AS4MT.pdf'],
    older_reason='公开商用 ReRAM 原始 datasheet 稀少，保留完整普通存储时序定义。',state_mode='普通数字存储',
    confirmed_content='Fujitsu 原厂数据表从开发板厂商合法文档镜像取得，封面确认 2016.12 和文件编号；不声称该器件为 28 nm。')
add('RRAM-05','05_rram',2023,'WeightedHybrid_2T1R','28 nm 专用感测；CIM 求值桥接；局部并行组织','阵列／局部 macro','P1',
    'foundry RRAM 的解耦存储／计算路径及 reference-subtracting sense amplifier 补另一类 28 nm 阵列读出结构，防止只依赖 NeuRRAM 单实现。',
    doi='10.1109/JSSC.2023.3280357',state_mode='WH-2T1R／权重映射待全文核查',process_class='直接的 28 nm 证据（专用 RRAM 外围）',request_rank=12)

add('MRAM-01','06_mram',2022,'ResistanceSum_Crossbar','读写服务；CIM 求值桥接；互补单元与局部并行度','阵列／局部 macro','P1',
    '实际电阻求和 MRAM 阵列与 TDC 读出给出读写及互补编码线索；仅支持其实际器件／求值机制，不自动代表所有 MRAM。',old='t1_jung2022',state_mode='二值互补 MTJ；电阻求和／TDC',
    confirmed_content='已有正式正文含 Methods 与 Extended Data，阵列、更新、时钟边界已初筛。')
add('MRAM-02','06_mram',2023,'Spintronic_CIM','CIM 求值桥接；局部并行度；独立 macro 交叉核查','阵列／局部 macro','P1',
    'CMOS 集成 spintronic macro 补真实局部服务机制、精度和写入路径；与 Jung 的电阻求和实现分开核查。',old='t1_chiu2023',state_mode='STT-MRAM；具体求值／写入步骤待全文',request_rank=13)
add('MRAM-03','06_mram',2019,'SelfWriteTermination','写入完成与终止；感测服务；28 nm 专用外围','阵列／局部 macro','P1',
    '1T1MTJ 存储 macro 的 self-write-termination 和 offset-cancelled sense amplifier 补完整写入终点及局部读出，避免将外部脉冲等同普通写周期。',
    doi='10.1109/JSSC.2018.2872584',state_mode='binary 1T1MTJ STT-MRAM',process_class='直接的 28 nm 证据（专用 MRAM 外围）',
    older_reason='实测 28 nm STT-MRAM 自终止写入／感测电路，直接支撑局部服务与更新完成定义。',request_rank=19)
add('MRAM-04','06_mram',2018,'2T2MTJ_ReadMacro','读侧时间尺度；感测与操作粒度；结构交叉核查','阵列／局部 macro','P2',
    '互补 2T2MTJ 局部读出补与 1T1MTJ 不同的面积／可靠性／感测组织；题名 read-access 指标仅是读入口，不能当完整多位 MVM。',
    doi='10.1109/ISSCC.2018.8310394',state_mode='binary 2T2MTJ STT-MRAM',process_class='直接的 28 nm 证据（专用 MRAM 外围）',
    older_reason='直接 28 nm 互补 MRAM 阵列原始电路，有助区别不同读机制。')
add('MRAM-05','06_mram',2025,'EMxxLX_v3p4','直接更新语义；字节粒度；普通存储交叉核查','整芯片／封装接口','P2',
    '商业 STT-MRAM 的字节读写、无需物理擦除及 NOR 兼容模拟命令用于更新方式核查。xSPI 速率仅是产品端口服务；工艺未由此 datasheet 证明为 28 nm。',
    title='EMxxLX — Expanded Serial Peripheral Interface (xSPI) Industrial STT-MRAM Persistent Memory',authors=['Everspin Technologies'],venue='官方 datasheet，v3.4',document_id='EMxxLX v3.4，©2025',
    official_url='https://www.everspin.com/design-support',access_urls=['https://www.everspin.com/file/158451/download'],
    state_mode='binary STT-MRAM；NOR erase 指令可模拟',process_class='功能与时序定义参考（该文件不证明 28 nm）',
    identity_note='网页工具可读 81 页官方 v3.4 PDF；直接下载返回 404，候补人工获取。')

add('PCM-01','07_pcm',2023,'PCM64_Core','CIM 求值桥接；并行 writehead；多级编程与校验','阵列／局部 macro 及整芯片','P1',
    '完整多相位求值、writehead 组织和闭环编程为 PCM 局部参考情景提供结构；预印本的测量／RTL 时序需保留证据类型。',old='t1_pcm64',state_mode='模拟多级 PCM、差分映射',family='ibm_pcm_platform',
    confirmed_content='现有 arXiv 全文含宏结构和编程说明；未将预印本数值声明为已与期刊逐项相同，不重复要求内容相近正式版。')
add('PCM-02','07_pcm',2023,'AnalogAI_Speech','CIM 求值桥接；行并行编程；局部与系统边界','阵列／tile、芯片与系统','P1',
    '不同 IBM 芯片的模拟 tile、并行编程及脉宽输入用于交叉核查服务组织；只使用可识别局部边界，不以语音系统总体性能替代本地操作。',
    doi='10.1038/s41586-023-06337-5',state_mode='模拟多级、2/4 PCM-per-weight',family='ibm_pcm_platform',
    access_urls=['https://www.nature.com/articles/s41586-023-06337-5.pdf','https://research.ibm.com/publications/an-analog-ai-chip-for-energy-efficient-speech-recognition-and-transcription'],
    confirmed_content='已取得正式正文含 Methods／Extended Data；初筛确认 tile 架构、输入和编程组织，未做吞吐换算。')
add('PCM-03','07_pcm',2022,'Hybrid_SLC_MLC','CIM 求值桥接；binary／multi-level；操作粒度','阵列／局部 macro','P1',
    'TSMC／NTHU PCM macro 补独立产业团队与 SLC/MLC 模式差异，核查写入、读出精度和求值服务，避免仅依 IBM 平台确定范围。',
    crossref_query_index=0,state_mode='hybrid SLC／MLC（分模式）',request_rank=14)
add('PCM-04','07_pcm',2017,'Subnanosecond_Nucleation','器件写入时间尺度；材料差异；独立量级交叉核查','器件／材料','P2',
    'Sc-Sb-Te 原始研究用于解释材料／成核条件导致的极快写入报道。保留它作为条件性器件基线，不将单次晶化脉冲替代 GST 多级阵列完整写入。',
    doi='10.1126/science.aao3212',state_mode='Sc-Sb-Te 晶化／相变条件；非默认多级 PCM 写入',
    older_reason='关键器件写入基线，能解释跨材料时间尺度差异，不能用于拼接最佳芯片参数。')
add('PCM-05','07_pcm',2024,'PCM_Drift','SET／RESET 与多级编程；测试条件；独立量级交叉核查','器件测量与电路／网络仿真','P2',
    'ST 合作的 Ge-rich GST 器件测量提供多级编程脉冲、终态与漂移测试条件，用来补高速 headline 之外的实际操作约束。外围／网络仿真与器件测量分开。',
    doi='10.3390/jlpea14040050',state_mode='Ge-rich GST 多级 PCM；SET／RESET 分开',
    access_urls=['https://mdpi-res.com/d_attachment/jlpea/jlpea-14-00050/article_deploy/jlpea-14-00050.pdf'],
    confirmed_content='已核验正式全文与 PCM Characterization 小节：确有器件编程和测试方法，不是仅综述漂移。')

add('FERAM-01','08_feram_hfo2',2023,'C2FeRAM','CIM 求值桥接；读／恢复机制；写入步骤','HfO₂ 系 FeCAP 器件实验与电路仿真','P1',
    '2T2C C2FeRAM 将 HZO 电容与非破坏性求值连接，可解释普通 1T1C 破坏性存储读和计算读的差别；不能将分立实验写成完整实测 CIM。',old='t1_c2feram2023',state_mode='HfO₂ 系 FeCAP；2T2C',
    confirmed_content='作者接受稿题名、FeCAP 实验和电路方案已初筛；页面 running header 模板字样保留为版本说明。')
add('FERAM-02','08_feram_hfo2',2021,'UltrathinHZO_1T1C','读写时间尺度；1T1C 阵列操作；低压条件','器件／存储阵列','P1',
    'SK hynix 的超薄 HZO 1T1C FE-RAM 补实际低压读写与状态判读条件；需全文核对读取是否含恢复、操作粒度和偏置。',
    doi='10.1109/IEDM19574.2021.9720545',state_mode='5 nm HZO；1T1C FeRAM',request_rank=15)
add('FERAM-03','08_feram_hfo2',2020,'SoC_1T1C_HZO','阵列读写；局部操作粒度；独立交叉核查','器件／1T1C 阵列及外围','P1',
    'Sony／NaMLab／Fraunhofer 阵列集成研究补局部操作电路与 program/read 实验，避免只由电容切换脉冲估计 FeRAM 服务。',
    doi='10.1109/VLSITechnology18217.2020.9265063',state_mode='Hf0.5Zr0.5O2；1T1C',
    access_urls=['https://publica.fraunhofer.de/entities/publication/03fdad8b-f3a2-4201-9987-faacc3b81673'],
    older_reason='HZO 1T1C SoC-compatible 原始阵列集成基线，直接补电容到阵列操作的桥梁。',request_rank=16)
add('FERAM-04','08_feram_hfo2',2023,'NVDRAM_32Gb','完整读写服务；操作粒度；大阵列交叉核查','阵列／die 与整芯片','P1',
    'Micron 的 HfO₂ 系非易失铁电存储补器件到三维阵列的实际读写与外围实现；需从整芯片中辨识可用于局部参考的边界，不能把标题 near-DRAM 当数值时序。',
    doi='10.1109/IEDM45741.2023.10413848',state_mode='HZO 1T1C 铁电存储；不归为普通 DRAM',request_rank=17)
add('FERAM-05','08_feram_hfo2',2024,'Codoped_Hafnia','器件切换时间尺度；测试偏置与终点；独立交叉核查','器件／铁电电容','P2',
    'La/Ta 共掺杂 HfO₂ 电容给出切换动力学及测量条件，补产业阵列之外的材料维度；不以 PUND／脉冲宽度直接代替存储读写周期。',
    doi='10.1038/s41467-024-47194-8',state_mode='共掺杂 HfO₂ 铁电电容',
    access_urls=['https://www.nature.com/articles/s41467-024-47194-8.pdf'],
    confirmed_content='正式全文已核验题名、铁电薄膜和 switching 测试；已定位并获取 Supplementary Information。')
add('FERAM-06','08_feram_hfo2',2025,'Ferroelectric_Memristor','FeCAP 阵列写入；并行粒度；训练／推理桥接','FeCAP／memristor 阵列与计算实验','P2',
    '同片 Si-doped HfO₂ 的 FeCAP 和 memristor 阵列补近期阵列级证据；本组只用 FeCAP 支路支持 FeRAM，不能混入 memristor 的读写指标。',
    doi='10.1038/s41928-025-01454-7',state_mode='Si:HfO₂ FeCAP 为本组主体；memristor 支路另区分',
    access_urls=['https://www.nature.com/articles/s41928-025-01454-7.pdf'],
    confirmed_content='已核验公开正式 PDF；初筛确认两类阵列分开测试，附补充资料。')

add('GC-01','09_gain_cell_edram',2022,'GainCell_CIM','完整求值；读写端口；保持与泄漏','2T1C gain-cell 局部 macro','P1',
    '明确 gain-cell 结构和输入位相位／ADC 读出，提供局部计算组织；写入路径与 refresh 条件需在后续与存储来源组合。',old='t1_gaincell2022',state_mode='65 nm CMOS 2T1C gain-cell；数字权重',
    confirmed_content='原始 VLSI 全文已核验 2T1C 结构、独立读写端口、数据流和测量图；与 2021 年普通 1T1C eDRAM 区分。')
add('GC-02','09_gain_cell_edram',2018,'MixedVT_4T_GainCell','28 nm 读写服务；保持／刷新；普通 gain-cell 粒度','实测 gain-cell 局部 macro','P1',
    '28 nm bulk 4T gain-cell 存储原始实测补读写端口、retention 与刷新边界；approximate storage 的错误容忍条件不能忽略。',
    crossref_query_index=0,state_mode='28 nm bulk mixed-VT 4T gain-cell',process_class='直接的 28 nm 证据（gain-cell 存储）',
    access_urls=['https://www.eng.biu.ac.il/temanad/publications/','https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8356248'],
    older_reason='直接实测 28 nm gain-cell 读写／保持基线，而非以普通 DRAM 参数替代。',request_rank=18)
add('GC-03','09_gain_cell_edram',2024,'OxideGainCell','读写设计方法；保持与刷新；28 nm 映射桥接','器件依据与局部 macro 仿真／建模','P2',
    'oxide／hybrid gain-cell 设计指南连接器件、互连和 macro 服务，提供可复算建模方法；28 nm macro 结果属于模型／仿真，不是统一实测芯片。',
    title='Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform',authors=['Shuhan Liu','Koustav Jana','Kasidit Toprasertpong','Jian Chen','Zheng Liang','Qi Jiang','Sumaiya Wahid','Shengjun Qin','Wei-Chen Chen','Eric Pop','H.-S. Philip Wong'],venue='IEEE Transactions on Electron Devices 71(5), 3329–3335',doi='10.1109/TED.2024.3372938',publication_date='2024-05',
    access_urls=['https://poplab.stanford.edu/pdfs/Liu-DesignOSFETgainCell-ted24.pdf'],official_url='https://poplab.stanford.edu/pdfs/Liu-DesignOSFETgainCell-ted24.pdf',
    process_class='直接的 28 nm 模型条件／其他工艺器件依据（须逐项区分）',state_mode='OS–OS／hybrid gain-cell，保留不同通道结构',
    confirmed_content='已核验作者正式 PDF、模型与器件来源；具体参数尚未采集。')
add('GC-04','09_gain_cell_edram',2024,'DynamicCascoded_MLC','写入建立；多级状态；CIM 求值与保持','3T1C gain-cell 型局部 macro','P1',
    '电流编程动态 cascode 3T1C 多级 eDRAM 补不同于二值 2T1C 的写入／保持和求值步骤；保留其模拟状态接受条件。',
    crossref_query_index=1,state_mode='3T1C current-programmed dynamic-cascode MLC',request_rank=20)
add('GC-05','09_gain_cell_edram',2025,'DualMode_GainCell','完整精度求值；局部并行度；近期产业交叉核查','gain-cell 局部 macro','P2',
    '16 nm 产业 gain-cell macro 的 integer／floating-point 两模式补现代控制及精度组织。对 28 nm 仅为结构与量级交叉参考，不直接移用速率。',
    crossref_query_index=1,state_mode='16 nm gain-cell；INT／FP 分模式',process_class='其他工艺的量级交叉参考（16 nm）')

add('FENOR-01','10_fenor_3d',2025,'3DNOR_FeFET','器件读写时间尺度；更新步骤；局部阵列结构','器件／三层小阵列与 CIM 仿真','P1',
    '指定原稿支撑 IGO／HZO 三层 NOR-type 器件脉冲、写后读及阵列结构；不能把脉冲宽度和层数直接变为完整 CIM 服务。',old='t1_zhou2025',
    family='zhou_igo_vertical',state_mode='IGO／HZO；NOR-type；器件偏置分条件',
    confirmed_content='根目录原始 3 页题名、作者与正文结构已核验；页 1 与器件／阵列图快速初筛，未提取新范围。')
add('FENOR-02','10_fenor_3d',2026,'Vertical_FeFET_Array','器件读写；写扰与并行选择条件；局部阵列验证','器件／四层阵列与 TCAD／SPICE','P1',
    '指定原稿补半选／相邻单元扰动、写入方案、Kb 图案验证和读出建模。正文明确 AND-type vertical array；单 cell、图案验证与外围仿真分别保留。',old='t1_zhou2026',
    family='zhou_igo_vertical',state_mode='IGO／HZO；AND-type vertical FeFET；SL/SS 与 O-rich/O-poor 分条件',
    confirmed_content='根目录原稿 3 页已核验；2026-06-14 出版登记和作者／题名匹配。DOI 元数据把 > 误编码为 ¾，规范题名按 PDF 的 >10^12 保留。')
add('FENOR-03','10_fenor_3d',2024,'BEOL_Vertical_FeNOR','阵列结构；写扰与更新方式；独立团队交叉核查','器件／BEOL 三维阵列','P3',
    'Feng 团队的 ZnO/MFMIS side-fin 3D FeNOR 补独立结构与写入／扰动线索。优先先取 FENOR-04 期刊文，避免一开始重复下载；两项的实验复用关系待全文确认。',
    doi='10.1109/VLSITechnologyandCir46783.2024.10631352',family='feng_beol_fenor_2024_2025',state_mode='ZnO／MFMIS BEOL vertical FeNOR',
    access_urls=['https://scholar.nycu.edu.tw/en/publications/first-demonstration-of-beol-compatible-3d-vertical-fenor/'],
    duplicate_package='FENOR-04')
add('FENOR-04','10_fenor_3d',2025,'FeNOR_CIM_Design','CIM 求值桥接；局部读出／并行条件；独立团队交叉核查','器件／阵列及计算建模','P1',
    '直接 3D FeNOR-CIM 原始研究补读出／权重映射和器件到参考设计的桥接，优先获取较完整的期刊版本。与 FENOR-03 高度相关，保守计一个资料包，不称两份独立交叉证据。',
    doi='10.1109/TED.2025.3554164',family='feng_beol_fenor_2024_2025',state_mode='MFMIS 3D FeNOR；计算映射待全文',request_rank=21)
add('FENOR-05','10_fenor_3d',2023,'Integrated3D_FeFET','器件编程；三维阵列读出；独立结构交叉核查','器件／三维 FeFET 阵列与计算实验','P2',
    'POSTECH 的真实三维 FeNAND／FeFET 阵列用于条件性的器件编程、垂直集成及 VMM 结构交叉核查。其串联 NAND 读路径不是 Zhou 的 NOR／AND，不能作为直接 FeNOR 读出速度或并行度证据。',
    doi='10.1038/s41467-023-36270-0',state_mode='HfZrOx 三维 FeNAND；串联选择、multiple layers／VMM 实验',
    access_urls=['https://www.nature.com/articles/s41467-023-36270-0.pdf'],
    confirmed_content='已核验正文摘要明确 3D FeNAND，以及补充材料；仅保留直接相关的垂直 FeFET 编程和集成信息，不视为直接 FeNOR 独立验证。')
add('FENOR-06','10_fenor_3d',2026,'GateStack_FeNOR','器件读写与偏置；栅堆栈差异；更新约束','器件／三维 FeNOR','P2',
    '直接比较 3D oxide-channel FeNOR 的 MFS/MFIS/MIFS/MIFIS 栅堆栈，有助解释脉冲与状态窗口的差异。来自 Zhou 相关团队，只作为机制补充，不增加独立团队数量。',
    doi='10.1109/EDTM65772.2026.11498024',family='zhou_igo_vertical',state_mode='3D oxide-channel FeNOR；不同栅堆栈分条件')

# Primary request list is deliberately capped; available main text is never re-requested.
# Includes all medium-specific critical gaps, then common baseline gaps and complements.
FIRST_BATCH_ORDER = ['CMOS-03','CMOS-04','CMOS-05','SACIM-04','MRAM-03',
    'NAND-01','NAND-02','NAND-03','NAND-04','RRAM-05','MRAM-02','PCM-03',
    'FERAM-02','FERAM-03','FERAM-04','GC-02','GC-04','FENOR-04']
