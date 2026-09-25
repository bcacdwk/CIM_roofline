# Step 4：六模型 QKV Projection

本目录覆盖固定六模型所选完整/全局 GQA 层的 QKV 投影，各一个 token、权重预驻留，共 6 工况。沿用 `WS128-INT8-semantic-banks-v1`：128×128，各数值角色 1 Byte，ports 主口径，operator 对照。Step 3 基线为 `e472a0d864b8fb9afb14b0c306217a0e5653e122`。

- [独立中文研究稿](output/pdf/qkv.zh.pdf) / [TeX](tex/qkv.zh.tex)：结构差异、计数推导、六模型与分项结果、来源及独立回查。
- [六模型概览](OVERVIEW.zh.md)、[精确 JSON](data/results.json)、[CSV](data/results.csv)：稳定 case_id，20 个语义矩阵，双边界 Q_S/Q_R/RI、容量、tile 与调用。
- [输入与来源快照](data/config.json)：固定 revision、所选层、原生精度与形状、原始来源 URL/定位/哈希。研究状态变更不参与数值输入 hash。
- [独立检查](data/checks.json)、[PDF QA](data/pdf_qa.json)、[交付清单](DELIVERY.json)。`ready_for_review` 只表示内部待审，不代表用户已通过。

两款 Qwen 保留 Q 旁的 output gate G；按头交错原生行经无复制语义重排后形成独立 Q/G bank。Hy3 Q=8192，不能由 hidden_size=4096 反推为 4096。Ling/MiMo 原生融合仅决定存储切片，按独立 Q/K/V bank 计数。MiMo QK head_dim=192，但投影 Q/K 总输出宽度和 D 均整除 128，此行没有半宽尾 tile。

所有分项与汇总 Q_R=0、RI=∞。六模型 ports 输入分别为 81920、196608、147456、327680、655360、1302528 Byte；有效/分配容量同为 10、24、18、40、80、159 MiB。静态 RI 不反映容量或工作量大小。输出投影 W_O、KV 写入、norm/RoPE/门控数字处理不加进本行；不做硬件匹配或性能预测。

`operator` 分项是独立入口，同源 token 输入在汇总中按身份去重，扣除量单列；`ports` 各 tile 接收直接累计。`tile_evaluations` 为 ports 调用数，operator 为 null，不表示无计算。容量是状态规模，与窗口累计 Q_R 分开；allocated_tile_bytes 是逻辑 tile 槽位，不是物理编码容量。分数采用精确 numerator/denominator，∞ 用字符串 `infinity`。

从仓库根复算（默认只比对，不覆盖）：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/01_qkv_projection/scripts/render.py
```

主流程仅调用共享 API 计算。独立检查不导入生产计数模块，而从六份原始 config 与实现静态锚点重建矩阵，以真实 tile 区间累加输入与有效 resident 矩形；operator 以 `(token, element)` 身份集合求并集。每个汇总、分项、布局、窗口字段都比对。Ministral/Qwen3.6 两个重叠工况重新计算后对 pilot 完整 case 逐字段回归。源文件与来源清单 SHA-256 交叉检查；没有执行模型代码或下载权重。

修改后，先撤销 `DELIVERY.json` 的 ready，再对两个 Python 入口顺序加 `--emit` 刷新数据；编译、渲染并逐页核验最终 PDF 后更新 QA，最后重写递增版本的交付清单。所有 build/tmp 和 bytecode 均局部隔离；原始证据、共享方法和 pilot 只读。
