# GC-04 V5：有限电流模型与真实周期维护

状态：三点已真实新源码、新构建、新运行，全部 `conditional`，A 组独立审查已通过（有限条件范围）。共同计算快照 `095f2d8a8fe534039a0fe5fb26b003def10e1c62ef10ff16162cfb9203fb6fd0`；正式复跑入口 `run_components.py --case gc04 --scenario reference --run-id <unique>`。本例是**易失性**硅 gain-cell eDRAM。

最终身份 `gc04_silicon65_3t1c_complementary_k64n16_q4_v1`：K64×N16、8 位权重平面、每 bit 两个 GC-04 3T1C cell，16384 物理 cell。每平面有两个 32-row×16-pair 子阵列；16 子阵列使用 128 pair 读/反馈写端口，256 个真实 single-ended 11-bit SAR，再用128个12-bit subtractor求差，16 路32-bit数字重构。每支路明确配置4 pF外部hold，总1.024 nF；这是为了控制采样门电荷，不是零成本精度标签。另有200 fF积分与20 fF ADC输入假设。native只给外围部分面积，外部电容与完整反馈引擎未作全布局，因此不能称等面积宏。

旧 K64×N64 候选在真实 200 ns 时钟下失败：stream296.2 µs、刷新358.4 µs/400 µs，上层剩余10.35%空闲仍放不下一条请求。100 ns时钟也被实际数字路径否决。最终 N16 是明确架构收缩，不是旧设计快角。反例见 `design_failures.json`；300 µs维护政策在最终N16下也因整请求放不下而拒绝，本地 `hold300_failure.json` 保留。

## 参考值与成对范围

| 情景 | rho 有效 MB/s | tau 有效 MB/s | RI* | U* |
|---|---:|---:|---:|---:|
| optimistic | 0.199128811 | 9.699634850 | 0.020529516 | 0.328472260 |
| reference | 0.199128811 | 8.238870016 | 0.024169432 | 0.386710918 |
| pessimistic | 0.199128811 | 7.526912316 | 0.026455577 | 0.423289239 |

optimistic/reference/pessimistic 分别采用完整反馈写65/75/75 ns与最大保持期限400/350/330 µs。同一宏、时钟与模拟前端固定；这是有限控制政策情景，不是材料概率区间。反馈写的差别被200 ns外围时钟粒度掩盖。stream每次读后都需刷新，三个政策都只能容纳一条完整请求，因此rho真实重合；resident按批可跨刷新，期限改变tau。

参考 raw 单次stream/无维护间隔116.4 µs、完整raw resident51.4 µs；64组刷新共204.8 µs，实际stream维护周期321.4 µs。参考长期resident等效间隔124.288889 µs。51.4 µs是声明的刷新后入场相位下单次装载真实延迟；长期等效间隔不是单次延迟。服务排除外部排队，输入从本地128-bit口就绪并接收。刷新payload为0。

## 机制、来源与边界

源GC-04 DOI10.1109/JSSC.2023.3339887提供10 fF MOM、700 nA端点、动态HVT/LVT cascode、50 fF负载的完整65/75 ns反馈写。该完整写包含5 ns粗写、细写和replica建立，不重复收费。源测量温度未给，353 K移植是明确条件；不能称已测同温新宏。半列25 fF由原50 fF/64-row几何转用，再加真实bank OFF drain与匹配电容到50 fF；此组织/固定负载假设单列，不叫提取布局。

读使用源Eq(5)/(8)的电流/节点关系及有限cascode headroom，NeuroSim真实计算选择、RWL/WWL独立驱动、bank/采样TG、预充、SAR、保持、Xsum和加减。每支路连接阵列BL→积分→ADC输入，CDAC在积分时已连接；RC均衡时间和SAMP关闭电荷显式计。外部4 pF计入动态负载。保守采样界用完整N/P gate charge，不假设二者完美相消；参考每branch电压界6.7290 mV，pair界约13.458 mV。最小cell BL约0.7336 V；低于原Fig7实测0.9 V的部分是受cascode饱和约束的紧凑延伸，未称测量。

参考保持采用两端点拟合的状态相关净电荷泄漏：100/700 nA的400 µs仿真端点来自FF/80°C；未参与拟合的400 nA预测411.97 nA、源约406 nA，差约1.49个百分点。另一条off-access弱反型注入/常量sink模型保留为压力检查：400 nA漂移符号不符，且零节点外推不同。这些不被包装成统计分布。压力模型下单行刷新信号下界约113.39 mV，仍大于pair误差界。源400 µs测量仅99.7% tested pair小于1原LSB，温度未给，不能成为所有bit可靠保持承诺。

存储状态是 Q=(10 fF+Cc)V_SN−CcV_RWL，Cc=0.2 fF为明确工程寄生。idle/read往返显式保电荷，RWL为源端，不当作纯栅负载。写通过完整反馈原语把实际选中pair更新到新码，未选行WWL保持关断；独立WWL和RWL program-force存在，关WWL后再释放RWL。

## 精度与实际维护

互补bit使D=Σx(2b−1)，输出必须计算(Σsigned-weight-plane D−Xsum)/2。Xsum是实际16-bit寄存与64次累加，末端减法和算术右移均计；右移最多丢1/32输出单位。nominal Q4/32-bit是格式，**不是ENOB或实测INT8精度**。原始ADC码、有限模拟误差与真值仅用于离线诊断，不用真值替换输出。65,536个scalar编码组合与零/极值/抵消/孤立输入及刷新符号检查已执行。

`maintenance.py`逐组执行read→差码→sign hold→反馈写→progress，64组真实writeback。stream整请求不抢占；resident仅在已提交16-weight批之间暂停，不在刷新前偷收下一个target，resident进度寄存不被刷新clear。初态声明为已运行的周期维护相位、旧矩阵值任意；历史回写时刻按组错开，首次维护也验证期限，不把全部age免费设0。初始历史周期比所选期限短一个guard周期。raw、已入场单次、长期能力分列。

最终运行目录为 `/Users/shine/neurosim/runs/step4-v5/component-services/case-gc04-gc04-final-{optimistic,reference,pessimistic}-r2-20261005`。完整事件轨迹、实际C/R/尺寸、阶段与原始码留在各目录；`candidate_points.json`/`reference_snapshot.json`是小型权威导出。独立审查只绑定最终哈希，不沿用早期candidate结论。
