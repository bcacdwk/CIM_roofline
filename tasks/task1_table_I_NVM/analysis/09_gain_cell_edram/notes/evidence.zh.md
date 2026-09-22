# Gain-cell eDRAM：证据、选择与复算边界

本地 PDF 页序从 1 开始。只使用本任务资料；没有检索、下载或改动原文。主模式是 GC-04 的 3T1C current-programmed 端点二进制伪差分 ACIM。它是以 65 nm 器件/宏为锚、接共同 28 nm 外围能力的条件参考设计，不是已测 28 nm 宏。PDF 输出六页，完整原值与工程桥接留本文件和 `data/inputs.json`。

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

## 2. 主模式工程桥接（不是原文实测）

1. **状态**：将GC-04的15级差分状态缩为两个端点±700nA，pair两支路一高一零。128×128×8bit×2cell=262144个3T1C cell。每权重16cell，逻辑payload只1Byte。不同于任意MLC round-to-nearest，此处只符号判决，零阈值理想距端点700nA。原ADC-LSB未转换为电流LSB；反复刷新不误判仍是需检验的条件。
2. **阵列/资源**：原64row负载，8权重平面同时工作；每平面2row groups×2本地64列组，合计32个64×64pair子阵列。每次16output选通，128个真实差分ADC；八平面共同表示矩阵，不是8份复制。128个pair write driver（256支路）提供同批更新；每driver最大目标700nA，合计目标89.6µA，粗写瞬态、replica source、局部select/level控制需资源。此供流数只为目标电流，不能当完整功耗。
3. **数字映射**：s=2b−1，64项z=Σxs范围−64…64，共129级，q=(z+Σx)/2。输入popcount每输入bit/rowgroup共享；16输出通道两拍包括偏移/缩放、8平面和输入bit重构、signed sign权重。ADC约8有效bit匹配129级，但模拟误差仍存在。
4. **专用读取占用**：100/150/200ns为工程槽，由原180ns完整宏周期支持量级，未伪装成原文提取的阵列响应。再加共享TI与真实TA，CA=112/175/260ns。原5bitADC没有替代共享10bit名义SAR；公共TA变化真实传播。
5. **单pair刷新读取**：MAC读脉冲1ns、单pair符号读64ns；同满幅积分电荷44.8fC，后者放进100/150/200ns dedicated槽，剩36/86/136ns。每支路有效C=200fF，包括位线、积分/采样适配后负载；ΔV=44.8fC/200fF=224mV，ADC差分范围至少±224mV；128×2支路总C=51.2pF。配0.9V预充时理想单支路最低约0.676V。C、脉冲、cap/ADC接入及隔离、noise/common mode必须验证；这不是原文示出的已测电路。编程时通过局部开关将新增积分/SAR采样C断开，写端BL+开关寄生需仍在原约50fF量级；重接与恢复在tm内。若200fF仍挂于写端，不得继续沿用65ns。更大有效C需重新调脉冲/增益和槽长，不能免费维持本预算。
6. **写与控制**：每16逻辑权重128pair、256支路控制bit，经128bit入口两拍（first在command）。电流幅值固定700nA，不能误计成256×3bit多级自由码。每事务控制两拍加额外数据一拍=3TD；P=65/65/75ns同时建立完整两支路，65包含5ns coarse+60ns fine。无需额外假造program/verify；状态失败和尾部不能靠隐形重试消除。
7. **刷新**：每ADC一路本地sign decoder，主模式128路、wide32为256路；它与16条MVM重构通道分开，一TD并行符号译码。1024group，每group CA+TD(sign decode)+3TD(control/data)+P，共短185/参260/长375ns。全矩阵189440/266240/384000ns，不使用原宏1.1%。所有131072pair均读、所有262144cell均写；Q_R不增加。
8. **固定刷新策略**：周期400µs、同一顺序、同一起点执行一整轮刷新。在每个预定刷新开始前G（最大不可中断计算或写组长）停止发新批，剩余数字状态寄存；预留每周期G=116/185/280ns最大空隙，只扣一次，避免“等当前批结束再刷新”造成超过400µs的cell间隔jitter。冷启动需先建立有效状态和固定刷新相位，本表仅稳态；cold整矩阵raw写占用可读results但不是维护后的每请求latency。
9. **no refresh credit**：定期全矩阵维护不因用户新写而跳过，是简单明确的控制策略而非介质必要限制。连续全矩阵new-write可以本身满足保持期限；随意局部更新不能替其它cell refresh。若换策略，应重新算竞争和两路availability，不照搬共同α。
10. **可行边界**：长点raw refresh384µs加guard0.280µs，α=3.93%。以其它长点参数不变，(1024+1)tm+179280<400000，即tm<215.34ns；200ns工程槽仅余约15.34ns/组，不能暗中再加64ns单行积分。若该电路条件不成立，长点应报不可行而非裁成小正数。

## 3. 原值、选择与推导分层

- 原值：GC-04 64×64pair、0–700nA、two-step write5ns、simulated60ns、measured65/75ns、whole compute180ns/5bADC、±7 retention0.4ms/99.7%/原ADC LSB；GC02/03/05各自条件保留在本节。
- 选择：共同28nm外围/0.9V近标称参考由共享JSON读；binary endpoint、16输出组、128diffADC/128pairdriver、100/150/200ns dedicated槽、1/64ns读pulse、200fF/branch、固定0.4ms全刷新与guard策略。
- 推导：32物理分片、262144cell；NE=NC=128，Ndig=256，16384scalar conversion；Nrefresh=1024；BR=16Byte，load256bit/2beats；原始服务、维护占用、α与成对指标由脚本生成。
- 结构对照：仅输出宽16→32、ADC128→256、pairdriver128→256，数字lane16保持，容量/状态不变。32Byte事务512bit需4数据拍，5TD+P；refresh512组。前端175ns保持是局部同负载预算条件，不等于自动验证扇出。

## 4. 参考手算与复现

参考：TI=5、TA=20、TD=5、tm=150、P=65，均ns。

- CA=5+150+20=175ns。
- CS=128×175+258×5=23690ns。
- CR=3×5+65=80ns，BR=16Byte。
- group刷新=175+5+80=260ns；全矩阵266240ns。
- G=175+2×5=185ns；α=1−(266240+185)/400000=0.3339375。
- rho=128×α/23690=0.0018043056GB/s；tau=16×α/80=0.0667875GB/s。
- RI*=(128/16)×80/23690=0.0270156184。
- 原始整矩阵更新1024×80=81920ns，按同样固定刷新预留的平均服务81920/α；不能把它当第一次cold load实测latency。

默认检查只读，`--emit`明确更新派生JSON/TeX。共享JSON/API哈希和5份原PDF哈希均检验；输入常数来自共享API，不复制公共公式。检查覆盖端点/signed映射、容量、物理并行、服务粒度、分组覆盖、refresh恢复量、周期可行、两路单位/配对和整矩阵聚合。PDF用XeLaTeX/ctex/Fandol编译并逐页渲染检查。构建/渲染临时文件位于本例build与tmp且被本例.gitignore忽略。
