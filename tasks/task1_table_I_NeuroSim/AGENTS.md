# Step 3 当前工作约定

用户已授权的三个 reference pilot（01 SRAM ACIM、02 SRAM DCIM、05 RRAM）已完成并独立验收。当前停止在 Step 3，不扩展其余案例、不改历史验收。

- supervisor 唯一维护公共 `pilots/backend*`、`pilots/schedule.py`、`scripts/run_step3.py`、公共报告和导出；案例 agent 只写分配的 `pilots/adapters/<case>.py` 与 `<case>.zh.md`。
- 每 agent 本地使用独立 `runs/step3/<role>-<id>`，共享锁定 worktree、兄弟 NVM、Table II、论文只读。所有构建、完整日志与大 trace 留本地。
- Step 2 配置和证据不改；生效值另存 Step 3 快照。采用接口 3.0.0 与已有路径/环境变量。
- reviewer 不修改实现，在新的本地目录实际编译复跑，再核对调用、数值、来源与计量；supervisor 白名单导出审查结论。
- 不暂存、提交或推送；保留用户 `.DS_Store` 修改。

以下为历史 Step 2 工作约定（原文保留，不限制已授权 Step 3）：

# Step 2 工作约定

- 本轮仅做 Step 2：源码覆盖、十例典型输入接口及机制探针。Step 1 已归档；不生成十例新性能表，不进入 Step 3。
- 当前轮为 `faf8a421…` 上的 Step 2 收敛修订：数字时钟/原生服务边界、物理与能力依赖、数字覆盖状态、资源量纲及旧时间回放。既有结果证据保留，新修订使用独立运行目录。
- 仓库内只写本目录。兄弟 NVM、Table II、论文及用户原有修改保持只读；不暂存、提交或推送。保留用户提供的 README。
- supervisor 为唯一集成写入者，负责 contracts、scripts/check_step2.py、公共报告、provenance/step2*、results/step2、AGENTS/STATUS。需要补取锁定源码也仅由 supervisor 操作 Git/worktree；不安装工具链，不修改共享源码树。
- 子任务 A 只写 probes/read_timing；B 只写 probes/write_update；C 只写 probes/special；D 只写 configs/cases 和 probes/encoding_resources。各自本地运行目录为 runs/step2/<role>-<id>，构建副本独立。不得共改 Param.cpp，不得覆盖 Step 1 证据。
- 本轮两组只写 `probes/interface_revision/` 中各自的 clock_dependency 或 digital_resources 文件/注释/必要小探针；不直接修改公共文件。supervisor 作为唯一集成者更新生成器、配置、schema、公共脚本与报告，并实现独立旧时间回放。
- 独立 reviewer 在集成后只读复核，使用新的本地目录运行最终统一入口；证据先保存在本地，再由 supervisor 白名单导出。
- 运行根默认 `$HOME/neurosim`，先解析真实路径并验证不在云盘；源码、构建、完整日志、缓存和临时文件全部留在运行根。云端仅保存小型规范脚本/配置、版本证据、必要数值输出与报告，不建立本地树符号链接。
- 稀疏检出按实际文件清单；MLP 根目录数据包不得获取。锁定完整 SHA，不静默跟随远程更新。
- 上游公式保持原样；必要移植改动单列补丁。探针只验证机制和接口，不生成正式 rho/tau。完整原生周期保持 opaque block，不推测拆除外围后再次计费。
- 入口从任意 cwd 可用，路径完整引用；可重入并产生新运行目录。标准库优先。文件只按白名单导出。
- 探针 runner 统一 CLI：`python3 run.py --root <local_root> --out <new_local_dir> --cxx <compiler>`；输出 summary.json、命令/退出码、原始输出及断言。后端由根目录 worktrees.json 定位；stdout 简短。规范脚本先复制本地并记录哈希，禁止在云端产生 pycache。
- 十例采用 INT8 的 Byte/element 计量；GC-04 保持硅 CMOS gain-cell，NAND 保持 split-sign/base-4。工艺、原生器件负载、枚举身份与阶段计数分开记录。
- 本轮收敛修订验收后停止；仅在用户启动 Step 3 时实施 01 SRAM ACIM/05 RRAM 两个 pilot。使用 contracts 3.0.0、集中初始化和显式计数，完整原生写周期不拆除再叠加驱动。秒返回无换算 clock_id；constraint_clock_id 只标路径归属，完整且已实例化的单周期寄存路径才能约束数字时钟，独立模拟/器件服务不行。旧probe说明记录当时机制，当前公共政策以 parameter_policy.json 为准。
