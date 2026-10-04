# Step4 V2 执行接口 2.0.0

冻结输入/输出3.0.0与Step3时序2.0.0不改。`step4/` 与旧入口完整保留；V2使用 `step4_v2/` 和 `scripts/run_step4_v2.py`。原生参数、资源、编码、数字网络与计数保持；本轮修正窗口资格、早稳来源、捕获边界及来源表达。

- `backend.build(case, root, out, cxx, own)` 返回可实际执行的函数；同V1参数与锁源规则。路径保存launch/capture/available_cycles、required_period、实际负载和稳定源。
- PCM/GC完整数据图E0→E2，E1仅phase；独立capture-enable E1→E2单拍。没有中间bank或提前释放。四个二元数字MAC保持单拍，早稳input/group在原生read期间建立，first weight/ibit/accumulator仍受单拍约束。
- `adapter.build(case,p,b)` 返回streaming/resident/maintenance有序模板。`digital`是完整周期型操作，`cycles`乘实际周期，入口margin必须0；目的setup已在组合路径。`boundary`仅采样/发布，在原物理完成时刻加一次实际setup后选边沿，不再加周期；原生已含捕获或纯ready标记不重复setup。
- `repeat/steps`只是有序容器，包装不得提前消费/取整。纯注释wrapper用repeat=1，不能插入一个有边沿消费含义的boundary冒充透明wrapper。
- NOR/FeNOR operand_capture和MRAM/FeNOR terminal capture由旧一tick预算改为实际边沿采样；MRAM operand_capture有capture+IBMD isolation/reset的来源，保留完整1cycle。FeRAM native read已经含capture/restore，保留完整。
- 时钟只由已资格路径决定；四例早稳信号先验证源pin建立时间在原生read可用窗口内，不把read时长从整个MAC路径减掉。无法满足该前置条件则拒绝此资格。
- 阶段来源分为direct_neurosim_module、neurosim_gate_composition、retained_native_or_arithmetic_service、interface_and_schedule。数字周期是声明拓扑/边界下的调度成本，DFF计时不独立认证整条路径。禁止按阶段数量做覆盖率。
- NAND可通过backend快照的retained_affine_budget_scale与retained_calibration_budget_scale进行少量预算对照；默认1，仅放大非零保留算术占用，不改工作周期、公开模型、阵列参数或资源。
- GC重新计算busy/guard/availability；单次raw物理服务与长期effective成本分开，不可行返回null。

GC刷新采用不超过原保持限制的整数公共拍固定帧。原保持参数400000ns不变，5.5ns时帧为399998.5ns；逐组物理写回在三帧中执行校验，间隔不超过原限制。H/guard/availability以实际帧重算，避免非整比帧的边沿漂移。
