# Task III 共同计量接口

Task I、Task II 已经用户验收。这里仅转换坐标、组织有限代表工况；不修改原参数或重新认证原始模型。当前本地 HEAD 与指定检查点均为 `100c233a2dbdb74ca3894aa96ee39c358e9ebe41`，实际值也由构建器写入 `source_index.json`。

## 数据入口与复现

从仓库根运行：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task3_matching_figures/shared/build_shared.py
```

构建器只读取 Task I/II，所有输出均位于本目录。不导入会写原目录的绘图脚本。`data.json` 是绘图共同输入；`hardware.csv` 保存 30 个成对原生情景的完整精度；`selected_workloads.csv` 保存四个代表状态；`source_index.json` 记录输入 SHA-256 与实际 HEAD；`validation.json` 保存恒等关系与少量跨图数值检查。`interface.py` 提供只读访问和共同公式，`style.py` 提供颜色、介质标记、尺寸及文件保存约定。

来源以现行汇总为准：

- Task I：`analysis/data/ten_case_results.json`、`11_summary_figures/data/table_scenarios.json` 和已验收圆图点 CSV；每条记录继续保存原生 `source_mapping`、`source_result` 和 case ID。构建器逐条追溯原生 JSON 指针，核对 K、N、完整装载和向量服务时间。
- Task II(a)：`table_IIa/data/results.json` 的有限单矩阵工况；原始整数 Byte 与 RI 精确分数均保留。
- Task II(b)：`04_crosscheck/data/{conventions,model_inputs,results}.json` 的 QKV 全阶段计数及输入共享扣除。
- 方法：Task I `shared_baseline/README.md` 的“Table I 到 Table II”和 Task II `04_crosscheck/CONTRACT.zh.md`。

## A/C/D/E：完整原生矩阵的复用坐标

硬件每条记录继续代表其自己的 K×N、资源与完整装载模式。设一次完整 resident 装载服务时间为 T_R，完整输入向量服务间隔为 Δ_S。对等宽 INT8、一次装载后累计服务 U 个输入向量：

```text
Q_S = U K               Q_R = K N
rho = K / Δ_S           tau = K N / T_R
sigma = N rho           U* = sigma/tau = N RI* = T_R/Δ_S
P_bound = min(rho, (U/N) tau)
P_bound/rho = min(1, U/U*)
```

σ 为 **full-matrix-equivalent streaming capacity**，单位仍为十进制 MB/s；是把输入字节率乘以各自 N 后的显式坐标转换，不是原始 streaming 输入率，也不是新增实测量。A 横轴 τ、纵轴 σ，平衡线为 σ=Uτ。真实情景点在线上方为 resident-bound，线下方为 streaming-bound。C 将同一关系画成 U*。D 是两通路资源参考上界的归一化，不是利用率；相同平台不意味着相同实际吞吐。E 解析倍增使用 `min(a rho, b (U/N) tau)`，分别提高 streaming 和 resident 能力；a、b 不代表相同成本或新测量。

四个代表状态来自已验收的单矩阵 GEMM `W[128,128]`：U=1、128、1K、128K。1 表示首次使用；128 位于 MRAM/FeFET 等参考阈值附近；1K 位于 RRAM 与 Flash 阈值之间；128K 跨过典型 NOR 阈值，但仍低于其长情景阈值。选点覆盖低、中、高复用及真实情景跨界，而非只选会产生统一分类的端点。标签应写具体算子、矩阵及 U；U 不是 batch size，也不是 L。

**四个状态的 U 可以作为所有原生服务的复用要求参照，但 W[128,128] 只有在硬件原生 K=N=128 时与其需求字节数直接同边界。** A/C/D/E 对十类硬件比较的是相同复用要求，而不是把一个 128×128 算子不经映射部署到十种不同原生形状上。模型适配结论仅限下节已明确推导的 QKV 子集。

## B：QKV 唯一逻辑需求与顺序 tile 服务的有限映射

仅选两个已验收的原生 QKV+可选 gate 阶段：Qwen3.5-2B（D=2048，N_proj=5120）和 MiMo-V2.5-Pro（D=6144，N_proj=27136）。Q/G/K/V 在同一矩阵阶段使用同源输入，故可沿输出维拼为 W[N_proj,D]，保持原合同的 Q_S=UD、Q_R=D N_proj，不把输入共享扣除恢复成重复的逻辑需求。

只使用原生 K=N=128 的四个硬件：SRAM ACIM、2D NOR、HfO2 FeRAM、3D FeFET。为该图明确规定一个**顺序 tile 组件服务参考**：一个原生 engine；每个完整 128×128 tile 装载一次，服务同样 U 个输入片段，再处理下一 tile。无 padding。令 m_K=D/128、m_N=N_proj/128，总 tile 数 M=m_K m_N。

| QKV 阶段 | m_K | m_N | 完整 tile 数 | 逻辑 Q_R (Byte) |
|---|---:|---:|---:|---:|
| Qwen3.5-2B | 16 | 40 | 640 | 10,485,760 |
| MiMo-V2.5-Pro | 48 | 212 | 10,176 | 166,723,584 |

总 native 输入为 M U·128=m_N Q_S；总 resident 装载仍为 M·128²=Q_R。因此：

```text
T_S_components = M U Δ_S       T_R_components = M T_R
rho_effective = rho / m_N      tau_effective = tau
RI*_effective = RI* / m_N = U* / N_proj
Q_S = RI*_effective Q_R        (balance ray on the logical-demand plane)
```

B 每个模型必须使用其自己的有效射线，不能把一条原始硬件 RI* 射线套到两个模型。点在需求射线上方为 streaming-bound，线下方为 resident-bound；与 A 上下方判定相反。两种坐标的判定都等价于 U 与同一原生 U* 的比较。`qkv_tile_mappings` 输出 m_K/m_N、每个真实 profile 的有效能力与累积服务时间；`qkv_mapped_workloads` 保留四个原有有限扫描 U=1/1K/128K/1M 的精确逻辑 Byte 及 native 累计 Byte。B 无需显示全部四档。

这里的 native 输入重放已进入累计组件服务时间。跨 tile 输出归约、切换、上游搬运、完整输出存储和容量/时序可行性不在本参考中认证；新增开销只会降低可达吞吐。两通路可以共享资源或串行执行，因此 `min` 是理想两路资源上界，**不是完整顺序任务的墙钟延迟**。如果两种服务完全串行，完整时间至少 T_S_components+T_R_components，平衡判定不变，但真实吞吐可能低于该上界。并不假定两路峰值同时可达。该推导增加模型需求与原生服务的明确连接，不构成模型部署或精度认证。

## 情景、单位与视觉约定

三情景逐行保留原有 `(rho,tau)` 配对，profile 为 short/reference/long；典型点不是统计中位数。任何 U* 区间来自三条真实记录的最小和最大值，不能分别取 rho、tau 极值得出不存在的组合。Gain-cell 的长期维护已在有效能力中保留。

圆只概括三条有限情景。A 的 `(log tau, log sigma)` 转换相对每类原始 `(log tau, log rho)` 是纵向平移 `log N`，可沿用圆的几何规则；不得从圆内部采样出新情景，跨界只检查真实点。圆不是概率、置信区间或所有可实现组合的包络。

能力单位使用 MB/s=10⁶ Byte/s。需求轴若使用 MiB，必须由 Byte 除以 1024² 并正确标为 MiB。复用后缀 1K=1024，1M=1024²。无限复用只以边界说明保留，不能塞入任意大的对数坐标。介质颜色继承 Task I，介质符号由 `style.py` 固定；复用参照用灰色线型，避免改变介质含义。论文目标尺寸为单栏 3.5 in 或跨双栏 7.16 in，图保存时不通过紧裁剪改变物理尺寸。

结构性 signed-INT8 映射资格沿用已验收记录；ACIM 名义诊断不等于应用准确率或实物非理想性验证。图的结论限于瓶颈、平衡、复用要求及组件服务参考上界，不给综合产品排名。
