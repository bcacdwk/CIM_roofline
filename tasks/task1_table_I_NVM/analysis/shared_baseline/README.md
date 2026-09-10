# Table I 共享估算基线 v0.2

状态：**待审阅，尚未冻结。** 2026-09-10。

本轮从本地实际 HEAD `3cab061c92cae9bc5e7e0e02fe8bba9394f43c3d` 开始（即已审阅 v0.1），起点工作区干净。只修订本目录；未暂存、提交或推送。Task 0 的逻辑 payload、服务边界与 Roofline 定义继续沿用。

## 阅读入口

1. [中文两节 PDF](output/shared_baseline.pdf)，8 页（含参考文献）。
2. [第一节：外围参考](tex/01_cmos_periphery.tex)；[第二节：通用方法](tex/02_estimation_method.tex)。总入口为 [shared_baseline.tex](tex/shared_baseline.tex)。
3. [共享参数 JSON](data/shared_parameters.json)：共同数值、推荐实例、选择规则与介质填写入口。
4. [结构与时间敏感性数据](data/sensitivity_results.json)：合成情景，保留未取整数值、次数、资源条件及相对倍率。
5. [证据与判断笔记](notes/evidence.zh.md)：本轮独立判断、针对性 PDF 回查、详细原值及限制、敏感性手算。

## 判断与实质修订

**v0.1 的 64／256 步在原结构下成立，微秒级结果有明确来源；需要分离的是通用方法与具体串行实现。** ADC 分批数由转换资源决定，阵列求值次数由输出选通或保持组织决定，数字重构次数由输出通道与每轮功能决定，三者可以不同。

- **保留**：四项外围范围与推荐值；128×128 INT8、128 Byte 输入、128×24-bit 结果及原精度合同；单更新域；完整更新、verify、擦除摊销及成对范围传播；原结构与六个示意计算点。
- **改变**：将原结构命名为推荐实例 `R0`；先给 A. ACIM streaming、B. DCIM streaming、C. 直接更新 resident、D. 分步编程／擦除摊销 resident 四类模板，再代入 R0。共享 JSON 明确区分共同条件、结构实例和介质输入。ADC 共享、重新求值、保持和数字重构分别计数。
- **补充**：三个结构对照与单项外围小扰动，明确随动资源及 τ 是否变化。原始测量差异留在笔记，正文缩减重复说明；PDF 由 9 页缩为 8 页。

R0 没有结构修改：ACIM 八个二进制权重平面并行，每平面 16 ADC，每次 16 输出重新求值，16 条重构通道、两拍/轮；DCIM 输入逐 bit、权重八位并行，每轮 32 项×16 输出；顺序调度与两拍边界占用。公共时隙仍为 `T_I=2–10 (5)`、`T_A=10–50 (20)`、`T_D=2–10 (5)`、`T_W=4–20 (10)` ns，括号为推荐值。128-bit 写接口是实例资源，实际同时可编程的 cell 数由介质填写。

通用模板复现：

```text
R0 ACIM: N_E=64, N_C=64, N_rec=64, N_dig=128; 有用标量转换8192
Δ_S = N_E(T_I+t_m,A) + N_C T_A + N_dig T_D + T_H + 2T_D
    = 64(T_I+t_m,A+T_A+2T_D) + 2T_D  （R0 的 T_H=0）

R0 DCIM: N_D=N_rd=256, k_D=1
Δ_S = N_rd t_m,D + N_D k_D T_D + T_L + 2T_D
    = 256(t_m,D+T_D) + 2T_D          （R0 的 T_L=0）

ρ ≈ B_S/Δ_S；τ ≈ B_R/Δ_R；RI* ≈ (B_S/B_R)(Δ_R/Δ_S)
```

## 敏感性结论

使用合成读时间 ACIM 25 ns、DCIM 10 ns，固定完整直接更新 16 Byte/60 ns，τ=0.2667 GB/s。三项对照一次改变一个主要结构因素：

| 对照 | Δ_S | ρ 与 ridge 相对各路径 R0 | 必要条件 |
|---|---:|---:|---|
| R0（两路径各自基准） | 3850 ns | 1.000 | 原结构 |
| ACIM 每平面 ADC 16→32 | 2250 ns | 1.711 | 总 ADC 128→256，求值宽度与批码锁存容量翻倍；数字16通道不变，重构总拍仍128 |
| ACIM 全输出保持后分批读 | 2210 ns | 1.742 | 128输出并行求值、1024个有效模拟槽及隔离/缓冲，额外5 ns/求值，至少240 ns保持；尚非电路验证 |
| DCIM 输出通道16→32 | 1930 ns | 1.995 | 局部读出与乘法/归约资源同步增加，假设仍满足原节拍 |

