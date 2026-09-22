# 2D NOR：参数证据、原生映射与工程桥接

本笔记为当前中文章节的详细证据记录。所有页码为本地 PDF 页序（从 1 起），不是 Winbond 页脚页码；不使用网络新资料。原值以 PDF 正文/表格为准。`data/inputs.json` 区分 `reported_evidence` 与 mapping/scenario 工程选择；`data/provenance.json` 保存共享 JSON/API 和源 PDF 哈希。全部数字的实际计算入口为 `scripts/check_nor.py`，导入共享 API，不另造吞吐公式。

## 1. 所选服务及证据关系

主模式：**binary NOR + 本地精确数字归约**。INT8 权重是八个逻辑二进制状态，逻辑存储位总数 131072；输出格式为 128×24-bit signed。NOR-01 的 MirrorBit 一个物理器件可能具有两个独立 bit 存储位置，本章未从其器件数估面积；“八个 bit”不是“一 cell 256 个精细电流水平”。本文不依赖 binary cell 读电流一致，不把 program 至数字读窗当成模拟电流精调。

文献互补：NOR-01 提供完整数字随机读量级，NOR-02 提供原生页/sector 和完整 binary 内部更新，NOR-04/05 解释浮栅模拟 VMM 与调谐服务的区别。四份来源不构成一个实测 NOR DCIM 芯片。NOR-04/05 同团队/技术线，不能重复计独立验证。共享基线提供 28nm CMOS 数字资源与节拍，不把 NOR-01/02/04/05 的原工艺、介质偏置或高压操作冒充共同0.9V外围。

## 2. NOR-01：完整读周期和写入交叉检查

文件 `literature/03_nor_2d/NOR-01_2024_GL_S_MIRRORBIT_Military.pdf`，Infineon，002-18741 Rev.*E，2024-09-04，106页。源 SHA-256 见 provenance。

### 随机读：实际采用的时间锚点

- **PDF p85，Table57**：512Mb，speed option100，VIO=VCC=2.7–3.6V，−55至+105°C。`tRC` Read Cycle Time最小100ns；`tACC` Address to Output Delay最大100ns；tCE最大100ns；tPACC页访问最大20ns。
- **PDF p85，Table58（p86续表）**：128/256/512Mb和1Gb，speed option120，VIO=VCC=2.7–3.6V，−55至+125°C。tRC最小120ns，tACC/tCE最大120ns，tPACC最大20ns。
- **PDF p86，Table59**：speed option130，VIO=1.65V至VCC，VCC=2.7–3.6V，−55至+125°C。tRC最小130ns，tACC/tCE最大130ns，tPACC最大25ns。
- **PDF pp74–75 §9.4，p87 Figs17–19**：随机访问在地址/使能成立后输出有效；page read是已完成随机访问且高位地址保持时的低位地址选择。外部DQ15–DQ0不直接规定内部全部感测宽度。
- 摘要p2对页访问给出15ns；采用详细AC表20/25ns作为事实记录，主预算完全不使用page mode加速。

**工程桥接**：主三情景 `t_rd=100/120/130ns`，将以上完整随机二进制访问尺度转移到明确配置的128-SA本地读分片。每轮32片并行，4096SA和独立局部读偏置/选择/输出隔离资源都明确配置。完整读预算含选通、介质读电压建立、sense与有效结果，不再加ADC、T_I或另一份cell read时间。它不是把外部16-bit tACC免费扩成任意位宽；时延在该宽度/负载下可实现是明确设计条件，尚需电路验证。外部SPI/封装传输不参与ρ计算。

原文是65nm GL-S军规器件；100/120/130并非同芯片PVT测得的统计分位，也不是28nm cell读延迟。使用其量级而不按工艺尺寸缩放；三个条件与共同short/reference/long外围组合只是参考情景。相同binary状态下的跨来源读写互补是有条件估算，不标成原实物参数配对。

### 写入：仅交叉检查，不替换NOR-02主预算

- **PDF p22，§5.1/5.2**：EAC内部控制所需复杂program/erase序列；数字1可program成0，0恢复1需erase，擦除是sector粒度。
- **PDF pp24、26–32**：32Byte/ECC page、512Byte写buffer/Line与128KB sector不同层级；buffer填满后启动内部algorithm。
- **PDF p45，Table16，注29–34**：128KB sector erase典型410ms、最大1100ms，含擦除前预编程；单word program150/400µs；512Byte buffer program420/1050µs；256Byte buffer320/1050µs。有效满buffer每word1.64µs仅为420µs/256words摊销，不是任意word的完成时延。
- 典型条件（注30）：25°C、VCC=3.0V、10000cycles、随机数据。最大条件（注31）：105°C、VCC=2.70V、100000cycles、随机数据。注33明确擦前所有word预编为0000h。
- p2摘要1.5MBps buffer、477KBps sector erase，不优先于详细表；本章不反推它们替代原始tPROG/tERASE。

若改用NOR-01 native128KiB sector，必须重新算有效容量和实际擦除次数；不能把其完整erase值按NOR-02的4KiB粒度除掉，也不能把1.64µs/word乘任意小word数当完整更新。

