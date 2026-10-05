# 历史归档与恢复索引

`history/` 保留迁移前任务树的全部 1101 个文件，沿用原任务目录相对路径，合计 14,966,596 字节。原文、机器结果、版本名称、历史路径和时间戳语义不改写；归档后的每个文件 SHA-256 与迁移前清单一致。原 HEAD 为 `8d75481fbf0d9005c5285ff4b4fecdb9f7d6a5e6`。

- [原路径 → 归档路径、大小及 SHA-256](migration_manifest.json)
- [迁移保全检查](maintenance/consolidation-20261005/migration_verification.json)
- [集成复算回归](maintenance/consolidation-20261005/integration_regression.json)
- [独立复算审查](maintenance/consolidation-20261005/independent_reproduction.json)
- [独立迁移与恢复审查](maintenance/consolidation-20261005/independent_migration_review.json)
- [独立图表与方法说明审查](maintenance/consolidation-20261005/independent_figures_review.json)
- 所选计算证据：[十例历史机器入口](history/results/step4_v2/reference-v2-final-20261004/summary.json)、[原报告](history/reports/step4_v2_reference.zh.md)、[原审查](history/reports/step4_v2_review.json)。历史定位提交为 `b7795fd5acc8f5f3816d1022111330fc569b6853`；它与迁移前 HEAD 的这些计算代码/输入/结果一致。

本次维护记录在 `maintenance/consolidation-20261005/`。迁移前本地全树快照、独立结果证据和完整构建/trace 留在 `/Users/shine/neurosim/runs/consolidation-20261005/` 与 `/Users/shine/neurosim/runs/cim-reference/`，没有将本地运行树搬入同步目录。

历史文档中的任务内相对路径应以恢复后的原树解析；原文内指向旧管理区的路径可按迁移清单映射到 `history/`。不要求历史命令在新管理区原路径直接执行。恢复脚本只向全新的非同步本地目录复制，并逐项验证哈希：

```sh
python3 -B "<本任务>/archive/restore_history.py" --out "$HOME/neurosim/runs/restored-task"
```

恢复包含原任务树；历史命令若依赖当时的兄弟任务或工具环境，需要另外按其锁与来源记录准备，当前正式复算不需要它们。当前业务入口见 [README](../README.md)。归档不作为当前模型的输入或绘图数据源。
