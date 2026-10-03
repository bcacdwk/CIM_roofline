# MRAM 证据、工程桥接与逐项边界

页码均为本地 PDF 从 1 开始的页序，非期刊页码。资料入口是 `literature/06_mram/NOTES.zh.md`，重要原值另以本地 PDF 文字及页面渲染回查；没有新增检索或下载。主路径为互补 MTJ bitcell 数字 CIM。所有源文件及 SI 的哈希在 `data/inputs.json`，脚本逐一校验。

## 1. 原值与来源用途

### MRAM-06：数字机制、正确两相、原生资源与写验语义

文件 `MRAM-06_2025_LosslessParallelSpintronicCIM.pdf`，24 页；SI 为 15 页。

- **p.2 正文（期刊1047），p.4 Fig.2a–d（1049）**：40 nm CMOS STT-MRAM、64 kb 宏；每个 IBMD bitcell 包含两个 1T1MTJ 支路并使用本地 latch。左侧 W，右侧反相权重。输入触发感测/数字化后输出数字 AND；P 低阻编码 0，AP 高阻编码 1。
- **两相不可改写**：p.2 明确第一相选中行 SL=VW、BL=BLB=0，使两个 MTJ 均 P；第二相 SL=0，目标 BL 或 BLB=VW，另一侧为 0，使一侧 AP。Fig.2b/d 可视核查相同。并不是 MRAM-01 的左写完再右写完。
- **SI p.4 Fig.2**：标出一组选中 256 对时第一相两条支路均通电，SL 累计 `IW×512`；第二相只有目标支路通电，总计 `IW×256`。本章缩到 64 对时需 128/64 条活动电流支路，且 SL 总电流能力随动；这比仅数数据接口位数更接近实际资源。
- **p.5（1050）**：64 bank，每 bank `256-row×4-column`，七级 full-precision adder tree。输入 MSB-first bit serial；四位输入明确四周期。bank 内一拍 256 个 1-bit×4-bit 乘法；通过 shift adder、weight-precision control 与 bank 合并支持 4/8/12/16 bit。说明数字重构机制可行，不要求所有 MRAM 都有此 bank 数或行数。
- **p.4 Fig.2e 及正文**：655360 个 bitcell 的读测量，0.65 V 为 1890 个错误；0.85 V 及以上无观察错误。对应 Monte Carlo yield 是另一组仿真量，不能把无观测错误作为零错误率证明。p.2/p.4 nominal 1.1 V、TT 的 88 ps 上升/22 ps 下降是 **bitcell 后仿**，不是 MVM 周期。
- **p.5 性能段**：4-bit 最高吞吐 4.42 TOPS、540 MHz@1.20 V；最佳能效 7.02–112.3 TOPS/W@0.65 V/80 MHz、50% weight sparsity、6.25% input toggle。不能与 0.85 V 的读可靠性合成同一工作点。
- **p.9 Methods（1054）**：先写入权重，read/verify，256 行逐行循环；读回不匹配时定位并重写错误行。没有完整写验绝对周期、没有指定固定重试次数。Fig.2c 测试流程也只给流程。原逻辑读通过加法树取回所选行数据，不能从文中推导它已经单独检查每个物理 MTJ 的 P/AP 有效性。

**使用**：采用互补数字计算/两相写机制、正确位串行与重写语义。**工程修改**：采用原64bank容量映射为K256/N32，活动32项/16输出；增加原加法树之前的局部OUT抽头、单tile寄存与数字AND，设置八权重更新组和左右绝对状态验证。64 单端 sense/64 compare/128-bit 状态寄存均是显式新增资源，不是原文给出的免费功能。

- **p.8 Methods / p.14 Extended Data Fig.1(b–f)**：原生MTJ直径78nm，R_AP均值9199.2Ω、R_P均值3363.7Ω；准静态I–V图在所示约±0.6V内电流幅值到约180µA。此量级只用于条件写驱动额定能力选择，不能当20/30ns脉冲的电流实测或最低成功电流。

