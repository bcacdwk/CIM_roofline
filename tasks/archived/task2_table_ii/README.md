# Task 2 — Table II

状态：已生成并验证的独立交付；详见 `AUDIT.md`。采用已授权 Task 0 基线 `6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`。本任务只写此目录，不改共享论文或 Git 状态。

- `output/table_ii.pdf`：英文 Table II（第 1 页），完整参考文献（第 2 页）。
- `tex/table_ii.tex`：自动生成的可复用通栏表格片段，无 documentclass。
- `tex/table_ii_standalone.tex`、`tex/table_ii.bib`：独立入口与 t2_ bibliography。
- `SUPPORT.zh.md`：中文推导、窗口、映射、逐行代入及论文改写说明。
- `sources/manifest.json` / `.csv` / `README.md`：固定来源、版本、定位、权利策略与 SHA-256。
- `configs/`：官方原始 config、场景和映射参数。
- `data/operator_catalog.json`：两个模型共 16 个独立算子形状。
- `data/task3_demands.json`：Task 3 需求接口；与 `data/demands.json` 同源生成。
- `data/table_rows.json`、`exact_counts.csv`：主表选择、显示值及全部精确结果。
- `data/independent_enumeration.json`：非整除小 tile 的输入、写入、MAC 索引及 attention 对照。
- `output/tests.txt`、`export_audit.json`、`pdf_qa.json`：测试和产物检查。

## 离线复现

从仓库根目录运行；所有产物仍只写入本任务目录：

```sh
/opt/anaconda3/bin/python3 tasks/task2_table_ii/scripts/build.py
```

本机已有 Anaconda Python、NumPy、pdfplumber、pypdfium2 和 TeX Live 2026；没有修改共享依赖。其他环境以含同类依赖的 `python3` 替代该绝对解释器路径。生成计数仅用 Python 标准库；NumPy 仅用于小规模数值验证，PDFium 用于渲染（本机未发现 Poppler）。

分步命令（在本目录）：

```sh
python3 scripts/test_counts.py
python3 scripts/generate.py
python3 scripts/verify_exports.py
python3 scripts/summarize.py
cd tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../build table_ii_standalone.tex
```

生成不同的 tile 参数而保留主数据与主表选择：

```sh
python3 scripts/generate.py --tile 96 80
```

该命令输出 `data/demands_custom_tile.json`；默认例子 r/c 为 128/128、192/160，不是通用硬件尺寸。主记录始终注明 `logical_operator` 或 `tile_port`。

## 来源恢复

模型配置、卡片和必要实现文件已保存，可离线复算；不需要权重。可选联网按固定 manifest 恢复缺失来源：

```sh
python3 scripts/fetch_sources.py
python3 scripts/fetch_sources.py --include-fulltext
```

全文只放 `sources/local-only/`，默认忽略；配置／代码附原许可证，自己的来源说明、推导与数据可提交。`source_manifest.py` 是来源建档工具，仅在已有完整原始资料时重建 manifest；正常离线构建不运行它。

## 数据使用

主参考：独立权重投影，因果可见前缀 attention（append 后长度），GQA 的每组一份 K 与 Vᵀ，训练两套权重布局和每 microbatch 临时 Xᵀ。所有场景是本文选择，格式默认 BF16/2 Byte。

用精确分数读取 payload；RI 另含 finite/infinite 状态。只有明确需要的组件才参与后续汇总；attention/cycle parent 和其 children 不重复相加。训练子组件为一次 microbatch，parent events 已累计 A 次。边界能力、格式支持、容量、partial update、输入重放和输出归并必须在硬件配对时核对。本目录没有器件速率、分区、token/s 或性能推断。
