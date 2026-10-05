# P3 两条独立物理前端的最小公共需求

本文件仅按FeRAM/GC-04路线卡读取形成；不复用V1.5 Cap或MLP _3T1C作为材料状态模型。P1/P2已适用的译码、选择、寄存/数字部分可共享，但电荷与电流源不能混成一个电容单元。

|边界|HZO 1T1C FeRAM|GC-04 硅 gain-cell eDRAM|
|---|---|---|
|case物理状态|二元剩余极化；两条极化/介电电荷分支及破坏读后的状态|10fF存储节点电荷/电压、HVT/LVT读支路、电流反馈写、保持时间与漂移|
|端口网络|PL、BL、WL/访问管、参考；解电荷守恒和plate驱动电流|SN、read BL、integration node、write BL/隔离；由状态相关I(V)积分与采样|
|native消费者|实际WL/PL/BL负载→相容选择/驱动/预充/二元感测/全激活域holding|实际RWL/BL/隔离/积分负载→选择/预充/采样、必要SAR/重构/寄存|
|写/维护|外部完整写与每次破坏读恢复分开；恢复整个128bit激活域|外部反馈写与周期refresh分开；refresh单行读电流不同于64行MAC，必须重算积分时间|
|必需资格门|PL电荷/电流预算、两状态margin、恢复前保持和所有状态覆盖|current-flat电压域、50fF写负载及隔离寄生、符号/保持窗口、实际每组写回间隔与不可抢占guard|

FeRAM示例的2Pr下界对应1µm² cell完整翻转>400fC；128路可超过51.2pC。不能只算250fF BL而省PL翻转电荷。2.5V访问/plate不是低压native工艺的默认能力；若同源14ns是完整polarization/writeback服务，必须按其真实包含范围保留，不能拆成每极性14ns后再叠加已含外围。需要独立于原校准面积点的电荷/负载检查。

GC-04保持易失身份。700nA×64×1ns/200fF=224mV的量纲关系是阵列设计检查，单行refresh要达到同摆幅需64ns；不能从普通MAC时槽复制refresh。65/75ns反馈写若是同50fF条件下完整服务，其已包含coarse write不再计一次。read/SAR负载必须在写时物理隔离且off寄生计入50fF。原400µs测量与FF/80°C仿真不能混成所有温度/全部cell保持保证；仅在作者明示的二元符号保持条件下检查刷新可持续性。

公共最小实现应有两个独立入口：`polarization_port` 返回Q分支/状态变化/PL&BL负载，`gaincell_current_port` 返回存储节点/电流/积分/隔离与age；它们分别接native外围。现有MLP没有SAR时可借锁定V1.4或Training的实际SAR模块，记录分支SHA/电压/码宽及其固定时延公式限制，不以“10bit容器”宣称10ENOB。

维护聚合在GC专用调度层完成：给raw单次物理服务、refresh工作/共享资源/guard/每组写回时间和长期有效能力；不能将raw/availability当真实单请求延迟。FeRAM恢复是每次破坏性read的组成工作，GC refresh是payload=0的独立周期工作，两者不得共用一个模糊maintenance比例。
