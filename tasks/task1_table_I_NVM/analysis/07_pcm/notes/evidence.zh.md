# PCM证据、工程桥接与复核

本轮只使用 `literature/07_pcm` 本地原PDF及共享基线，不检索新文献。PDF页序从1计。原值、选择、推导分开；原始PDF和共享参数/API的SHA256记录在 `data/results.json`。正式入口为 `tex/07_pcm.tex`，当前PDF经XeLaTeX构建后逐页渲染检查。

## 1. 主模式和组合电路

主模式：binary/SLC、8个权重平面、电压式近似ACIM；原生一次8条WL求和。256×128 INT8矩阵对应262144个PCM cell；原生BS=256Byte、bR=1Byte/weight。整矩阵不是一个原生写事务，BR=32Byte对应同一行的32个间隔列权重。

PCM03的8行电压求值与PCM01的32-IDAC波形不是同一个实测实现。主配置保留原生WL，采用PCM06支持的行并行原理、32个独立列电流驱动和列读写隔离。相同row的未选BL/SL等电位inhibit，其他row gate关闭；单行公共回流额定22.4mA，确保实际current compliance。原PCM01的对角接线只说明其自身避免共线拥挤的方法，不构成本配置的gate网络。资源和建立时间条件集中记录在第5节。

## 2. PCM-03：主读组织与尺度

原PDF：`literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf`，3页，40nm实测宏。

- p1正文、p2 Fig11.3.2：一次1bit输入施加到8条WL；8bit输入串行8拍。8bit补码权重为相邻5cell，最高2bit为2SLC，低6bit为3MLC；共享输入不是8bit原生同时乘法。
- 同图：列内固定IM经NBIAS形成电压VMAC_IN，SLC计数0…8、MLC0…24；后续原文VSR-VSA给4bit码并移位加法，8项19bit结果。这里选择纯SLC八个等尺度平面，保留8项组织；p2 Fig11.3.5纯SLC对应最大average signal margin，但本文不把它描述为整片纯SLC实测新模式。
- p1、p2 Fig11.3.4：VSR-VSA由2bit flash和电压重映射组成，四阶段包含先粗读、选择Vshift、电压稳定/耦合和再次比较。公共SAR替代量化路径，不能将其raw voltage code直接当整数部分和。
- 新前端配置每ADC通道9等级校准阈值/译码LUT，按所选列切换标定参数；第一TD完成并行等级译码+八平面位权合并，第二TD按输入bit累加。共128个并行译码通路、16个8路合并器、128个输出累加寄存器。该组合满足2/5/10ns所选TD是资源/时序条件，尚非综合结果。
- p1整体3.25–15.9ns；p2 Fig11.3.6 Shmoo正文0.95V、8bIN/8bW/19bOUT14.3ns。图像已直接渲染核对，图中0.95V约14ns，正文给14.3ns。不能以14.3/8反推单cell时间，也不能完整14.3ns额外叠加全部公共阶段。
- 工程选择F_A=10/20/50ns：F包含输入形成TI、局部复位、WL/列选择与电压建立；额外SAR TA和数字TD仍从共享JSON读取。这些是同量级预算，不是从完整macro拆出来的实测前端。API tm=F−TI（8/15/40ns）。原生8行是本参考拓扑选择，不是PCM材料只能8行。
- 8输入bit×32行组×8输出组=2048次求值、2048批ADC、4096数字拍；每批128 scalar codes，合计262144。8项有9类，不因共享有效8bitADC而假定能消除PCM类别内变异/电压等级重叠。

## 3. PCM-01：真实写资源、端态与长读验

原PDF：`PCM-01_2023_PCM64_Core.pdf`，25页作者稿，14nm IBM PCM。

