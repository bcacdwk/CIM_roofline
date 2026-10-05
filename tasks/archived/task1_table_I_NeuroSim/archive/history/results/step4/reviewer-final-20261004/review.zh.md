# Step 4 独立复核

结论：**PASS，无未解决的阻断问题。** 通过范围是十例 reference 典型配置的混合服务评估，保留原生服务和明确的条件预算；不等同于完整宏、电路签核或模拟准确度认证。

reviewer 未参与实现，只读审查接口、接入表、代码、冻结输入和必要原计算器，将问题反馈给唯一代码维护者后，复核冻结修复。从 `/tmp` 执行 `run_step4.py --run-id reviewer-final-20261004 --no-export`，在 `/Users/shine/neurosim/runs/step4/reviewer-final-20261004/` 完成十例独立新源码副本、新编译和实际执行，不依赖旧二进制。全部命令退出成功。

**复现与独立计算。** 三个 pilot 的完整 `result.json` 与已验收 Step3 V2 一致。十例主结果、解析配置、回放、敏感性和分组检查与 supervisor 的 `reference-final-20261004` 一致；NAND 数值诊断仅有各自本地 snapshot 的 comparison-only 绝对路径前缀不同，所有数值及相对路径相同。另用不导入生产 engine、adapter、legacy_replay 或原计算器的独立脚本，按七例原始阶段和实际边沿写闭式公式，复算 streaming、resident、维护、rho/tau/RI*/U*，并检查 native primitive 的原输入 JSON 指针、原单位和归一化值；共 299 项检查通过。98 个 snapshot 文件哈希、十例上游文件及 constructor patch/request 哈希通过。

**模型接入与完整边界。** 新七例未调用 SubArray 或把原宏改成 SRAM/RRAM/Cap/通用 FeFET。实际 DFF、Adder、SarADC 调用不读 MemCell 字段，SRAM 枚举只是构造上下文。SAR 10-bit 的 11 ns 来自锁定 `CalculateLatency` 的位宽拟合，不推导器件电压、阵列负载或精度。NOR page/sector、MRAM两方向写及双支绝对终验、PCM RESET/完整SET与两次新鲜验证、FeRAM恢复及已有捕获、GC两个积分模式、垂直FeFET guard中的最终返回均只计一次。NAND 5760数据页＋384参考页、64块擦除、960正常与12校准SAR批次和格式化负载核对通过；仿射乘法和校准除法仍为非零未验证预算。

**审查发现已闭环。** 初审发现的 PCM 端点比较缺失完整 ADC 阈值/rail/目标态路径、输入/目标寄存器访问 mux 隐去、嵌套计数 state 分配不足、PCM低位宽诊断 fixture 截断，均已修复后新编译。冻结代码实际包含 binary input-group mux、NAND 288:1 word mux及48-bit formatter、MRAM/PCM/FeNOR终验源选择、PCM严格上下阈值及等值/rail/old-done边界 fixture。所有新增数字路径按单周期核查；PCM/GC仍保留两拍预算，但第二拍必须覆盖完整解码→重构→累加路径，未继承 pilot 多拍豁免或添加影子寄存器。七例工作周期依次为 NOR 10、NAND 9、MRAM 11、PCM 9.5、FeRAM 10、GC 11、FeNOR 10 ns。

**维护与数值。** GC独立重算维护 busy=73,216 ns、guard=132 ns、保持周期400,000 ns，availability=0.81663，可行；内部维护载荷为0，单次原始延迟与长期有效服务成本分开。缩短保持期的负例保持负 availability 并返回不可行及空有效能力，未裁剪。SAR增加8 ns时，正常32批和刷新256批物理时间分别增加256和2048 ns；刷新总时长不增加是原边沿余量吸收，guard仍由132变143 ns，有效能力随之重算，不能因总时间平台误判漏依赖。数值检查保留 NAND 孤立1→0、4608→4592、小幅2→24及组边界误差；GC保留正端511码饱和和取整前残差；PCM仅检查已校准类算术，未造阈值表。

进入 Step5 前需继续明确：NAND 乘除/舍入与校准工作状态尚未电路闭合；PCM物理阈值及模式校准来源未提供；FeRAM PL 总寄生和并发恢复供电未经验证；GC保持端点不证明长期反复刷新误差。公共数字路径仍是基于公开公式和声明局部线负载的结构性时序估计，不是抽取布线或可敏化 STA。上述限制已进入机器结果，不构成本轮隐藏缺项。

证据：本目录 `review.json`、`review_independent.json`、`review_build_comparison.json`、`review_static.json`、`check_independent.py`，以及统一入口产生的各案例结果、timing/grouping/numerical/sensitivity 检查。完整构建与 trace 保持在本地，未修改原 NVM、pilots、上游或执行 Git 写操作。
