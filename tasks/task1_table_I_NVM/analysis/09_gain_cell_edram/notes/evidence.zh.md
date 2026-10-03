# Gain-cell eDRAM：证据、选择与复算边界

本地 PDF 页序从 1 开始。只使用本任务资料；没有检索、下载或改动原文。主模式是 GC-04 的 3T1C current-programmed 端点二进制伪差分 ACIM。它是以 65 nm 器件/宏为锚、接共同 28 nm 外围能力的条件参考设计，不是已测 28 nm 宏。完整原值与工程桥接留本文件和 `data/inputs.json`。

## 1. 核心原文回查

### GC-04 — Jiahao Song et al., JSSC 2024

题名：*A 4-bit Calibration-Free Computing-In-Memory Macro With 3T1C Current-Programed Dynamic-Cascode Multi-Level-Cell eDRAM*。DOI: 10.1109/JSSC.2023.3339887。

- **pp.4–5，Fig.4–7，原理/仿真**：电流编程使 storage node 的 VGS 自适应器件 Vt；dynamic cascode 降低读电流对 RBL 电压的敏感性。10 fF MOM storage capacitor 用于降低采样噪声及保持漂移。不能把动态 cascode 省掉再沿用电流稳定性。
- **p.6，Fig.8，结构**：每个 3T1C cell 是八电流级，0–700 nA；两 cell 伪差分形成 −700…+700 nA 的 15 级带符号权重。不是一个 cell 存四个完整二进制 bit，也没有天然 −8 的 signed nibble。正文说 4b signed 指其 15 级编码，不自动覆盖 INT4 的全部二补码 16 种状态。
- **p.6，Fig.9，仿真**：100/400/700 nA，FF、80°C，0–0.4 ms。加 10 fF 后计算电流漂移改善，文中列出 1.5–20.4%。该仿真漂移百分比不能直接代替 p.10 的实测 ADC-LSB 分布。
- **pp.6–7，Fig.10，实测宏操作**：64×64 pair；64 个 4b DTC、64 个 5b SAR、64 个 4b 电压/电流两步 write driver。完整 180 ns 划为 precharge、DTC/MAC、SAR 三阶段。数字块 1.0 V、阵列预充 0.9 V、ADC 0.7 V。原 ADC 为 5bit，不能将该 180ns 当作名义 10bit/约8有效bit 公共 SAR 的实测时间。
- **p.7，Fig.11，写机制**：50 fF 写 BL 寄生以 100 nA 单独驱动需要约 400 ns；先用电压块在 5 ns 内将 BL/BLb 置 VW=0.52 V 或 VSS，再电流精写。replica cell 提供电流源 operating point，避免 startup 慢、保持写晶体管饱和。50 fF 是文中写寄生条件，不能直接当作新读前端包括 ADC CDAC 后的有效积分电容。
- **p.8，Fig.12，仿真**：全部电流级在所示 60 ns 时窗建立。该图明确标注 simulated，不能称实测；也不能只取开头 5 ns 当完整更新。
- **p.9 文字 + p.10 Fig.16，实测完整写锚**：原文固定 5 ns voltage coarse，再扫描 10–70 ns current fine，步进 10 ns。Fig.16 给总 15/25/65/75 ns 四组传输函数；正文明确所有权重的传输函数在 **总 65 ns** 建立并达到目标范围。这是真正可用于主模式完整写的实测证据，强于只引用 Fig.12 的仿真。它是宏级传输建立，不是每一个 cell 的 BER、寿命或无限重试结论。主表 P=65/65/75 ns，分别含 coarse 5 ns、fine 60/60/70 ns；不另外加 5 ns。
- **p.9–10，Fig.17–18，实测保持**：全部 cell 写 +7/−7，立即读一次，再在等待指定保持时间后逐行 ADC 读回；通过调 RWL pulse width 使用 ADC 动态范围。两次读差抵消 ADC offset。0.4 ms 内 99.7% 被测 cell 漂移 <1 个原 ADC LSB。这里的 LSB 属于调过脉冲的 ADC 读码，不等于 100 nA 相邻电流编程级；也没有证明所有 cell 无符号错误。
- **p.10，Fig.19–20 对应文字**：四 bit ResNet/CIFAR10 软件91.67%，fresh90.78%，0.4ms后>90%。原宏刷新 delay=64×65ns=4.16µs、能量1204pJ；其吞吐 refresh overhead=4.16/(400−4.16)≈1.1%。延时表达式只呈现逐行重写，不可据此推定一个不保存原码的 ADC 读回/译码已免费包含。该网络准确率不移植给本 INT8 合同。

