# PCM 独立复核：读链通过，完整装载阻断

结论为 **PASS_partial_read_ONLY_resident_BLOCKED**。本审查只认可指定读安全初态下的阵列读、控制、计数和数字服务；没有认可完整 resident、tau 或成对 Roofline 点。审查者是 MRAM、FeNOR、GC-04、NAND 作者，未修改 PCM 生产；发现的公共清零问题由公共维护者修复。

从新的源码、构建及运行目录复跑：`/Users/shine/neurosim/runs/step4-v5/p1/case-pcm-pcm-independent-read-ref-r2-20261005`。精确输入与公共代码哈希见 `review.json`；它们绑定 read-only 修复包，不沿用原三点的资格。执行脚本是 `independent_audit.py`，不导入生产聚合器或其 RK4 求解器。

独立以约化节点导纳矩阵和缩放平方矩阵指数计算 48 个状态/负载/初态/使能偏移组合，含 WL 同时接通但未感测的 64 列。最小差分为 15.000097 mV，符合该模型 15 mV 门槛；KCL 残差 <2.2e−19 A，耗散/电容能量关系残差 <2.8e−20 W。该数值一致性不提供器件统计裕量。±1 ns 是有限工程使能条件，非测得的抖动或 STA。

独立重建 K=128、N=16、16384 物理位、256 个读组、1792 正向与 256 符号位更新。全周期 MAC/保持/比较调度及真实 clear 门核查通过：从非零旧结果与 sticky 状态开始的反例已由公共 clear 硬件关闭。条件读服务间隔 259.729839 µs，rho=0.492819771 MB/s。它只在全体 BL 已处于 0..0.2 V 的读安全初态成立，不是一个已完成装载的完整服务点。

明确未闭合的是 **post_program_HV_return_and_read_isolation**。0.5 mA RESET / 0.2 mA SET 的同源波形证据不能提供高压端口返回低压域或低压开关耐压资格。生产包已清空 resident stages、标记 program blocked 并抑制成对 rates；这是正确处理。必须另有额定端口/回零/隔离及其时间与资源后才能重新审查 tau。

工作状态窗口 Ron≤20 kΩ / Roff≥200 kΩ 是经先验表征的限定服务条件，普通二元 verify 不能在线量出该窗口，也不代表所引论文的全体分布/良率。0.2 V 读点及 5 mV 总输入误差预算仍是显式工程条件；无长时漂移/读扰统计或硅签核结论。

复跑审计：

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/reviews/p1_pcm/independent_audit.py --run /Users/shine/neurosim/runs/step4-v5/p1/case-pcm-pcm-independent-read-ref-r2-20261005 --out /Users/shine/neurosim/runs/step4-v5/p1/pcm-independent-prereview-20261005/read_audit_final.json
```
