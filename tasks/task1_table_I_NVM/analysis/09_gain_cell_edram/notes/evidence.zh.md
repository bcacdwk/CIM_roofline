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

## 2. 原生映射与整数服务

八个64×64pair tile编码K64/N64 INT8，4096Byte有效容量、32768pair/65536cell。每bit取±700nA端点，每权重16cell。每轮16输出、128差分ADC、128pair写驱动及256支路选择固定；16重构通道两拍，输入512bit、输出64×22bit。更新256个16Byte事务完整覆盖4KiB，65/65/75ns写含5+60/60/70ns两步；控制3TD使事务71/80/105ns。

共享7bit输入popcount记p，差分整数d=sum x(2b−1)，理想q=(d+p)/2。名义前端是声明的理想电流积分Vdiff=700nA×1ns/200fF×d=3.5mV×d，不是拟合的实测器件曲线。10bit signed code−512…511，零码0，LSB448/1024mV；先向最近码取整（半码向+∞），再裁剪。

第一数字拍在既有offset/correction槽实施qhat=(code+8p+8)>>4。code符号扩展、p移位、常数8并入偏移加法，固定右移；临时值至少12bit，名义qhat为0…64；任意ADC码/popcount组合可得−32…64，按有符号保留而不隐藏裁剪，均在既有22bit重构通道宽度内。16输出通道保留各自8plane并行前处理，第二拍位权重构/累加；不增加parity LUT、fraction accumulator或额外循环。共同脚本统一检查实际顺序，并保存整数舍入前连续affine residual与+rail裁剪。实现级门时序未验证；ENOB量级不是随机噪声模拟或网络精度保证。

## 3. 按模式推进的主调度

GC-04 p.6 III.B和p.7 Fig.10显示既有CCTRL、PRE、SAMP、可调延迟/PWM和独立SAR阶段；p.10单行保持读通过调RWL宽度适配量程。参考逐bit输入每轮活动RWL均在1ns结束，未发现必须等到refresh64ns或未结束多位输入脉冲的依赖。主策略early_release复用这些相位信号，无需增加ADC、driver、模拟保持阵列或shadow；fixed_slot是附加控制预留的保守对照。

预充、局部选择、写隔离回接建立、隔离/采样和恢复的共同残余t_c=36/86/136ns全部保留，公共TI/TA/TD照常计入。原180ns仅总量级锚点，未提供各阶段实测ns，故不人为分拆t_c。模拟相位/可调RWL不必为数字TD整数拍，数字控制/重构拍数并未减少。所谓按积分结束推进包括已分配的采样建立，绝非1ns后零延时强制采样。

MAC1ns、单pair刷新64ns、700nA、200fF/branch给相同最大44.8fC和±224mV。相同电荷核对量程，不证明共模、漏电与噪声完全相同。新增积分/SAR负载在program隔离；约50fF写BL加开关寄生仍是沿用65/75ns写锚的条件。50fF×0.52V/5ns≈5.2µA/branch为粗写电容供流量级，128pair端点电流89.6µA并非总瞬态供流。

## 4. 无shadow刷新与独立典型算术

正常前端CA_M=TI+t_c+1+TA=49/112/197ns；刷新CA_F=TI+t_c+64+TA=112/175/260ns。128个本地sign decoder在一TD内判符号，只保存当前128bit并编码为256写控制，随后完整写回。256组覆盖全部32768pair/65536cell，内部payload为零。

```text
CS=32*(5+86+1+20)+66*5=3914ns
CR=3*5+65=80ns
H=256*((5+86+64+20)+5+80)=66560ns
G=max(112+2*5,80)=122ns
alpha=1-(66560+122)/400000=.833295
rho_raw=64e9/3914=16.3515585079 MB/s
tau_raw=16e9/80=200 MB/s
rho_effective=13.6256719469 MB/s
tau_effective=166.659 MB/s
RI*=.0817577925396
TR_raw=256*80=20480ns
TR_average=20480/alpha=24577.130548ns
DeltaS_average=3914/alpha=4697.01606274ns
U*=20480/3914=5.23249872253=64*RI*
```

