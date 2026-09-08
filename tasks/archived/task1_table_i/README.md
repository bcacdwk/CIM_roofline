# Task 1 — Table I

基线：`6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`（用户已授权）。
状态：**已完成独立交付，局部文献缺口已记录**。调研／访问日期：2026-09-07。仅本目录写入；未提交、未推送，未修改主论文或 Table II。

## 审阅入口

| 交付 | 文件 |
|---|---|
| 英文 Table I；第二页为完整解析的 13 条引用 | [output/table_i.pdf](output/table_i.pdf) |
| 可引入主文的片段；独立编译入口；独立文献库 | [tex/table_i.tex](tex/table_i.tex)、[tex/table_i_standalone.tex](tex/table_i_standalone.tex)、[tex/table_i.bib](tex/table_i.bib) |
| 中文逐行证据、推导、候选及论文改写段落 | [SUPPORT.zh.md](SUPPORT.zh.md) |
| 复算、证据数量、版面检查、交接缺口 | [AUDIT.md](AUDIT.md) |
| 全部硬件记录；后续匹配导出 | [data/hardware_records.json](data/hardware_records.json)、[data/task3_hardware_export.json](data/task3_hardware_export.json) |
| 主表显示记录；平面表 | [data/main_table.json](data/main_table.json)、[data/main_table.csv](data/main_table.csv) |
| 来源身份、版本、访问与证据页面 | [sources/manifest.json](sources/manifest.json)、[sources/EVIDENCE_INDEX.md](sources/EVIDENCE_INDEX.md)、[sources/access_log.json](sources/access_log.json) |

主表 12 行覆盖全部十类介质，SRAM ACIM/DCIM 分开，两篇 Zhou 铁电晶体管论文分别呈现。底表有 16 条实现记录、17 组原始证据和 190 项提取事实；来源共 21 项，本地全文 PDF 14 份。六行可换算 ρ；只有 Jung MRAM 当前具备同配置 τ 与 RI*。未知为 `null` 加原因，主表显示长横线。D6CIM 的一拍写参考情景单独保存，不混入主表能力。

## 复现

在仓库根目录进入本任务目录。以下命令已在现有环境通过，未安装或改动共享依赖：

```sh
cd tasks/task1_table_i
/opt/anaconda3/bin/python3.12 scripts/build_data.py
/opt/anaconda3/bin/python3.12 scripts/check_data.py
/opt/anaconda3/bin/python3.12 scripts/prepare_sources.py
cd tex
/Library/TeX/texbin/latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build table_i_standalone.tex
cd ..
/opt/anaconda3/bin/python3.12 scripts/render_pdf.py
```

数据生成和检查只需 Python 标准库；`prepare_sources.py` 不加参数也只需标准库。PDF 编译使用 TeX Live 2026、IEEEtran、amsmath、booktabs、array、tabularx、cite、hyperref。渲染使用已有 Python 3.12.7、pdfplumber 0.11.7、pypdfium2 4.30.0、Pillow 10.4.0。这里没有 Poppler，采用 pypdfium2 渲染并逐页目视检查。

若保留了本地全文，还可重建 47 个关键页面缓存：

```sh
/opt/anaconda3/bin/python3.12 scripts/prepare_sources.py --render
```

所有构建输出均留在本任务目录。共享环境的系统 `python3` 受 Xcode 许可状态影响，以上命令因此明确使用已可用的 Anaconda Python。其他环境可替换解释器及 TeX 可执行路径。数据重建不需要网络，也不需要被忽略的全文；缺少全文时检查结果会明确列出，不能据此声称重新验证过原始材料。

## 数据与来源的维护边界

手工维护的输入是 `data/extractions.json`（原始事实、两维证据标签与来源位置）、`data/implementations.json`（边界、模式、格式、几何和算式）、`data/main_selection.json`（选行与文字）及 `data/reference_scenarios.json`。来源身份在 `sources/manifest.json`，访问经过在 `sources/access_log.json`，页面选择在 `sources/capture_plan.json`。

`build_data.py` 从上述输入生成标准化事实、全部中间步骤、主表 JSON/CSV、覆盖清单、Task 3 JSON、TeX 和 BibTeX。不要手改生成的数值。`prepare_sources.py` 生成逐来源索引与证据笔记；`--render` 另保存带来源哈希的 `sources/page_index.json`。`tmp/` 中早期整理脚本和试验文件不是复现入口。

逻辑矩阵统一为 `n_out × n_in`；格式名称和位宽同时保留，内部单位为 Byte、second、OP，GB/s 使用十进制。模拟 resident 没有离散逻辑码本时 b_R 为空；普通存储写入和条件参考设计使用独立字段。接口含义和候选处理见 [data/schema_notes.json](data/schema_notes.json)。

全文及其页面／文本派生文件集中于默认忽略的 `sources/local-only/`，不默认公开提交。两篇根目录 Zhou 文件保持原位，任务副本的原路径、来源身份和哈希见 [sources/repository_copies.json](sources/repository_copies.json)。网页可读但未取得本地 PDF 的两项来源，以及仅取得题录／摘要的五项来源，均在访问记录中明确区分。

## 完成状态

- 原始调研、写入证据追查、原位副本与来源记录：完成。
- 10 类介质覆盖、12 行主表、底表和参数化导出：完成。
- 数据生成、两项以上独立复算、单位／兼容性检查：通过。
- 独立编译、引用解析、两页渲染与可读性检查：通过。
- 未闭合的完整写入事务、器件到阵列时序及访问缺口：详见 [AUDIT.md](AUDIT.md)，不补造参数。
