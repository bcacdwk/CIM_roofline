# Step 1：本机环境、版本快照与最小执行

执行日期：2026-10-04。**Step 1 功能验收 PASS，独立复核 PASS，无阻塞**；两项非阻塞例外单列于末节。逐项状态见 `STATUS.md`。本轮没有进入 Step 2。

## 工作区与基线

- 管理区：现有仓库的 `tasks/task1_table_I_NeuroSim/`。原 README 保留，仓库内写入限于本目录。
- 运行区：实际 `$HOME/neurosim`，本机为 `/Users/shine/neurosim`。源码、构建、完整日志、运行副本及缓存均在本地；跨目录读、写、执行和小结果复制证据见 `results/smoke/cross_directory_probe.json`。
- 本地 HEAD 与指定基线均为 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`（`task1_refine_v3`）。初始仅有两处 `.DS_Store` 修改及本目录 README 未跟踪，见 `provenance/repository.initial.json`。

## 工具链与版本

macOS 26.6.2（25G83）、arm64；GNU GCC 16.2.0，实际 C++ 编译器 `/opt/homebrew/bin/g++-16`，目标 `aarch64-apple-darwin25`；GNU make 3.81、Git 2.52.0、Python 3.9.6，复用既有 Xcode/CLT。详细路径、版本与运行库证据见 `provenance/environment.json`。

OpenMP 编译、链接、运行均 PASS：`-O2 -fopenmp` 的 reduction 得到 `500500`，记录 10 线程及 `libgomp.1.dylib` 加载。两个 NeuroSim 后端均使用 `make CXX="/opt/homebrew/bin/g++-16"`，保留上游编译参数 `-fopenmp -O3 -std=c++0x -w`，无源码移植补丁。

实际远程查询登记了 15 个 heads。下列远程 head 均与指定锁定 SHA 相同；完整 SHA、实际核心路径、精确文件白名单和源码哈希见 `provenance/neurosim.lock.json`，全部分支见 `provenance/remote_heads.tsv`。

| 分支 | 准备 | 编译 | 运行 |
|---|---|---|---|
| 2DInferenceV1.4 | PASS | PASS | PASS，原 main 两次非空计算 |
| 2DInferenceDCIMV1.0-dev | PASS | PASS | NOT_RUN，本轮不要求 |
| 2DInferenceV1.5-dev | PASS，C++ 源码 | NOT_RUN | NOT_RUN |
| 2DTrainingV2.1 | PASS，C++ 源码 | NOT_RUN | NOT_RUN |
| MLPInferenceV3.0 | PASS，根目录及引用子目录源码 | NOT_RUN | NOT_RUN |
| 3DInferenceV1.0 | PASS，锁定及 README 导航 | NOT_RUN | NOT_RUN |

采用 `--filter=blob:none --no-checkout` 和各 worktree 独立的 non-cone sparse 配置，按实际文件白名单检出。没有获取/解压 MNIST，没有安装 DNN 依赖。上游版权、许可证与各分支引用入口见 `provenance/upstream-notices.txt` 和锁定文件。

## 非空执行证据

使用原版 V1.4 `main`，不是自写仿真驱动。辅助 C++ 程序仅实例化原 `Param` 导出参数。规范生成器 `scripts/smoke_io.py` 仅用 Python 标准库，生成一层 1×1 卷积：128 输入、32 输出、4096 个混合正负非零权重，以及一个 8-bit 激活向量的 128×8 二进制 trace（4096 MAC，8192 ops）。

V1.4 保持原生 22 nm SRAM、并行模式、128×128 子阵列。DCIM 保持其 1 nm、256×256 默认参数，仅编译；不据此比较两分支优劣，不添加 28 nm 技术表。实际生效参数保存在 smoke 的 `parameters.json`。

两次运行退出码均为 0；案例、映射和完成标记均存在，关键面积、延迟、读能耗及吞吐有限且为正。49 条稳定数值行精确一致，比较排除墙钟时间。代表性原始值：芯片面积 `91470.1 µm²`，CIM 阵列面积 `8881.44 µm²`，层读延迟 `192.655 ns`，读动态能量 `396.526 pJ`。这些仅为环境测试点；写入指标未报告，保存为 `null/NOT_REPORTED`，未计算 rho/tau。最终小型输入、命令/退出码、两次原始输出、参数、哈希及断言见 `results/smoke/review-20261004T031950Z/`。

过程中保留两次失败证据于本地：参数导出辅助程序的 include 顺序错误已修复；初始 16×8 网络不足以满足原版层级映射，改用上述支持规模后通过。未修改上游时延公式。空输出或失败运行不能通过数值复现断言。

## 复跑入口

从任意当前目录使用管理区绝对路径执行：

```sh
TASK_DIR="<REPO_ROOT>/tasks/task1_table_I_NeuroSim"
sh "$TASK_DIR/scripts/setup_step1.sh"
sh "$TASK_DIR/scripts/smoke_step1.sh"
```

路径覆盖与示例见 `configs/workspace.example.env`。入口创建新的本地运行/构建目录，保存规范脚本运行副本及哈希，完整命令、退出码和日志留在 `runs/step1/`。云端只导出小型输入、必要原始数值输出与断言摘要。管理区只读复跑可执行：

```sh
NEUROSIM_ROOT="$HOME/neurosim" \
NEUROSIM_RUN_ID="review-$(date -u +%Y%m%dT%H%M%SZ)" \
NEUROSIM_EXPORT=0 sh "$TASK_DIR/scripts/smoke_step1.sh"
```

## 安装与复核

依赖安装 PASS：新增 GCC 16.2.0、gmp 6.3.0、isl 0.28、mpfr 4.2.2、libmpc 1.4.1、xz 5.8.4；六项实际分配磁盘合计 520,654,848 B。Python 及其他工具复用，无新增 Python 包、PyTorch、CUDA、模型、数据集、conda 环境或 TeX。未替换系统编译器、全局 upgrade 或修改 shell 配置。

安装后处理 FAIL（非阻塞）：现有 Homebrew 5.1.0 解析新 GCC formula 时遇到 `Resource::Patch.file` API 不兼容。GCC bottle、libgomp 与实际编译/运行均通过，未为此升级 Homebrew，不需要用户处理。首次 brew 下载曾使用已有 `~/Library/Caches/Homebrew`；发现后停止并改用运行根，未清理用户缓存。重试及后续下载、临时文件和日志已定向本地根，过程日志保留在 `runs/step1/`。

独立复核 PASS：reviewer 从 `/tmp` 使用最终版入口运行 `review-20261004T031950Z`，重新编译两个后端、原 main 两次非空运行并比较，结果与执行者一致。六个工作树的 SHA、独立 sparse 配置、文件清单及每个 Git blob 均一致；构建副本源码哈希和规范脚本运行副本哈希一致。空输出、错误、NaN、零面积、截断输出五类负例均被断言拒绝。详见 `reports/step1_review.json`。

源码和内容保护 PASS；根目录元数据一致性 FAIL（非阻塞例外）：旧 NVM、Table II、论文等其他已跟踪内容未变，原 README 和 `tasks/.DS_Store` 初始哈希保持，暂存区为空。根 `.DS_Store` 的哈希在会话期间发生变化（独立复核快照 mtime 北京时间 11:05:35），导出收尾时又检测到变化（mtime 11:28:48），归因未知，未回退。前后哈希分别写入独立审计及最终交付审计；不把这项例外表述为“全工作区字节不变”。

磁盘占用以 `du -sk` 的实际分配大小计：独立复核结束时运行根约 257.1 MiB，其中上游 Git 1,152 KiB、worktrees 5,672 KiB、build 21,132 KiB、runs 1,652 KiB、cache 233,424 KiB、staging 232 KiB。依赖安装位于 Homebrew 前缀，不计入运行根。最终管理区 280 KiB、33 个小文件；白名单文件清单与复核后的导出记录见 `provenance/delivery-audit.json`。完整运行树未复制或链接到云盘。

reviewer 复跑期间未写管理区；完成后由 supervisor 按小文件白名单导出最终版复跑结果及审计，保留唯一最终成功结果集。先前成功/失败完整证据均留在本地 `runs/step1/`。没有待用户处理的阻塞，没有执行 Git 暂存、提交或推送。下一步仅指向 README 的 Step 2，另行安排。
