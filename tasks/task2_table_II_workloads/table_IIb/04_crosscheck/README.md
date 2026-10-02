# 共同记号与统一复核

2026-10-02：用户认可此前三份中文稿的结构和计算；本轮由主 Agent 亲自修改 II(a)/II(b) 的复用记号、扫描档位和小数显示。**修订完成，待用户审阅。** 目录与文件路径保持，未新增归档或版本目录。

- [共同约定](CONTRACT.zh.md)、[精确接口与扫描](data/conventions.json)、[固定模型输入](data/model_inputs.json)。
- [统一排版](template/preamble.tex)、[正文骨架](template/report.zh.tex)、[显示函数](../../scripts/format_results.py)。
- [复核说明](REVIEW.zh.md)、[小数预览](PREVIEW.zh.md)、[精确 JSON](data/results.json) / [CSV](data/results.csv)。
- [独立复算与交付检查](data/checks.json)、[来源追踪](data/source_manifest.json)、[输入保护与 II(a) 授权修改记录](data/protected_inputs.json)。

统一 U 为复用次数（reuse count）：一次完整装载后累计服务的向量数，包含首次使用，可跨 batch 或请求。K/M 数量后缀为 1024/1024²。RI≥1 保留一位小数，RI<1 保留三位有效数字；机器值仍为整数／精确分数。表中所有小数来自 Python 显示函数。

II(b) 共90个有限工况、6个极限格、262条组件记录；CSV 共358条数据行、18列。前三稿各2页，中文 II(a) 为1页。四份 PDF 已逐页查看。

主复算不导入生产计数程序，独立按矩阵行、源输入身份和因果前缀累计。归档回归包含30个按 U 缩放的 FFN 对照、12个1K Attention 同窗口对照、6个 QKV 一次装载窗口对照；Attention 分类检查另复算全部36个旧长度工况，其中未进入新扫描的工况只作回归。

从仓库根运行（默认只读）：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/04_crosscheck/scripts/crosscheck.py
```

`--emit` 只刷新第四目录的统一结果、预览与检查报告。分类 READY 清单、来源哈希、精确字段、分项/汇总、CSV、中文节次、表格样式及 PDF QA 均先核对。页面 PNG 为可重新渲染的忽略文件；本地存在时也核对哈希。所有原始模型资料保持不动，II(a) 的本次改动由用户明确授权并留有前后哈希。
