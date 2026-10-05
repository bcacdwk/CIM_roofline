# Step4 V5

七例21个带明确模型条件的成对服务点已完成；只读加入V4九点后为10类30点。GC-04是易失性存储。已完成实际新构建、逐点独立哈希绑定和最终表图独立复核，停止在V5。

- [中文总报告、参考值与范围](REPORT.zh.md)
- [21点CSV](results/final-reviewed-20261005/points.csv) / [JSON](results/final-reviewed-20261005/points.json)
- [30点总表](results/final-reviewed-20261005/combined_points.csv) / [旧NVM独立背景](results/final-reviewed-20261005/legacy_background.csv)
- [七例圆图](results/final-reviewed-20261005/figures/v5/v5_rho_tau_circles.png) / [十类圆图](results/final-reviewed-20261005/figures/ten/ten_rho_tau_circles.png)
- [运行、计算包与后处理](RUNNING.zh.md)
- [最终运行manifest](provenance/final_run_manifest.json) / [21点独立绑定](results/final_review_bindings.json) / [最终图表审查](reviews/p5_overview/review.json)
- [来源和接口](INTERFACE.md) / [图形规则](PLOT_PIPELINE.zh.md) / [保护审计](provenance/preservation.final.json)

最终compute-only包在 `/Users/shine/neurosim/runs/step4-v5/packages/final-compute-seven-r2-20261005`，最终运行集合在 `/Users/shine/neurosim/runs/step4-v5/integration/final-seven-complete-20261005`。构建、缓存、完整trace和二进制均在非同步区；没有git add/commit/push。

先前候选、failed/partial证据和阶段说明保留；最终资格以总报告、final manifest和review绑定为准，不沿用修复前PASS。原阶段及其停止约定作为历史保留，本轮未进入新器件、workload、DNN训练或论文修改。