本次已视觉回查 GC-04 p.6/7/8/10（包括 Fig.8/10/11/12/16/17/18）；数值与原文核对，所有原 PDF 哈希保存在输入 JSON。

### GC-02 — Robert Giterman et al., JSSC 2018

题名：*An 800-MHz Mixed-VT 4T IFGC Embedded DRAM in 28-nm CMOS Bulk Process for Approximate Storage Applications*。DOI: 10.1109/JSSC.2018.2820145。

- pp.4–6，Fig.4/6/7：28nm bulk mixed-VT 4T IFGC、128×32、4kbit macro；WWL 用 VBOOST 使写1不受 NMOS Vt-drop；读 RBL 预充到VDD再驱动RWL，需差分感测、专用时序。
- p.8–9：800MHz，近0.9V；保持统计涉及0/27/85°C。5µs 对应 **99% bit yield**，不是所有bit保证；原128行宏约93% memory availability。这不代表放大容量后仍93%。
- p.9 Fig.13：图中85°C、0.9V的100%样本bit yield曲线在800MHz约1µs，99%曲线约5µs；图读只用于说明阈值差异，不精细取最差时间作新模式参数。6sigma平均DRT外推图不作为最差cell保证。
- 该文是数字存储访问，不支撑把 1/800MHz=1.25ns 直接当本 3T1C 的精细电流建立、完整MVM或刷新时间。本文不将它与 GC-04 拼成同状态读写。

### GC-01 — Shanshan Xie et al., VLSI Symposium 2022

题名：*Gain-Cell CIM: Leakage and Bitline Swing Aware 2T1C Gain-Cell eDRAM Compute in Memory Design with Bitline Precharge DACs and Compact Schmitt Trigger ADCs*。DOI: 10.1109/VLSITechnologyandCir46769.2022.9830338。

- p.1 完整正文，p.2 Fig.1–4：65nm 2T1C、读写端口解耦；1bit weights complementary form；2bit input用RBL预充编码，read multiplication、self-detect clipper、charge share、2bit ST-ADC五步，其他weight bit arrays并行、输入2bit分片串行。
- clipper专门抑制未选cell leakage sneak paths，不能忽略其占用；ST ADC半周期转换不是INT8最终服务时间。用途是另一路gain-cell ACIM的机制对照；不套其ADC精度/读时间/保持给主模式。

### GC-03 — Shuhan Liu et al., IEEE TED 2024

题名：*Design Guidelines for Oxide Semiconductor Gain Cell Memory on a Logic Platform*。DOI: 10.1109/TED.2024.3372938。

- p.2 Fig.2：28nm GEMTOO模型、256row×32column，bandwidth由频率与memory availability共同决定；刷新前残余读电流决定最坏读取速度。99.9999% availability定义saturation point，约10s是设计模型所设目标。
- p.3：OS–OS/hybrid结构、off-current与read-current联动规格（如1V及负栅压条件），不是完整oxide CIM实测。不能把其10s保持移植到硅3T1C。

### GC-05 — Ping-Chun Wu et al., JSSC 2025

题名：*An Integer-Floating-Point Dual-Mode Gain-Cell Computing-in-Memory Macro for Advanced AI Edge Chips*。DOI: 10.1109/JSSC.2024.3470215。

