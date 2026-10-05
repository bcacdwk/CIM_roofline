# 三维垂直 AND FeFET V5

状态：三情景真实新源码/构建/运行均为conditional，等待独立review。共同计算快照 `81880c5e60e9cb036319b4643cf859694da84f3d04d0f621fd3e2e51758038fc`。它保留四层垂直AND与32条真实横向通路，未以二维probe替代。

最终身份 `fenor3d_fourlayer_32lane_k128n16_active_mux2_v1`：K128×N16，4layer×32lane×128binarycol=16384cell；每次仅一个layer活动，每lane两64-column读组，总2048个data SA与同数参考。4096bit tilehold只保存一层32行，随后16路25bit数字单元完成128×8=1024次MAC，不免费安装32-input归约树。层数贡献容量，不直接乘吞吐。

三个有限成对点完全重合：rho=0.536013400 MB/s、tau=6.146458583 MB/s、RI*=0.087206868、U*=1.395309883；Δ=238.8 µs，完整T_R=333.2 µs。optimistic/reference/pessimistic是低/高阈值向外50/0/向内50 mV的工程敏感性包，幅度入口为源C2C已报告<50mV；没有材料分布，所以不称统计角落。20ns固定读pulse与200ns数字时钟掩盖了变化。三ID保留，圆图应显示退化点，不人为挪数据。

读采用FENOR-02阈值/电流量级与EKV1995连续前向减反向I–V，实际计算selected与三条unselected并联支路、共享SL电阻和真实负载；不是RRAM瞬态R=V/I。0.1V归一读点/n1.5/背景介电常数等是显式模型条件，原2026论文没有给独立VDS曲线；另一gate/state约9.12nA与0.307nA检查符合原图10nA/.3nA量级，不称唯一提取。native提供真实译码/MUX/VSA/DFF/数字；主动源跟随偏置/1.2MΩ参考以nativeIon/W/Vth、长沟道比例与明确body allowance计算，条件二元感测而非ENOB声明。参考20ns末margin12.76/11.43mV，高于5mV threshold+2mV误差预算；三包最小仍>10mV。

负WL与program isolation是固定SKY130 HV尺寸、锁定原始I–V/TT C/额定域支撑的有限端口块。8ns控制预算、隔离井与负域level translation是明确端口资格，未假称完整负电压levelshifter已逐管实现。源等效±2V/20ns写保持独立材料原语；新驱动/负载/回零另计。电源启动排除，偏置/瞬时电流条件公开。read最大|Vgc|1.328V，低于4/3V；有效20ns读窗口连同边沿约39ns暴露仍需要有限重复操作资格，不扩成长期无扰保证。native latch作阈值事件，之后输出相位保留，array偏置早释放；没有把<100ns RAWD变成额外材料常数。

Resident从任意旧二元状态开始，128个128-bit行依次完整RESET与target-mask PROGRAM，共256材料pulse；每行都读回整个4096bit layer的两个读组，再对当前128bit target比较。完整2048B只计一次，失败注入的payload为0。半选采用源Vw/3方案：selected WL±4/3、其他WL±2/3、目标BL/SL∓2/3、inhibit BL/SL±2/3；完整场±2V、最大halfselect4/3V。未选层的容量、电容、泄漏与扰动条件可见。

局部早期反例（gate0不是OFF、−2V会擦除、8layer相同bias泄漏分离失败）与P0/第二条EKV探针保留在非同步区；它们没有被包装为正式点。native面积为部分外围，HV端口、显式电容/参考与版图匹配不构成完整等面积宏PPA。

运行：`run_components.py --case fenor3d --scenario reference --run-id <unique>`。最终目录 `/Users/shine/neurosim/runs/step4-v5/component-services/case-fenor3d-fenor-final-{optimistic,reference,pessimistic}-r2-20261005`；小型权威输出在 `candidate_points.json` 与 `reference_snapshot.json`。来源/身份/输入/代码均由其哈希绑定。

独立review发现的128-bit写目标通路问题已修正：program_lanes从误用16逻辑Byte数改为128物理bit，原生targetmask实际128路；原16路候选不沿用通过。修后200ns时钟继续通过，三点数值不变。
