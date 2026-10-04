# Table I · NeuroSim 评估任务

当前完成：**Step 3 三个 reference pilot，最终集成及独立复跑 PASS；停止在本阶段。**

阅读入口：[Step 3 中文报告](reports/step3_pilots.zh.md) · [结果总表](results/step3/integration-final-20261004/summary.csv) · [独立复核](reports/step3_review.json) · [统一入口](scripts/run_step3.py)。规范输入仍为 Step 2 `configs/cases/`；生效配置在三个案例各自的 `resolved.json`，旧时间回放与新结果分开。

## 1. 目标与起点

以已确认的 `task1_refine_v3` 为器件、原生阵列及服务流程输入，引入 NeuroSim 的公开电路模型，建立从配置到服务时间、`ρ / τ / RI*` 的可复现评估链。这里的“端到端”指输入配置到最终表图，不要求运行完整神经网络。

起始版本：`bcacdwk/CIM_roofline@a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`。实际执行时同时记录本地 HEAD；原 NVM 目录、Table II 和论文保持只读。沿用当前十例及各自原生尺寸，包括现有 GC-04 gain-cell eDRAM；不重新引入统一 128×128 约束。

优先阅读兄弟目录 `../task1_table_I_NVM/` 的 `README.md`、`analysis/TEN_CASE_CONVENTIONS.zh.md`、`analysis/TEN_CASE_REVIEW.zh.md`、`analysis/shared_baseline/README.md`。按具体任务读取案例输入和计算器，不遍历历史归档或一次性加载全部文献。

## 2. 两个工作区

**交付与管理区**：`CIM_roofline/tasks/task1_table_I_NeuroSim/`，位于现有 OneDrive 仓库内。

```text
README.md                  目标、阶段及阅读入口
STATUS.md                  当前进度、已确定决策、下一步
AGENTS.md                  分工与写入边界
prompts/                   分阶段任务书
scripts/                   搭建、运行、检查、导出脚本
configs/                   小型输入、实际配置和参数来源
patches/                   相对锁定上游版本的必要补丁
provenance/                版本锁、环境记录、文件哈希
reports/                   简短审阅和阶段报告
results/                   正式 CSV/JSON 与必要的小型原始输出
paper/                     最终 TeX、参考文献、图和 PDF
```

目录按阶段建立，不预先生成空报告。

**本地运行区**：默认 `$HOME/neurosim/`。在用户名为 Shine 的常见 macOS 安装中通常是 `/Users/Shine/neurosim/`；以实际 `$HOME` 和解析后的真实路径为准，不使用 `/user/Shine` 或 `/Shine` 猜测路径。

```text
upstream/                  NeuroSim Git 对象与上游版本
worktrees/                 独立、锁定的分支源码
build/                     编译副本和二进制
envs/                      必要的独立工具环境
runs/<step-or-case>/<run>/  输入快照、完整日志和中间结果
cache/                     下载与临时缓存
staging/                   待审核的小型交付包
```

云端保存规范源码、配置和正式结果；执行前在本地生成带哈希的运行快照。上游仓库、编译产物、完整日志、缓存及 TeX 临时文件留在本地。`.gitignore` 只控制 Git，不是 OneDrive 排除机制；不使用指向本地运行树的符号链接。通过路径配置调用本地脚本，经过文件白名单检查后导出结果。

Agent 从 OneDrive 工作目录访问本地运行区，先做一次真实读写及执行测试。需要额外目录授权时，仅申请运行区权限，保留已完成工作和明确的阻塞状态。

## 3. 评估原则：默认模型，显式配置

| 内容 | 采用方式 |
|---|---|
| 晶体管、互连、感测、ADC、数字模块的模型实现 | 在适用范围内优先采用选定 NeuroSim 版本；记录实际默认值及校准开关。 |
| 器件状态、读写条件、原生几何、编码、精度和资源数量 | 沿用 v3 的对应实例，显式传入；不被上游示例默认值覆盖。 |
| 擦除、写验、破坏性读恢复、刷新及专用高压时序 | 核对后端覆盖；已建模阶段由后端提供，缺失阶段保留 v3 模型。每个阶段只计一次。 |
| 后端不支持的组织 | 使用可复用电路模块加必要的服务流程适配；单纯更名为 RRAM/nvCap 不算完成适配。 |

先尽量统一公共电路后端。特殊分支用于补充机制或交叉检查；跨版本结果须先对齐工艺、资源和服务边界，不以哪个数值更理想选择版本。

保留 `ρ=B_S/Δ_S`、`τ=B_R/T_R`、`RI*=ρ/τ`，以及完整矩阵装载时的 `U*=T_R/Δ_S`。`B_S/B_R` 为有效逻辑 Byte；编码、内部读写和维护进入时间/资源，不重复增加 payload。分别保存单次延迟、稳态服务间隔及维护前后能力。

Step 1 使用上游默认支持配置完成环境测试。正式工艺在 Step 2 决定：v3 的 28 nm 不能自动变成 NeuroSim 的默认节点；采用其他原生节点时按真实节点报告，并将工艺变化与模型变化区分。