## 3. NOR-02：主更新过程及BUSY终点

文件 `NOR-02_2019_W25Q128JV_RevG.pdf`，Winbond W25Q128JV Rev.G，2019-04-08，78页。

- **PDF p5，§1/2**：65536×256Byte programmable pages；16页=4KB sector，128页=32KB block，256页=64KB block；最多256Byte一次编程。电源2.7–3.6V。声称每sector至少100K program/erase cycles、超过20年保持；仅作为寿命约束记录。
- **PDF p14，§7.1.1/2**：执行page program/erase时BUSY=1；完成后BUSY=0，设备接受后续指令。WEL需相应命令建立，操作后自动清除。主边界是本地控制器正常就绪、未保护、已上电条件；本地控制拍包括发起和完成处理，不依赖外部SPI逐位轮询。
- **PDF p37，§8.2.13/Fig29a**：写1–256Byte到预擦为FFh的地址，256Byte整页需低地址0对齐，超页数据会绕回，不能跨page写入。命令、24-bit地址和数据输入结束、CS升高才开始self-timed tPP；BUSY降为0才结束。故tPP不含host数据装入，但不是一个cell脉冲。
- **PDF p38，§8.2.14**：Quad Page Program最多256Byte；高速输入场景内部页编程远长于clock-in，因此Quad输入收益很小。该段直接支持把传输和内部完成分开。
- **PDF p39，§8.2.15/Fig31a**：4KByte全部擦为FFh；CS升高启动self-timed tSE，BUSY降为0结束。
- **PDF p65–66，§9.6 AC表**：page program typ0.4ms/max3ms；4KB sector erase typ45ms/max400ms。32KB erase120/1600ms、64KB150/2000ms是其他native操作，不用于本主映射的四个独立sector预算。
- p65普通03h读时钟最高50MHz、其他相应模式104/133MHz，p5连续传输66MB/s：均为接口能力，不代替cell/array读周期，不代替tPP/tSE。
- p66注5“TA25°C、VCC3.0V、25%driver strength”不能无区别附到表中所有tPP/tSE；保留原表typ/max标签和器件工作范围，不发明每一项未标注的测量PVT。

**主更新桥接**：用一套本地128-bit低压装入接口和256Byte页缓冲连接单域自定时页算法；每页数据16拍，准备/完成2拍，erase每次2控制拍。内部高压驱动、脉冲、所需verify/retry/恢复全部以原tPP/tSE完整块保留，不复制CMOS数字预算覆盖高压操作，也不再叠统一HV余量或循环数。接口更换为本地直接buffer装入是工程选择；不能声称这是封装W25Q的直测更新接口。

## 4. 物理映射：读选择与擦除选择分开

导入共享R0，32个读分片×128SA=4096SA；各片保存4个输入行×128Byte=512Byte。输入索引i映射片s=i mod32，局部行g=floor(i/32)；每轮32片同时读各自g行的16个输出权重。如此实现R0每轮32输入项×16输出且每片只选一个局部字线。

主布局8片共用1sector：sector=floor(s/8)，sector内Byte地址=(s mod8)×512+g×128+o。取s=0…31、g=0…3、o=0…127构成4个sector各0…4095地址的一一覆盖，脚本逐项检验。每片2页，每页2个128Byte逻辑输入行；每sector16页，矩阵64页。

原文规定4KB是擦除单位，没有可见证据规定sector内只允许一个本地read port。将八个读片置于共同erase域是工程布局选择，要求WL/BL分段、read偏置缓冲、输出隔离、页选通抑制、sector共同高压erase控制。它并非W25Q内部组织的反向工程结论，也不是已验证电路。没有依据强迫32read片=32erase块，同时也不声称32片可以免费并行program。

主映射只有一份16KiB逻辑矩阵，物理有效分配也16KiB。32read片不是32份独立复制矩阵；写更新域始终1。更新时服务暂停，不读写重叠。各sector专用，无无关数据read-modify-write；任意整矩阵重写含全部4次erase和64次program。

**唯一组织对照**：每片独占4KiB，32sector，物理分配128KiB。每片仅512Byte有效，64page不变但每erase仅2有效page；其余111KiB不计逻辑payload。读组织和时间不变，τ/RI*同步改变。这是可移植性约束的有量化后果的对照，而非主布局默认公理。

## 5. NOR-04/05：模拟CIM不与binary更新混用

### NOR-04

文件 `NOR-04_2017_EmbeddedNOR_Classifier.pdf`，Guo等，IEDM2017，4页，180nm改造ESF1。**p1§II，p3 Figs1/2/6**：阈值/导通电流表示权重；第一层输入门极0/4.2V，第二层gate-coupled模拟VMM，差分cell表示正负权重；阵列改布线支持单cell调整，面积成本也存在。实际网络784输入、64hidden、10output，共2×[(784+1)×64+(64+1)×10]=101780cell。

**p2§II/III，p4 Figs8/9/14**：785bit输入先串行shift后并行施加；约30%cell被调，选择5%单cell导入目标以缩短导入；三个芯片平均调谐误差4.4/5.6/3.6%，随后半选扰动导致部分超出目标，未重调。网络平均分类延时低于1µs，但Fig14文字限定相位稳定和输入电路限制，波形估计0.45µs不能直接升级为完整事务周期。p4Fig16更先进ESF3对大网络估计是预测。

