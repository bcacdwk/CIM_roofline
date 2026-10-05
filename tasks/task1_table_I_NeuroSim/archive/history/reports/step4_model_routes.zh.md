# Step 4 器件—阶段—后端接入表

接入决策先于分派；依据 Step2 coverage 和已验收 Step3 V2。公共后端统一锁定 V1.4 `8a88abf85844c0e1ba17cc771ea535fff6040456`、22 nm/LSTP/300 K。以下为执行路线，最终实跑细节记入解析快照。

|案例|实际信号/阶段|公开模块与上下文|保留的原生边界|
|---|---|---|---|
|01/02/05 pilots|已验收电荷/数字/WH-2T1R 路线|原 Step3 V2 原样调用|原前端、D6 MAC、SRAM写、RRAM有限写验|
|03 NOR|二元读码保持→32项逐输入bit数字MAC；页装载|DFF、Adder/门级组合、formula 控制；无SAR、无SubArray|完整二元读、page program、sector erase；内部验证恢复已含|
|04 NAND|原生string/WL/SSL/BL/SL前端→SAR→仿射/合并/符号重构；格式化与校准|SarADC::Initialize/CalculateLatency、DFF、Adder/组合控制；未覆盖乘除保留明确算术预算|WL/BL/SL建立、完整页编程、块擦除；正负分存/base4/双符号相位不改|
|06 MRAM|互补2T2MTJ/IBMD读→保持/32项数字MAC；两相写与终验比较|DFF、Adder/组合比较控制；无SAR；MLP DigitalNVM仅机制参考|完整IBMD、方向写、互补两分支绝对状态读验|
|07 PCM|受限活动WL的voltage-mode前端→SAR→重构；单行端点读验|SarADC正常/验证共享；DFF、按本例位宽组合重构及控制|完整电压前端、32-cell电流批、RESET/完整SET与恢复|
|08 HZO FeRAM|1T1C破坏读/恢复/捕获→32项数字MAC|DFF、Adder/组合控制；无SAR；不采用Type::Cap|完整PL/BL读恢复捕获、外部极化写；未知原生负载不声称验证|
|09 GC-04|硅CMOS伪差分3T1C积分→SAR→解码；单pair刷新|SarADC正常/刷新共享；DFF、组合解码重构及控制|1ns/64ns积分分模式释放、完整current-programming与负载隔离|
|10 vertical AND FeFET|strip/layer二元读→保持/32项数字MAC|DFF、Adder/组合比较控制；不以Type::FeFET代替宏|原生选通/抑制、双相写、guard含最终返回、终验|

新增七例不调用 SubArray，不把逻辑K×N作为物理行列。数字模块的 MemCell 仅是构造上下文；执行只调用 area/latency 所需函数，逐函数核查 `cell` 字段读取。SAR 本轮只提供名义码宽对应的转换时间与模块实例，不调用依赖读电压/列电阻的功耗函数，不把其固定转换拟合当作模拟准确度验证。电压、介质负载、读写波形继续在有来源的原生服务中绑定，不用局部10µm数字线替换原生寄生。

每例从现有寄存与源保持推导路径窗口；32项数字MAC不继承pilot两拍资格。NAND未实例化乘除路径明确保持预算与时序未验证状态。5ns目标与向上0.5ns网格政策统一，物理前端不选择数字时钟。GC重新计算完整维护占用、非抢占guard与可行性，内部刷新payload为零。
