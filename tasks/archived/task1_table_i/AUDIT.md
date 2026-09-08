# Task 1 审计与交接

日期：2026-09-07。状态：独立 Table I 交付完成，保留明确的局部证据缺口。授权基线为 `6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`。所有写入均在 `tasks/task1_table_i/`，不更改共享 Git 状态，不处理另一任务的文件或未跟踪文件。

## 1. 完成范围与来源覆盖

主表 12 行，覆盖十类介质；SRAM ACIM 与 DCIM 分列，2025／2026 铁电晶体管分别成行。完整底表 16 条实现记录，另有 1 条独立 D6CIM 条件情景。未重建 Table III，未分类 workload，未改主论文。

| 材料层级 | 数量 | 范围 |
|---|---:|---|
| 来源清单 | 21 | 原始论文、期刊扩展版、正式摘要和厂商 datasheet |
| 已保存并校验的全文 PDF | 14 | 含 2 份仓库 Zhou 原位副本；全文默认忽略 |
| 在线读取但无可用本地 PDF | 2 | NAND 原文正文（Table 1 原图缺失）；Infineon F-RAM datasheet |
| 仅题录、作者清单或摘要 | 5 | D6CIM 2026、Dyamond 2024/2025、Lue 2019、Chiu 2023 |
| 关键页面缓存 | 47 | 原 PDF 整页渲染，170 dpi，页码与来源 SHA-256 可追溯 |
| 原始证据组／独立事实 | 17 / 190 | 所有主表行均有来源位置和具体适用配置 |
| 主表数值能力 | 6 个 ρ；1 个 τ；1 个 RI* | MRAM 为唯一闭合的同配置数值配对 |

事实来源的 A 维标签共：实测芯片 110 项、实测器件 45 项、仿真 27 项、参考情景／厂商规格 8 项。按证据组顶层标签计分别为 9、3、3、2 组；组内混合来源仍以逐项标签为准。B 维独立记录原文报告、换算或条件估计；主表六项 ρ 中五项是实测配置换算，一项 PCM 是 RTL 仿真时间换算。τ 与 RI* 是同一 MRAM 实测配置的换算，未标为原文直接报告本文变量。

部分厂商规格无法从 datasheet 判定为独立实测样本，放在 `reference_scenario` 来源类并说明为正式规格，不冒充实测 CIM。NeuRRAM 56 μs/cell 同样保持作者条件预估身份。

逐项材料见 [来源索引](sources/EVIDENCE_INDEX.md)、[访问记录](sources/access_log.json)、[页面索引](sources/page_index.json)、[覆盖清单](data/coverage.json)。关键页取值来自文字或明确数字标签；没有连续曲线插值，不编造读图误差区间。程序校验和人工阅读各有作用：算术检查不能证明文献事实，页面缓存也不表示对整页所有主张作了验证。

## 2. 单位、payload 与兼容性检查

`scripts/check_data.py` 的八组检查通过，结果保存于 [output/check_results.json](output/check_results.json)：

1. 原始 JSON 经脚本重新生成记录、TeX、文献库及导出，与已有生成文件逐字节一致。表内逻辑尺寸、位宽及数值时序条件绑定原始事实／标准化记录；模式名中的数字（如 4-phase、2T2C）保留为模式标识。
2. `hw_`／`t1_` ID、来源存在性、定位、格式、未知值原因、逻辑尺寸与两维证据标签完整。
3. bit/Byte、Kibit/Byte、ns/μs/minute/second、MHz 和十进制 GB/s 换算通过；没有 GiB/s 输入混作 GB/s。普通存储与投影写入不进入 CIM 实测能力字段。
4. SRAM 位切片、RRAM／MRAM 互补器件、NAND 复制及 FeFET 制作／验证容量分开；物理器件不重复计入 payload。
5. D6CIM、MRAM 和 Jia 的独立计算与脚本一致，细节见下一节。
6. RI* 仅由兼容数值对生成；反向区间分母检查通过。区间算术使用标明的合成测试，未将其当作硬件观测。本轮没有虚构能力区间。
7. 十类介质均有主表行，SRAM 模式分开，表内全部 citation key 在独立 bibliography 中存在。
8. 14 个本地全文 PDF 文件头及 SHA-256 全部核对通过；两篇根目录原文件哈希与副本一致。无应在当前工作区存在而缺失的全文副本。

所有能力都保留峰值／本地调度／独立测量等性质，没有将应用平均吞吐当成普遍严格上界。`use_as_strict_upper_bound=false` 表示仍需后续在匹配边界上验证上界条件，不否定所保存工作点的原始证据。

## 3. 手工独立复算

手工路线采用不同于主公式的运算计数或整阵列重载，与程序结果对照。

| 实现 | 独立路线 | 结果 |
|---|---|---|
| D6CIM UINT8 | 每向量 2×128×16 OP，360 MHz／64 clocks；κ_S＝2×16 OP/Byte | 23.04 GOPS／32 OP/Byte＝0.72 GB/s，与脚本一致 |
| Jung MRAM | 逻辑全阵列 64×64/8＝512 Byte；64 行×2 clocks／11.1 MHz＝11.531531… μs | τ＝0.0444 GB/s；ρ＝(64/8)×11.1 MHz＝0.0888 GB/s；RI*＝2，与脚本一致 |
| Jia SRAM ACIM | 16 核×1152×64×2 OP×20 MHz／4 phases | 11.79648 TOPS，与原文 11.8 TOPS 的舍入一致 |

