# PCM证据、工程桥接与复核

本轮只使用 `literature/07_pcm` 本地原PDF及共享基线，不检索新文献。PDF页序从1计。原值、选择、推导分开；原始PDF和共享参数/API的SHA256记录在 `data/results.json`。正式入口为 `tex/07_pcm.tex`，五页PDF经XeLaTeX构建后逐页渲染检查。

## 1. 主模式和组合电路

主模式：binary/SLC、8个权重平面、电压式近似ACIM；原生一次8条WL求和。128×128 INT8矩阵对应131072个PCM cell；共同BS=128Byte、bR=1Byte/weight。整矩阵不是一个原生写事务，BR=32Byte对应32个非连续对角权重。

PCM03的8行电压求值与PCM01的32-IDAC对角编程不是同一个实测实现。参考电路为每cell访问管配置模式gate mux，选择输入WL门控或其所属对角线门控；两套栅线分开，经mux/电平转换选择，未选平面关闭。外侧模式开关隔离电压MAC前端和program电流IDAC。因此不是将不相容的两种gate布线直接相连。所需128条输入行/128条对角门控网络、每cell mux、电平转换、plane-select、IDAC至SL路由、16ADC/plane的verify列mux都须实际存在。没有面积等价主张，也没有声称完成新芯片设计。读前端F及写驱动g涵盖这些寄生下的目标建立时间。

## 2. PCM-03：主读组织与尺度

原PDF：`literature/07_pcm/PCM-03_2022_Hybrid_SLC_MLC.pdf`，3页，40nm实测宏。

- p1正文、p2 Fig11.3.2：一次1bit输入施加到8条WL；8bit输入串行8拍。8bit补码权重为相邻5cell，最高2bit为2SLC，低6bit为3MLC；共享输入不是8bit原生同时乘法。
- 同图：列内固定IM经NBIAS形成电压VMAC_IN，SLC计数0…8、MLC0…24；后续原文VSR-VSA给4bit码并移位加法，8项19bit结果。这里选择纯SLC八个等尺度平面，保留8项组织；p2 Fig11.3.5纯SLC对应最大average signal margin，但本文不把它描述为整片纯SLC实测新模式。
- p1、p2 Fig11.3.4：VSR-VSA由2bit flash和电压重映射组成，四阶段包含先粗读、选择Vshift、电压稳定/耦合和再次比较。公共SAR替代量化路径，不能将其raw voltage code直接当整数部分和。
- 新前端配置每ADC通道9等级校准阈值/译码LUT，按所选列切换标定参数；第一TD完成并行等级译码+八平面位权合并，第二TD按输入bit累加。共128个并行译码通路、16个8路合并器、128个输出累加寄存器。该组合满足2/5/10ns所选TD是资源/时序条件，尚非综合结果。
- p1整体3.25–15.9ns；p2 Fig11.3.6 Shmoo正文0.95V、8bIN/8bW/19bOUT14.3ns。图像已直接渲染核对，图中0.95V约14ns，正文给14.3ns。不能以14.3/8反推单cell时间，也不能完整14.3ns额外叠加全部公共阶段。
- 工程选择F_A=10/20/50ns：F包含输入形成TI、局部复位、WL/列选择与电压建立；额外SAR TA和数字TD仍从共享JSON读取。这些是同量级预算，不是从完整macro拆出来的实测前端。API tm=F−TI（8/15/40ns）。原生8行是本参考拓扑选择，不是PCM材料只能8行。
- 8输入bit×16行组×8输出组=1024次求值、1024批ADC、2048数字拍；每批128 scalar codes，合计131072。8项有9类，不因共享有效8bitADC而假定能消除PCM类别内变异/电压等级重叠。

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

工程驱动资源：32电流IDAC总域；活动一平面，每IDAC4列mux；峰值RESET22.4mA、SET4mA。新增256bit事务缓冲、32mask/done位、plane/diagonal/slot控制及专用电源、耐压路由。每program batch oneTD选通，3个g=10/20/50ns分别达到：RESET前目标电流建立、RESET后零电流quench/SET偏置建立、SET300ns尾沿完成后的readbias恢复。其数值不是晶体相变冷却常数，只是低于125–300ns主波形的有限工程余量。不是RRAM微秒HV预算。

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

