# Step 1 状态

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
