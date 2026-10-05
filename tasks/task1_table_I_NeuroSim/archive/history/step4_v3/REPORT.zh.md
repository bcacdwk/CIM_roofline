# Step4 V3：三个新的 NeuroSim 原生宏参考实现

三个新案例已完成阵列／外围求值、完整矩阵装载、实际新构建及独立复跑。**结果为条件性参考模型，读写服务均闭合；不是三颗旧特殊宏的复现，也不是硅签核。** 内部独立审查见 [审查结果](reports/review.json) 与 [复核说明](reports/review.zh.md)。本轮停止于 Step4 V3，等待用户及外部 ChatGPT 后续审阅；后者未参与本轮验收。

## 主结果与身份

三例共同为 **256×31 signed INT8**，输出容器25bit；B_S=256 Byte、B_R=7936 Byte。第32组 unsigned 权重用于常量1参考。全部采用请求间不重叠政策，表中单次延迟=Δ_S；保留原生内部流水。速率为十进制 MB/s。

|新 case_id／身份|后端，22nm/LSTP/300K|物理组织及主要资源|单次延迟=Δ_S ns|完整 T_R ns|rho MB/s|tau MB/s|RI*|U*|状态|
|---|---|---|---:|---:|---:|---:|---:|---:|---|
|ns_sram_acim：SRAM parallel ACIM|Training V2.1 `f80a4345f70d…`|256×256 bit；32个9bit SAR，MUX8；256bit写口|4546.744915|2008.288856|56.304016|3951.622783|0.01424833|0.44169816|条件性有效|
|ns_rram_1t1r：普通CMOS-access binary RRAM|Training V2.1 `f80a4345f70d…`|256×288 cell；32个10bit SAR，MUX9；32bit写口，288bit单行目标保持|10841.396653|470779.334776|23.613194|16.857155|1.40078171|43.42423304|条件性有效|
|ns_sram_dcim：专用 SRAM 数字CIM|DCIM V1.0-dev `38eedf926fc1…`|256×256 bit；64棵256-input/4bit树；4组64bit写外围同时工作|147.879789|2912.094308|1731.135821|2725.186468|0.63523573|19.69230769|条件性有效|

[完整JSON](results/reference-v3-reviewed-20261004/summary.json) · [CSV](results/reference-v3-reviewed-20261004/summary.csv) · [分阶段原始返回与诊断](results/reference-v3-reviewed-20261004/)。

ACIM不是旧9T1C电荷域结构；RRAM不是旧WH-2T1R双通路；DCIM不是旧D6CIM，也不是DRAM。旧完整服务时隙、5ns SRAM写／MAC、特殊码缩放及公共10μm门图没有进入V3输入。三个逻辑矩阵自然对齐，但资源、面积、校准及线模型不同，仍不能当作等面积或最优架构排名。

两族标签同为22nm/LSTP/300K，实际Vdd均0.85V。Training显式使用32nm wire参数，DCIM使用其22nm分支原生40nm金属及阻挡层模型。DCIM保留 `validated=true`，解析alpha=1.44、beta=1.4；这些开关只按源码实际分支消费，不给所有时间统一乘一个校准系数。Training没有同一套校准开关。派生数字周期分别为4.620307、4.253677、5.687684ns，没有5ns性能目标。

## 输入、映射与数值资格

SRAM器件宽度与几何来自锁定上游原生参数。RRAM采用锁定MLP V3.0 `DigitalNVM` 的小型参考包：Ron=8kΩ、Roff=24kΩ、access=5kΩ、read=0.5V、SET/RESET各1V及10ns、CMOS-access 4×8F。仅借该参考包的器件输入；读写仍在同一个Training Technology/MemCell/SubArray及外围对象上计算。它不是特定22nm实测RRAM材料包。1.1V access rail为显式Training接口条件，不能说所有字段均出自MLP器件实验。解析access宽3.454F可装入8F单元。

存储 u=w+128；输入 q=x mod256。两次完整8bit服务分别处理q和sign(x)（第二次低位为sign，其余位为0），获得A=Σqu、B=Σsign(x)u及参考输出C=Σq、D=Σsign(x)。三次有寄存25bit原生加减实现：

`y = A - (C << 7) - (B << 8) + (D << 15)`。

