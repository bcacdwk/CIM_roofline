# GC-04 3T1C eDRAM：原生64×64与周期刷新

[中文 PDF](output/gain_cell_edram.pdf) · [正文](tex/09_gain_cell_edram.tex) · [输入](data/inputs.json) · [结果](data/results.json) · [证据](notes/evidence.zh.md)

主模式保留GC-04的65 nm current-programmed dynamic-cascode 3T1C。原生64×64 pair负载用八个位平面编码K64×N64 INT8，4 KiB有效容量、65536 cell；端点(700,0)/(0,700)nA，每权重16cell。128差分ADC、16重构通道、128pair写驱动、单128bit更新接口固定，64个22bit输出。

| 正常情景 | 原始求值/16Byte写 (ns) | 全刷新 (μs) | 有用率 | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|---:|---:|---:|
| 短 | 1700 / 71 | 47.36 | 88.1% | 33.2 | 199 | 0.167 |
| 典型 | 3914 / 80 | 66.56 | 83.3% | 13.6 | 167 | 0.0818 |
| 长 | 6964 / 105 | 96.00 | 75.9% | 6.98 | 116 | 0.0603 |

主调度`early_release`复用CCTRL/PRE/SAMP及可调RWL，在1ns MAC或64ns单pair刷新积分结束后推进既有采样与SAR阶段；预充、选择、隔离回接/建立、隔离采样及恢复的36/86/136ns共同预算完整保留，另计公共TI/TA/TD。原180ns完整周期只作总量级锚点，没有强制MAC等待刷新64ns的物理依赖。按模式调度无需新增ADC、保持阵列、写驱动或shadow；这些时间仍是工程预算，并非实测分段时序或实测提速。

每400μs读取/符号判决/重写256组，各组16权重、128pair；仅保存当组128bit符号及256bit写控制，无全矩阵shadow。刷新前禁发最大71/122/217ns不可抢占组；短点guard由完整写主导。计算在转换与重构完成后暂停，输入和数字部分和保持。正常长点有303.783μs有用窗口，内部维护payload为零。

典型未取整ρ=13.6256719469 MB/s、τ=166.659 MB/s、RI*=0.08175779254。原始完整装载256×80=20480ns；周期长期完整装载平均T_R=24577.130548ns、平均向量间隔4697.016063ns，U*=5.23249872253=64RI*。它们是同周期稳态平均服务，不是任意到达相位的请求latency。16KiB仅辅助平均成本换算。

65ns完整写已含5ns粗写+60ns精写，75ns较长点含5+70ns；新增积分/SAR电容在写时隔离，保留原约50fF写负载。700nA×64×1ns及700nA×64ns均给44.8fC，200fF/branch对应±224mV差分量程；同满幅不证明相同噪声或建立。

名义10bit有符号码为−512…511、零码0，LSB=448/1024mV；每单位d产生3.5mV。普通整数部分和解码`qhat=(code+8*popcount+8)>>4`位于既有第一TD偏移槽，至少12bit临时值容纳在22bit重构数据路内，第二TD继续位权累加；不使用parity LUT或隐藏fractional位。共同诊断保留舍入前连续残差和正满幅裁剪，10bit名义无噪声服务、8ENOB量级与22bit输出宽度不混同。

`fixed_slot`另列保守控制对照：MAC保留64ns窗口、共同阶段与刷新不变。典型原始计算5930ns、guard185ns、alpha=.8331375，有效ρ=8.991703204、τ=166.6275MB/s、RI*=.0539629005。主调度相对其ρ为1.51536倍，τ微差来自guard；固定窗口不是必须的物理等待。

容量与资源对照使用主调度：K128×N128典型CS=15626ns、H=266240ns、guard122ns、alpha=.334095，有效ρ/τ=2.736731/66.819MB/s。大容量长点alpha=.0394575仅属临界压力；刷新专用前端216ns时H+guard=400617ns不可行，能力/RI*为空。宽32输出实际翻倍ADC/写pair驱动/sign decoder至256，CS=2122ns、guard132ns、H=34560ns，不混入主三点。

共享参数传播与九项有限扰动见[服务诊断](data/service_diagnostics.json)。独立计数检查覆盖计算、刷新、完整写、最大非抢占guard、alpha及两路能力，另核对容量/资源/压力与U*。数据检查不代替电路时序、噪声或重复刷新可靠性验证。

```sh
/opt/anaconda3/bin/python scripts/check_gain_cell_edram.py --emit
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

默认检查只读；图表与统一结果卡由公共导出唯一生成。