- p7 Methods/Weight programming：门选择为对角线，目的为每BL/SL仅一个目标，避免电流拥挤；32 parallel current DACs，每个关联8条正极性SL和8条负极性SL（16 total）。虽然diagonal覆盖256cell，实际32SL并行，一次完整对角线需8cycles/极性/deviceID。不是256并行，也不是接口128bit保证128cell写。
- 同页波形：RESET pulse width125ns、700µA；SET pulse width250ns with trailing edge50ns、125µA。未见独立标时示意消除“250是否含50”歧义。主保守使用300ns，总250ns作为单项敏感性。无论哪种解释，50ns尾沿已计入波形，第三段g只从尾沿结束后开始做隔离/低读偏置恢复。
- 原文weight programming先RESET所有4PCM再按权重极性SET，ODP仅device1、TDP可两只，然后才对中间模拟目标调谐。本文仅借端态波形，不保留4PCM/unit-cell或ODP/TDP。
- p4和p14 Fig2a：单元SET/RESET分布。在63/64cores，超过99% unit-cell可达到 |GRESET|<5、GSET>50 ADCcounts，剩余core为98.4%。图示unit-cell SET为一个正PCM SET、其余RESET。说明端态大幅可分离，不能把unit-cell yield当本参考256cell事务良率，也不能把这两个码直接复制给不同ADC。
- p8 Methods：每次program后verify用0.2V、512ns PWM读和256ns预充电，因为单cell电导信号小。原CCO读值在pulse内生成，原文未声明这是纯器件响应。唯一组织对照将768ns保守保留为新弱信号前端预算，再顺序接入共享SAR完整TA和16路终点比较TD。原CCO被替换，没有额外计其转换；主binary路径改用同一电压CIM前端F_A。
- 768ns不是二进制必需时限。主预算明确采用同一IM/钳位/列负载及访问gate电平的binary终验；8行SLC读本来含q=1（一个SET、其余HRS）与q=0（全HRS/off），F_A要覆盖其最弱有效等级，不能只对八个SET有效。单cell选通后，未选支路泄漏/偏置差经专用两终态阈值标定，HRS/off端由钳位提供确定输出，列路径不浮动。于是主tV=F_A+TA+TD，每批重新执行F_A，不因binary凭空缩短源时钟或取零感测。若上述最弱码和负载兼容不成立，应改写FV并检查streaming q=0/1能否成立。768ns组织对照只是精细模拟弱信号的保守操作配额，占该对照写服务73.9%。
- p8连续模拟调谐：square125ns、125–700µA、error margin5ADCcounts或最多30iteration停止。不是固定离散MLC，也不是binary强制30次。超过迭代上限并不等于成功。本文不把5count窗转移为算法误差合同。
- p10 Power measurements：latency运行RTL得到；p18 TableI MVM-only133ns(1phase)/520ns(4phase)，包含原time-coded输入/ADC。它们没有匹配当前8行电压式结构，故不进入主DS，不称全部直接测量。
- p9 mapping给原ADC约100µA上限，饱和造成非线性。本文采用8项电压式IM偏置前端，没有偷把128个全SET电流同时加到该100µA CCO上，也不沿用该100µA作为新SAR硬规格；量程须由所选IM和9等级标定覆盖。

工程驱动资源：32电流IDAC总域；活动一平面，每IDAC4列mux；峰值RESET22.4mA、SET4mA。新增256bit事务缓冲、32mask/done位、plane/row/slot控制及专用电源、耐压路由。每program batch oneTD选通，3个g=10/20/50ns分别达到：RESET前目标电流建立、RESET后零电流quench/SET偏置建立、SET300ns尾沿完成后的readbias恢复。其数值不是晶体相变冷却常数，只是低于125–300ns主波形的有限工程余量。不是RRAM微秒HV预算。

二进制正常服务程序：每batch RESET1次+masked SET1次+最终2次新读验，最终检查全部32cell。HRS和SET阈值根据当前cell/读偏置/ADC标定，须保持分离并检查量程；不预设未经报告的绝对电导窗，也不保证unit current一致。成功cell的完整逻辑payload在8平面全部通过后提交。失败拒绝且BR不计成功；当前表是正常端态预算，未宣称批yield/最坏完成期限，不把失败尾部变成任意K。若实现在此两波形后经常失败，必须按实测补编程占用重估持续tau。

## 4. PCM-06与PCM-05：为什么可桥接及不借哪些量

PCM-06，8页，14nm IBM同技术生态，并非与PCM01完全独立工艺验证。

