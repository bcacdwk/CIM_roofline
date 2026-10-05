# P0 环境与公共入口

公共维护者 `/root/integrator` 于本轮真实核对：仓库 HEAD 为 `216d3f8af6e58fc75632a526b73d017252b2e969`，恰为 V4，之后无本地提交。任务开始已有修改只有根 `.DS_Store`；其初始哈希已记录，未改、未纳入本轮变更。未执行暂存、提交、推送、升级或清理。

`NEUROSIM_ROOT` 未设置；已有 `machine_paths.json`、`worktrees.json` 与 `$HOME/neurosim` 一致指向 `/Users/shine/neurosim`。本轮实际目录为 `/Users/shine/neurosim/runs/step4-v5/p0/integrator-20261005T0400`。全部六个锁定 worktree 的实际 HEAD 匹配旧锁且工作树干净。五个 2D/MLP 分支已有 C++ 源码；3DInferenceV1.0 当前只稀疏取有 README，**不能宣称已可构建其 3D 模块**。确需使用时只补取指定 SHA 的必要文件至本地独立副本，不改原工作树和旧锁。

现有编译器 `/opt/homebrew/bin/g++-16`，版本 Homebrew GCC 16.2.0；系统 Python 3.9.6。`/usr/bin/g++` 为 Apple 工具链入口，正式后端沿用明确的 GCC 路径以支持已有 OpenMP 依赖。本阶段不安装任何工具。实际独立构建运行了 Training 原生 `Technology`、`DFF`、`formula`、`FunctionUnit`：45 nm/LSTP/300 K、32 个 DFF、100 MHz，返回面积 1.6547e−10 m²、数据端电容 1.7556e−16 F、时延 5 ns。它只证明工具链/调用顺序，不是任一案例性能。初试 40 nm 被原生模型明确拒绝，但其 `exit(0)` 仍返回成功码；后端必须同时检查错误文本和必需有效字段。失败现场保留，40 nm 不伪装为支持节点。

[V5 独立锁](provenance/dependencies.lock.json) 和 [初始证据](provenance/environment.initial.json) 保留本轮版本与环境。锁中 `ports` 暂为空，表示尚未完成移植，绝非“无须移植”。[接口](INTERFACE.md) 是 P0 可审查边界；此时没有七例正式服务值，输入校验程序也不等于完整后端。

## V4 只读衔接

V4 九点是 `ns_sram_acim`、`ns_rram_1t1r`、`ns_sram_dcim` 各三点；均为 256×31 signed INT8、本地宏边界，但硬件/精度资格不同：ACIM 为普通 SRAM 多行模拟求和，读稳定性与 transfer 未证明；RRAM 为 16 个 16×288 bank、512 ADC、29 bit Q4 近似输出，有限线阻诊断存在残差且有稳定读电源及有界写验成功条件；DCIM 为原生 256×256 bit、64 棵 nibble 树及数字名义算术。

300/350/400 K 分别为 optimistic/reference/pessimistic，属于固定架构、自动尺寸变化的热设计情景，不是同一芯片 PVT，也未覆盖材料统计/编程重试。V5 后处理只读纳入，不重验整个 V4、不替换其值或资格。V4 的实际 read/write 数字、旧 NVM 完整时间和 legacy replay 都不是 V5 新计算输入。

可复用：独立快照/精确 SHA 源复制、数字加法/寄存/接口资源计量思路、按消费者记录初始化值、白名单导出、成对点计量，以及经具体适用性复核的 RowDecoder/MUX/Bus 修正。不可直接通用化：256×31、16-bank RRAM 组织、22 nm 低压驱动、固定 SAR 精度、温度三点、任一材料的写算法和 `delta==latency` 政策。

## 首批后端建议与待依赖

PCM 与 MRAM 的实际材料包先由对应作者闭合；后端以真实读端口电导/偏置/几何/访问负载接入 Training V2.1 `SubArray` 或适用 MLP `DigitalNVM` 感测路径。MRAM 优先二元感测后实际本地数字归约；PCM 若选并行电流求和，应先做有限线阻/状态裕量，不能默认沿用 V4 大阵列。热写/自旋写的方向电流和脉宽由同源器件证据进入专用流程；低压 RRAM write 返回不能代替。

公共代码只接受各例可辨识的前端量、锁定模块输出和外部原语明确包含范围。FeRAM 极化/破坏读、GC 反馈写/保持、垂直 AND 层选与 NAND string 均需专用端口模型；暂不为统一外观填入完整旧读时间。独立 reviewer 需先审查接口并给出首批路线意见，P1 才冻结初版共享实现。
