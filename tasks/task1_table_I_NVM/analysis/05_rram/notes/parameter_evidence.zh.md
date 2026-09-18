# RRAM 参数证据表

原值、参考选择与推导分开；从 `data/inputs.json` 生成。

| ID/来源 | 原值与单位 | 条件与定位 | 采用/换算理由 |
|---|---|---|---|
| E01 / RRAM-05 | 28nm；64×128 cell由4个64×32子阵列构成；32输入项；RHRS/RLRS典型100/10 kΩ；m=1的LRS约0.5 µA，HRS<30 nA | VTBL=0.1 V、VBL=0.3 V、VWL=0.6 V；3-bit空间权重、4-bit原读出；PDF p.3 Fig.3/4；p.4 Fig.7；p.7 Fig.16/17 | 仅取32项、二状态与m=1电流机制；八个等尺度位平面由本文选择；不把典型电阻当verify窗口 |
| E02 / RRAM-05 | PH0=5 ns；PH1–4各20 ns；4-bit输出access=66 ns；按5/1/1/1 ns估计优化access=13 ns | PH0电流稳定与漏电补偿；PH1–4比较和逐次参考扣除；测试板外部DAC提供偏置；PDF p.5 Fig.9/10；p.7 Fig.18及正文 | 5 ns作前端条件锚点；公共SAR替换完整量化功能，保留前端补偿与接口要求；66和13 ns均不作为8-bit公共转换周期 |
| E03 / RRAM-05 | memory模式以AX/AY选择cell，DIN/DOUT数据；CIM通路与memory通路解耦 | IO器件承受写电压，core器件用于CIM；未报告完整write/verify时间或128cell并行；PDF p.3 Fig.3(a)/(b)及D节 | 单域单cell顺序写p=1；共享128-bit口只缓冲128个编码bit |
| E04 / RRAM-03 | 28nm、1Mb；每SET/RESET后读比较阈值；大多数cell名义条件完成，数十cell需额外program；读扰测试10 ns脉冲 | 二状态P&V后HRS/LRS分布无重叠；不报告绝对SET/RESET/verify周期或重试分布；PDF p.5 E节及Fig.9；p.4 Fig.7 | 证明二状态也需独立终点/重试建模；不将10 ns应力脉冲当array access；不给K=1/2概率 |
| E05 / RRAM-06 | 40nm、2Mb；两个G0/G1组，每IO每组选一列；组内全done再推进；timeout报fail；时间轴归一化；99.2% page-write缩短 | HRPW先在idle RESET全页再SET所需cell；FORMING为另一步；无绝对page时长；PDF p.1 AF/ARST/ASET；p.2 Figs.3–10 | 仅作分组/自终止/hidden-RESET机制约束；不把99.2%当绝对写时间或省掉RESET；不移植并行数 |
| E06 / RRAM-01 | 130nm；SET初值1.2 V、RESET1.5 V、步进0.1 V；脉宽1 µs；read 1–10 µs；±1 µS；30次极性反转timeout；平均8.52脉冲；集成预测56 µs/cell | 差分多级；gmin=1 µS，gmax=30/40 µS；99%达窗；外部DAC/ADC控制限速；3轮重编程后至少30min再测推理；PDF p.10 Methods；p.11延续；Extended Data Fig.3在PDF p.18 | 只作时间层级与多级模式对照，禁止嫁接为本二状态28nm写周期；1 µs=1000 ns仅记录单位换算 |
| E07 / RRAM-02 | 28nm、576K；64 ADC；512输出需8轮；单cell verify；模拟program最多1000脉冲；32/128输入MVM相对误差1.14%/2.03% | 1T1R/2T2R/hybrid多级差分；速度按平均脉冲数比较；PDF pp.3–5 Figs.2–5；p.7 Fig.11正文 | 确认verify与计算资源可共用且较大fan-in有精度代价；不能据此令二状态RRAM-05的32项变128项 |
| E08 / RRAM-04 | 256 Byte buffer；tWC在50%翻转为8500/17000 µs典型/最大，100%为16000/25000 µs；SPI最高5MHz | 1.65–3.6 V，−40至85°C；CS上升启动NVM提交，WIP清零才结束；PDF p.9 WRITE；p.17 AC表 | 完整数字存储提交证据，与本地CIM单元分开；µs到ns乘1000；不能配本读侧给ridge |
| E09 / shared_baseline | 128×128 INT8；BS=128 Byte；8权重平面、每平面16ADC、16数字通道、每轮2拍；TI/TA/TD为2/10/2、5/20/5、10/50/10 ns | 共同28nm、0.9 V/25°C近标称参考，非实测PVT保证；顺序服务；shared_parameters.json common_conditions / reference_instance / selection_rules；tex/01、02 | 原样调用共享计算接口；唯一主读结构变化r=128→32；写p=1是媒体选择不是接口宽度 |
