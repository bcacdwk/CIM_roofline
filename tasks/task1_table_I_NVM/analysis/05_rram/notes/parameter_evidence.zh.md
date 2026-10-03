# RRAM 参数证据

原始PDF是证据，输入JSON保留原值与采用参数。局部切换和rail生命周期分开。

## E01 — RRAM-05

PDF p.3 Fig.3/4；p.4 Fig.7；p.7 Fig.16/17

原值：28nm；64×128 cell由4个64×32子阵列构成；32输入项；RHRS/RLRS典型100/10 kΩ；m=1的LRS约0.5 µA，HRS<30 nA；Fig.7(b)仿真使用LRS10%/HRS30%变化标准差

条件：VTBL=0.1 V、VBL=0.3 V、VWL=0.6 V；3-bit空间权重、4-bit原读出；RRAM-05为BEOL TaOx

采用：二状态与m=1读取；选择LRS8–12kΩ/HRS≥70kΩ为设计验收窗，原typ与仿真标准差不冒充保证界；计算需要电流可校准与HRS贡献受控，原文未证明8/12/70kΩ为计算充分界，memory可辨二态不单独保证MAC。

## E02 — RRAM-05

PDF p.5 Fig.9/10；p.7 Fig.18及正文

原值：PH0=5 ns；PH1–4各20 ns；4-bit输出access=66 ns；按5/1/1/1 ns估计优化access=13 ns

条件：PH0电流稳定与漏电补偿；PH1–4比较和逐次参考扣除；测试板外部DAC提供偏置

采用：5ns作读前端锚点；PH1 intrinsic5ns支持本地判决量级；binary完整sense用共同10/20/50ns能力预算，另计选通/建立；非SAR精度缩放

## E03 — RRAM-05

PDF p.3 Fig.3(a)/(b)及D节

原值：memory模式以AX/AY选择cell，DIN/DOUT数据；CIM通路与memory通路解耦

条件：IO器件承受写电压，core器件用于CIM；未报告完整write/verify时间或128cell并行

采用：memory电流SA与CIM读出解耦支持专用binary verify；采用128个实际列写驱动和256窗口比较器，需独立BL/SL路径、耐压和38.4mA供给，原文并未实测该资源配置

## E04 — RRAM-03

PDF p.5 E节及Fig.9；p.4 Fig.7

原值：28nm、1Mb；每SET/RESET后读比较阈值；大多数cell名义条件完成，数十cell需额外program；读扰测试10 ns脉冲

条件：二状态P&V后HRS/LRS分布无重叠；不报告绝对SET/RESET/verify周期或重试分布

采用：二状态阈值P&V支持一次及少量追加尝试情景；K为设计情景而非统计；10ns读扰脉冲仍不替代完整读回；未给出精确追加次数，也未给本窗的达窗概率。

## E05 — RRAM-06

PDF p.1 AF/ARST/ASET；p.2 Figs.3–10

原值：40nm、2Mb；两个G0/G1组，每IO每组选一列；组内全done再推进；timeout报fail；时间轴归一化；99.2% page-write缩短

条件：HRPW先在idle RESET全页再SET所需cell；FORMING为另一步；无绝对page时长

采用：借双group、独立mask/done和分组等待机制；每平面每group实际扩为8个列驱动，8平面×2group×8lane=128目标；显式RESET再SET并计全部RESET，不从归一化图取绝对时间；RESET较慢仅支撑非对称预算方向，不量化2/1。

## E06 — RRAM-01

PDF p.10 Methods；p.11延续；Extended Data Fig.3在PDF p.18

原值：130nm；SET初值1.2 V、RESET1.5 V、步进0.1 V；脉宽1 µs；read 1–10 µs；±1 µS；30次极性反转timeout；平均8.52脉冲；集成预测56 µs/cell

条件：差分多级；gmin=1 µS，gmax=30/40 µS；99%达窗；外部DAC/ADC控制限速；3轮重编程后至少30min再测推理；HfOx加TaOx热增强层，与RRAM-05的TaOx不同stack

采用：跨stack借用实际1µs波形；1–10µs读回保留测试层级，不压入本地binary主服务。8.52次/56µs、成功概率和G目标不移用；本LRS83–125µS高于其gmax，不能把相同1µs脉宽解释为该窗可达保证。

## E07 — RRAM-02

PDF pp.3–5 Figs.2–5；p.7 Fig.11正文

原值：28nm、576K；64 ADC；512输出需8轮；单cell verify；模拟program最多1000脉冲；32/128输入MVM相对误差1.14%/2.03%

条件：1T1R/2T2R/hybrid多级差分；速度按平均脉冲数比较

采用：保留32项主读分组；28nm最终SET幅度见E10；多级平均脉冲数不充当binary分布

## E08 — RRAM-04

PDF p.9 WRITE；p.17 AC表

原值：256 Byte buffer；tWC在50%翻转为8500/17000 µs典型/最大，100%为16000/25000 µs；SPI最高5MHz

条件：1.65–3.6 V，−40至85°C；CS上升启动NVM提交，WIP清零才结束

采用：完整数字存储提交证据，与本地CIM单元分开；µs到ns乘1000；不能配本读侧给ridge

## E09 — shared_baseline

shared_parameters.json common_conditions / reference_instance / selection_rules；tex/01、02

原值：Shared logical-byte/INT8/native-size policy;128bitencodedport,up to128realprogramtargets;16digitaloutputlanes

条件：Nominal28nmCMOS reference;resource qualification and full-cycle accounting

采用：K128N64,8fullnative64x128macros;32activeinputs;8parallelbitplanes×16ADC;actual128writeDRVs and256binary comparators are explicit additions,not inferred from input port

## E10 — RRAM-02

PDF p.7 Fig.8(b)

原值：最终SET编程BL电压约1.1–1.5V；插图WL约0.6–0.7V

条件：28nm、1T1R/2T2R/hybrid模拟编程，图为末次SET的分布而非binary完整波形

采用：与RRAM-01共同支持1V量级可调专用写域；不据图反推脉宽或循环次数

## E11 — 本文选择

adopted_inputs与configuration.write_resources

原值：128drivers,256binarycomparators;300uA/lane,total38.4mA;<=1pF switchedload/lane;railboundary1us+1us

条件：Dedicatedvoltage-ratedIO and regulatedsupply;eachlocalbiastransition50/100/250ns beforeprogram/afterprogram

采用：Separatefull-loadrail lifecycle from eachattemptlocal switching;1.8V/8kOhm225uA and1pFload yield24ns charge/headroom check,not measuredprogramcurrent or timing;16driver version is resource comparison