## 5. 映射与完整计数的复算

令d=0…127、s=0…3、h=0…31。c=4h+s，r=(c+d)mod128；32权重位置跨8平面顺序写。每batch32cell且不共row/column。16ADC按8列一组，pass k=0/1选择c=8a+4k+s，a=0…15，重新做完整F_A/reset/read/ADC/compare。无32槽hold。

每位置唯一d=(r−c)mod128、s=cmod4、h=floor(c/4)，全矩阵512事务覆盖16384权重。脚本遍历所有事务并检查无重复覆盖，显式保存参考事务各plane/batch/verify坐标。主/弱信号对照保持32IDAC和16ADC不变，program批8、verify批16；无跨批模拟保持。

正常reference：

- DS=1024×(F20+TA20+2TD10)+boundary10=51210ns。
- front=3TD=15ns；8batches each [select5+3g60+RESET125+SET300+2×(F20+TA20+TD5)] =8×580ns。
- DR=4655ns；tau=32/4655GB/s=6.874328679MB/s；rho=128/51210GB/s；ridge=4DR/DS=0.363600859。
- 全矩阵DR=512×4655=2383360ns=2.383360ms，字节同比，tau不变。
- 写分解：front15、batch-select40、g480、RESET1000、SET2400、binary front320、SAR320、compare80ns，总4655。
- 配对short/reference/long：DS24580/51210/122900ns，DR4014/4655/6470ns。主配对ridge0.210578…0.653214不是总体材料界；rho0.0010415…0.0052075GB/s，tau4.9459…7.9721MB/s。
- 唯一弱信号组织对照tV=768+TA+TD，DR16623ns、tau1.925044MB/s、ridge1.298418，读侧完全不变。增量16×(768−20)=11968ns，main写由脉冲73.0%主导，对照写由weakread73.9%主导。
- SET总250ns敏感性DR4255ns、tau7.520564MB/s、ridge0.332357，作为波形歧义记录而非额外结构情景。

## 6. 待主审点与验证

两个主要假设：端态波形在所选binary cell/驱动上的正常一次完成条件；同一IM/钳位/列路径对binary终验最弱q=0/1状态的建立覆盖。原768ns仅为保守模拟组织对照。八行组织是明确主实现选择，32IDAC/16ADC导致每plane两次重读。扩为128行、用MLC、增加并行平面写或采用512rowwise必须重新说明电路与状态，不能只替换分母。

构建前检查共享API及JSON哈希，源PDF哈希与manifest一致。默认check不写文件；import关闭pycache，未修改共享目录。检查generated数据、单位、BS/BR粒度因子、SUM stages、PCM cell数、ADC路由及全矩阵唯一覆盖。文件编译为ctex/Fandol XeLaTeX；渲染图仅在ignored tmp。长期漂移维护/耐久不伪装成当前瞬时tau；未向主论文或共享TableI写值。

## 本轮统一复核

回查 PCM-01 PDF pp.7–8 的32 IDAC、对角选通、125 ns RESET、250 ns SET及50 ns尾沿措辞、512+256 ns弱信号读验；回查 PCM-03 PDF pp.1–2的八WL电压求和和完整access。保留完整SET/RESET与主二态终验、弱信号组织对照，不将原模拟30次精调搬到二态写。

统一入口明确32 Byte是对角选通的32权重组，512组一一覆盖16 KiB矩阵。低ridge部分源自八行组织造成1024轮streaming和较小ρ；不能据其单独推断动态工作负载适配。三档外围与驱动预留只是条件配对，移除不兼容端点交叉外包络。固定参考外围仅改变g=10/50 ns的独立对照为DR=4415/5375 ns、τ=7.24802/5.95349 MB/s、ridge=0.344854/0.419840，ρ保持2.49951 MB/s；g仍是工程余量，不是实测材料热恢复时间。