- p.2结构：16nm FinFET、108kb GC storage、24 banks；每bank64GC-CB；每GC-CB有72bit GC storage、18SRU、18个7T STU。四份GC storage对应一份stationary数据；INT8带原文具体格式变换，不能把全部108kb当作同时可计算的INT8矩阵。
- p.6 Fig.13/14、p.7 Fig.15(a)：stationary update先读GC→RBL/SRU，再启用STU write-assist，最后脱离WBL/RBL并预充。**resident完成端点要包含这步。**
- p.7 Fig.15(b)：storage-update GBL→N0→SRU→WBL→选中GC，可与已有STU计算并行；这不是新权重已提交到计算。
- p.7 Fig.15(c)：self-refresh PRE/RWL读RBL→SRU→WWL/WBL重写GC，不经高寄生GBL；已有STU可继续MAC。应按实际GC/SRU/读写端口与STU/计算口分别排程，不应硬加不相冲突工作，也不可把stationary更新或维护端口忽略。
- pp.8–9 Fig.19/20：INT8 128 accumulations、24 outputs、23bit output；文字报1.9ns at0.6V，图中1.9ns pass相符；Fig.19摘要还列0.8V的access条件。该compute latency不是storage update或stationary update的完整实测预算。资料没有足够理由把它与GC-04保持/写入直接配对，因此作为组织解释而不另造完整数值模式。

## 2. 原生64×64映射与实际资源

保留GC-04原64row/64paircolumn局部负载，八个64×64pair位平面表示K64N64INT8，4096Byte有效容量、32768pair/65536cell。每bit只取±700nA端点，一对两cell，每权重16cell；没有权重副本或逻辑容量倍率。每次16输出，128差分ADC和128pair驱动、256支路选择固定；16重构通道、两拍，输入512bit、输出64×22bit。

64项差分z范围-64..64共129级，q=(z+inputpopcount)/2。前端专用槽100/150/200ns由共同阶段36/86/136ns与固定64ns控制窗口构成，仅以180ns完整周期支持总量级；加TI/TA后CA112/175/260ns。1ns MAC脉冲后至64ns采样边界的63ns为控制预留，需保持模拟样本，不是MAC必需积分时间。MAC1ns、单pair符号读64ns给同满幅44.8fC；200fF/branch和±224mV，128双支路共51.2pF。新增积分/SAR在program隔离，写BL+开关寄生维持原约50fF。0.52V/5ns粗写在50fF下电容电流5.2uA/branch为驱动量级条件，128pair端点目标电流合计89.6uA不是总瞬态供流。

写65ns包含5+60ns，75ns包含5+70ns；不重复粗写，不加入未知verify/retry。每16Byte256控制bit两数据拍，首拍命令同入，front3TD，CR71/80/105ns。256事务完整装载4KiB。

## 3. 无shadow维护及独立算术

每组128pair读取、128个sign decoder一TD判决，只存该组128符号码并生成256支路控制bit，随后写回。刷新256组，每组CA+TD+CR=185/260/375ns；全刷新H=47360/66560/96000ns。覆盖32768pair读取、65536cell重写，内部payload零，无完整数字权重shadow。

固定每400000ns刷新起点/顺序，提前G=max(CA+2TD,CR)=116/185/280ns停止发新不可抢占组，确保同一cell写回间隔不超过400us。计算在完整求值/转换/重构后暂停，输入和数字部分和保持；完整写组才暂停。不跨窗口保持模拟样本。每周期有用窗口352524/333255/303720ns，均足以调度所述最大组；冷启动先完整装载并建立相位。

独立手算典型CS=32*175+66*5=5930ns；CR=3*5+65=80ns；H=256*(175+5+80)=66560ns；alpha=1-(66560+185)/400000=.8331375。rho=64alpha/5930=8.991703204MB/s；tau=16alpha/80=166.6275MB/s；RI*=(64/16)*80/5930=.053962900506。

完整TRraw=256*80=20480ns；TR有效平均=20480/alpha=24581.7767175ns，U*=20480/5930=3.4536256324=64RI*。有效间隔为同周期预留下稳态平均服务，不是任意到达相位的固定latency。16KiB平均换算×4仅作辅助，不是实际16KiB事务。

## 4. 有限情景、容量与资源对照

主三情景同原生64²、同资源，alpha=.88131/.8331375/.7593均非临界。原始CS3716/5930/8980ns，CR71/80/105ns；长期rho15.17864/8.991703/5.411492MB/s，tau198.6051/166.6275/115.7029MB/s，RI*.0764263/.0539629/.0467706。

