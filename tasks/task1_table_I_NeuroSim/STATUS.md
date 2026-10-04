# Step 3 三个 pilot：完成并停止

接手基线 `e93cd8aec72d61d8a55c00c76453d58615ef5b67`（接口3.0.0）；器件基线 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`。**最终集成 PASS，独立全新编译复跑 PASS。**

|案例|Δ_S ns|T_R ns|ρ MB/s|τ MB/s|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|
|01 SRAM ACIM|3623.420115|11522.926080|35.325741|1421.861069|0.0248447205|3.180124224|
|02 SRAM DCIM|330|640|387.878788|3200|0.1212121212|1.939393939|
|05 RRAM|5783.968755|1949377.516224|22.130133|4.202367|5.2661113813|337.031128405|

- 实际调用：锁定V1.4的SAR、Adder、DFF及formula/Technology；全位宽组合树、符号/移位/反馈/控制/清零路径明确连接，数字周期分别11.252858/5/11.252858 ns。两拍重构期间保留已有SAR码，无额外中间bank。
- 保留：ACIM完整电荷前端/普通SRAM写，D6CIM完整16项HCA/BFA MAC/写，WH-2T1R正常/verify前端、独立20ns窗口及完整有限写流程。缺失聚合write返回null，完整混合T_R可计算。
- 明示工程条件：局部连接10µm及门负载/控制扇出，FF边界两级INV近似，32-bit控制状态；名义二进制ADC尺度仅用于算术诊断，不证明模拟精度。5/20µm小范围检查和独立物理服务扰动保存。
- 独立审查修复后，在 `/tmp` 启动 `runs/step3/review-final-20261004`，新编译三例，结果/快照/敏感性与 `integration-final-20261004` 完全一致；逐事件核算、服务公式及来源检查通过。单选DCIM和三例旧时间replay均实际运行通过。
- 完整Step2回归 `step3-review-regression-final-20261004` PASS。首次五组机制通过但README导航触发旧归档守卫失败，现场保留；仅放宽当前README导航例外，未改历史证据。
- 公共驱动/后端由supervisor唯一维护；三案例适配分工、独立本地运行，另设未参与实现的reviewer。最终报告与当前入口更新，历史验收原文在下方保留。
- 未运行：其余七例、三情景/大扫描、独立上游256×256 DCIM对照、论文/Table II修改；没有安装、上游工作树写入、Git暂存/提交/推送。用户 `.DS_Store` 修改保留。

入口：[主报告](reports/step3_pilots.zh.md)、[总表](results/step3/integration-final-20261004/summary.csv)、[独立审查](reports/step3_review.json)、[统一CLI](scripts/run_step3.py)。公共链具备后续扩展条件，其他案例仍需各自适配，本轮到此停止。

---

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