**用途**：解释NOR如何在电流域做VMM，以及为什么实际单cell电流目标需要另外的调谐服务。它不支持“普通binary状态自然有均匀ION、可直接精准模拟求和”，也不为本章digital R0提供实测周期。本章数字判决避开这项模拟匹配依赖；计算语义为精确整数，不给统一模拟误差阈值。

### NOR-05

文件 `NOR-05_2016_NOR_ModelBased_Tuning.pdf`，Merrikh Bayat等，DRC2016，2页，180nm改造ESF1，100cell及两行外围镜像电路。**p1摘要/正文**：10pulse平均3%，35pulse约0.3%，动态范围约4个数量级；不是线性8-bit字节容量的直接定义。

**p2 Fig2**：初始化全擦，read state，模型更新；按状态选择program/erase，并读回检查误差终点。**Fig3**显示program表征脉冲Duration100µs、erase Duration2.5ms；**Figs5/6**是精度/脉冲数和分布，非固定完整阵列写服务。**Fig7**是约1日保持表征，不用于本章refresh。

若另选模拟模式，完整update还需初始化、每轮选择/HV建立、program或erase、read/verify、模型更新及array并行/half-select预算；固定脉冲数×某一单脉冲宽度不能替代这些过程。本次不对该不同服务填一个伪完整τ。

## 6. 实算与支配项

参考公共TD=5ns，read_full=120ns，tPP0.4ms，tSE45ms。

- Streaming：256×120+256×5+2×5=32010ns；ρ=128/(32010×10^-9)=3998750.390502968Byte/s。读占约95.97%。
- 每页：18×5+400000+(45000000+10)/16=3212590.625ns，B_R,page=256Byte。
- 矩阵：64×(400000+90)+4×(45000000+10)=205605800ns，B_R=16384Byte；τ=79686.4679887435Byte/s。
- RI*=(128/16384)×205605800/32010=50.18104693845674。不能删掉1/128粒度因子。
- 擦除180ms占87.5462%，program25.6ms约12.45%，front5.8µs不到0.003%。降低低压接口时隙不消除erase支配。
- private-sector对照：32×45ms+64×0.4ms+6080ns=1465606080ns。物理分配128KiB、逻辑仍16KiB；读相同，τ约降7.13倍。

short/reference/long按同一映射，short/reference都采用typ写，long采用max写；共同外围每组同步传播。结果范围不是统计置信区间、不是材料界，也非“最大读配最小写”的跨情景拼接。本轮移除把不同共同外围端点直接相除的外包络；JSON与正文均以条件配对ridge范围为主。另固定写及TD，仅对移植read_full作±20%检查，其ρ/ridge分别+23.753%/−16.103%；未对不确定性作普遍稳健承诺。

## 7. R4覆盖、维护、生命周期与未闭合条件

- 完整binary读锚点覆盖选择/感测，低压数字归约另加；没有完整cycle再叠感测周期。
- tPP/tSE按BUSY完整块，内部verify和HV不重复累加，命令/页装入另计且按native operation准确次数。
- 128bit interface是装入资源，native page algorithm的cell并行度保持封装来源内部未知，不强行填128cell批并以此加速。
- 正常读不破坏状态；正常有效窗口不设refresh。保持与endurance为状态可行性，非workload Q_R，非瞬时τ的折扣。
- 全矩阵任意重写每次消耗每个活动sector一次erase endurance；来源100K寿命是商品规格，不是重构宏的保障。
- R0读写不能同时占用阵列/高压选择；P≤min(ρ,τRI)不证明可同达两独立峰值。

**最重要的物理待验证条件**：128-SA宽读片的负载/判决裕度是否支持100–130ns；32片并行的选择隔离；8片共sector高压擦除/页program抑制；保留NOR-02 native tPP/tSE量级。这些明确工程桥接是估算成立条件，不冒充未提供的硅测。

## 8. 检查与文件范围

只修改`analysis/03_nor_2d/`。`check_nor.py`默认只读，`--emit`才刷新JSON/TeX。校验共享基线/API与原PDF hash、R0计数、全部权重地址一一覆盖、页/sector对齐、64page/4erase与对照32erase、完整阶段sum、按页/按矩阵τ相等、手算与统一单位。构建XeLaTeX；所有PDF页渲染并逐页看图检查，记录在`notes/review.zh.md`。读源码和渲染PNG均在ignored tmp，不复制原PDF、不改共享文件、不做Git操作。

## 本轮统一复核

回查 NOR-01 PDF pp.85–86 与 NOR-02 pp.37/39/66，保留读周期、完整program/erase及4sector主布局数值。32读片、4096SA与4sector是不同层级的资源选择；binary本地感测＋数字归约的身份和商品读周期向本地读槽的工程桥接已在标题与结果入口明确。参考点仍为ρ=3.99875 MB/s、τ=0.0796865 MB/s、ridge=50.1810。无周期维护，原始占用即本地持续重复服务间隔；寿命另计。