移位是连线。32组中31组是payload，第32组常量1。公共扩展仅为9:1输入选择器、控制DFF，以及原生Adder/DFF的符号校正与必要反相／广播驱动；没有免费CPU补结果。DCIM的64个nibble输出经32路原生24bit合并器，直接捕获到A/C或B/D独立operand bank，另一bank保持。NOR乘法明确采用 `NOR(~input, SRAM_Qbar)`；输入反相器计负载与时间，Qbar是既有SRAM互补节点，其NOR负载计入写翻转节点电容。

SRAM ACIM名义9bit ADC可容纳0..256计数；这不证明多WL稳定性、线性或9 ENOB。RRAM每8个数据列另有1个HRS参考列，256×288包括全部参考单元。名义ADC步长为 `(1/13000−1/29000)/2` S，half-up量化下，参考差值右移1得到整数计数；最大理想码928<1024。相同32个SAR与9:1 MUX用于求值和onehot读验。校准转移是必要条件，NeuroSim SAR本身只给电路时延／资源，不产生这条精度保证。

零、正负极值、抵消、混合和单点输入均实际执行位平面检查。独立reviewer另行穷举INT8标量乘积与(active,ones)理想码组合，并核对nibble/位容量；25bit中间值不溢出。它们验证映射与理想算术，不验证器件噪声、IR-drop精度或网络准确率。RRAM时延采用单选HRS最慢非零列RC包络，所有16个位轮次均预留完整时间，包括零注入位，不按稀疏数据跳过。

## 真正执行的模型与必要改动

统一入口只读本包与锁定上游。三例均经过Initialize→CalculateArea→物理路径／Latency；面积阶段产生的电容没有省略。实际调用和修改位置见 [来源记录](provenance/sources.json)、[路线说明](reports/routes.zh.md) 及规范补丁。

|类别|实际覆盖|
|---|---|
|原生阵列／外围|Training SRAM/1T1R SubArray的WL/SL、cell RC、MUX、SAR、ShiftAdd、SRAM写驱动／预充；DCIM SubArray专用NOR/AdderTree_DCIM、原生存储外围；Adder、DFF、Comparator、RowDecoder、Mux。|
|有来源的缺陷修正|Training SRAM access栅／漏负载；write DFF按写次数；逐输入位MUX／列建立正确计数；RRAM显式access值与真实列阻；DCIM初始化顺序、NOR PMOS类型、9/8浮点返回。|
|必要接口／写侧扩展|公共signed映射与真实输入选择；RRAM HRS基线减法、目标选择、双向大小Comparator＋OR/status等值验证；同技术V1.4 LevelShifter移植；DCIM同一SRAM组织上的覆盖写及已加载单元翻转。|
|外部原语／政策|RRAM二元电阻、两方向10ns脉冲、一次脉冲通过验证；稳定供电；本地端口、有限写批、读写互斥、请求不重叠及公开的原生DFF时钟抽象。|

Training逐输入位返回秒，8位只聚合一次；ADC/MUX/ShiftAdd内已有的次数不重复乘。逐组预充的SRAM也逐组计BL建立。首次WL/MUX选择允许并行，随后列组顺序选择；不能把MUX总成本无证据除以8。ShiftAdd保留原生内部隐藏规则，绑定实际感测窗口。DCIM先取得专用组合路径秒数，再按同步9周期unsigned服务聚合，最后只乘一次周期。输入选择流水填充、nibble合并和公共校正计入，共26周期。

V1.4的LevelShifter只移植相容的未校准电路路径，与Training相同tech/cell及实际gate load共用；未拼接另一运行的最终写数字。它的延迟仍使用低压Technology MOS公式，**不是独立校准的1V/1.1V器件模型或完整电源系统**。电源上电、charge pump及可靠性不在本地服务边界内。

## 两条服务、状态保持与瓶颈

输入数据在公开2048bit本地端口就绪后才进入计时的输入DFF；没有免费预装输入。输出以31×25bit寄存结果就绪为终点。SRAM完整覆盖写来自任意旧内容，256个物理行均写；相同数据也不跳过。SRAM公开256bit写口中的参考位由固定连线注入，仍占物理写资源。RRAM从32bit口按9个物理beat形成一行288bit目标缓冲，参考与编码占内部位/时间，logical payload仍是31 Byte/行。没有整矩阵shadow。

