# NeuroSim 与器件估计结合的 CIM 评估

本评估结合文献支持的器件与阵列服务估计、NeuroSim 电路模型，以及明确的映射和调度政策，计算 resident–streaming 两路服务能力。十个参考配置采用各自已声明的阵列组织、精度、资源和服务预算；结果不是等面积或等精度的通用材料排名。

- [方法、边界与适用条件](analysis/METHOD.zh.md)
- [Table I 与 rho–tau 图](analysis/11_summary_figures/README.zh.md) · [两页 PDF](analysis/11_summary_figures/output/table_I.pdf)
- [完整精度权威数据](analysis/data/ten_case_results.json) · [CSV](analysis/data/ten_case_results.csv)
- [验证摘要](provenance/validation.zh.md) · [输入来源](provenance/input_sources.json) · [NeuroSim 版本锁](provenance/neurosim.lock.json) · [上游版权与引用](provenance/upstream-notices.txt)
- [历史归档索引与恢复说明](archive/README.zh.md)

## 目录

```text
README.md / AGENTS.md
analysis/
  METHOD.zh.md
  shared/                     复算入口、选定后端、适配器、时序与服务输入
  01_sram_acim/ ... 10_fenor_3d/  输入、资源/映射、结果与简要说明
  data/                       十例权威 JSON、自动派生 CSV
  11_summary_figures/         原 NVM 风格的绘图脚本与正式表图
provenance/                   来源、真实上游版本/版权及简短验证摘要
archive/                     原相对路径历史树、迁移清单和维护证据
```

每例的 `input.json` 包含逻辑计量、器件 primitive、物理映射、资源与服务组织；`resolved.json` 记录该输入的实际模块返回、时钟和调度，`result.json` 保存 raw/effective 时间、分阶段计数、维护及结果。`stage_sources.json` 区分来源类别。主表图只读 `analysis/data/ten_case_results.json`，不从归档或其他任务补值。

## 完整复算

先保留既有 `$NEUROSIM_ROOT`（未设置时为 `$HOME/neurosim`）及其中的 `worktrees.json`。所需源码为锁定 NeuroSim `2DInferenceV1.4`、SHA `8a88abf85844c0e1ba17cc771ea535fff6040456`；入口会检查共享源码与 Git blob 一致，并为每例重新复制、构建。需要 Python 3、`g++-16`（可通过 `NEUROSIM_CXX` 或 `--cxx` 指定兼容编译器）。不会下载或更新源码。

```sh
TASK_DIR="<仓库>/tasks/task1_table_I_NeuroSim"
python3 -B "$TASK_DIR/analysis/shared/run_evaluation.py" --run-id reference-check
# 上一个 run-id 已存在时需换一个新名称；成功后按白名单更新现行业务数据：
python3 -B "$TASK_DIR/analysis/shared/run_evaluation.py" --run-id reference-export --export
```

默认运行仅写本地区 `$NEUROSIM_ROOT/runs/cim-reference/<run-id>/`，保留调用、输入哈希、新构建、完整 trace 和日志。最小运行快照只有当前公共代码、十份输入和版本锁，不含归档、旧结果、兄弟任务产物或文献 PDF。`--export` 只导出十例业务结果及小型来源证据；重新绘图是独立操作。

## 只重绘表图

```sh
/opt/anaconda3/bin/python -B "$TASK_DIR/analysis/11_summary_figures/build_figures.py"
```

所需绘图工具、参数与输出见[图表说明](analysis/11_summary_figures/README.zh.md)。绘图不构建 NeuroSim。速率使用十进制 MB/s；GC-04 为易失性 gain-cell eDRAM，其速率使用维护后的长期有效间隔，raw 单次时延另列。`10_fenor_3d` 的实际技术是垂直 AND FeFET。
