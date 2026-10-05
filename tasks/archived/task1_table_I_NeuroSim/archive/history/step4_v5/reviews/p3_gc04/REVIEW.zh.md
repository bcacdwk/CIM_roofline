# GC-04 独立轻量审查

结论：**PASS_conditional_model_scope**。按用户最新数量级/范围优先要求，完成一次最终包新源码、新构建、新运行的三点复核及主导机制、计数与维护检查，不扩展成器件签核。审查者为PCM/NOR/FeRAM作者，未参与GC04或公共生产实现。

绑定共同计算SHA `095f2d8a8fe534039a0fe5fb26b003def10e1c62ef10ff16162cfb9203fb6fd0`；完整输入/源码hash、三个独立运行路径见`review.json`。实际目录为 `component-services/case-gc04-reviewer-gc04-{opt,ref,pess}-final-20261005`，每点都有新的native frontend/digital目录和二进制。

|情景|有效ρ MB/s|有效τ MB/s|长期resident间隔 µs|
|---|---:|---:|---:|
|optimistic|.199128811|9.699634850|105.570984|
|reference|.199128811|8.238870016|124.288889|
|pessimistic|.199128811|7.526912316|136.045161|

独立脚本不调用生产聚合器或scheduler来产生预期答案：以200ns整数tick重新执行逐组维护、组提交、每矩阵clear、guard及保留progress的有限循环，得到与最终三点一致的长期区间。全64组每轮刷新204.8µs；每个维护窗口只容一条116.4µs不可抢占stream，故实际stream周期321.4µs、三点ρ真实重合。resident原子组可跨刷新，64组原始完整装载51.4µs；350µs政策的循环是16次refresh完成45次矩阵装载，均值124.288889µs。它不是单次装载延迟。300µs政策虽然有正空闲比例，却容不下一条stream，独立计数同样拒绝。

资源重新计为16384个硅3T1C cell、16子阵列、256个真实single-ended SAR、128个差码操作器、1.024nF外部hold、64次Xsum更新与32个正常模拟group/256次plane MAC。原生程序连接负载≤50fF，16bit deadline计数和8bit resident/refresh progress真实存在。65,536个scalar编码组合独立验证 `(Σsigned_plane D−Xsum)/2`；原始ADC码不由真值替换。

原论文已实查pp6/7/9/10：50fF、5ns粗写后细写、65ns完成及400µs的99.7%测试pair限定；FF80°C仿真与未注明温度的测量分开。旧180ns计算cycle和4.16µs完整刷新未作为新性能输入。控制与来源边界成立，未发现改变数量级、状态或主导计数的阻断。

保留的条件：GC04是**易失**存储；353K反馈写转用、有限漏电模型/零状态延续、低于原0.9V图点的cascode电流延伸均有明确范围。Q4/32bit只是近似格式，不是ENOB/实测INT8精度。源400µs不能推广成所有cell可靠保持。已入场单次116.4/51.4µs与长期能力分列；初态已处于维护周期、各组历史写回时刻错开，不能改写为全部age免费为0。

独立工具与整数事件证据：`independent_counts.py`/`independent_counts.json`；源核查：`source_check.json`。复跑入口是独立包 `/Users/shine/neurosim/runs/step4-v5/p3/reviewer-gc04-20261005/package/run_components.py --case gc04 --scenario reference --run-id <唯一新ID>`。
