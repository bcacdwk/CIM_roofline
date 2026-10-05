**最新：B组独立三点PASS，supervisor D035内部accepted。下面记录保留作者交付阶段。**

# 当前：完整三点ready_for_review，生产冻结

完整模型/输入/三个fresh结果已落，入口REPORT.zh.md、candidate_points.json、reference_snapshot.json、diagnostics.json。共同计算SHA090bd4723ad86566350ac6dc4e9721a5d85af76b7fc4d052748c0e50bcd445fb。

K32N16、4096数据HV1T1C、128reference/SA、128真实恢复与外写，BL250.138fF；source100ns域转为稳定bias之后额外100ns保守policy。14/20/50ns是完整写服务一次/行，HVfloor11.23ns，绝不每极性拆14ns。完整read/restore/target/PE在同一输入生成，无旧性能replay。

B组已收到最终三点并做一次轻量fresh独立审查。生产只处理影响机制、数量级、实际计数的大问题，不再扩微观研究；小未知公开为条件。更早charge/原生不兼容探针留本地作为失败/路线证据。