## 4. 分阶段推进

| 阶段 | 核心工作 | 验收产物 |
|---|---|---|
| **1. 本机环境与版本快照** | 两区建好；最小 C++/OpenMP 工具链；分支清单与锁定；原版编译和小型执行测试。 | 搭建/测试脚本、版本与环境记录、Step 1 报告。 |
| **2. 后端覆盖与接口设计** | 审阅主要分支的实际读写代码；为十例确定可复用模块、缺失阶段和参数归属；确定工艺与默认策略。 | 分支—器件覆盖表、参数来源表、服务阶段及输入/输出约定。 |
| **3. 三个 pilot 打通链路** | SRAM ACIM、SRAM DCIM、RRAM 的典型配置，完成输入、后端、完整服务聚合、导出和独立复算。 | 三个可重跑案例；逐阶段与 v3 对照，解释差值来源。 |
| **4. 扩展十例** | 按 Step 2/3 固定接口并行适配其余案例；特殊机制保留所需专用模型。 | 十例配置、适配代码、覆盖身份和检查结果。 |
| **5. 三情景与一致性检查** | 运行相容情景；检查主导参数敏感性、维护与映射；区分工艺、资源、后端带来的变化。 | 机器可读总表、与 v3 的差异分解、独立复核。 |
| **6. 精简交付与文稿** | 导出必要输入、代码/补丁、输出和 TeX/PDF；从新的本地目录重建。 | 可重现正式结果的交付包和简洁讨论。 |

每阶段独立验收。当前 Step 3 三个 pilot 已完成并独立验收，Step 1/2 历史证据保留；不提前开展其余七例或修改 v3 结论。

## 5. 分支候选与用途

以下是 2026-10-04 核对后的候选方向，最终采用范围由 Step 2 的代码覆盖检查确定。

| 分支 | 优先研究用途 |
|---|---|
| `2DInferenceV1.4` | 公共 C++ 电路后端候选；SRAM ACIM、RRAM，以及相容的阻变/FeFET 读出模块。 |
| `2DInferenceDCIMV1.0-dev` | SRAM DCIM 专用模型与数字模块交叉检查。官方当前仅声明支持 256×256 子阵列，不直接缩成 v3 的 128×16 逻辑配置。 |
| `2DInferenceV1.5-dev` | nvCap 和较新的接口/非理想性模型候选。nvCap 不等于当前破坏性读 1T1C FeRAM；其硬件 PPA 仍采用 bit-serial 输入，须核对原生编码。 |
| `2DTrainingV2.1` | 权重更新与 FeFET 极化相关代码；核对完整覆盖写入与训练增量更新的区别。 |
| `MLPInferenceV3.0` | 数字 eNVM/MRAM 及器件更新机制参考，避免将旧外围和新外围未经对齐混用。 |
| `3DInferenceV1.0` | 3D 集成/层间互连参考，不等于 NAND string 或垂直 FeFET 的原生器件模型。 |

`2DInferenceDigitalSystolicArrayV1.0` 与较早版本登记在清单中，按特定机制需要追溯，本轮不全部安装或编译。

十例安排：SRAM ACIM、SRAM DCIM、RRAM 已完成三个 Step 3 pilot；PCM 核查阻变类接口及专用写入；MRAM 查数字 eNVM；SRAM DCIM 查专用数字分支；FeFET 联合检查读出与更新代码；NOR、NAND、FeRAM、现有 eDRAM 优先按“公共外围＋各自原生服务流程”组织。支持某类元件，不等于已支持当前整个参考宏。

## 6. 协作与可复现交付

主 Agent 担任 supervisor：维护本目录的公共文件、分派任务和验收。子 Agent 只写获分配目录；每个案例使用独立运行/构建目录，避免共改 `Param.cpp`。安装和 Git 上游管理设唯一写入者，复核者只读结果并在自己的临时目录复跑。向 supervisor 返回结论、文件路径、测试状态及少量待决事项，不粘贴完整日志。

每个正式结果关联上游完整 SHA、v3 输入 SHA/哈希、补丁、实际生效参数、命令、依赖版本和必要随机种子。复现验证使用新建运行目录，不依赖原工作区缓存或已有输出；数值比较采用声明的容差。

原论文及 Table II 不在本任务写入范围。Git 暂存、提交和推送由用户负责。

### 资料入口

- 基线：`https://github.com/bcacdwk/CIM_roofline/tree/a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0/tasks/task1_table_I_NVM`
- 上游及各分支 README：`https://github.com/neurosim/NeuroSim`
- 实际分支清单：`https://api.github.com/repos/neurosim/NeuroSim/branches?per_page=100`
- Git 工作树与按需获取：`https://git-scm.com/docs/git-worktree`；`https://git-scm.com/docs/git-clone`
- macOS 工具链：`https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/`；`https://formulae.brew.sh/formula/gcc`
- OneDrive 同步限制：`https://support.microsoft.com/en-us/onedrive/restrictions-and-limitations-in-onedrive-and-sharepoint`
