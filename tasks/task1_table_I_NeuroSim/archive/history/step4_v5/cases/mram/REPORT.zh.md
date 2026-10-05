# MRAM：公开 STT 模型参考与三组完整服务

**当前状态：独立审查提出的TG偏置与两态source最坏方向均已修复，三个同哈希新构建候选已通过模型门，等待独立复审。不是实测典型宏、硅准确率或写入成功概率保证。**

采用 UMEM 1.0.1 的同一完整 MRAM 参数包：70nm×70nm CoFeB/MgO p-STT，以普通1T1MTJ＋二元感测＋局部数字归约实现 signed INT8。外围是锁定 MLP V3.0 的65nm LSTP，而非旧MRAM-06的40nm 2T2MTJ/IBMD。K=N64，八个64×64 data bank、32768 MTJ、256 SA、32并行数字更新lane；八bank读并行，32写lane为全域共享、一次只写一个bank。物理资源/端口与旧案例不同，不能把数值变化统称“工具修正”。

|情景|每方向编程平台|Δ_S = 单次延迟|完整T_R|ρ (MB/s)|τ (MB/s)|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|---:|
|optimistic|500ns|160.6μs|2.1506ms|0.398506|1.904585|0.209235|13.3910|
|reference|1μs|160.6μs|3.1746ms|0.398506|1.290241|0.308861|19.7671|
|pessimistic|2μs|160.6μs|5.2226ms|0.398506|0.784284|0.508114|32.5193|

MB为十进制。每成功向量仅64逻辑Byte，每次完整矩阵仅4096逻辑Byte。三组使用同一硬件、固定300K平台点、0.15V读入口、0.6V编程入口、100ns数字周期，只有有限编程平台政策变化；不覆盖材料分布、温度角或随机重试。ρ不变是正确的成对结果。U*是装载—求值平衡阈值，不是工作负载实际复用次数。

NeuroSim真正执行SubArray、访问管尺寸化、译码/读MUX/独立write TG、SA、匹配reference使能/隔离、低读电平预充、全组保持/zero mask、25bit add/sub、target mask、逐位verify与clear门。原始Type::RRAM仅承载通用电阻端口；原生短unsigned aggregate未直接当完整signed服务。单行读不再按64行并流尺寸化MUX，write路线与readMUX分开；所有原生内部clock段按其包含范围计一次。连续MAC、保持/比较至少使用完整合法周期；本例group decode串联后的42.52ns组合路径需要至少85.04ns周期，最终固定100ns，而不是沿用曾失败的80ns。

器件专用部分在 `umem_port.py`：同源非线性R(V,s)、双向电流驱动状态演化；外加按actual native尺寸/Ion/Vth饱和锚统一标定的访问管、readMUX、writeTG与reference N管。CACTI的1.77×VDD/Ion有效R只用于native尺寸/时延，不当成小VDS微分R；每个端口使用实际VGS/VDS、反向源极退化、线电阻及共享SL反馈。源回流采用显式2μm×1μm金属列线/横向strap和耦合C估计，不能让细信号线承担全部写电流。读时物理WL打开64cell，即使只转换32列；P数据的背景采用所有64列恒最大初始Vread、无readMUX的更强电流上界，AP数据则采用零source抬升的保守下界；选中victim始终经过真实readMUX，固定quiet reference返回网络不随目标态改变。不能用最大IR同时声称两侧最坏。每SA参考是固定12kΩ电阻、真实隔离开关与匹配C；PRE阶段两端均断开，避免参考分压破坏预充。

读网络检查±1%预充初态、±100ps有限相对step-enable偏移，以及5mV判别门限＋2mV有限误差预算；该偏移不是实测抖动，native匹配负载仅支持名义step端口近似。0.1V早期方案裕量过窄，已被0.15V设计替代。P/AP捕获余量为8.703/7.064mV，实际发展1.23ns；最大共同余量10.504mV。整个WL开启/SA输出/释放窗口对最小/最大source抬升均以恒定最大读偏置施加同模型读扰检查，强于实际被动BL放电；不把无热噪声模型的稳定性称为现实BER保证。

完整resident从任意旧二态开始，1024个32bit组逐批装入；每组两极性真实波形/归零、完整周期mask控制、同一路径readback和比较后才复用目标缓冲，全部通过才发布矩阵。未重复计算bit-plane payload，也无全矩阵shadow。实际短脉冲/source退化失败、过窄单元布局、过快时钟、固定β修复、reference隔离和跨请求clear反例均保留本地。码流/物理状态先求出再判定，不通过真值修正写失败。

关键限制：UMEM源码的正电流方向与其手册/Carboni图展示的电极极性不同；本实现保留代码约定，并不声称复现实验极性。UMEM raw state软限幅可略越±1，电阻使用源码内部限幅变量，未取越界端点作为更好状态。MOS端口是actual native Ion饱和锚下的固定尺寸最小模型，body effect/velocity saturation等未独立标定；旧R-matched端口只保留为敏感性，并不构成foundry误差界。固定正向0.15V读是该模型的工作条件；Carboni原实验按上次写极性读取，不能移植读扰保证。比较器offset/noise与完整STA、匹配cap/参考电阻布局、全芯片PDN不在本模型签核范围。

证据与复跑：`inputs.json`是唯一生成输入；`model.lock.json`锁定UMEM原始SHA/哈希/许可；`candidate_points.json`记录三点及完整计算哈希；`reference_snapshot.json`保存实际R/C/尺寸/端态/电流/阶段资格。生产目录为 `/Users/shine/neurosim/runs/step4-v5/p1/case-mram-mram-sidebound-final-{opt,ref,pess}-20261005`。详细作者诊断在 `/Users/shine/neurosim/runs/step4-v5/p1/mram-model-20261005/`。

```sh
python3 -B '/Users/shine/Library/CloudStorage/OneDrive-个人/Files/02 Works/202609-ISCAS2027-Roofline/tasks/task1_table_I_NeuroSim/step4_v5/run.py' --case mram --scenario reference --run-id <新的唯一名称>
```

三点文件保持 `formal_eligibility=false`，直至独立review和最终P5集成资格明确；本报告不是独立验收记录。

修复后的编程状态仅使用电气建立后的平台，不借边沿spin加快成功；边沿以共模相关TG最小g、真实连接C及source返回RC预算计时，有限斜率充电电流与共享供给分别核查，并验证两倍边沿长的反向应力未跨二态。端口波形/初态条件与完整边沿签核仍属于模型适用范围。