### MRAM-03：28 nm 普通 1T1MTJ 完整 read/write access 锚点

文件 `MRAM-03_2019_SelfWriteTermination.pdf`，9 页。

- **p.4 Figs.8–11**：constant-current voltage sensing、single-cap offset cancellation；读时序含 offset cancellation、equalizing、BL sampling 和 sensing。部分 offset/equalizing 与地址译码重叠。不能仅从 transistor delay 推出完整可复用服务。
- **p.5 Figs.12–14**：传统 read-before-write / write-verify-write 会反复应用短写脉冲和独立读取直到数据正确，需要多周期。该工作使用写时持续感测，使 switching 时 BL 电压突变触发 self-termination，主要节省继续通电造成的能量。
- **p.6 Fig.15**：写周期也从 offset cancellation 起步，随后 write enable 与 termination/reset 信号；不是裸 MTJ 翻转时长。测试系统采用亚阵列和共享本地电路，原文 p.6 提到单个 128 kb array 的 **16 个 sense amplifier**；本文不把原16-lane与所选128驱动混同，资源数是新的参考选择。
- **p.6 Fig.17，p.7 Fig.19 / Table I**：25°C、1.2 V 下 2.8 ns read access；120°C 时约3.6 ns，约 `1E-5` 读错误量级。Table I 供电列为 1.2/1.8 V；2.8 ns 不能称为 0.9 V 下实测。read fail 不是 ADC 量化误差。
- **p.7 Fig.21 / 正文**：常规固定写时间达到 `1E-5` 级失败需约20 ns（正文措辞 longer than 20 ns；括注与表以20 ns作锚点）；20 ns 的 self-termination 节能47%。30 ns 对应正文 `1E-6` 标签与61%节能；图中30 ns及以后已达 **“Zero Error Floor for 1Mb Chip”**。保留这一有限样本分辨地板，不能称真实测得 p=10^-6，更不能将其外推为互补新实现的 BER 保证。
- **p.7 Fig.22**：写20 ns、checkerboard 数据，温度更高时 switching 更快，self-termination 节能增加；没有证明外部写槽自动缩短。
- **p.7 左栏**：该偏置/短访问条件下连续读超过1E6次无观察扰动。是 read-disturb，不是写耐久寿命。

**使用**：20/30 ns 作为本参考单方向物理写槽量级；3/5/10 ns 完整单端验证读槽的量级锚之一。**限制**：它是1T1MTJ，不能直接向本文0.9 V互补数字bitcell移植概率、驱动电流或完整波形拆分。

### MRAM-04：较接近互补读结构的独立 28 nm 锚点

文件 `MRAM-04_2018_2T2MTJ_ReadMacro.pdf`，3 页。

- **p.1 / p.2 Figs.30.3.2–4**：28 nm、32 kb 2T2MTJ，continuous-recording-and-enhancement VSA。操作有 P1 precharge/VTH sample、P2 BL development/continuous recording、P3 sensing，P1/P2有与其他阶段重叠的组织。
- **p.1 测量段、p.2 Fig.30.3.6**：1.3 ns macro-level read access，`VBL_RD=0.3 V`；对应 conventional VSA 1.86 ns。0.3 V 是读位线偏置，不应被改成核心供电。
- 室温 CRE 可在 `VBL_RD=140 mV` 工作，传统为280 mV；这支持读扰动与感测余量相关，而非所有偏置下都是无错瞬时读。

**使用**：为短读槽3 ns提供更相近的互补差分结构量级支持，不直接复制原CRE电路为MRAM-06 bitcell，不据此声明4096bit活动负载的3ns实测或普通存储读等于CIM计算。

### MRAM-01：明确隔离的电阻求和路径

文件 `MRAM-01_2022_ResistanceSum_Crossbar.pdf`，17 页。

