# Step4 公共后端：模块边界、路径和本地验证

`backend.py` 从锁定 V1.4 SHA `8a88abf85844c0e1ba17cc771ea535fff6040456` 的工作树逐文件核对 Git blob，然后复制到新的本地目录。只在副本集中设置 22 nm、LSTP、300 K；补丁、请求头、编译清单、源码哈希和实际命令保存于该目录。编译链接 `step4.cpp/Param.cpp/Technology.cpp/formula.cpp/FunctionUnit.cpp/DFF.cpp/Adder.cpp/SarADC.cpp`。不调用 SubArray、不修改 pilots、不改共享上游。

`DFF/Adder/SarADC` 构造函数需要 MemCell 引用；这里 Type::SRAM 只是零器件字段的必需上下文，**不代表 SRAM 或其他材料阵列仿真**。Python 对三个完整 `.cpp` 实际执行 `cell.<field>` 读取审计，结果为空。实际调用 Initialize、CalculateArea、CalculateLatency；SAR 另调用 CalculateUnitArea。仅使用 SAR 名义码宽的 `(bits+1) ns` 转换拟合，不调用依赖列电阻或电压的功耗函数。

`step4_dag.h` 保留已验收 Step3 V2 的 NAND 门到达时间/斜率 Pareto 包络工具；所有本轮算术拓扑在 `backend.cpp` 单独实例化。门尺寸和输入/输出电容来自真实初始化的 Adder，门延迟来自锁定 formula/Horowitz。局部连线仍为每段 10 µm、0.2 fF/µm，电阻使用锁定 Param 线模型；DFF 边界沿用两级有负载反相器工程近似。这是明示拓扑与负载的结构包络，不是布线提取、可激活路径 STA 或硅精度保证。原生 PL/BL/string/SL/脉冲负载不由局部数字线代替。

|案例|完整公共组合路径|寄存/资源边界与局限|
|---|---|---|
|03/06/08/10|32 个 signed INT8 权重按当前输入 bit 门控；9/10/11/12/13 bit 五级归约；输入 bit 移位/符号；23/24 bit 输出累加|4096 bit 原保持区和完整 K×8 输入寄存出发；输入 row-group mux、bit mux、16 lane 分发、输出 bank mux、捕获 mux/setup 均计；单拍资格，未新增选中输入缓存|
|04|INT8→幅值/符号；原 staging 的 digit/极性格式化；14 bit count 的 16/16/20 bit base-4 merge；21 bit 极性相减；29 bit 输入 digit 移位/符号累加|输入 4608×8 与 staging 4608×9 各按16 lane、288:1 word-bank mux 选取，按512:1 padding 包络计data/control扇出；formatter生成48bit的LSB/MSB/MSB固定复制。使用已有 64×14、16×20、8×21 和 240×29 位边界，分阶段单拍。Q8.16 仿射乘法/舍入及校准除法明确保留原非零 tick 预算，完整路径未验证|
|07|每 SAR 八路上下阈值比较形成九级类码，4 bit class→5/7/11 bit signed weighted tree→24 bit shift/acc；单 WL 终验包含上下阈值、目标 byte 的 plane 选择、rail check 和 16 lane 归约|原生列相关校准阈值作为稳定输入，**没有造出实际阈值表、阈值 bank 或存储精度**；阈值存储/生成未建模，组合时序有条件。两 tick 原预算保留，phase2 整条单拍，不借两拍放宽|
|09|当前输入 bit 的 64 项 popcount；`floor((signed_code+8*popcount+8)/16)`；7 bit count→8/10/14 bit tree→22 bit shift/acc；刷新 signed-code sign 解码|10 bit 名义公式保留 half-up 和正端点饱和；popcount 为组合电路，无新增 popcount 寄存。两 tick 原预算保留，phase2 整条单拍；刷新使用已有 128 bit hold|

控制状态按并存 row/group/digit/page/phase/flag 分配，小型工程控制状态位明确列入快照；控制路径只用其中最长增量计数器，不把全部控制状态串成一个加法器。页口装载只实例化其数字控制和已有数据保持；完整原生读码、program/erase、restore、current programming 等依然由原生服务拥有，不再次拆加其内部外围。

PCM/GC 只允许已有 SAR 状态保持到第二数字消费边沿，期间不启动下一转换、刷新或覆盖。没有中间树结果寄存、没有多周期时序例外。所有已实例化路径用完整单拍时序下限，统一选择 `max(5ns, timing_min)` 上取 0.5 ns 网格。NAND 所选周期仅证明已实例化路径；原生仿射/校准预算仍是需要后续验证的条件。SAR/原生物理时长不参与数字选频。

作者实际新构建结果在 `/Users/shine/neurosim/runs/step4/backend-v2-<case_id>/`；NAND 补全 bank mux/formatter 后另从新目录 `/Users/shine/neurosim/runs/step4/backend-v3-04_nand_3d/` 构建。MRAM/PCM/FeNOR 终验源 mux 和 PCM 严格阈值边界修订后另从 `backend-v4-06_mram/`、`backend-v4-07_pcm/`、`backend-v4-10_fenor_3d/` 新目录构建。下表为 10 µm、10 bit reference 的模块结果；后续正式汇总以统一入口运行快照为准。

|案例|时序下限 ns|工作周期 ns|主路径|同门图逻辑 fixtures|
|---|---:|---:|---|---:|
|03 NOR|9.700951561|10|32项完整MAC|256|
|04 NAND|8.858794040|9|29bit移位/累加|2600|
|06 MRAM|10.657026967|11|32项完整MAC及8组输入选择|272|
|07 PCM|9.407240373|9.5|条件阈值decoder至24bit累加|232|
|08 FeRAM|9.700951561|10|32项完整MAC|256|
|09 GC|10.500414735|11|popcount/解码至22bit累加|260|
|10 FeNOR|9.700951561|10|32项完整MAC|272|

终验源选择不是免费的已选寄存器：MRAM 的128 bit互补目标通过2:1分支mux提供64个比较目标；PCM的32 byte目标先按2:1 parity组选择16 byte，再逐byte作8:1 plane选择；FeNOR的128 bit native捕获和目标分别通过8:1组mux供16比较器分8拍处理。data与select扇出均进入路径，未增shadow bank。最终终验路径分别为2.573466790、3.739784811、3.002373709 ns，没有改变上述主周期。PCM原条件严格为`code < lower`或`code > upper`；等于任一阈值均拒绝。16组终验门图fixture覆盖两目标态、lower/upper等号、两端rail、间隙和`old_done=0`；实际阈值仍未虚构。

七例均实际拒绝固定 5 ns；分别在 reference 加 0.5 ns 的合法慢频点重跑，组合物理时序和 SAR 时长保持不变。PCM 另外执行 7/9/11/16 bit 的类型/精度适配检查，SAR 分别返回 8/10/12/17 ns，码宽缩放后的通用 comparator fixtures 通过。此测试改变的是诊断硬件精度，不把任意 fixture 阈值当作实际 PCM 标定。GC reference 的 nominal 数值/维护可行性由原生 adapter 的独立检查和完整调度另行给出。

面积返回只覆盖本次初始化 DFF/SAR/Adder 模块，未加 formula mux/control、native array/front/write 或全局布线，不是宏 PPA。未知聚合写返回保持 `null`。所有率必须由统一调度器结合完整原生服务产生，不能用此表时钟直接替代完整 streaming/resident 时间。
