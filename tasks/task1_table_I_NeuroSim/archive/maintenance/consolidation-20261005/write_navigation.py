from pathlib import Path
import json,hashlib
base=Path('/Users/shine/neurosim/runs/consolidation-20261005/integration');cur=base/'current'
(cur/'README.md').write_text('''# NeuroSim 与器件估计结合的 CIM 评估

本评估结合文献支持的器件与阵列服务估计、NeuroSim 电路模型，以及明确的映射和调度政策，计算 resident–streaming 两路服务能力。十个参考配置采用各自已声明的阵列组织、精度、资源和服务预算；结果不是等面积或等精度的通用材料排名。

- [方法、边界与适用条件](analysis/METHOD.zh.md)
- [Table I 与 rho–tau 图](analysis/11_summary_figures/README.zh.md) · [两页 PDF](analysis/11_summary_figures/table_I.pdf)
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
python3 -B "$TASK_DIR/analysis/11_summary_figures/build_figures.py"
```

所需绘图工具、参数与输出见[图表说明](analysis/11_summary_figures/README.zh.md)。绘图不构建 NeuroSim。速率使用十进制 MB/s；GC-04 为易失性 gain-cell eDRAM，其速率使用维护后的长期有效间隔，raw 单次时延另列。`10_fenor_3d` 的实际技术是垂直 AND FeFET。
''')
(cur/'AGENTS.md').write_text('''# 本任务区工作约定

当前任务是十个参考配置的 NeuroSim 与器件估计结合的 CIM 评估。当前入口为 `analysis/shared/run_evaluation.py`；表图入口为 `analysis/11_summary_figures/build_figures.py`。先阅读 README 和 METHOD，保护用户已有修改。

- 当前业务名称不使用项目版本号、final 或 latest；真实 NeuroSim 分支、SHA、接口版本与上游版权必须保留。
- 计算只读取当前公共代码、小型服务输入和各例 input.json；归档与历史比较只能用于审计，不作为生成新结果的模型输入。主表图只读取 analysis/data/ten_case_results.json。
- 保持所选器件身份、逻辑精度、资源、调度、维护和预算。任何新模型研究都需用户明确新任务；不要在维护中自动引入历史替代分支。
- 构建、源码副本、完整 trace、日志、临时文件、PDF 渲染与失败现场全部留在非同步本地区，默认 $NEUROSIM_ROOT 或 $HOME/neurosim；禁止先在 OneDrive 生成再删除，也不建立通往运行树的 symlink。
- 当前目录仅保留规范代码、输入、必要结果、正式图表与简短来源/验证说明。过程记录放 archive/maintenance 或本地区。archive/history 原始文件按哈希保全，不重写历史报告。
- 兄弟 NVM 任务、Table II、论文及其他任务区只读。本轮用户未授权 git add、commit、push 或清理无关修改。
- 多人协作时仅指定的集成维护者执行实际移动/安装；其余候选在各自本地目录，独立审查使用新构建，不复用生产二进制。
''')
names={'01_sram_acim':'SRAM ACIM','02_sram_dcim':'SRAM DCIM','03_nor_2d':'2D NOR','04_nand_3d':'3D NAND','05_rram':'WH-2T1R RRAM','06_mram':'MRAM','07_pcm':'PCM','08_feram_hfo2':'HZO FeRAM','09_gain_cell_edram':'GC-04 gain-cell eDRAM','10_fenor_3d':'垂直 AND FeFET'}
notes={'01_sram_acim':'所选模拟 SRAM 参考实现；10-bit SAR 容器与条件标定部分和，不能视作经过模拟精度认证。','02_sram_dcim':'所选数字 SRAM 参考实现；原生 MAC 完整周期采用有来源服务预算。','03_nor_2d':'完整 native program/erase 服务预算保留；读切片资源不等于并行编程头。','04_nand_3d':'split-sign/base-4 映射，数据页与参考页均计时；仿射乘法/舍入与校准除法仍是未完全闭合的非零算术预算。','05_rram':'WH-2T1R；两次 RESET/一次 SET 上限与独立二元窗读验，条件成功发布，不推断开关成功概率。','06_mram':'互补 MTJ 参考映射；两方向写入与两支绝对状态读验均计时。','07_pcm':'32 个实际电流通道与九级条件解码；物理阈值/列标定未完整实例化。','08_feram_hfo2':'HZO 1T1C 参考映射；破坏性读后的原生 capture/restore 已包含，不重复收费；PL 负载仍有适用条件。','09_gain_cell_edram':'硅 CMOS gain-cell 易失性存储；刷新占用、guard、整数拍保持帧进入有效间隔。raw 时延不能直接覆盖维护后的 rho/tau。','10_fenor_3d':'目录保留技术索引名称；实际技术为垂直 AND FeFET。极化、两相更新和终验服务保留。'}
for cid,name in names.items():
 p=cur/'analysis'/cid;c=json.loads((p/'input.json').read_text());l=c['logical']
 (p/'README.zh.md').write_text(f'''# {name} 参考配置\n\n逻辑矩阵 **{l['K']} × {l['N']}**；输入 {l['input_bits']} bit、权重 {l['weight_bits']} bit，逻辑输入/权重分别为 {l['bytes_per_input']}/{l['bytes_per_weight']} Byte/element。完整输入 payload 为 {l['B_S_Byte']} Byte，完整矩阵 payload 为 {l['B_R_Byte']} Byte；内部编码、位平面和维护不增加逻辑 payload。\n\n{notes[cid]}\n\n[输入、资源与映射](input.json) · [实际解析与模块返回](resolved.json) · [计算结果](result.json) · [阶段来源](stage_sources.json) · [方法与适用条件](../METHOD.zh.md) · [源参数引用和哈希](../../provenance/input_sources.json)\n\n统一复算入口：`../shared/run_evaluation.py`。本目录结果由统一入口生成；十例主表与图只读[权威数据](../data/ten_case_results.json)。构建和完整 trace 留本地区。\n''')
# Finish code source hashes after extraction.
p=cur/'provenance/code_sources.json';x=json.loads(p.read_text())
for r in x['files']:r['current_sha256']=hashlib.sha256((cur/r['current_path']).read_bytes()).hexdigest()
x['entrypoint']={'path':'analysis/shared/run_evaluation.py','sha256':hashlib.sha256((cur/'analysis/shared/run_evaluation.py').read_bytes()).hexdigest(),'source_functions':['scripts/run_step4_v2.py::worker (selected computation only)','scripts/run_step3.py::main (selected computation only)','probes/interface_revision/legacy_replay.py::parameters (primitive loading only)'],'excluded_from_runtime':['legacy replay and saved-result comparison','historical sensitivity and synthetic diagnostics','old performance tables','sibling task execution artifacts']}
p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
