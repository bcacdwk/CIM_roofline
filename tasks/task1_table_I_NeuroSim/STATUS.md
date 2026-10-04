# Step 2 定向收敛修订

当前基准/HEAD：`faf8a42165e5d3655ec0fe70f4597e4baebe3f6f`（`task1_neurosim_step2`）。器件基线仍为 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`。**最终集成 PASS，修复后独立复跑 PASS，本轮已完成并停止。**

- 保留：V1.4／22 nm／LSTP／300 K、六个锁定SHA、十例身份/原生资源/编码、GC-04、缺失写返回null、完整原生服务。
- 数字时钟：5 ns目标；只受本域已实例化的完整单周期寄存路径约束。独立模拟/ADC/器件服务仅阻塞相关资源，在明确数字消费边界对齐一次。
- RRAM窗口：独立20 ns原预算，SAR位数不驱动；T_B=T_A只为默认关闭的能力政策对照。PCM/GC/NAND真实共享依赖保留。
- 接口3.0.0：覆盖状态区分路由、构件探针、案例pending与原预算；写资源区分电气输出、选中目标、编码装载单元、逻辑Byte和更新域，不从偏置输出或端口推导编程并行度。
- PASS：原466条机制检查、新408条收敛/资源/回放检查、9条输出接口检查；统一运行 `step2-revision-unit-reviewed`。
- PASS：十例原有时间独立回放；streaming、完整resident及GC busy/guard/维护后服务与v3一致，最大浮点差约4.7e-10 ns。没有以旧总时间作输入，没有新时钟/边界策略混入回放。
- PASS：独立额外审计164项；资源单位/批数负例缺口已修复。最终两次运行1792个数值字段逐值一致，独立运行 `step2-revision-independent-final-20261004`。
- 原Step 1和Step 2结果证据保留；`.DS_Store`仅记录。没有新依赖、上游/兄弟目录写入或Git操作。
- NOT_RUN：Step 3、十例新NeuroSim性能、三情景扫描、主论文/Table II改动、暂存/提交/推送。

入口：[主报告](reports/step2_coverage_and_interface.zh.md)、`contracts/`、`configs/cases/`、`scripts/check_step2.py`、`probes/interface_revision/`。本轮独立审计为 `reports/step2_revision_review.json`，原审计仍为 `reports/step2_review.json`；Step 1报告和smoke目录未变。

下一轮仍为01 SRAM ACIM、05 RRAM两个pilot，需实例化实际寄存路径/负载、SAR码保持、数字门控/符号/累加与消费边界；未覆盖模拟窗口、高压操作等继续原生服务。本轮不启动。
