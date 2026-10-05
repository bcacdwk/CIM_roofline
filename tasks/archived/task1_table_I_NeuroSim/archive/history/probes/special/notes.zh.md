# 特殊分支：接入边界

结论：主模型采用 V1.4 低压 primitive；DCIM、Cap、MLP hybrid 不替换 v3 原生宏。精确 SHA、文件哈希及函数行定位在 `source_map.json`。

- **DCIM**：锁定 `38eedf…` README 明确仅支持 256×256。`Param::Param` 的 `memcelltype=4` 对应该分支 `Type::DCIM`，默认 1 nm、`parallel_weightprecision=4`。`SubArray::Initialize` 的原生 addertree 以 256 行归约及 4 bit 并行权重初始化，感测/预充/写驱动含 `numCol/4`，布局/延迟含 `numCol/4/parallel_weightprecision`。不是 v3 的 128×16 逻辑 D6CIM/16 项 HCA/BFA。入口的组织 guard 只允许 256×256；D6 主方案保留完整原生 MAC 周期，不再次追加 SRAM read/ADC。
- **V1.5 Cap**：锁定 `9825ef…` 的相同数字 `4` 对应 `Type::Cap`。runner 在独立本地构建副本中只将构造输入 `memcelltype=2` 改为 4，使条件派生在构造期间执行；完整 diff 留在本地，没有修改时延公式。使用原 `ProcessingUnitInitialize → SubArray::Initialize/CalculateArea → CalculateLatency(true)`，分别调用 64/128 活动行、5/10 ns `chargeDelay`。原始 `colDelay` 为 2.5/5/10 ns，精确符合 `chargeDelay/128*numRowParallel`；感测 critical 对该项的增量还乘原 beta=1.4。该延迟是外部预算驱动的宏模型，不是极化/积分/恢复的物理求解。
- Cap 默认构造还显示 `resistanceAccess=1500 Ω` 先于条件内 `resistanceOn=1e20 Ω` 改写，不能通过最终枚举名称推断所有派生量相容。这里只按上游真实行为做接口探针，Cap 不成为主案例后端。
- Cap 的输入是等效列电阻向量、活动行数、外部建立时间与 peripheral 配置；`CalculateclkFreq=true` 返回物理秒的感测路径，第二遍同步路径则包含行分组、mux 和数字重构周期。没有返回 HZO 破坏性读/PL 恢复、GC current-programming/保持刷新，也没有原生 NAND string/SSL 时序。
- V1.5 README 的 `dac_precision` 只用于软件准确率，硬件 PPA 仍 bit-serial。不得将其当作任意 multibit DAC 硬件支持。
- **MLP hybrid**：锁定 `6098fe…` 的 `HybridCell` 含一份 `_3T1C LSBcell`、两个 `RealDevice` MSB（LTP/LTD）及 `WeightTransfer`。其服务是低有效位累积与向高有效位转移，不是 GC-04 八个 binary endpoint 平面的宏。GC-04 保持硅 CMOS、差分积分、按模式释放和周期刷新；此处不移植 hybrid 模型。

17 个机制/组织断言通过。probe 输出使用 17 位精度；DCIM 原型只调用构造器，Cap 调用原 C++ 初始化/时延路径，MLP hybrid 以源码结构核验。没有执行完整训练或生成十例性能值。