MRAM 的互补 MTJ 两次写入只增加时间，逻辑权重不计两遍；该交叉验证同时检查 payload 与完成条件。额外的 PCM 单核 256 Byte／520 ns 对应约 0.4923 GB/s，64 核乘 2 OP/MAC 可还原约 16.13 TOPS，与原文 16.1 TOPS 对应。

## 4. 编译与版面检查

复现命令见 [README.md](README.md)。本机使用 Python 3.12.7、TeX Live 2026／latexmk 4.88。编译入口为 `tex/table_i_standalone.tex`，中间产物只在 `tex/build/`，最终 PDF 由 `scripts/render_pdf.py` 复制及渲染。

`latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build table_i_standalone.tex` 已完成并确认目标最新。BibTeX 引用完全解析；13 条实际引用在第二页。没有 undefined citation/reference、overfull box 或裁切。PDF 两页均已渲染并目视检查，公式、区间符号、长横线、表注、文献指数与 DOI 换行可读，无重叠或缺字。

| 版面量 | 实测值 |
|---|---:|
| IEEE 双栏通栏宽度 | 516 TeX pt＝181.353 mm |
| 表格正文及表注高度 | 295.433 TeX pt＝103.833 mm |
| 含 caption 的实际文字总高度 | 112.915 mm |
| 表体／表注字号 | 8.5 pt；正常数学下标约 6 pt |
| 页数 | 2 |
| 未解析引用／overfull | 0 / 0 |

未使用整体缩放。TeX pt 按 72.27/in 换算，PDF 坐标 pt 按 72/in 换算；两个单位没有混用。机器版面结果与最终 PDF 哈希见 [output/pdf_qa.json](output/pdf_qa.json)。中文“可供论文改写的说明”共 397 字符，其中 339 个汉字，满足约 300–600 字要求。

交付前另核对全部本地 Markdown 链接、21 项来源与访问记录一一对应、47 个缓存图像哈希、最终 PDF 哈希及 13 条已解析 bibliography 项，均通过。显示字段改为数据绑定后的 TeX 与已目视检查版本逐字节相同。

## 5. 具体缺口及对下一轮匹配的影响

| 实现／类别 | 尚缺信息 | 下一轮影响 |
|---|---|---|
| Jia SRAM ACIM | 同工作点普通写口并行宽度与完整权重 ready 间隔 | 可匹配求值；不能闭合写入 ridge |
| D6CIM DCIM | 正常 SRAM 写周期是否可在 360 MHz 一拍完成；扩展版全文 | 参考 τ＝5.76 GB/s 只在独立假设情景，不可直接代入实测 Roofline |
| DRAM | Ambit 多位乘加／归约完整序列；Dyamond 原始全文及精度、读写时序 | 布尔原语不能直接实例化完整整数 MVM |
| Gain-cell eDRAM | 宏内服务组复制、互补排布、输入有符号编码、写口时序、刷新 duty | 当前 ρ 是单 MAV 组；不能按 32 Kibit 容量任意放大 |
| 3D NAND | 原文 Table 1、完整相位／重构时间；同芯片 verify、编程并行度和擦除策略 | 保留几何和符号式；303 ns 不是 MVM；不能拼接商品页写带宽 |
| 2D NOR | 单次完整求值 II、完整精度 resident 格式、调谐成功／verify 时间与并行写 | 分类器平均延迟及其他 ESF1 测试不能合成配对能力 |
| RRAM | NeuRRAM 实际外控完整编程时间及逻辑码本；Liu 绝对 pulse／verify 时间 | 单核 ρ 可匹配，但差分行、输出精度和松弛准备条件需保留 |
| MRAM | 主机数据准备、部分行更新效率、输出码／误差接受条件与校准边界 | 当前配对仅适用于完整行、本地已备数据和原生近似 TDC；不证明读写可无干扰重叠 |
| PCM | 预印本与最终版逐项比对；模拟 resident 码本、迭代成功分布和 32 writeheads 调度 | 4-phase RTL ρ 可匹配；不能用 8-bit I/O 推定 b_R 或 τ |
| FeRAM | 完整集成 CIM、数字输出时间、阵列并行写入及 ready | 分立 FeCAP 测试和普通 F-RAM 写入均不能替代 CIM 能力 |
| 2025 FeNOR | 验证过的并行写入数量、完整事务 ready／verify、阵列级完整 CIM 时序 | 50 ns、<100 ns 与 192 物理 cell 不足以构造能力 |
| 2026 vertical FeFET | 同工艺模式完整并行读写时序及 CIM 求值，温度／精度条件 | ±2 V／20 ns 和 1 Kib 图案验证保留为器件／阵列证据；不推定层并行 |

这些缺口是局部证据限制，不影响其他记录复算或本轮交付。访问失败均记录已读范围，没有绕过访问控制或声称读过不可获取的全文。下一轮入口是 `data/task3_hardware_export.json`；先检查格式名称、边界、逻辑尺寸、服务单元和输出条件，再实例化映射。寿命、刷新与编程松弛保持可行性／维护字段，不无条件折算为寿命平均 τ。

仅修改 `tasks/task1_table_i/`，未提交、未推送。
