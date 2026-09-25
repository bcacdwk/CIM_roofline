# Step 4 · Attention（Agent C）

六模型既定完整/global GQA 子层的 Prefill/Decode，各 L=1024/16384/131072，共 **36 条工况**。沿用已审阅 `WS128-INT8-semantic-banks-v1` 与稳定 `case_id`，Step 3 起点为 `e472a0d864b8fb9afb14b0c306217a0e5653e122`。

- [中文独立 PDF](output/attention.zh.pdf) / [TeX](tex/attention.zh.tex)：8 页；结构、代表代入、两边界全部 RI、尾片与容量、窗口关系、独立校验和固定来源。
- [六模型概览](OVERVIEW.zh.md)、[精确 JSON](data/results.json) / [CSV](data/results.csv)：QK/AV 分项与两边界汇总、初末容量与完整 tile、调用、K 行/V 列追加切片、有效形状直方图。
- [输入和来源哈希](data/config.json)、[独立检查](data/checks.json)、[逐页 PDF QA](data/pdf_qa.json)。最终交付状态与哈希以 [DELIVERY.json](DELIVERY.json) 为准。

`ports` 是 tile 接收端主边界；`operator` 是整矩阵阶段入口对照。各角色每元素 1 Byte INT8；非整数用精确分数对象，未先取整。QK query 与 AV 系数是不同输入，operator 共享输入扣除量为 0。`tile_evaluations` 是逻辑调用，operator 为 null 不代表没有运算。

Prefill 从空 KV 建到 L，Decode 从 L−1 追加 1 后在 L 求值。每 KV head 一份状态，由组内 query heads 共享。`capacity` 为最终状态，`initial_capacity` 为初态活跃 tile；完整槽位不表示额外有效 payload，也不约定物理预分配时刻。`append.logical_slice_write_events` 是逻辑切片数，不是器件写事务。

MiMo 固定 global 第 7 层、QK/V=192/128，K 尾片 128+64，Value 缩放 0.612，未引入 SWA sink。Ling 128K 条件保留官方 YaRN factor=4、original_max_position_embeddings=32768、type=yarn，运行端 --max-model-len 131072；原始 config 不改。选中层不推广成全模型结果。

主计算调用共享 API；独立检查不导入生产计数或生成脚本，从原始 config 重新提取参数，以绝对 token tile 的存活期反向累计，再由真实输入块/输出块组合得到有效字节和调用。小长度另按 query、KV head、tile、输入/写入元素身份显式枚举。128K 只保存紧凑直方图和 resident tile 网格，无 L×L 数组或大调用事件表。

检查通过：36 主工况，24 显式边界点（六模型各 L=1/127/128/129），18 主长度 Prefill 差量，14 pilot 重叠条目的全部既有语义字段回归，六模型来源审计。pilot 只作回归比较，主结果重新生成。

从仓库根执行：

```sh
TASK2_PYTHON=/opt/anaconda3/bin/python sh tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/build.sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/render.py
```

仅复算：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python tasks/task2_table_II_workloads/table_IIb/03_attention/scripts/check.py
```

`generate.py` / `check.py` 默认比较现有产物，不覆盖；显式加 `--emit` 才更新。修改后先撤销 DELIVERY ready 状态，依次重新生成/校验、编译、渲染和逐页查看，再更新 QA 与 DELIVERY 版本/哈希。build/tmp 局部忽略。build 只编译本目录 PDF，不编译历史稿或写共享目录。

不推断时间、token/s、端到端性能或器件适合度。相同 RI 不消除总字节、调用和容量差异；数字交接与物理 append 效率留给后续兼容实现。
