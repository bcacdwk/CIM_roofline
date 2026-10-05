# Step4 V2 独立复核

结论：**PASS；无未解决的实现阻断问题。** 本结论覆盖十例 reference 的混合服务、时序资格、边界语义和可复现性，不代表完整宏 STA 或模拟精度签核。

**独立性披露。** reviewer 曾编写 V1 的六例 `native.py`/`native.zh.md`；本轮没有参与 V2 生产设计或实现，所有检查与文件写入均在本地 reviewer 目录。这里声明的是对 V2 实现的独立审查，不是从未参与 V1。V1 已有另一位未参与当轮实现的审计记录，仍应保留。

从 `/tmp` 以绝对路径执行冻结的 `run_step4_v2.py --run-id reviewer-v2-final-20261004 --no-export`，十例使用新源码副本、新编译和实际执行，全部命令成功。独立脚本以原始阶段计数、实际模块返回和明确边沿公式复算十例完整 streaming/resident、GC维护与所有率；预期值不调用生产 engine、adapter、legacy replay 或原计算器。另将冻结 engine 作为测试对象，独立检查边界和错误生命周期。共 **1693 项检查通过**。

主运行 `reference-v2-final-20261004` 与独立运行的 82 份关键 JSON 逐项一致；仅将各自本地绝对运行根规范为同一占位符。三个 pilot 的完整 `result.json` 与已验收 Step3 V2 相同，十例旧时间回放通过。检查源输入指针和单位、snapshot文件哈希、十例真实编译命令/上游源码/constructor patch/request，以及实际公共模块不读取 MemCell 字段。新增七例没有使用 SubArray 或替换原生材料身份。

## 时序与边界

PCM完整重构数据路径为9.407240373 ns，以SAR、原阈值条件、输入选择和旧累加器从E0保持至E2，时序下限4.703620186 ns，按统一政策选5 ns。GC对应10.500414735 ns、下限5.250207368 ns，选5.5 ns。两例E1只更新phase，输出累加器只在E2写入；没有中间数据bank、重新发射的数据、下一SAR或刷新重叠。E1→E2捕获使能另计2.059455648 ns的**单拍**路径，未借用E0周期。

独立检查实际trace中的2048个PCM批与32个GC批，确认E0是转换完成后的首个launch边沿，E1/E2间隔和source保持一致。提前在E1写累加器、E2前覆写源、在两拍中间启动新SAR的负例均被拒绝。PCM实际阈值仍未提供，门图仅在既有列相关阈值稳定这一条件下成立。

NOR/FeRAM/FeNOR的每拍动态MAC下限为8.380406817 ns，工作周期8.5 ns；MRAM为8.539941102 ns，工作周期9 ns。源分类保留V1全部门和负载；各源类别最大值准确重组V1全源同时重发的9.700951561/10.657026967 ns包络。输入数据及row/output group选择在原生读开始时建立，并保持八个输入bit；ibit与累加器反馈仍逐拍变化，第一拍新权重捕获也保留完整单拍资格。独立核对各早稳源pin到达和完整source→capture均落在实际原生提前窗口加首MAC周期内，没有免费选中数据缓存。

完整`launch→组合→capture`周期入口不再追加目的setup；目的setup已经进入该周期的路径资格。纯capture/ready在`完成时刻+setup`的首个合格边沿接收，不再加整拍。用完成时刻9.70、9.75、9.80、9.99、10.00、10.01 ns，周期10 ns及setup0.25 ns独立验证：恰满足setup的9.75 ns捕获于10 ns，晚于该界限则20 ns；完成恰10 ns时纯capture需20 ns，而完整周期从10 ns发射、20 ns结束。含原生capture的零setup边界恰10 ns即完成。透明一层模板、两拍分写或合写均不改变物理边沿。禁止给完整cycle入口另加setup的负例通过。

NOR/FeNOR单组读码捕获和MRAM/FeNOR终验capture是纯边界；MRAM求值捕获继续保留一拍IBMD隔离交接；FeRAM原生读包含恢复与已有capture，没有重复收取。页编程内部验证/恢复、PCM完整SET尾沿、FeNOR guard中的最终返回同样保持只计一次。

## GC发现与闭环

初审发现400000 ns维护帧不能整除5.5 ns时钟：从相邻名义帧实际执行，维护busy随时钟相位变化，部分同组写回完成间隔达400004 ns。此前仅从phase0计算availability并声称固定偏移，不能证明逐cell保持资格。

supervisor修订后保持器件400000 ns输入不变，将实际帧设为`floor(retention/P)×P=399998.5 ns`，以实际帧为availability分母。最终raw streaming=3707 ns、resident=21120 ns，维护busy=66176 ns，非抢占guard=115.5 ns，alpha=0.8342706285148569。独立展开11帧、检查2560组相邻物理current-program完成端点，间隔全部恰399998.5 ns且不超原保持界限。维护内部payload仍为0；长期平均有效成本与单次物理延迟分开。1 ns和30000 ns不可行负例分别保留空/负availability并返回空有效能力，没有裁剪。

## 来源、差异与限制

阶段输出明确区分直接NeuroSim SAR、具体门图组合、保留原生/算术预算、接口调度；边沿等待单列。NAND仍为原生string/SSL/WL/BL/SL、双幅值base-4、固定两符号相位；正常及校准共享SAR均计入。乘法/舍入与校准除法保持明确的非零、未完成电路时序验证预算。2倍/4倍预算使streaming增加8640/25920 ns，resident增加4032/12096 ns，与960轮及448校准拍的独立公式相符；不能据此宣布乘除时序已验证。

NOR完整resident中99.995%来自保留page program/sector erase；NAND为99.164%保留page program/block erase。新旧resident接近主要由原生完整P/E占主导，**不是NeuroSim独立验证了这些原生周期**。V1→V2对比先在V1周期纠正边界，再以同配置选择V2周期，未混用两路频率或payload。

继续保留的具体限制是PCM物理阈值和模式标定、FeRAM PL总寄生及并发恢复供电、NAND乘除/校准工作状态，以及GC重复刷新误差。公共电路时序仍为基于公开公式和声明局部线负载的结构包络，不是抽取布线或可敏化STA；本轮没有虚构对应的准确度保证。

证据入口：`review.json`、`review_independent.json`、`check_independent_v2.py`，以及`gc_frame_phase_probe.json`和`gc_frame_fix_check.json`保留发现及闭环过程。完整源码副本、构建日志、trace继续留在本地运行目录；未执行Git暂存、提交或推送。