三项保留逻辑容量、写接口和直接更新步骤，τ 不变；带共享 ADC verify 的介质必须重新检查写服务。以上是带条件的示意，未作等面积比较，不用于介质排名。

在 R0 下单独将 `T_A=20 ns` 改为16/24 ns，ACIM 的ρ与ridge变化 −6.23%至+7.12%；单独将 `T_D=5 ns` 改为4/6 ns并同步改写控制，ACIM ridge约±0.04%，DCIM ridge为−3.16%至+3.61%。前者较稳来自本示意两路占用接近同比变化；结构造成的1.7–2倍差异更明显。不能据小扰动结果推断全范围或所有介质同样稳定。

## 后续 Agent 的使用规则

JSON 的稳定入口：

| 键 | 含义 |
|---|---|
| `common_conditions` | 逻辑配置、边界、工作条件、外围范围及共享情景 |
| `reference_instance` | R0 的 ACIM、DCIM、resident 结构参数；`derived` 为待校验计数 |
| `selection_rules` | 默认、原生约束、结构对照、完整周期替代及两路一致性规则 |
| `media_required_inputs` | 读侧、写侧、映射、专用驱动、维护和例外记录要求 |
| `examples` | 保留的 v0.1 六个成对回归计算点；不绑定介质 |
| `structural_sensitivity` | 本轮示意输入、结构变更及随动条件 |
| `reported_evidence` / `sources` | 原文数值、定位与本地 PDF 哈希 |

默认沿用 R0、逻辑合同和外围情景。遇到原生行数、选通、平面并行或编码限制，按有证据的映射增加组数/步骤；对相同约束使用相同规则。更多 ADC、多位输入、保持或更多输出通道单列对照，不能各自选最快配置代替默认。

每项例外记录：规则 ID、原因及证据定位、R0 值、变更值、必要资源与时间变化、对两路的影响。更新保留真实 page/block、有效逻辑字节与完整操作；verify/restore/refresh 与同一配置衔接。原值、工程选择和推导分别标记。v0.1 顶层 `acim/dcim/resident` 和外围键已移入上述分层入口，不再保留第二套并行参数。

脚本实现顺序调度的四类模板，包含尾组计数、示意保持及输入分片间权重锁存检查；流水组织由正文给出使用条件，后续需依真实资源另算。合成 `hold_capture=5 ns` 不是通用外围推荐值。

## 复现与验证

本机已有可用 `/opt/anaconda3/bin/python`、XeLaTeX/BibTeX/latexmk、ctex/Fandol 与 pypdfium2/Pillow；无需下载。检查只依赖 Python 标准库。从本目录执行：

```sh
/opt/anaconda3/bin/python scripts/check_shared.py
BASELINE_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改共享参数后显式刷新派生文件，再构建：

```sh
/opt/anaconda3/bin/python scripts/check_shared.py --emit
```

默认检查不改文件；`--emit` 更新外围表、原算例表、结构敏感性表、时间扰动段落及 `data/sensitivity_results.json`。计算输入与生成数据分开，防止手工结果成为推导依据。表内算术精度用于复算，物理范围按量级理解。

本轮验证：12组检查通过，涵盖通用模板与R0对应、位展开/尾组/输出覆盖、8192次有用转换、完整权重与编码/写批、verify和擦除摊销、Byte/ns/GB/s与粒度因子、六点回归和敏感性独立复算、源PDF哈希、生成数据与正文入口一致性。中文PDF编译为8页并逐页查看，最终日志无Overfull/Underfull、未定义引用、缺字或Warning；`git diff --check`通过。构建日志在 `build/`；渲染PNG在 `tmp/pdfs/rendered/`，均被本目录现有忽略规则排除。

## 待审阅的关键选择

1. **精度合同**：推荐继续保留ACIM近似重构、DCIM精确整数及共同INT8/24-bit格式。若要求相同最终误差阈值，需要另设约束，再核对分组、转换精度与服务次数。
2. **默认结构与例外规则**：推荐以R0作默认代入，采用本文的证据约束例外规则；保持及更多资源仅作明确对照。当前比较声明资源而非等面积，是否在冻结前另设共同资源上限需用户判断。

普通时间推荐值与原生页/块的有效payload规则已有明确选择。本轮到v0.2待审阅为止：未计算十类介质结果、制作最终Table I或修改主论文、Table II及共享理论定义。等待用户审阅后再决定是否冻结。