- **pp.6–8 Methods**：28 nm电阻串联求和/TDC。8192 MTJ-FET支路的 RH≈26kΩ（σ≈2.0kΩ）、RL≈13kΩ（σ≈1.6kΩ），含FET导通电阻。
- “Crossbar array weight update”：一行先所有左支路同时写 W，再所有右支路同时写反相 W，每个步骤各一个 **11.1 MHz 时钟**；写电压1.5 V，每支路写电流显著小于100µA。这些与MRAM-06先双P再一AP不同。
- “Operating frequency”：列末节点到VREF为13–29ns，理论最高频率以两倍最大延迟为界约17.2MHz；计入数字控制后实际11.1MHz。

**使用**：证明另一MRAM CIM机制及不能混用的时间/写序列。本文主表不使用以上响应、TDC与11.1MHz。其独立支路读电路也不能悄悄作为主机制免费的validity检测资源。

### MRAM-05：正式产品的更新语义

文件 `MRAM-05_2026_EMxxxLX_B_HR_v3p7.pdf`，82页；v3.7日期2026-07-23，部分页内版权仍2025。

- **p.15**：back-to-back写时无须再次载入WREN的模式说明。
- **p.42 WRITE / p.43注释**：persistent memory模式可写任意字节数量，无page限制；NOR Flash兼容模式限制256Byte页并页内地址回绕，两模式不能混写。**p.48 ERASE**明确任何bit可由旧状态直接写0或1，无需ERASE；支持ERASE操作码是用户兼容语义。产品是xSPI封装接口，不能映射为本地MTJ并行写吞吐。
- **p.1** 明确 Program/Erase emulation；ERASE命令名不能推导STT必须先物理擦除。

**使用**：普通STT可直接更新、无需将NAND block擦除套进本章；不证明28nm、不借其封装总线速率计算局部ρ/τ。

## 2. 原生容量、真实节点和有限保持

