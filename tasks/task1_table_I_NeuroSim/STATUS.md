# Step 4：十例 reference 完成并停止

基准 `ab306ed8f804a8056e27f9763a8a8cc9bbd89b22`。**十例统一主运行 PASS；独立新目录编译复跑、来源与数值审查 PASS。**

- 主结果：[十例表](results/step4/reference-final-20261004/summary.csv)、[中文报告](reports/step4_reference.zh.md)、[接入表](reports/step4_model_routes.zh.md)、[独立审查](reports/step4_review.json)。
- 统一入口 `scripts/run_step4.py` 支持全部十例、单选和旧时间回放；输入/输出3.0.0与pilot时序2.0.0不变，新增Step4执行扩展1.0.0。
- 新七例实际运行 DFF/Adder/formula 与相容 SAR。没有将 NOR/NAND/MRAM/PCM/FeRAM/GC/垂直 AND FeFET 改称其他阵列类型；MemCell占位字段没有被这些调用读取。原生完整周期与特殊负载保留。
- 三个pilot完整 `result.json` 与已验收Step3 V2相同；旧代码和历史运行证据只读。
- 新七例周期：NOR10、NAND9、MRAM11、PCM9.5、FeRAM10、GC11、FeNOR10 ns。32项MAC与各自实际重构/选择/读验路径决定合法周期，没有继承pilot多拍资格。
- GC raw Δ_S/T_R=4246/25344ns；维护H=73216ns、guard=132ns、alpha=0.81663；有效ρ/τ=12.309072/131.980606MB/s，不可行负例返回null。
- 十例旧时间回放、完整Step2回归、模板/展开等价、共享消费者与非法时钟检查通过。独立 reviewer 从 `/tmp` 启动 `runs/step4/reviewer-final-20261004`，独立闭式边沿公式及来源指针/单位/哈希通过。
- 修正了审查发现的输入/暂存/终验选择路径、控制状态分配、PCM严格阈值边界和GC边沿slack诊断；正式结果只使用修正后新构建。失败/中间现场保留本地。
- 保留明确限制：NAND仿射/校准乘除完整路径与工作状态；PCM阈值表/存储/标定；FeRAM原生并行负载；GC保持/重复刷新准确度。不是完整宏PPA、STA或实物验证。
- 未开展Step5三情景、大扫描、workload mapping或论文排版；无Git暂存/提交/推送。718个受保护文件与全部锁定工作树保持不变，用户 `.DS_Store` 修改保留。

本地最终运行：`/Users/shine/neurosim/runs/step4/reference-final-20261004`；源码、构建、完整trace留本地，管理区仅规范代码、关键快照、结果、来源和审查。

---

# Step 3 V2：完成并停止

审查基准 `88448197c570b113f6002524aaacd1bd8865ca86`。**最终主运行/独立新目录编译复跑PASS，无剩余阻断项。** V1历史证据保留。

|案例|时序下限ns|运行周期ns|Δ_S ns|T_R ns|ρ MB/s|τ MB/s|
|---|---:|---:|---:|---:|---:|---:|
|SRAM ACIM|3.278867|5|2890|5120|44.290657|3200|
|SRAM DCIM|2.616069|5|330|640|387.878788|3200|
|RRAM|3.216484|5|4490|1911765|28.507795|4.285045|

- E0→E2：SAR码、输入位/组选择、旧累加值保持；E1只更新phase；E2写回输出，无新增中间bank。phase→capture-enable、控制/I/O/clear/verify_done仍为单拍。
- 重构采用明确9/11/15bit加权树和23bit符号融合累加；公开Adder尺寸/电容及formula提供门级位到达模型。同一图执行算术检查；固定资源的恒定输出门仍保留输入负载。
- 数字时序下限与运行周期分开。主政策保持合法5ns目标，少量5.25/5.5ns工作点分别报告完整rho/tau。短连线同频对照通过，非法同频请求拒绝。原生5ns写及真实公共写口间隔分开。
- V1原C++保留为 `backend_v1.cpp`；实际重建5µm/10.5ns对照得到ACIM3381ns、RRAM5397ns streaming，未作为V2目标值。
- 主运行 `runs/step3-v2/integration-audited-v2`；独立 `review-audited-v2` 在/tmp发起全新编译。结果/快照/敏感性/工作点/时序检查逐字节一致，另独立核算服务公式、事件账本和编译门图算术/物理负载。
- 单选DCIM、旧时间回放、完整Step2回归PASS；V1与Step2输入哈希未变。冻结输入/输出3.0.0继续校验；Step3时序扩展2.0.0明确局部演进。
- 原生前端/D6CIM MAC/SRAM写/RRAM有限写验、rail、独立20ns窗口和失败不发布均保留；缺失聚合写仍null。没有重新估计器件参数。
- 没有其余七例、大扫描、NVM/TableII/论文/锁定上游改动；没有Git暂存、提交、推送。用户 `.DS_Store` 保留。

入口：[V2报告](reports/step3_v2_pilots.zh.md)、[V2结果](results/step3_v2/integration-audited-v2/summary.csv)、[V2审查](reports/step3_v2_review.json)、[统一CLI](scripts/run_step3.py)。结果限于公开模型/原工程条件，不声称STA或实物精度。本轮停止在三个pilot的Step3 V2。

---

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