固定400000ns周期和逐cell写回位置。刷新前G=max(CA_M+2TD,CR)禁发新不可抢占组，计算在转换与整数重构完成后暂停，既有输入和数字部分和保持，不跨维护窗口保持模拟样本。短点G=max(49+4,71)=71ns，由完整写主导；参考/长122/217ns。H=47360/66560/96000ns，alpha=.8814225/.833295/.7594575；正常长点仍有303783ns有用窗口。平均间隔不冒充任意相位latency；16KiB只作平均成本辅助换算。

## 5. 保守控制、容量和资源对照

fixed_slot在同一1ns MAC后附加等待至64ns采样边界，额外保持须满足泄漏/共模条件；同t_c、TI/TA/TD、程序、保持期、资源和刷新流程。对照CS3716/5930/8980ns，G116/185/280ns，H不变。典型alpha=.8331375、rho8.991703204MB/s、tau166.6275MB/s、RI*.053962900506；主输入服务相对1.51536倍来自32组未用控制预留，不是实测介质加速。

容量K128/N128和资源wide32均使用主early_release。容量典型CS=128*112+258*5=15626ns，H=1024*(175+5+80)=266240ns，G122ns，alpha=.334095，rho/tau=2.736731/66.819MB/s。容量long的H384000ns、G217ns、alpha.0394575仅属临界压力，不放入普通主点。

令刷新专用前端t_f=t_c+64ns，共同t_c也必须传播MAC。容量long满足1025*t_f+179217<400000，严格上限215.3980487804878ns。t_f=216ns时MAC前端213ns、刷新前端276ns、H400384ns、G233ns、alpha−.0015425；有效能力/RI*/U*均为空，不放宽保持期或截断负alpha。

wide32实际翻倍ADC、pair写驱动及sign decoder至256，数字16通道不变。CS=16*112+66*5=2122ns；CR=4*5+65=90ns；H=128*(175+5+90)=34560ns；G=max(112+4*5,90)=132ns；alpha=.91327，rho/tau=27.544430/324.718222MB/s。控制、编码和数据拍仍按实际宽度计数。

## 6. 参数传播和复算

`data/service_diagnostics.json`保存九项有限扰动，独立预期由32计算组、256刷新组、3TD写控制、1TD符号译码及最大组算术产生，不调用主生成函数给预期：

| 参数扰动 | CS增量(ns) | CR增量(ns) | H增量(ns) | G增量(ns) |
|---|---:|---:|---:|---:|
| 主共同阶段+10ns | 320 | 0 | 2560 | 10 |
| 主TI或TA+1ns | 32 | 0 | 256 | 1 |
| 主TD+1ns | 66 | 3 | 1024 | 2 |
| 主MAC脉冲+1ns | 32 | 0 | 0 | 1 |
| 主刷新脉冲+1ns | 0 | 0 | 256 | 0 |
| 主完整写+1ns | 0 | 1 | 256 | 0 |
| fixed窗口+1ns | 32 | 0 | 256 | 1 |
| fixed内部MAC脉冲+1ns | 0 | 0 | 0 | 0 |

每次重新计算alpha、两路能力和RI。固定窗口仍拒绝超窗刷新脉冲。独立检查还覆盖两种控制策略、短点写主导guard、宽32输出、容量、临界/不可行、完整装载及U*。原PDF哈希与公共方法哈希按实际输入检查；量化服务由共同诊断脚本唯一生成，不在本例建立平行平台。

保留的实现条件是1/64ns脉冲、200fF前端及采样建立、写隔离后65ns建立和并行供流，以及400µs内符号读回的重复刷新稳定性。无噪声参考语义检查不证明噪声、保持尾部或全阵列错误率。未移植oxide或其他gain-cell身份，未调用NeuroSim/SPICE。
