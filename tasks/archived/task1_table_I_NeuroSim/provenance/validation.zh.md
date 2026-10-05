# 复算与来源验证

2026-10-05：十例的 optimistic / reference / pessimistic 配对工程情景完成集成运行及未参与实现的独立复核。独立包只带当前公共代码、十份 input.json、十份 scenarios.json 与源码锁；外部环境只提供锁定 NeuroSim 源码/编译器，不读取 archive、旧结果或兄弟 NVM 运行产物。

- 每例一次全新编译，共 10 个二进制；各情景独立实际执行，共 30 个成对结果。各例三情景的编译结构、二进制哈希相同，模块调用、原生提前量资格和调度分别执行。
- 13,046 个 reference 逐叶值精确一致，唯一排除项是记录接口解耦的 Python 后端源文件哈希；393 条阶段行及 592 项独立检查通过。独立服务公式核对 raw/effective 时间、全部参数消费者、固定资源/计数、共享 SAR/时钟、维护与两率，不依赖生产适配器/调度器计算答案。
- 69 个情景来源值以及所收录原文摘录、原文件哈希一致。源字段、原单位、条件和消费者在各例 scenarios.json 中。
- 原典型权威 JSON 保持字节不变，SHA-256：`2ae8f342b777798d2f3c6ff3266462acc33ad34686fea1f097362f6b3ee4ed24`；全新计算出的 reference 文档也与其完全相等。
- MRAM 原 3 ns 读候选实际未通过既有资格检查：pin settle 为 3.36230030248378 ns；见[排除记录](../analysis/06_mram/excluded_candidate_checks.json)。普通 optimistic 采用有来源且合法的 5 ns 读与 20 ns 写条件。
- 单例或单个非 reference 情景的 `--export` 实际被拒绝，避免部分结果覆盖完整权威表。

GC 三情景都可持续；保持帧均为 399998.5 ns。optimistic / reference / pessimistic 的 busy 分别为 53504 / 66176 / 81664 ns，guard 为 82.5 / 115.5 / 165 ns，可用率为 0.8660332476246786 / 0.8342706285148569 / 0.7954267328502482。两率统一使用重新计算的有效间隔。

正式图表只读取当前完整精度数据；来源和实际渲染检查见[图表说明](../analysis/11_summary_figures/README.zh.md)。情景只覆盖声明的工程服务预算，不追加材料统计、PVT、模拟精度或完整阵列认证；原有适用条件见 [METHOD](../analysis/METHOD.zh.md)。

长审查报告、输入快照、新构建、完整 trace、日志和失败现场仅留本地区 `$NEUROSIM_ROOT/runs/paired-scenarios-20261005/` 及 `runs/cim-reference/paired-engineering-verified-20261005/`。本轮 archive 与兄弟任务保持只读；历史恢复索引见[归档说明](../archive/README.zh.md)。

本地主要审查证据及 SHA-256：

- `integration/integration_validation.json`：`d9d912d8ae3ccfabbc962dbf8f719262291486b2f51dee891c4e0ef803f95b8f`
- `reviewer/independent_paired_review.json`：`73056b89036276abb8c56d1e90131ba82aedaa75797f23a5dd46f038444f56a3`
- `reviewer/scenario_sources_review.json`：`551f772dd326bd0933d9dfebcf87e7557b52aaaeda4279ab9dd672ffdf9a7b77`
