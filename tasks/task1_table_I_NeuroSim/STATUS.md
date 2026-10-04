# Step 2 已完成

**功能验收 PASS，独立复核 PASS；无功能阻塞。** 当前 HEAD 为已审阅提交 `e519b923382d03d3e54c043f02c59c01a20919f3`；器件基线仍为 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`。

- PASS：V1.4 / 22 nm / LSTP / 300 K 为公共低压主后端；5 ns 目标周期，实际周期由所用完整组合/感测路径约束。原生器件负载不随工艺缩放。
- PASS：接口 2.0.0、十例典型规格、唯一计时提供方、嵌套服务计划、来源定位及生成覆盖表。保持 GC-04 硅 CMOS 和 NAND split-sign/base-4，不生成新十例性能。
- PASS：四组机制探针 52＋69＋17＋328＝466 条断言，另8条输出单位/缺失值检查；最终独立新目录复跑通过，C++数值与首次独立运行完全一致。
- PASS：独立审计50个 primitive 来源/SI换算、60次源哈希和41条上游映射；两项发现（秒返回 clock_id、MRAM完整方向写槽绑定）均已修复并复跑确认。
- PASS：原 NVM、Table II、论文和 Step 1 归档不变（获准修改的 AGENTS/STATUS 除外）；共享上游 clean；无新增依赖或Git暂存/提交/推送。
- FAIL（非阻塞元数据例外）：根 `.DS_Store` 在会话期间持续出现未归因变化，前后哈希在独立审计中，未恢复。独立审计共448项，447 PASS，此项单列。
- NOT_RUN：完整十例仿真、三情景扫描、正式rho/tau/PPA、TeX/PDF和Step3。

交付入口：[主报告](reports/step2_coverage_and_interface.zh.md)、[独立审计](reports/step2_review.json)、`contracts/`、`configs/cases/`、`probes/`、`scripts/check_step2.py`、`provenance/step2_source_map.json`、`results/step2/step2-integration-reviewed/`。

下一轮仅实施 **01 SRAM ACIM 与 05 RRAM** 两个混合服务 pilot：生成集中初始化，绑定原生负载/实际时钟/寄存复用；调用 SAR 和显式数字模块，保留电荷域前端/普通SRAM完整写，以及RRAM独立CIM/verify前端、有限RESET/SET尝试与全装载rail。主报告已列具体函数、宽度和阶段边界。本轮到此停止，没有待用户处理的阻塞动作。

## Step 1 归档状态

**Step 1 功能验收 PASS，独立复核 PASS，无阻塞。** 日期：2026-10-04。本轮已停止在 Step 1，Step 2 尚未启动。

- PASS：本地 HEAD 为 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`，提交为 `task1_refine_v3`，与指定基线无差异。
- PASS：已读本目录 README、NVM README、共同计量约定与共享基线 README；未遍历十例文献或历史归档。
- PASS：初始状态已保存至 `provenance/repository.initial.json`；已有 `.DS_Store`、`tasks/.DS_Store` 修改和本目录 README 保留。
- PASS：本地非云运行区、跨目录读写执行、GNU GCC/libgomp 的 arm64 OpenMP 实算。
- PASS：15 个远程 heads 已登记，六个重点快照与指定 SHA 一致，源码/README 按白名单稀疏准备。
- PASS：V1.4 和 DCIM 原版 C++ 后端编译，无源码补丁；V1.4 原 main 两次非空计算、49 条稳定数值精确一致。
- PASS：独立 reviewer 从 `/tmp` 使用最终入口在 `review-20261004T031950Z` 新目录重新编译与复跑，管理区保持只读。最终版两次非空数值再次一致。
- PASS：云端白名单；旧 NVM、Table II、论文、原 README 和 `tasks/.DS_Store` 未变；暂存区为空。
- FAIL（元数据例外）：根 `.DS_Store` 初始哈希不一致，且复核后再次变化；各快照见审计记录，归因未知，未回退；不影响功能验收。
- FAIL（非阻塞）：Homebrew GCC postinstall 遇到既有 Homebrew/formula API 不兼容；安装产物及实际编译、链接、运行均可用，详情见环境记录。
- NOT_RUN：Step 2–6、正式 rho/tau 适配、十例评估及 Git 暂存/提交/推送。

交付入口：`reports/step1_setup.zh.md`、`reports/step1_review.json`、`provenance/neurosim.lock.json`、`provenance/environment.json`、`results/smoke/review-20261004T031950Z/`。脚本入口为 `scripts/setup_step1.sh` 与 `scripts/smoke_step1.sh`。

下一步指向 README 的 **Step 2：后端覆盖与接口设计**，另行安排。没有需要用户处理的阻塞动作；未暂存、提交或推送。
