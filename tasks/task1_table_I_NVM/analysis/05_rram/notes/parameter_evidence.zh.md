# RRAM 参数证据表

原值、跨实现操作锚点与工程选择分开；从 `data/inputs.json` 生成。

| ID/来源 | 原值与单位 | 条件与定位 | 采用/换算理由 |
|---|---|---|---|
| E01 / RRAM-05 | 28nm；64×128 cell由4个64×32子阵列构成；32输入项；RHRS/RLRS典型100/10 kΩ；m=1的LRS约0.5 µA，HRS<30 nA；Fig.7(b)仿真使用LRS10%/HRS30%变化标准差 | VTBL=0.1 V、VBL=0.3 V、VWL=0.6 V；3-bit空间权重、4-bit原读出；RRAM-05为BEOL TaOx；PDF p.3 Fig.3/4；p.4 Fig.7；p.7 Fig.16/17 | 二状态与m=1读取；选择LRS8–12kΩ/HRS≥70kΩ为设计验收窗，原typ与仿真标准差不冒充保证界 |
| E02 / RRAM-05 | PH0=5 ns；PH1–4各20 ns；4-bit输出access=66 ns；按5/1/1/1 ns估计优化access=13 ns | PH0电流稳定与漏电补偿；PH1–4比较和逐次参考扣除；测试板外部DAC提供偏置；PDF p.5 Fig.9/10；p.7 Fig.18及正文 | 5ns作读前端锚点；PH1 intrinsic5ns支持本地判决量级；binary完整sense用共同10/20/50ns能力预算，另计选通/建立；非SAR精度缩放 |
| E03 / RRAM-05 | memory模式以AX/AY选择cell，DIN/DOUT数据；CIM通路与memory通路解耦 | IO器件承受写电压，core器件用于CIM；未报告完整write/verify时间或128cell并行；PDF p.3 Fig.3(a)/(b)及D节 | memory电流SA与CIM读出解耦支持专用binary verify；不再把逐cell完整SAR当物理要求；本设计新增明确的16lane资源 |
| E04 / RRAM-03 | 28nm、1Mb；每SET/RESET后读比较阈值；大多数cell名义条件完成，数十cell需额外program；读扰测试10 ns脉冲 | 二状态P&V后HRS/LRS分布无重叠；不报告绝对SET/RESET/verify周期或重试分布；PDF p.5 E节及Fig.9；p.4 Fig.7 | 二状态阈值P&V支持一次及少量追加尝试情景；K为设计情景而非统计；10ns读扰脉冲仍不替代完整读回 |
| E05 / RRAM-06 | 40nm、2Mb；两个G0/G1组，每IO每组选一列；组内全done再推进；timeout报fail；时间轴归一化；99.2% page-write缩短 | HRPW先在idle RESET全页再SET所需cell；FORMING为另一步；无绝对page时长；PDF p.1 AF/ARST/ASET；p.2 Figs.3–10 | 采用每IO双group、独立mask/done及分组等待机制，8位平面×双group选择16lane；显式RESET再SET并计全部RESET；不从归一化图取绝对时间 |
| E06 / RRAM-01 | 130nm；SET初值1.2 V、RESET1.5 V、步进0.1 V；脉宽1 µs；read 1–10 µs；±1 µS；30次极性反转timeout；平均8.52脉冲；集成预测56 µs/cell | 差分多级；gmin=1 µS，gmax=30/40 µS；99%达窗；外部DAC/ADC控制限速；3轮重编程后至少30min再测推理；HfOx加TaOx热增强层，与RRAM-05的TaOx不同stack；PDF p.10 Methods；p.11延续；Extended Data Fig.3在PDF p.18 | 跨stack借用实际1µs波形；1–10µs读回保留测试层级，不压入本地binary主服务。8.52次/56µs、成功概率和G目标不移用 |
| E07 / RRAM-02 | 28nm、576K；64 ADC；512输出需8轮；单cell verify；模拟program最多1000脉冲；32/128输入MVM相对误差1.14%/2.03% | 1T1R/2T2R/hybrid多级差分；速度按平均脉冲数比较；PDF pp.3–5 Figs.2–5；p.7 Fig.11正文 | 保留32项主读分组；28nm最终SET幅度见E10；多级平均脉冲数不充当binary分布 |
| E08 / RRAM-04 | 256 Byte buffer；tWC在50%翻转为8500/17000 µs典型/最大，100%为16000/25000 µs；SPI最高5MHz | 1.65–3.6 V，−40至85°C；CS上升启动NVM提交，WIP清零才结束；PDF p.9 WRITE；p.17 AC表 | 完整数字存储提交证据，与本地CIM单元分开；µs到ns乘1000；不能配本读侧给ridge |
| E09 / shared_baseline | 128×128 INT8；BS=128 Byte；8权重平面、每平面16ADC、16数字通道、每轮2拍；TI/TA/TD为2/10/2、5/20/5、10/50/10 ns | 共同28nm、0.9 V/25°C近标称参考，非实测PVT保证；顺序服务；shared_parameters.json common_conditions / reference_instance / selection_rules；tex/01、02 | 共同逻辑/读ADC/数字预算不变；读r=32；写并行由16个驱动/双组寻址给出，非128bit口 |
| E10 / RRAM-02 | 最终SET编程BL电压约1.1–1.5V；插图WL约0.6–0.7V | 28nm、1T1R/2T2R/hybrid模拟编程，图为末次SET的分布而非binary完整波形；PDF p.7 Fig.8(b) | 与RRAM-01共同支持1V量级可调专用写域；不据图反推脉宽或循环次数 |
| E11 / 本文选择 | 16lane、32binary比较器；每lane限流300µA、总4.8mA；每次HV建立/回读各1µs；两目标验收窗；binary完整sense时隙10/20/50ns、另计选通和5ns建立 | 8位平面×双组，2计数器和独立mask/done；1.8V/8kΩ=225µA只作额定电流量级检查；1.8V需独立耐压I/O/电平转换，原core0.8V/IO1.2V测量不提供耐压证明；adopted_inputs与configuration.write_resources | 补齐可审查资源及HV恢复预算，明确工程选择；不把欧姆比值声称为RRAM动态编程电流测量 |
