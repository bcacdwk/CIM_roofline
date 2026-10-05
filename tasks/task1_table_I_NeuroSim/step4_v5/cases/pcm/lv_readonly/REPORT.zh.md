> **独立复核后状态更新：以下三点已撤回，不能用于正式图表。** 未感测BL历史与初始clear正在修后新跑；post-program高压return/read isolation尚未闭合，resident当前为blocked。旧数字仅留过程审计，当前资格见candidate_points.json。已启动唯一有来源HV端口替代probe，尚无完整tau通过。

# PCM P1：三个完整成对候选，待独立复核

状态为 `ready_for_review`；三点均已从同一规范代码/输入快照独立新构建、新运行，机器资格为 `conditional / not_reviewed`，不代表独立验收或实测芯片保证。正式入口是 [inputs.json](inputs.json)、[case_adapter.py](case_adapter.py)、[adapter.py](adapter.py)；机器小包 [candidate_points.json](candidate_points.json) 与 [reference_snapshot.json](reference_snapshot.json) 保留全哈希、阶段、资源和物理门。

## 身份和数值

新实现采用 Ti₀.₄Sb₂Te₃ 普通 1T1R 二元位平面、单行感测和本地 signed INT8 数字运算。K=128、N=16，B_S=128 B、B_R=2048 B，16384 个数据单元；64 SA 分两组，16 路实际编程电流源，128-bit 权重保持与独立目标保持，16 个25-bit输出。材料来源是40nm器件；外围是45nm LSTP、1.0V、300K的重新设计，8µm列pitch容纳实际7.077µm访问管，并非40nm实测宏的面积。

| 同硬件有限脉宽政策 | RESET / SET (ns) | Δ_S (µs) | T_R (µs) | ρ (MB/s) | τ (MB/s) | RI* | U* |
|---|---:|---:|---:|---:|---:|---:|---:|
| optimistic | 10 / 100 | 259.7250 | 434.8825 | 0.492829 | 4.709318 | 0.104650 | 1.674396 |
| reference | 20 / 200 | 259.7250 | 547.5225 | 0.492829 | 3.740486 | 0.131755 | 2.108085 |
| pessimistic | 100 / 1000 | 259.7250 | 1448.6425 | 0.492829 | 1.413737 | 0.348600 | 5.577601 |

这是来源支持的脉宽平台区中的三种操作政策，不是统计典型、概率边界、同芯片PVT或热角。固定资源与读条件意味着ρ相同；不为图形制造读侧变化。U*=16RI*是装载/求值平衡阈值。

## 读出、资源与完整生命周期

程序保持源论文的0.5mA RESET和0.2mA SET，按16路覆盖：每方向1024批，SET只使能目标1，但所有批次保留时隙。每行全部完成两阶段后，使用同一实际64-SA读口分两组读回128bit并与目标比较；全矩阵共256个verify组。失败耗尽单次预算就结束，整个矩阵不计成功payload。原生零写返回从未作为程序完成；每个控制RC、原语、终验和状态提交分开。

原论文 Fig.6 的 PULSE_SET 与 RESET 跨器件分布存在重叠，正文低阻范围不能误作脉冲SET总体分布。因此本例使用明确的已表征工作端态条件：名义10kΩ/500kΩ，读检查覆盖所声明的端态窗口。**现场单阈值binary verify只检错位，不在线测量或认证20kΩ/200kΩ窗口。** 没有良率或随机重试概率。

每SA有独立40kΩ参考、实际隔离开关及按寄生扣除后实现的匹配电容。参考和数据在预充时断开；原生低读rail NMOS预充、数据WL开关、reference匹配enable replica和额外1.688pF匹配负载均计入。参考/数据名义enable边沿相同；共同source RC模型进一步实际计算±1ns/零skew × 四种端态负载组合。共同发展3.9696ns后最弱侧达到15mV。10mV感测目标及5mV总误差预算是工程资格，NeuroSim不预测offset、噪声或BER；±1ns不是测得的jitter分布或STA保证。

写电流要求不能由读电阻替代：实际native访问管额定Ion约3.54mA；独立100Ω程序TG与5250Ω读MUX分离，强程序TG关断的13.008fF寄生仍进入实际380.877fF读节点。原先按128行并流定尺寸的单行MUX已作有范围的修正，R/W/C、信号、驱动和面积共同重算。

上层source网含128 data +64 reference支路，各128µm、2µm×1µm；1536µm汇流条20µm×2µm。工程Cu等效电阻率2.2e−8Ωm给local1.408Ω、shared0.8448Ω。16路0.5mA写的source压降7.4624mV，读的保守共同source压降上界约1.117mV；43.280fF/column几何耦合实际进入native负载。原细row产生81.92V而被否定。程序驱动还需在约0.947V路由压降之外提供源材料实际端子波形所需的合规电压；`write_port=1V`不等于已提供完整热写电源。

每行一次读捕获后，128bit权重保持服务8个输入bit、两输出组，合计2048次8-lane25bit更新。零输入mask、符号加/减选择、分组旧状态保持、输入与目标分beat接收、verify归约/状态均有实际外围资源。80ns完整数字更新周期满足完整case组合路径37.375ns≤40ns半周期；native DFF半拍不是连续launch间隔。bit选择在MAC路径内，不再另收一遍周期。

## 主导路径和证据范围

参考 streaming 约63.1%在完整时钟数字更新，24.8%在二元读前端，7.9%在权重保持。Resident约41.1%在RESET/SET波形、29.9%在每批程序mask/控制接收、11.8%在最终读验，其余为选择、路由、比较和提交；没有将旧完整读写时隙接回计算。

[Song等原始论文](https://doi.org/10.1007/s40820-015-0030-z)支持同材料电流脉冲和有限端态条件。论文未分别定义边沿/冷却或新阵列的合规电压；本模型保留报告的不可分脉宽，并要求电流引擎复现源端子波形及其quench/恢复条件，不伪造额外材料时间。若实际引擎不能满足，这些点不适用，不能靠低压读R推算热写或补一个无来源等待。

0.2V非破坏读、端态在完整装载及后续本地求值期间保持、感测总误差预算和source-equivalent程序端口是明确条件。模型支持这些条件下的本地两路服务及有限政策比较；不支持总体yield、长期漂移/重校准间隔、实测准确率、完整宏面积或硅签核。原生面积不含已列账但尚未版图签核的参考被动件、上层电源网和电流源。旧案例是256×128、八行电压求和与其他PCM波形；身份、规模、精度链和后端均不同，数值变化不能统一称作工具修正。

## 可复跑与审核

```sh
python3 -B '/Users/shine/Library/CloudStorage/OneDrive-个人/Files/02 Works/202609-ISCAS2027-Roofline/tasks/task1_table_I_NeuroSim/step4_v5/run.py' --case pcm --scenario reference --run-id pcm-review-new-id
```

将scenario改为optimistic或pessimistic，各用新run-id。正式候选目录为 `/Users/shine/neurosim/runs/step4-v5/p1/case-pcm-pcm-author-final-{opt,ref,pess}-20261005/`；每个目录有规范快照、native独立源码/构建链接、实际解析参数、资源、阶段、数值/状态诊断与结果。源文件哈希见机器小包。全部旧失败与已撤销候选保留在同一非同步P1运行根。B组从新目录独立复跑后才能提升资格。
