# GC-04 硅 gain-cell eDRAM P0 路线卡（2026-10-05）

**身份为65nm硅3T1C current-programmed dynamic-cascode，可保持/刷新且易失。采用GC-04二元±700nA端点子集，不换IGZO、1T1C DRAM或MLP HybridCell。可进入P3紧凑电流/节点与外围实现。**

- **物理证据**：GC-04 DOI10.1109/JSSC.2023.3339887；p5–6 Fig7/8为10fF MOM存储节点、HVT主读管+LVT动态cascode及共享栅、约200mV阈差，实物cell6μm²。0–700nA八等级，伪差分双支路；p7写负载50fF、coarse VW=0.52V/5ns（100nA工作点）+电流反馈细写、replica保持电流源工作点。p9–10 Fig16实测完整65/75ns转移曲线，**65ns包含5ns粗写，不再另加**；60ns是Fig12仿真，不叫实测全服务。
- **读链／相容模块**：由Q=C_SN V_SN、存储节点到HVT/LVT current transfer、Icomp(VBL)及I/C积分构成前端；用锁定NeuroSim65nm相容选择、precharge、mux、DFF、SAR与数字树，独立加入积分与program isolation。0.9V阵列预充、1.0V数字、0.7V原ADC是原宏条件，不能强行全部用22nm低压。原180ns完整计算及36/86/136ns工程开销仅对照；实际precharge/选通/隔离/采样与RC由模块算。MLP6098 `Cell.cpp:784… _3T1C`默认100fF、6.67μA、500ps，Read=V×G，Write直接改G，既无GC反馈写也无retention；875行`if(...);`使后句无条件执行，chargeStorage/maxCharge在构造器未初始化。**不采用该状态模型**，仅研究端口/外围。
- **组织候选**：K=N64；8位平面×64×64伪差分pair=65536 cell，128差分ADC（每plane16）、128pair反馈写driver、256branch；single128bit刷新code寄存，无whole-matrix shadow。16对齐权重/批完整覆盖4KiB，256批。原研究的200fF积分、MAC1ns/单行刷新64ns、10bit名义ADC是重新设计选择，需用同负载和真实RWL门边沿验证；I/C独立量纲检查：64×700nA×1ns/200fF=224mV，单row需64ns达到同摆幅。BL从0.9降到0.676V需在Fig7的current-flat工作域内。
- **外部写服务边界**：允许有来源65/75ns电流反馈黑盒，限定原50fF负载及适用电流端点，新增积分/SAR负载必须写时隔离且开关寄生计入50fF；不能以黑盒同时再计其已含写driver/coarse/settle。重连与read建立另计。刷新按同一读/符号译码/双支路反馈写资源运行，失败或漂移跨符号阈值不得通过真值修正。
- **保持条件**：p6 Fig9是FF/80°C仿真（10fF，700nA在0.4ms漂移3.3%）；p10 Fig17/18实测400μs对应99.7% tested cell<1原5bit ADC LSB漂移，正文未标测量温度。**该证据不是400μs全bit成功，也不支持300/350/400K热角。** 可固定标称实验温度域并显式条件保持资格，不能将80°C仿真与未标温测量混为联合实测包。独立检查单行刷新门限、0端点泄漏、反复刷新误差与每组写回时间。
- **范围候选**：固定器件/资源/标称室温模型域，完整写65/75ns、100/200/400μs刷新政策构成有来源上限内的有限服务包；周期更短是政策改变不声称材料更差的分布。先reference检查二态保持窗口与维护可行，再定三包。raw单次Δ/T_R、物理单请求延迟、维护busy+不可抢占guard与有效rho/tau分列；禁止把raw/availability称真实单次延迟。
- **验收门**：Q/I/C和common-mode、program隔离、load反事实；零/极值/抵消与刷新sign-read链；逐组实际回写间隔≤经资格约束的hold，guard不可抢占且alpha≤0输出无效；不复用原64×65ns=4.16μs维护结果。缺失的transistor尺寸/gm输出斜率可用公开相容65nm模型明确重设计并交叉检查Fig7；不能依赖旧时隙或仅凭非零SA返回。