同资源扩到128²需要32native tiles、四倍容量和1024刷新组，referencealpha.3339375仅作容量对照。该容量long占384000+280ns，alpha.0393单列压力；专用读216ns时400680ns占用，alpha-.0017不可行，能力/有效间隔/RI*/U*为空。保持期不放宽，负alpha不裁剪。

64²宽32输出对照真实翻倍ADC/pairdriver/sign-decoder至256，16重构通道不变；CS3130ns、32Byte更新90ns、刷新128*(175+5+90)=34560ns、guard195ns。额外资源明确，不能混进固定配置正常三点。

## 5. 复算与外部判断

公共logical/API贯通K/N，逐情景保存mapping_interface与raw/effective，维护经公共apply_maintenance，完整载入覆盖经full_load_service检查。主检查包含端点和补码、真实capacity/刷新资源、完整两步写、周期可行、alpha零/负空值、U*及生成同步。

原始关键GC-04 p7Fig10/11、p10Fig16/17/18已按现有原页渲染回核。主要外部判断是1/64ns脉冲、200fF读前端与噪声/漏电、写隔离后65ns建立和并行供流，以及400us端点符号读的重复刷新稳定性。原99.7%/1ADC-LSB统计不包装为全阵列精确概率。其他GC证据保留身份边界，不移植保持时间或计算接口。

## 6. 正常MAC与单pair刷新读取的模式资格

GC-04 p.7 Fig.10原页图明确BL预充、DTC/RWL积分、采样后SAR三阶段；p.6正文说明先连接BL/CDAC并预充，再产生RWL脉冲，最后量化已采样结果。p.10保持测量则明确区别多行CIM与逐行ADC读出，调RWL宽度以利用ADC量程。已重新目视这些原页，以及p.10 Fig.16的65/75ns完整写和Figs.17–18保持。原文没有本参考1/64ns、200fF及分阶段ns，不能从180ns锚点分解出独立已测预算。

本参考两模式保留700nA、64-cell局部位线、200fF/branch、±224mV与同一转换器。活动行数和脉冲不同；44.8fC同满幅仅核对动态范围，不保证相同建立、共模、漏电或噪声。共同阶段预算包括预充、选择、隔离回接建立、采样和恢复，只有合计36/86/136ns，不人为给各阶段拟合独立数值。共享TI单独处理输入驱动，TA处理转换。

主fixed_slot模式为实际控制选择：两种读均在64ns积分窗口边界采样；MAC只积分1ns，其后等待。此时原三点全部保留。等待期间模拟保持是明示资格。条件early_release模式让MAC/refresh分别在1/64ns后采样，只有在同一共同阶段预算仍覆盖各模式、控制器允许提前结束且不增加资源时成立。它是操作模式对照，不是同模式参数误差包络，也不是已证实提速。

典型独立算术：MAC CA=5+86+1+20=112ns，refresh CA=5+86+64+20=175ns；CS=32*112+66*5=3914ns，CR=80ns；H=256*(175+5+80)=66560ns，G=max(112+10,80)=122ns；alpha=.833295。raw rho/tau=16.3515585/200 MB/s，effective=13.6256719469/166.659 MB/s，RI*=.0817577925396，U*=20480/3914=5.23249872253。短模式G=max(49+4,71)=71ns，长模式G=max(197+20,105)=217ns；两者H仍47360/96000ns，alpha=.8814225/.7594575。固定原生容量、400us保持期和读码重写流程不变。

`data/service_diagnostics.json`保存8个有限扰动。独立预期由32计算组、256刷新组、每写3TD和每刷新译码1TD产生：共同阶段+10ns给CS+320ns、H+2560ns、G+10ns；TI或TA+1ns给CS+32ns、H+256ns、G+1ns；TD+1ns给CS+66ns、CR+3ns、H+1024ns、G+2ns。固定窗口+1ns同时增加CS/H/G；其内部MAC脉冲+1ns不改变占用。early_release的MAC脉冲+1ns给CS+32ns、G+1ns；刷新脉冲+1ns给H+256ns。每次均完整重算alpha及两路能力。固定窗口内65ns刷新脉冲被拒绝，避免在未扩展控制槽时静默隐藏超时。检查不调用主生成函数来产生预期导数，也不宣称电路验证。
