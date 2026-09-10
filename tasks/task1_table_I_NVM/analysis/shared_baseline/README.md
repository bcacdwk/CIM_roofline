# Table I 共享估算基线

本设计以共同的 28 nm CMOS 外围条件和明确的局部资源配置，结合介质的阵列响应与完整更新过程，估算 streaming 输入吞吐 ρ、resident 写入吞吐 τ 及 ridge RI*。方法包括 ACIM streaming、DCIM streaming、直接更新 resident、分步编程／擦除摊销 resident 四类模板。

## 阅读入口

1. [中文设计稿 PDF](output/shared_baseline.pdf)。
2. [第一节：外围参考](tex/01_cmos_periphery.tex)；[第二节：通用方法](tex/02_estimation_method.tex)。总入口为 [shared_baseline.tex](tex/shared_baseline.tex)。
3. [共享参数 JSON](data/shared_parameters.json)：共同条件、参考配置、选择规则与介质输入要求。
4. [结构与时间敏感性数据](data/sensitivity_results.json)：合成情景的操作次数、资源条件、未取整结果及相对倍率。
5. [证据笔记](notes/evidence.zh.md)：文献原值、详细定位、参考选择依据及敏感性手算。

## 设计条件与参考配置

共同逻辑任务为 128×128 INT8 矩阵乘 INT8 向量，每向量输入 128 Byte，交付 128×24-bit 结果。streaming 边界从本地宽向量接口接收输入到结果寄存器就绪；resident 边界从本地写事务开始到相应状态可计算。独立服务单元和更新域均为一。

精度合同采用 ACIM 经校准的近似部分和及重构、DCIM 精确整数结果。两条路径共用输入、权重和输出格式，分别声明计算语义，不设共同最终误差阈值。资源按配置显式声明，不施加等面积约束。

默认配置 `R0`：ACIM 八个二进制权重平面并行，每平面 16 ADC，每次 16 输出重新求值，16 条重构通道、两拍/轮；DCIM 输入逐 bit、权重八位并行，每轮 32 项×16 输出。必要阶段顺序执行，输入捕获与结果提交合计两拍。128-bit 写接口用于编码数据装入，实际同时可编程的 cell 数由介质驱动能力确定。

公共时隙为 `T_I=2–10 (5)`、`T_A=10–50 (20)`、`T_D=2–10 (5)`、`T_W=4–20 (10)` ns，括号为推荐值。ADC 分批数由转换资源决定，阵列求值次数由输出选通或保持组织决定，数字重构次数由输出通道与每轮功能决定。各项时隙经这些次数代入，才得到完整逻辑服务耗时。

```text
R0 ACIM: N_E=64, N_C=64, N_rec=64, N_dig=128; 有用标量转换8192
Δ_S = N_E(T_I+t_m,A) + N_C T_A + N_dig T_D + T_H + 2T_D
    = 64(T_I+t_m,A+T_A+2T_D) + 2T_D  （R0 的 T_H=0）

R0 DCIM: N_D=N_rd=256, k_D=1
Δ_S = N_rd t_m,D + N_D k_D T_D + T_L + 2T_D
    = 256(t_m,D+T_D) + 2T_D          （R0 的 T_L=0）

ρ ≈ B_S/Δ_S；τ ≈ B_R/Δ_R；RI* ≈ (B_S/B_R)(Δ_R/Δ_S)
```

## 结构敏感性

使用合成读时间 ACIM 25 ns、DCIM 10 ns，固定完整直接更新 16 Byte/60 ns，τ=0.2667 GB/s。三个对照分别改变 ADC 数量、模拟结果保持组织和数字输出通道数：

| 对照 | Δ_S | ρ 与 ridge 相对各路径 R0 | 必要条件 |
|---|---:|---:|---|
| R0（两路径各自基准） | 3850 ns | 1.000 | 默认配置 |
| ACIM 每平面 ADC 16→32 | 2250 ns | 1.711 | 总 ADC 128→256，求值宽度与批码锁存容量翻倍；数字16通道不变，重构总拍仍128 |
| ACIM 全输出保持后分批读 | 2210 ns | 1.742 | 128输出并行求值、1024个有效模拟槽及隔离/缓冲，额外5 ns/求值，至少240 ns保持；为带条件的电路预算 |
| DCIM 输出通道16→32 | 1930 ns | 1.995 | 局部读出与乘法/归约资源同步增加，满足5 ns节拍 |

这些对照保持相同逻辑容量、写接口和直接更新步骤，τ 不变；带共享 ADC verify 的介质需同步检查写服务。保持负载、噪声与漏电必须满足精度目标，表中结果未经电路验证。

单独将 `T_A=20 ns` 改为16/24 ns，R0 ACIM 的ρ与ridge变化为−6.23%至+7.12%；单独将 `T_D=5 ns` 改为4/6 ns并同步改变写控制，ACIM ridge约±0.04%，DCIM ridge为−3.16%至+3.61%。ACIM ridge较稳来自该示意两路占用接近同比变化；结构造成的1.7–2倍差异更明显。稳定性取决于具体读写配对与资源组织。

## 参数入口与介质填写规则

| JSON 键 | 含义 |
|---|---|
| `baseline_id` | 共享设计标识 `shared_baseline` |
| `common_conditions` | 逻辑配置、边界、工作条件、外围范围及共享情景 |
| `reference_instance` | R0 的 ACIM、DCIM、resident 结构参数；`derived` 为公式推导计数 |
| `selection_rules` | 默认配置、原生约束、结构对照、完整周期替代及两路一致性规则 |
| `media_required_inputs` | 读侧、写侧、映射、专用驱动、维护和例外记录要求 |
| `examples` | 两个不绑定介质的算例，各含三个成对情景 |
| `structural_sensitivity` | 示意输入、结构对照及必要资源条件 |
| `reported_evidence` / `sources` | 原文数值、定位与本地 PDF 哈希 |

介质分析默认采用 R0、共同逻辑合同和外围情景。原生行数、选通、平面并行或编码受限时，按有证据的映射增加组数/步骤；对相同约束使用相同规则。更多 ADC、多位输入、保持或更多输出通道作为明确对照，不按介质各自选择最快配置代替默认。

每项结构例外记录规则 ID、原因及证据定位、R0 值、配置值、必要资源与时间变化、对两路的影响。更新服务采用真实 page/block、有效逻辑字节与完整操作；verify/restore/refresh 与同一配置衔接。原值、工程选择和推导分别标记。

## 复现与检查

数值检查只依赖 Python 3 标准库；PDF 编译需要 XeLaTeX、BibTeX、latexmk 与 ctex/Fandol，页面渲染使用 pypdfium2/Pillow。本机可用 Python 路径为 `/opt/anaconda3/bin/python`。从本目录执行：

```sh
/opt/anaconda3/bin/python scripts/check_shared.py
BASELINE_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改共享参数后显式刷新派生文件，再构建：

```sh
/opt/anaconda3/bin/python scripts/check_shared.py --emit
```

默认检查不改文件；`--emit` 生成外围表、算例表、结构敏感性表、时间扰动段落及 `data/sensitivity_results.json`。计算输入与派生结果分开，表内算术精度用于复算。

检查覆盖通用模板与R0对应、位展开/尾组/输出覆盖、完整权重与编码/写批、verify和擦除摊销、单位及服务粒度因子、成对算例和敏感性独立复算、源PDF哈希、生成数据与正文入口一致性。脚本按顺序调度计算；流水组织依正文的资源和缓冲条件另行估算。构建日志位于 `build/`，渲染页面位于 `tmp/pdfs/rendered/`。
