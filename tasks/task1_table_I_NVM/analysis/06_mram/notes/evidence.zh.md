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

**使用**：采用互补数字计算/两相写机制、正确位串行与重写语义。**工程修改**：保留 R0 32 项/16 输出；设置八权重更新组、分组选通和左右绝对状态验证。64 单端 sense/64 compare/128-bit 状态寄存均是显式新增资源，不是原文给出的免费功能。

### MRAM-03：28 nm 普通 1T1MTJ 完整 read/write access 锚点

文件 `MRAM-03_2019_SelfWriteTermination.pdf`，9 页。

- **p.4 Figs.8–11**：constant-current voltage sensing、single-cap offset cancellation；读时序含 offset cancellation、equalizing、BL sampling 和 sensing。部分 offset/equalizing 与地址译码重叠。不能仅从 transistor delay 推出完整可复用服务。
- **p.5 Figs.12–14**：传统 read-before-write / write-verify-write 会反复应用短写脉冲和独立读取直到数据正确，需要多周期。该工作使用写时持续感测，使 switching 时 BL 电压突变触发 self-termination，主要节省继续通电造成的能量。
- **p.6 Fig.15**：写周期也从 offset cancellation 起步，随后 write enable 与 termination/reset 信号；不是裸 MTJ 翻转时长。测试系统采用亚阵列和共享本地电路，原文 p.6 提到单个 128 kb array 的 **16 个 sense amplifier**；本文不把原16-lane与所选128驱动混同，资源数是新的参考选择。
- **p.6 Fig.17，p.7 Fig.19 / Table I**：25°C、1.2 V 下 2.8 ns read access；120°C 时约3.6 ns，约 `1E-5` 读错误量级。Table I 供电列为 1.2/1.8 V；2.8 ns 不能称为 0.9 V 下实测。read fail 不是 ADC 量化误差。
- **p.7 Fig.21 / 正文**：常规固定写时间达到 `1E-5` 级失败需约20 ns（正文措辞 longer than 20 ns；括注与表以20 ns作锚点）；20 ns 的 self-termination 节能47%。30 ns 对应正文 `1E-6` 标签与61%节能；图中30 ns及以后已达 **“Zero Error Floor for 1Mb Chip”**。保留这一有限样本分辨地板，不能称真实测得 p=10^-6，更不能将其外推为互补新实现的 BER 保证。
- **p.7 Fig.22**：写20 ns、checkerboard 数据，温度更高时 switching 更快，self-termination 节能增加；没有证明外部写槽自动缩短。
- **p.7 左栏**：该偏置/短访问条件下连续读超过1E16次无观察扰动。是 read-disturb，不是写耐久寿命。

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

## 2. 选择、推导与阶段覆盖

共享入口 `analysis/shared_baseline/data/shared_parameters.json`，API `scripts/check_shared.py`。读过共享README和两节TeX；所有共同参数从API实际入口读入，不复制常数表或公式实现。

| 项目 | 原值/依据 | 本章选择 | 推导/边界 |
|---|---|---|---|
| 存储编码 | MRAM-06互补2T2MTJ | INT8八对/权重 | 262144MTJ表示16384Byte，不翻倍payload |
| 计算宽度 | 06本地数字AND/全精度归约；共享R0 | 32输入项×16输出×8权重位 | 4096活动pair，256轮，无ADC |
| 媒体读 | 04 1.3ns、03 2.8ns与附带条件 | 3/5/10ns完整媒体读槽 | 覆盖媒体读建立/预充/恢复/数字化，不含另计整数归约 |
| 写组 | SI第一相每对双支路、第二相单支路 | 64pair=8权重 | 128第一相路径、64第二相活动；SL电流承载同步 |
| 编码装载 | 共享物理128bit端口 | 本地64逻辑bit展开128P/AP目标bit | 一物理beat与命令同拍，front=2TD；逻辑payload8Byte |
| 单向写槽 | 03完整access约20/30ns | 20/30/30ns | 工程完整物理槽，非拆出的裸pulse；不叠高压余量 |
| 两相间切换 | 06两步改变SL/BL极性 | 1TD | 不虚称原03已分离测得此时间 |
| Verify | 06有row读验但不完整物理状态证据 | 64单端sense+reference，左右各一次，64比较器 | 两批检查全部128MTJ；每批tm+TD |
| 更新次数 | 06错误行重写，未给固定次数 | 主1次完整尝试通过；对照2次且第二次通过 | 主56/95/130ns，对照180ns；无无限retry模型 |

写相slot锚定完整access，但并无原文可移植的精细延迟拆分。本参考把该相的驱动/翻转/终止/恢复放入tW；把事务前后接口、两相间切换、独立低偏置读取及比较分别加入。若实际电路提供完整覆盖这些阶段的write-verify周期，应替代相应总块，不能重复相加。

单端验证必须检测P/P、AP/AP，不能只看差分输出正确。读低偏置、单支路隔离和参考电平是新增设计条件，3ns短端不是可靠性保证。无统一算法误差门槛或统计BER目标被另加进共同合同。

## 3. 失败压力、有限预算与手算

物理状态命令数192=128先P+64目标AP。旁注p取1e-5/1e-6/1e-6，形式union-bound规模192p=0.192%/0.0192%/0.0192%，不依赖组内独立性；由于移植p未验证，这不是新实现的概率上界。**q没有进入主表、没有改变ΔR，也没有设置无限重试策略。**

主服务为完成一次完整两相与两支路verify并通过的有限工程情景。失败时payload计0而时间保留；一次完整组重写对照展示失败时间成本，不称两次必定成功。实际持续吞吐需要该实现失败与终止统计，而非1T1MTJ的数据移植。

参考：DS=256×(5+5)+2×5=2570ns；front=10ns；C=2×30+5+2×(5+5)=85ns；DR=95ns；BS=128Byte，BR=8Byte。

- rho=128/2570=0.04980544747GB/s。
- tau=8/95=0.08421052632GB/s。
- ridge=(128/8)×95/2570=0.5914396887。
- 两尝试DR=10+2×85=180ns，tau=0.04444444444GB/s，ridge=1.120622568。
- 2048个8Byte组可覆盖整矩阵，无擦除摊销；完整控制仍逐组计，总194.56us，tau保持。

短/长两行从共享profiles读外围，媒体读3/10ns、单向写20/30ns；DS=1284/5140ns，DR=56/130ns。有限情景非统计范围，不以ρ/τ独立极值相除冒充paired ridge。

## 4. 检查与待主审点

脚本检查共享JSON/API与PDF哈希、映射容量/实际驱动/两支路验证覆盖、256轮逻辑覆盖、独立手算与整矩阵聚合、结果/TeX一致性；默认只读。build用XeLaTeX/ctex/Fandol，六页渲染后逐页查看，构建日志位于忽略的build目录。

待主审仍是明确的工程条件而非待填null：新0.9V bitcell的完整读槽与4096pair活动负载；128条第一相路径与SL供流；两支路绝对状态验证在3/5/10ns的有效性。对于相同局部边界的后续实测，可直接替换输入槽，不必改变payload定义。只要新电路不具备所需验证资源或选通，必须同时重数步骤，不能只改时间。
