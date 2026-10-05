# Step4 执行接口 1.0.0

冻结输入/输出3.0.0与Step3时序2.0.0不改。新增执行扩展逐案例显式分派，旧pilots只读。

## backend

`build(case, root:Path, out:Path, cxx:str, own:Path) -> execute`
`execute(label, wire_um=10., bits=10, operating_period_ns=None) -> dict`
返回至少 `actual_period_ns,timing_min_period_ns,policy_min_period_ns,selection_policy,boundary_setup_ns,sar_ns,paths,raw_module_returns,module_inventory,coverage,arithmetic_checks`。
backend直接读取case资源/服务，不依赖adapter。显式支持7个case ID，未知拒绝。无额外pipeline/影子缓存。必要的阶段预算及未覆盖路径须写coverage；原生时长不成为时钟下限。

## adapters

`build(case, p, b) -> dict`，p由现有legacy_replay.parameters从冻结输入获得ns，b为backend返回。
返回 `streaming,resident,maintenance` 事件序列；`snapshot,checks`；可选 `atomic_streaming,atomic_resident`（GC guard非抢占单位）及 `maintenance_period_ns`。
事件：`{id,kind,provider,resources,...}`，kind=physical时`ns`，digital时`cycles`，boundary时可含`margin_ns`。数字下一消费者才对齐边沿，physical子阶段不各自取整。事件可携带`coverage_status`、`source_refs`、`mode`。
重复模板：`{repeat: int, axis: str, steps: [...]}`，只重复完整有序模板，不直接乘子阶段。supervisor调度器支持模板和普通事件；可进行首轮/稳态模板等价压缩，必须保留计数和边界等待。
不要导入任何公共辅助模块以免名称冲突；在各自adapter定义简单事件构造。数字count为冻结输入中的次数，修改必须解释。`build`不调用旧计算器，也不读取旧总数。
`numerical_checks(case, repo:Path) -> dict`（建议）：只读规范输入与原数值合同，返回检查结果/层级/限制；允许读旧诊断作对照但不作为新模型目标。

## 独立性

旧时间回放由原legacy_replay独立执行，仅聚合后才读旧结果比较。主新模型不从旧总数反推。所有作者先实际单元运行本地，返回少量结论，不导出完整trace。