RRAM每行先RESET全部物理单元、onehot读验，再按目标mask SET、再次读验，最后释放单行目标缓冲。两方向各2304批，共4608个10ns槽；masked SET槽仍收费，固定dense目标实际有32000个LRS目标。两边沿合计9216个program控制更新；512次行验证×9组=4608个ADC轮次。预期码来自保留的行缓冲／RESET常量，经原生目标MUX和固定码连线；每lane两个大小比较器加OR判不等，不能把单个大小比较器直接当免费等值判断。

**RRAM compute-ready定义为held-read idle，而非全部WL关闭的中性状态。** 最后verify的ADC转换和status捕获已完成，读偏置稳定，最后onehot mask由WL控制DFF保持；program release已结束。下一次stream的首个原生DFF＋TG/实际RC mask-install同时清除旧行并设置新输入mask；下一次resident也先完成同样的完整选通／驱动建立，之后才进入编程脉冲平台。这里没有承诺额外的全关断release。连续读偏置的扰动、静态能耗和切换瞬态无毛刺保证未验证，属于该原生一阶状态更新抽象的适用条件。两路互斥使用阵列、端口与转换器，不承诺峰值同时达到。

SRAM写恢复由原生预充／选通路径计入；DCIM单行写包含capture、选通／退选、BL驱动、单元翻转、预充和编码。它实际只有3.062ns模拟写路径，但同一同步宏要等合法完成边沿，因此每行2个5.687684ns周期，256行共512周期。没有使用普通同尺寸SRAM的独立总写时间。

数值量级的原因很具体：ACIM每输入位的MUX decoder约188.879ns，而8组SAR合计80ns；两次完整8位服务成为读侧主体。其写侧主要是512次WL控制更新与256次端口捕获，cell翻转并非固定5ns。RRAM的低Ron输入使原生parallel MUX按 `(Ron+Raccess)/256` 尺寸化；同一大门负载MUX也用于验证，不能临时换成另一个快速读口。397.658μs读验比46.080μs器件脉冲更慢，解释了470.779μs装载。DCIM没有ADC列串行转换，主周期由公共25bit校正／广播路径限定；原生bit计算路径约1.197ns，所选公共周期仍须服务全部已装数字模块。

## 因果、独立性与复现

实际诊断分别改变相容尺寸／列数、线阻、访问器件、ADC码宽、写并行度和RRAM脉宽。读活动不污染同一完整装载；RRAM脉宽10→20ns只增加 `4608×10ns` resident时间；写并行度降低改变正确批次数。DCIM始终保持256×256，改访问负载／线阻和4→2写组；写批数与T_R倍增。ACIM的列数诊断保持每weight 8列，未用无法证明累加器生命周期的MUX16作为完整服务对照。部分电气变化只改变中间RC、未跨同步完成边沿，这不是输入未消费。

主运行：`/Users/shine/neurosim/runs/step4-v3/reference-v3-reviewed-20261004`。独立reviewer从不同路径重新复制锁定源码、新建二进制，并从只含本包、无旧results或legacy replay的独立包再次运行三例；另写检查器核算次数和总量。发现的负载、结果保持、输入极性、控制DFF面积及验证语义问题均修订后重构复核，记录保留在审查文件；过程／失败现场只在本地。本轮不默认重跑旧十例，也不要求新结果等于旧pilot。

`rho=B_S/Δ_S`，`tau=B_R/T_R`，`RI*=rho/tau`，`U*=T_R/Δ_S=31×RI*`。U*是装载—求值平衡阈值，不是workload实际复用率。本轮没有借旧值作性能输入或独立验证，也没有将架构／规模／资源差异统称为工具修正。

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v3/run.py --run-id my-v3-run --diagnostics --no-export
python3 -B tasks/task1_table_I_NeuroSim/step4_v3/run.py --case ns_sram_dcim --run-id my-dcim-run --no-export
```

默认本地根为NEUROSIM_ROOT或`$HOME/neurosim`，编译器为NEUROSIM_CXX或`/opt/homebrew/bin/g++-16`；可传`--root`／`--cxx`。每个新run-id建立独立快照和构建；已存在目录拒绝覆盖。`--export`只导出白名单JSON/CSV及哈希，不复制源码树、二进制或完整日志。也可将本包复制到本地无Git目录后运行；无需旧管理目录、旧结果或DNN数据。

历史step4/step4_v2/pilots、原NVM、Table II、论文、锁定上游及既有结果保持不变；仅追加任务根导航。不执行git add、commit或push。后续是否接受这些条件性参考配置由用户及外部审阅决定。
