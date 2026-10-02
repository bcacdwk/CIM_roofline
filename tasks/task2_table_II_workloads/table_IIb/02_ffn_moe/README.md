# FFN／MoE：矩阵阶段入口的输入复用与 RI

2026-10-02 主 Agent 修订，待用户审阅。正文为 [PDF](output/report.zh.pdf) 与 [TeX](tex/report.zh.tex)；[中文预览](PREVIEW.zh.md) 展示相同公式、参数和结果。六模型各取 U=1、16、128、1K、16K，共 30 个有限工况、90 个矩阵分项。

## 对象与计数

前两模型取一个 Dense FFN，后四模型取一个路由专家。`W_gate,W_up:[F,D]`、`W_down:[D,F]` 各完整装载一次，所有被计数角色为 1 Byte/element。U 为复用次数（reuse count），表示这份三矩阵权重一次装载后累计服务的向量数，包含首次使用、可跨 batch/请求；对 MoE，它是所选专家实际接收的向量数，不直接用全模型 batch 替代。

将累计输入按行记为 `X:[U,D]`，同阶段 gate/up 共享 `X`，其 `UD` 输入只计一次。`Z=SiLU(XW_gateᵀ)⊙(XW_upᵀ)` 成为 down 的新输入，另计 `UF`；输出为 `Y=ZW_downᵀ`。因此 **Q_S=U(D+F)，Q_R=3DF，RI=U(D+F)/(3DF)**。分项输入独立记录为 `UD,UD,UF`，总输入扣除 `UD`。当前矩阵输出不直接计入 Q_S；它作为下一矩阵阶段的输入时再计。

窗口初始权重为空，有效容量为 0；一次装载后保留三矩阵，有效容量为 `3DF` Byte。本窗口内累计写入恰好等于末态有效容量，两字段仍独立记录。范围不含路由矩阵、共享专家、其他路由专家、其余层和非矩阵运算；不乘 top-k 或上述对象数量。原生存储类型仅作来源备注，不改变 1 Byte/element 的统一计数。

## 固定来源

共同入口为 [CONTRACT](../04_crosscheck/CONTRACT.zh.md)、[schema](../04_crosscheck/data/conventions.json)、[模型输入](../04_crosscheck/data/model_inputs.json) 及当前 [II(a)](../../table_IIa/README.md)。模型、revision、层号均保持既定材料；本文以原生配置和实现重核 FFN 维度，没有执行模型或下载权重。

| 模型 | 层（零起点） | D | F | 本地结构卡 |
|---|---:|---:|---:|---|
| Qwen3.5-2B | 3 | 2048 | 6144 | [结构卡](../../literature/01_qwen35_2b/STRUCTURE.zh.md) |
| Ministral 3 8B (2512) | 0 | 4096 | 14336 | [结构卡](../../literature/02_ministral3_8b/STRUCTURE.zh.md) |
| Qwen3.6-35B-A3B | 3 | 2048 | 512 | [结构卡](../../literature/03_qwen36_35b_a3b/STRUCTURE.zh.md) |
| Tencent Hy3 (295B) | 1 | 4096 | 1536 | [结构卡](../../literature/04_hy3_295b/STRUCTURE.zh.md) |
| Ling-1T | 4 | 8192 | 2048 | [结构卡](../../literature/05_ling_1t/STRUCTURE.zh.md) |
| MiMo-V2.5-Pro | 7 | 6144 | 2048 | [结构卡](../../literature/06_mimo_v25_pro/STRUCTURE.zh.md) |

[config.json](data/config.json) 保存完整 revision、来源定位和 SHA-256；源注册表为 [sources.json](../../data/sources.json)。Qwen3.6 和 Hy3 实现将 gate/up 打包，逻辑上仍取两个 F×D 矩阵。Qwen3.5 与 MiMo 的 D/F 互换，所以汇总相同，分项输入及共享扣除不同。

## 精确数据与独立检查

[results.json](data/results.json) 和 [results.csv](data/results.csv) 保存每个工况及 gate/up/down 的原始 Byte、RI、有效容量与共享扣除量。计数均为整数或约分后的 `{numerator,denominator}`，未先转浮点。CSV 为 30 个总量行加 90 个分项行。

[generate.py](scripts/generate.py) 从共同原生参数生成主计数与表格；[check.py](scripts/check.py) 不导入它，也不导入旧 shared 生产 API。独立检查重新读取原始 config 的 D/F、核对层型与实现中的三矩阵构造，再按实际矩阵行宽累计写入。输入以 `(源阶段, 元素下标)` 标识，gate/up 的 x 身份重叠，down 的 z 独立，随后逐向量累计。

[checks.json](data/checks.json) 记录独立复算、共同 schema 检查、来源 SHA-256 和归档回归。归档只读路径为 `tasks/archived/task2_table_IIb_previous/02_ffn_moe/data/results.json`；未运行任何旧脚本。新扫描不与旧 B=8/64/512 重合；用新 U/旧 B 缩放旧 operator 的输入、RI 和共享扣除作迁移核对，写入量和有效容量不变。初始容量按当前明确的空权重窗口独立核验。

## 复算、编译与渲染

从仓库根运行；生成与检查默认只读比较，显式 `--emit` 才刷新相应数据：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/02_ffn_moe/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/02_ffn_moe/scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/02_ffn_moe/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/02_ffn_moe/scripts/render.py
```

如源材料经授权更新，先分别运行 `generate.py --emit` 和 `check.py --emit`，再编译、渲染与逐页查看。正文引用 [共同 preamble](../04_crosscheck/template/preamble.tex)，顺序为对象与公式、模型信息、代入结果、结果说明。`render.py` 只生成本目录 `tmp/pdfs/` 的图片和提取文本；人工逐页查看后才记录 [pdf_qa.json](data/pdf_qa.json)。交付清单 [DELIVERY.json](DELIVERY.json) 记录实际文件哈希；`ready_for_review` 不等同于用户批准。

数量后缀 1K=1024。结果显示 RI≥1 保留一位小数、RI<1 保留三位有效数字，原始分数保留。专家实际替换策略会改变 U，但本表不由模型大小断言实际替换频率。