MRAM-06 p.5的64bank×256row×4bit是65536个互补bitcell；两个bank合成8bit权重，故原生K=256、N=32、有效8192Byte；物理131072MTJ／16384Byte二元状态，不能把互补副本计入有效payload。地址W[o,i][b]→(bank=2o+b//4,row=i,column=b%4)全枚举恰覆盖64×256×4。输出精度24bit，32个结果；原生容量继承，原256项归约通路按共同资源政策改为16条32项活动归约，不声称原256项树全被利用。

原IBMD OUT=IN∧W，输入为0时OUT清零，原latch不是输入无关的W缓存。p.5 read mode令IN=1得到每cell的OUT=W，但原宏经bank加法树返回所选行数据。本参考增加加法树之前的4096路局部OUT抽头和隔离，在65536个固有IBMD/latch中选择4096个不同节点，八行组×两输出组共16tile，每通道对应16:1选择网络。不能把bank四列的求和值当4096个独立权重读口。

读槽tm包含初始化/预充、IN=1差分数字化、抽头/选择布线；独立1TD将W捕获到单4096bit register并完成隔离交接，下一tile预充由其自身读槽覆盖。新增4096个数字AND把真实输入位与保持W相乘，再接16条32项归约，组合功能按共同一TD预算；该周期须包含新增AND/布线，不是沿用原540MHz。各tile八输入位用完才替换，未建立全矩阵shadow。已有IBMD latch数量65536、活动4096，新增权重保持4096bit、输入2048bit、16×24bit部分和、32×24bit输出分别列账。阵列读/写/终验选择互斥。

## 3. 写资源、两相与终验

八个INT8权重一组，对应一个row的16个bank×4互补bit，64对／128MTJ，有效BR=8Byte。先128MTJ全部置P，再64目标侧置AP，仍是MRAM-06两相；一组192物理状态命令。单128bit接口装入物理目标一次，目标128bit寄存保持到完成及有限重试。bank/row写使能、未选SL高阻与选择隔离为实际参考资源。

固定128条200µA方向驱动，SL合计25.6mA，第二相64条对应12.8mA能力。依据为SI p.4两相512Iw/256Iw按64对缩放，以及原器件p.14准静态电流约180µA的量级；200µA为参考额定能力而非脉冲实测。三情景固定资源，实际20/30ns偏置/负载必须落在其额度内，不能由数据接口自动获得写并行。未借MRAM-01另一结构的<100µA数值。

终验另有64条单端感测＋参考、左右隔离、128bit状态寄存及64比较器，分两批读取全部128MTJ。每批完整read tm后明确1TD捕获、1TD比较；差分逻辑值不能代替P/P、AP/AP非法状态检测。此128bit状态寄存不是新增4096bit权重tile的免费替代，二者功能和端口分别列账。

单方向tW=20/30/30ns锚定MRAM-03完整write access，已含初始化/驱动/翻转/终止/恢复；两相间另1TD，事务front2TD，终验两批(tm+2TD)。完整尝试C=2tW+2tm+5TD；DR=2TD+C。主一次尝试通过是有限服务情景，失败时间保留、失败payload为0。对照是恰一次完整重写后通过，不把它当必然成功或普通悲观端，不用原1T1MTJ样本错误地板虚构新宏概率。

## 4. 独立手算与完整装载

本例16tile，八输入位：DS=16tm+16TD+128TD+2TD。典型tm=TD=5ns，DS=80+80+640+10=810ns；front10ns，写两相60ns、turn5ns、两支路读10ns、两次捕获10ns、比较10ns，C95ns，DR105ns。

- rho=256/(810e-9)=316.04938271604937MB/s。
- tau=8/(105e-9)=76.19047619047619MB/s。
- RI*=(256/8)×105/810=4.148148148148148。
- 1024个完整组覆盖8192Byte，TR=107520ns；U*=TR/DS=132.74074074074073=32RI*。
- 每16KiB平均更新成本215040ns=TR×16384/8192，不是原生8KiB请求延迟，也不据此缩放rho/tau。
- short/reference/long的DS=340/810/1620ns，DR=60/105/150ns；rho=752.9412/316.0494/158.0247MB/s，tau=133.3333/76.1905/53.3333MB/s，RI*=5.647059/4.148148/2.962963。
- 恰一次整组重写：DR=10+2×95=200ns，tau40MB/s、RI*=7.901235；只计8Byte完成payload。

原生N=32使每个向量所需输出数小于128，输入K=256则payload更大；有限tile保持也减少物理读。rho改变不能称为MTJ材料提速，图中为所选原生配置能力。写側约57%是完整两相，数字capture/compare/turn/control仍显著，不等于20/30ns单槽倒数。

## 5. 复算、原图核验与外部判断

check_mram.py显式logical_configuration，dcim_service传本例维度；full_load_service覆盖原生完整载入，mapping_metrics逐情景生成TR/RI*/U*。维护前后能力分别保存，局部无refresh/restore；寿命不作瞬时tau折扣。

原PDF直接回查MRAM-06 p2/4/5/8/9/14、SI p4，MRAM-03 p6/7和MRAM-04 p1；MRAM-06 Fig2、ExtendedDataFig1、SI电流图和MRAM-03 p7已渲染核看。检查保留所有源PDF及SI哈希、共享哈希，穷举原生bank地址和4096活动节点，核查编码/驱动/绝对终验、独立分项及整矩阵接口。

外部审阅重点：4096路16:1抽头/选择网络能否满足tm，新增AND与32项归约是否满足TD，128路200µA写驱动及SL25.6mA供给在对应脉冲下是否足够，以及64条绝对状态verify的低偏置和判决裕量。保持策略通过本地W读码实现，不依赖原输入触发latch跨任意输入位保持权重。内部检查不能替代该参考适配的电路验证或用户验收。

PDF QA：XeLaTeX/ctex重建6页，SHA-256 `6685562a4cad2594e0e0ffdc57da8575b74889d9fc64ccf03fbee186283e672d`；pypdfium2渲染当前全部页面到`tmp/pdfs/final/page-01.png`至`page-06.png`及同次contact，逐页目视确认表格、公式、中文字体和页眉页脚无裁切或遮挡，日志无Overfull／Missing character。默认四项测试及git diff --check通过。
