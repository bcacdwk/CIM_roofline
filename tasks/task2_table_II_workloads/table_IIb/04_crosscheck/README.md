# Step 4 · 独立复核与统一汇总

Agent D 的只写目录。已按主 Agent 的明确 READY 通知锁定 **A revision 2 / B revision 2 / C revision 1**，独立验证 60 个汇总与 146 个分项；这是内部交付，不代替用户审阅，也不启动 Step 5。

- [中文复核报告](REVIEW.zh.md)：方法、重点结论、pilot 对照、受保护文件和复算记录。
- [双边界四行六模型预览](PREVIEW.zh.md)：精确 RI，模型／B／L 顺序不变。
- [统一 JSON](data/results.json)：60 条完整原始结果，加原目录、results SHA-256、DELIVERY revision/hash、case_id 和 JSON Pointer。
- [统一 CSV](data/results.csv)：**412 条数据行，另有一行表头**。60 个汇总与146个分项各列 ports/operator 两边界；含精确 Q_S、Q_R、RI、调用、容量、B/L、append 和追踪字段。
- [独立检查结果](data/checks.json)、[输入与来源锁定](data/config.json)、[READY 通知锁](data/ready_sources.json)。
- [本目录最终交付清单](DELIVERY.json)：本地文件SHA-256与复算入口。

## 复算

从仓库根目录运行：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/crosscheck.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/verify_delivery.py
```

默认只读：校验上游最终 DELIVERY 清单的全部哈希；读取原始配置与固定实现；独立重算所有汇总、分项、tile、容量、调用及 append；比较全部22条pilot既有语义字段；运行5项既有默认只读回归；检查受保护 tracked 文件及 study_plan 的科学输入。最后逐字比较本目录5份生成物。约数秒完成，不编译／渲染旧 PDF，不导入生产 counting.py 或三个生成器作为预期值。

如经新的明确 READY 通知接受上游修订，先更新本目录 `data/ready_sources.json` 的通知锁，并在数据也变化时复核 `scripts/crosscheck.py` 的明确数据哈希；重新运行全量审阅。仅在需要刷新本目录生成物时使用 `--emit`。它只写 `04_crosscheck/`，不能修改上游。`--numeric-only` 是文稿修订等待期间的准备入口，不校验最终文稿清单，不生成交付产物，不可代替正式验收。

## 数据约定

统一 JSON 沿用原分项和精确值：整数不转浮点，非整数分数为 `{numerator, denominator}`，无穷为字符串 `infinity`。CSV 将分数写成 `p/q`、无穷写成 `∞`；operator 未定义 tile 调用数原为 null，在 CSV 中留空。JSON 内保留完整形状／调用直方图和初态；CSV 中 `matrix_N_K_per_copy` 与 `append` 为 JSON 文本。

CSV 的30列依次覆盖身份（case_id/model_id/revision/layer/row/B/L）、component/boundary、4项需求、5项矩阵与容量信息、operator 去重量、4项窗口初末状态、append，以及6项来源追踪。`component=total` 为汇总，其余为语义矩阵；CSV 的 JSON Pointer 指向该边界需求对象，统一 JSON 的 trace 指向上游原 case。

读取顺序是六模型固定顺序，模型内依 QKV、FFN、Prefill、Decode，扫描依 B=8/64/512、L=1024/16384/131072。全体遵循 `WS128-INT8-semantic-banks-v1`，ports 为主，operator 为对照。INT8 是研究逻辑参考；无整模型性能／硬件排名结论。

本目录不另造 PDF，不重写 A/B/C 三份底稿。旧稿、原始来源、shared、II(a)、pilot、Task I 和主论文只读。起点与保护基准均为 `e472a0d864b8fb9afb14b0c306217a0e5653e122`；README 和 study_plan 状态可由主 Agent 收尾更新，科学输入子集保持不变。
