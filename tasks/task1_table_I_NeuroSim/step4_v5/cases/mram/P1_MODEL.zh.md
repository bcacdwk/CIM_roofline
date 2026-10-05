> 本文件保留逐步建立模型时的旧候选。最终硬件、偏置、MOS标定与阶段资格以 REPORT.zh.md、inputs.json 和 candidate_points.json 为准。

# MRAM P1 接入过程与旧候选记录（最终见 REPORT.zh.md）

本例已从 P0 的40nm实测读证据候选转为**完整公开参数包的模型参考**：UMEM 1.0.1，70nm×70nm CoFeB/MgO p-STT，65nm LSTP相容外围，普通1T1MTJ二元读和局部数字归约。不是MRAM-06的40nm、2T2MTJ、IBMD宏，也不是实测典型值。

主源为作者公开 `umem.va` 与手册§6/7/10.1 Fig10.3；锁在 `model.lock.json`，MIT来源保存在 `LICENSE.umem.txt`。原拟合来源Carboni2019原文已取得，70nm方形、室温、40ns–10μs脉冲和±0.15V沿上次写极性的读法均已核查。UMEM源码正电流驱向state−1/AP，而手册图/Carboni的正电压是AP→P；当前保留源码electrode convention，绝不据此宣称独立复现实验极性或WER。

`umem_port.py`逐式移植MRAM分支的非线性R(V,s)和dS/dt，程序参数只由`inputs.json`解析后传入。source的smoothmax/min名称与数学上限/下限相反，保留实际公式；软夹紧允许原始s略越过±1，未用真值裁剪。无热噪声、失败概率或真实温度统计。

为了检查普通1T访问，两方向BL/SL均限制0..0.6V、栅1.1V；采用与native低VDS电阻匹配的三端长沟道适配，包括反向source degeneration和native线电阻。它不是额外实测BSIM参数包，body effect等未标定。早期理想1kΩ访问在80ns可翻转；加入实际源电位后反向160ns仍失败，最终脉冲政策改为500ns/1μs/2μs并逐点检查。当前同一硬件，不声称三个材料角或概率分位。

八bank各64×64 cell，K=N64，共32768MTJ；每bank32SA、4条25bit更新通道，八bank读并行，共256SA/32输出更新lane。两个列组串行覆盖64输出。每次读一个binary weight tile后保持并复用8输入位。write采用全域32活动lane、单bank/单row/group，不允许八bank同时写；10mA共享额定条件明确。器件数、按bank安装的外围和全域活动数分开。

native以1kΩ目标自动给出74.885F访问管；64F宽初稿实际被拒绝，选择96F=6.24μm固定宽度后可放置。局部SL另设固定2μm×1μm上层金属strap，长度来自native实际row，ρ=2.2e−8Ωm为显式工程导体条件；其R和32lane最坏状态电流反馈进入求解。参考有独立同几何quiet return，不把thin signal wire或理想公共源线当免费供电；不是全芯片PDN验收。

读不是把R=V/I喂给native再采用恒流发展。真实前端积分同UMEM非线性电流、访问/线电阻和实际cap；每SA一条12kΩ参考电阻及匹配cap，5mV判别阈值加2mV有限offset/noise预算。两态最差预充误差±1%分别处理。reference在PRE期必须通过真实TG断地，否则分压会破坏0.1V初态；必须以最终公共隔离TG/驱动版本重跑，旧没有该门的候选不进入review或正式图。native VSA在阈值到达处抽象锁存，此后原生clock项为输出准备，并非继续让被动BL放电；这是公开模型层级，不能称晶体管级比较器再生或STA验证。

已执行作者诊断：65536个signed标量组合经实际两态决策和二补码位重构，无真值修正，0个算术不匹配；增加sense C使真实develop延长；双向pulse步长减半、160ns失败反例、固定正read的确定性长应力均留本地。诊断不等于独立review。最终review必须绑定最后公共修复与本例输入/代码hash，重新构建三点并独立核计数、回流、reference和失败服务。

正式计算没有旧06_mram性能、20/30ns access或legacy replay依赖。旧P0文件保留为路线演进记录；最终数值以统一入口的新构建结果为准。暂不在本文件写旧候选rho/tau，避免修复前数值被误用。
