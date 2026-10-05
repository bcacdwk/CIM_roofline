# HZO 1T1C FeRAM：三点已独立复核并内部验收

身份 `feram_hzo1t1c_HV130_k32n16_128restore_dwell100_v1` 保持11nm HZO、1µm²电容、二元剩余极化与破坏性读。K32×N16、4096个数据cell，另有128个线性参考电容及128个参考访问管；128SA、全128bit保持、128条实际恢复/外写路径，8个25bit数字lane。较小K用于容纳真实HV访问管寄生并维持约250fF源BL负载，不是旧K128快角。

|情景|完整写政策 ns|ΔS µs|TR µs|ρ MB/s|τ MB/s|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|---:|
|optimistic|14|133.904887|13.648|.238975594|37.5146542|.006370193|.101923091|
|reference|20|134.096887|13.840|.238633429|36.9942197|.006450560|.103208958|
|pessimistic|50|135.056887|14.800|.236937195|34.5945946|.006848966|.109583453|

14ns是原文完整write标签，20/50ns是同一Fig11通过区中选择的完整周期政策，均不是每极性材料脉宽。每128bit行只计一次完整外写或恢复；没有2×14ns、免费预写或4096路内部恢复。写周期同时受实际HV端口11.23ns保守预算约束，三个源周期均覆盖该预算。数字输入/arming guard主导装载，因此范围较窄；它只覆盖这一有限政策族，不覆盖工艺/温度/全部材料动力学。

原Fig10在2.5V、1µm²、250fF、100ns操作下的约.466/1.03V读点校准非切换与切换路径的极化/介电电荷。它们是滞回路径secant，不是两个可编程普通电容。实际native SA Cin与HV访问/线/附加C合成250.138fF，得到.46579/1.02966V，参考.74771V，最小单支margin约.282V，超过50mV感测加50mV误差条件。Fig12另一面积点只作独立电荷数量级检查，不证明快速kinetics。

采用明确额外保守政策：**新驱动已使实际bias稳定后再等待100ns**，之后启用native SA。源100ns原为整次观察条件；这里的额外dwell没有被称为材料时间常数、旧access或NeuroSim预测。实际译码、HV建立、native感测/保持仍单列；原生SA包含的1/f仅计一次。SA在合格电荷点锁存，随后输出相位不被当作继续积累极化电荷的测量窗口。

数据/参考与所有未选行的PL负载都计算：全局PL读电荷约96.18pC，完整写绝对电荷预算约373.86pC；未选cell串联寄生负载产生约.172V FE摆幅，低于声明.5V有限操作guard。真实SKY130 3µm/.5µm HV访问与N20/P7驱动提供I/C端口，native130nm/1.3V只承担低压译码输入、电压SA/hold和数字，不能替代5V访问或2.5V写驱动。

HV写P7预算使用**已表征VSG=2V操作点**，即2.5V source对应ON gate .5V、OFF gate2.5V；这种偏置控制属于外部HV端口的必要条件，不是把gate0时2.5VSG向下取整当作峰值。该操作点最坏并行源电流约230.16mA，要求本地2.5V/250mA能力；完整电平转换/控制波形与PDN不作晶体管签核。已有source-equivalent完整写原语在新负载/偏置组合上的适用性始终是条件性转用，不是新的实测宏保证。

每次物理激活先保存全部128bit，读后的数据状态标为未资格，再从实际hold完成整个128bit域恢复；即使外部输入为零或只用部分输出也不省恢复。32次激活共恢复4096bit，payload=0。外部resident从任意旧内容收取512Byte并完成32个全行写。恢复与外写共享同一128条路径及真实hold/target选择；没有全矩阵shadow。简单状态与故障注入检查确认丢一位即不能提交完整payload。

`candidate_points.json`、`reference_snapshot.json`、`diagnostics.json`包含三点、来源/条件、原生C/资源、阶段与完整hash。共同计算快照 `090bd4723ad86566350ac6dc4e9721a5d85af76b7fc4d052748c0e50bcd445fb`；三点分别在 `component-services/case-feram-feram-full-{optimistic,reference,pessimistic}-r1-20261005` 重新构建运行。复跑：

```sh
python3 -B '<V5绝对路径>/run_components.py' --case feram --scenario reference --run-id '<新的唯一ID>'
```

这是条件性参考模型：Q模型、有限读dwell与完整写原语支持机制/数量级比较，不支持快速FE动力学、全阵列yield、ENOB、STA或完整面积签核。B组独立三fresh与主导机制/计数审查已`PASS_conditional_model_scope`，supervisor按D035内部验收。见[独立审查](../../reviews/p3_feram/REVIEW.zh.md)。
