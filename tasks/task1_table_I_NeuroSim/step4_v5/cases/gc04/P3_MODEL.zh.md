# GC-04 P3 当前模型与待接接口

状态：已有真实独立 current-sampling 新构建、专用 GC 状态/积分网络与逐事件维护探针；尚无完整正式服务点，公共数字/采样联接接口在实现中。原 `ROUTE.zh.md` 是 P0 候选，以下修订优先。

保持原 65nm silicon GC-04 的 10 fF 存储节点、HVT/LVT 动态 cascode 与电流反馈写。不是非易失存储，也不采用 `_3T1C` 的理想电导赋值。引用 GC-04 DOI10.1109/JSSC.2023.3339887，原文 Fig7 平坦输出电流测试在 BL 1.2→0.9 V；低于 0.9 V 是有饱和/内部压降约束的紧凑模型延伸，不能称实测平坦域。

逻辑 K=N64，8 个权重位平面，正负两支 GC cell 存互补二元 `{+700 nA,−700 nA}`，总 65536 物理 cell。没有使用 `(0,0)` 正式码，以对应原 ±7 pair 保持测试。每位平面分 2 个 32-row half ×4 个 16-output 子阵列，共 64 子阵列；总容量不变。256 个 single-ended SAR（两支一码，相减得到128组差分）/128 pair 反馈写驱动跨 8 组共享，16 MAC lanes，实际 bank MUX/隔离寄生必须接入。一次普通积分最多 16 活动行，其余子阵列的 RWL 不活动，不能让未感测列免费消失。源行长度按 16 pair×6 µm=96 µm；明确上层 0.8 µm×0.25 µm 铜等效线产生 10.56 Ω，局部驱动另计。

互补表示 `d=2b−1` 的真实算术是 `Y=(Σ_b signed(2^b)·D_b−Σx)/2`。`Σx` 范围为 [−8192,8128]，至少 14 bit，采用真实 16-bit 寄存/加法。每个输入请求先 64 次整周期 Xsum 累加，末 4 输出组修正；不是免费数字更名。每支 SAR 为 11-bit 名义量化、1.0 V 参考量程，真实128个12-bit subtractor与raw/diff保持；16 code/unit 部分和为候选 Q4 标度；32-bit 重构容器不等于 32-bit 模拟精度。负权重 MSB、负输入 MSB与末 `/2` 各有明确物理运算/连线。

`gc_model.py` 使用 `Q=C_SN·V_SN`、源 Eq(5)/(8) 的弱反型指数、约 0.2 V 动态 cascode 内部压降及有限 VDS 饱和项。Fig9 FF/80°C 的 700 nA −3.3%、100 nA +20.4%/400 µs 用于有限节点漏电标定；400 nA 实际是 +1.5%，不是 P0 曾写的负向。当前 T=353.15 K、n=1.5 明列紧凑模型条件；将 100 nA 的正漏电用于初始零节点是工程延用，非唯一器件提取。该候选低节点到半电流门所需漏电约为延用值 68 倍，只是因果裕量，不是概率。原 400 µs 实测仅 99.7% tested pair 小于 1 原 ADC LSB，温度未写，不能变成全部 bit 保持保证。

完整反馈写允许引用实测 65/75 ns，包括 5 ns coarse 与细写反馈，不另收费这些内部阶段。原实测温度未给，不能称 353 K 实测服务。适配须实际保持 BL 总负载≤50 fF、同隔离/replica 条件；新开关控制与重连接另算。实际初始 64-row/200 Ω 隔离方案在 353 K 产生 57.0719 fF，**失败已保留**。缩短为 32-row half，以原 50 fF column 的几何线性转用估 25 fF 阵列贡献、400 Ω 隔离真实 off-drain 后为 38.6408 fF，余 11.3592 fF 留给 bank MUX 与匹配电容。50→25 fF 是明确几何模型转用，不叫 source extracted layout；完整组件还须把 bank MUX 等加入后再核。

原文 Fig10 的 CDAC 在预充和积分时连接、采样之后断开；正式路径将使用这个真实三节点电荷拓扑。不能拿初始 fixture 的迟接 CDAC 电荷分享系数当原宏固有损失。普通积分与单行刷新使用同一电荷范围下不同脉冲，真实边沿/隔离/采样先后计算；原 SwitchMatrix 半拍延迟不是积分宽度。

`maintenance.py` 已实现固定次序逐组回写的实际事件，维护 payload 为 0。正式候选政策为 work-conserving：当下一完整 stream 请求或 resident 已提交批不能赶在保持 deadline 前结束，即提前进入刷新。stream 不抢占；resident 只在完整 16-weight 批间抢占，未接收下一 target，保持真实 group/address 进度。刷新专用 sign code hold 不得清除 resident progress、输出或 Xsum。用逐组实际 writeback 间隔验证保持，而不以 alpha 判成功。已跑反例：100 µs 周期中 60% 空闲仍放不下 70 µs 非抢占请求；跨维护 resident 真延迟 120 µs 而 raw 80 µs。正式三点的保持 deadline/反馈写时间组合须等完整 native 周期门和阶段计数后确定，不能提前固定旧100/200/400 µs。

实际证据目录：

- `/Users/shine/neurosim/runs/step4-v5/components/current_sampling-gc04-64x16-physical-r1-20261005`：50 fF 写负载失败。
- `/Users/shine/neurosim/runs/step4-v5/components/current_sampling-gc04-32x16-physical-r2-20261005`：单元组件通过，仍缺共享 bank MUX/完整数字重构。
- `/Users/shine/neurosim/runs/step4-v5/p3/gc04-electrical-20261005/electrical_diagnostic_r2.json`：65536 scalar 映射、source 耦合双 BL、极值/抵消/孤立/刷新与步长检查。
- 同目录 `maintenance_diagnostic_r2.json`：逐事件轨迹与 alpha 反例。

补充：RWL↔SN 耦合采用工程 Cc=0.2 fF，实际保存电荷为 Q=(10 fF+Cc)·V_SN−Cc·V_RWL。写/读时 RWL=0、idle=1 V 的往返显式守恒，不能把 source 跳变下的存储节点当固定电压源；原10 fF仍是MOM值。零/高态模型同时记录idle/read节点电压，Cc已要求进入RWL总负载。
