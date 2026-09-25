# Step 4：六模型 FFN / 单路由专家

覆盖固定模型顺序的 6×3=18 工况，每工况包含 gate/up/down 共 54 分项。六个所选层号为 3、0、3、1、4、7（零起点）。每窗口完整装载三矩阵各一次，服务 B=8,64,512 个实际向量。

- [中文独立研究稿](output/ffn_moe.zh.pdf) / [TeX](tex/ffn_moe.zh.tex)：结构、推导、结果解释、来源和复算。
- [六模型概览](OVERVIEW.zh.md)，[精确 JSON](data/results.json) / [CSV](data/results.csv)。
- [配置与来源哈希](data/config.json)，[独立复算及 pilot 回归](data/checks.json)，[页面 QA](data/pdf_qa.json)。

固定参考为 `WS128-INT8-semantic-banks-v1`：128×128、各角色 INT8/1 Byte、ports 主边界、operator 对照、独立语义矩阵 bank。MoE 只取一个路由专家，不乘 top-k、全部专家、共享专家或层数；router、非矩阵处理不计入三矩阵 payload。B 是该份权重在一次驻留中实际服务的向量总数。

全部 D/F 整除 128，因此 ports RI 都为 B/128，即 1/16、1/2、4。容量为 36、168、3、18、48、36 MiB；同 RI 仍保留总量差异。operator 汇总为 B(D+F)/(3DF)，gate/up 的共享 x 显式扣除 BD，down 的新输入 BF 保留。当前阶段输出不重复加入 Q_S。Qwen3.5 与 MiMo 的 D/F 交换使两边界汇总相同，但 operator 分项与共享扣除量不同。

JSON 保留精确整数及 `{numerator, denominator}` 分数。`result.parts` 中的 operator 是各矩阵独立入口；聚合扣除字段是 `operator_shared_input_overlap_removed`。ports 的 `tile_evaluations` 是真实逻辑调用数；operator 的 null 不表示没有计算。`capacity` 保存有效容量、完整逻辑 tile 槽位容量及驻留 tiles，和累计写入 Q_R 分开。当前一次全写入且无尾块，所以两容量恰等于 Q_R。

主计算调用共享 API；独立检查不导入生产公式，重新从原始配置获取 D/F，按真实 tile 切片累加写入面积，逐向量累加接收片长/调用，并按输入阶段与向量身份去重。6 个 pilot 重叠工况重新计算后逐字段比较完整记录，未复制结果作为正式数据。源码仅静态读取，没有执行模型或下载权重。

从本目录执行（数值检查只需 Python 标准库）：

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python scripts/generate.py
PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python scripts/check.py
TASK2_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render.py
```

默认验证已生成文件，不覆盖数据；更新时先分别运行 `generate.py --emit`、`check.py --emit`，随后编译、渲染并逐页检查。build/tmp 仅在本目录忽略；共享和其它计算目录只读。来源哈希只锁定原件与共享固定文件；study_plan 的状态更新不触发伪过期。

交付版本与最终 SHA-256 见 [DELIVERY.json](DELIVERY.json)。本轮为 Step 4 FFN 分类产物，没有进行硬件性能推算或 Step 5 英文总表。
