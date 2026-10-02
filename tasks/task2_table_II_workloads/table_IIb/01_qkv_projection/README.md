# QKV 投影：一次完整装载的输入复用与 RI

2026-10-02 主 Agent 修订复用记号、扫描与显示。固定六模型、revision 与所选层；数学入口为已认可的 [Table II(a)](../../table_IIa/README.md)。本目录覆盖 24 个有限工况（U=1、1K、128K、1M）与 6 个 U→∞ 极限格，采用 [共同契约](../04_crosscheck/CONTRACT.zh.md)。交付状态为待用户审阅。

- [中文 PDF](output/report.zh.pdf)、[正文 TeX](tex/report.zh.tex)、[中文预览](PREVIEW.zh.md)。
- [模型与来源配置](data/config.json)、[精确 JSON](data/results.json)、[精确 CSV](data/results.csv)。
- [独立复算与迁移检查](data/checks.json)、[PDF 逐页检查](data/pdf_qa.json)、[交付清单](DELIVERY.json)。

同一层完整／全局 GQA 的 Q、可选 G、K、V 权重完整装载一次；U 为复用次数（reuse count），是一次装载后累计服务的向量数，包含首次使用，可跨 batch/请求。每元素 1 Byte，各投影共享同一阶段输入 X，故 Q_S=UD，Q_R=D N_proj，RI=U/N_proj。初始有效权重容量为 0，最终为 D N_proj Byte；有限与无穷格的写入量均为这一次装载的大小。输出不加入本阶段 Q_S。QKV 对象不包含 O 投影。

模型参数直接保留原生值：两款 Qwen 的 `q_proj` 同时产生 Q 与输出门控 G，分别记录逻辑分项；MiMo 的 QK/V 头维为 192/128。Hy3 与 Ling 的 N_proj 同为 10240，所以 RI 完全相同。输入维度 D 在比例中抵消，但仍决定绝对字节。

## 来源与边界

原始配置、结构卡与相关实现均位于任务根 `literature/`；`data/config.json` 的 source_paths 和 sources 记录所用文件、定位与 SHA-256。官方 URL、checkpoint 和实现各自 revision 由任务根 `data/sources.json` 追溯，后者也被固定哈希。计算未执行模型实现或下载权重；矩阵形状由配置和线性层构造得到。

原生 BF16／混合 FP8 仅作为来源信息；本表的逻辑数值角色统一取 1 Byte。公式和结果不使用硬件结构参数。固定层号（从 0 起）依次为 3、0、3、1、4、7；本对象为各模型所选的一组投影，不乘主干层数。

旧版结果位于 `tasks/archived/task2_table_IIb_previous/`。用户已明确将 QKV 窗口从预驻留改为一次完整装载，因此旧 Q_R=0、RI=∞ 不要求与新有限档相等。迁移检查只要求 U=1 输入与旧 operator 一致，新写入等于原生权重元素数及旧有效容量；逐项细节留在 `data/checks.json`。

## 复算与编译

从仓库根执行以下命令，默认生成／检查脚本只读比较，不刷新结果：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/render.py
```

`generate.py --emit` 刷新配置、JSON、CSV、两份表格片段和 PREVIEW；`check.py --emit` 刷新独立检查记录。主计算根据固定维度使用闭式公式。独立检查不导入生成器，另读 raw 配置恢复投影宽度，按带投影名的权重行身份累计元素，并对各分支的输入行身份取并集；另以非整齐小形状显式枚举每个元素，验证同源重叠。极限以正输入斜率和固定正权重写入量验证。

编译使用共同 preamble、XeLaTeX 与固定 SOURCE_DATE_EPOCH。渲染器使用 pypdfium2 生成逐页 PNG，并与已记录的视觉检查哈希比对。内容修改后需再次逐页查看，再用 `render.py --record-review '第1页检查说明' '第2页检查说明'` 显式更新 PDF QA。只在完成复算、编译和逐页查看后写 DELIVERY；主 Agent 内部检查通过不代表用户已审阅通过。

数量后缀 1K=1024、1M=1024²；PDF/预览中 RI≥1 保留一位小数，RI<1 保留三位有效数字，精确 JSON/CSV 保持整数与分数。