- p3 Fig3：60/120/240ns pulse-duration响应，G120是同幅度序列脉宽120ns时电导，不是单写完成120ns。不同cell最终状态分布宽，device-to-device相关性强；Fig4 cycle-to-cycle中间状态变异更大，端点可比。支持二状态粗端点与模拟精调的分离，也要求正文保留binary幅度变异。
- p4 Fig6：single row512columns，tile DAC控制共同VG，各列ILP独立duration；同时读用每列capacitor、comparator和shared ramp。1tick约1.2ns为输出duration编码，不能用1.2ns作完整read。
- p5 Fig7和正文：每pulse后read，FPGA计算error和下一轮per-cell pulse duration，可能用secondary conductance补偿overshoot；明确连续analog targets、not trueMLC discrete states。512并行必须具有512专用per-column路径，不由本例32-IDAC自动升级；FPGA等待也不是local PCM必需等待。

PCM-05，12页，独立Ge-rich GST器件/28nm FD-SOI相关工作。

- p3 §2.1：75ns SET/RESET，SET1.5V，RESET1.8–2.7V，selector gate0.8–1.2V用于不同compliance；read0.1V。全序列每compliance重复10次、总1000 programming pulses，得到75kΩ–2MΩ十状态。
- §2.2：25s漂移记录、每500ms采样，是测量时间，不是每次program等待。这里仅据75ns交叉确认传统GST端态波形在几十至数百ns量级；不将材料、电流、电压、1000次序列或SNN补偿结果导入本设计。

PCM-04材料亚ns及实验2ms间隔未用于本模型，没有从笔记转抄为数值证据。PCM02的512rowwise组织已由本例直接使用的PCM06解释；未重复计独立证据来源。

## 5. 原生映射、并行选通和完整计数

PCM-03 p3 Fig11.3.7明确256 rows×1024 columns/sub-bank；一个8-SLC/weight bank为K256/N128，32768B有效容量、262144cell。p2 Fig11.3.2/3的8WL活动与256输入分32组支持活动宽度，Fig11.3.5包含纯8SLC信号间隔对照。128ADC形成8:1列mux，每平面16ADC；输出需24bit。

物理列p=8c+w。主更新采用原生同row：compute WL选r，32个IDAC选c=4h+s，其他列BL/SL等电位inhibit，其他行gate关闭；八plane逐一服务。需要1024列外围读写隔离与plane路由、256条原生WL控制、每IDAC4列mux和22.4mA公共回流额定，不需要per-cell gate mux。PCM-06 p4 Fig6支持同row/每列独立程序原理，不引入512列资源；PCM-01的对角接线是该原芯片规避BL/SL拥挤的办法，不能自动嫁接本bank。32IDAC和波形仍作为明确跨实现资源锚点。F/g包含模式切换负载与回流电流合规条件，未称完成电路验证。

每事务32B：8program批，16次全新verify，无32槽模拟保持。1024个事务覆盖完整矩阵。

```text
DS=2048*(20+20+2*5)+2*5=102410ns
DR_local=3*5+8*(5+3*20+125+300+2*(20+20+5))=4655ns
TR=1024*4655=4766720ns
rho=256/DS=2.49975588321MB/s
tau=32768/TR=6.87432867884MB/s
RI*=0.363636363636;U*=TR/DS=46.5454545455=128*RI*
```

SET250ns总长的解释敏感性、g10/50ns独立扫描、768ns弱信号组织对照保留。主三情景固定32IDAC、125nsRESET及300nsSET波形；写范围较读范围窄，因为主要波形已固定，不能为扩大范围虚构重试。读侧F10/20/50ns是主要不确定条件。

## 6. 复核与外部审阅判断

实际执行原生容量/精度、完整行内列组覆盖、ADC verify路由、门控与半选条件、独立典型算术、完整TR及U*、source哈希与生成同步检查。SET尾沿只计一次。完整原access不能再叠入F+SAR+数字；主binary终验F必须覆盖q=0/1最弱码及同偏置/钳位/列负载，768ns保持为另一读验组织。

外部审阅重点为所选PCM栈一次端态程序、跨实现列隔离/当前驱动路由的可实现时序，以及最弱码binary终验。内部检查不代表用户验收。
