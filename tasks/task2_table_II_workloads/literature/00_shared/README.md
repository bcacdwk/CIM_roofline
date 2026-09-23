# 共同算法与固定实现资料

这些材料只定义后续实际要用的 GQA、因果 Attention 和 SwiGLU/专家 FFN；不继承论文中的模型大小、GPU 流量或性能结论。B、L 与驻留策略由本研究另行指定。统一计数方法尚未开始。

| 资料 | 固定版本、发布日期与用途 | 本地文件 |
|---|---|---|
| Ainslie et al., GQA | arXiv:2305.13245v3，2023-12-23；§2.2 / Fig.2（PDF p.2），一组 query 共享一对 K/V heads | [PDF](raw/2305.13245v3.pdf)、[提取文本](extracted/2305.13245v3.txt)、[版本/许可页](raw/2305.13245v3.html) |
| Vaswani et al., Attention Is All You Need | arXiv:1706.03762v7，2023-08-02（首版 2017-06-12）；§3.2.1–3.2.3，QK 与系数乘 V、decoder 因果遮罩（PDF pp.4–5） | [PDF](raw/1706.03762v7.pdf)、[提取文本](extracted/1706.03762v7.txt)、[版本/许可页](raw/1706.03762v7.html) |
| Shazeer, GLU Variants Improve Transformer | arXiv:2002.05202v1，2020-02-12；§2、式(5)–(6)（PDF pp.1–2），带门控 FFN 的三矩阵定义 | [PDF](raw/2002.05202v1.pdf)、[提取文本](extracted/2002.05202v1.txt)、[版本/许可页](raw/2002.05202v1.html) |

路由专家、top-k 和共享专家的确切定义用各模型自己的实现；共同的 MoE 说明复用 [Ling 报告](../05_ling_1t/raw/2510.22115v2.pdf) §2.1–2.2，不再下载一套大综述。所有 DOI、来源 URL、SHA-256 在 [sources.json](../../data/sources.json)。GQA v3 许可为 CC BY 4.0；其它两份共同论文的 arXiv 页仅声明 non-exclusive distribution，全文及派生文本局部忽略。

## 上游实现快照

[Hugging Face Transformers](https://github.com/huggingface/transformers/tree/2c4914fb939fe9de0d8e7a798af4684d552f18b4) 固定 commit `2c4914fb939fe9de0d8e7a798af4684d552f18b4`（2026-09-22 15:27:31 UTC）。这里只作为静态实现依据，未安装或执行，也不要求其版本等于 checkpoint 的 `transformers_version`。运行端版本兼容性未在本轮验证。

| 对应模型 | 文件与关键类 |
|---|---|
| Qwen3.5-2B | [modeling_qwen3_5.py](raw/transformers/modeling_qwen3_5.py)：Attention 749–821、MLP 824–838、DecoderLayer 861 起；[configuration](raw/transformers/configuration_qwen3_5.py) |
| Qwen3.6-35B-A3B | [modeling_qwen3_5_moe.py](raw/transformers/modeling_qwen3_5_moe.py)：Attention 751 起、Experts 845 起、SparseMoeBlock 904 起、DecoderLayer 947 起；[configuration](raw/transformers/configuration_qwen3_5_moe.py) |
| Ministral 3 8B 2512 | [modeling_ministral3.py](raw/transformers/modeling_ministral3.py)：位置缩放 105 起、Attention 111 起、MLP 176 起；[configuration](raw/transformers/configuration_ministral3.py) |
| Hy3 | [modeling_hy_v3.py](raw/transformers/modeling_hy_v3.py)：MLP 123 起、Attention 210 起、Experts 311 起、MoE 350 起；[configuration](raw/transformers/configuration_hy_v3.py) |

[Apache 2.0 原始许可证](raw/transformers/LICENSE)。不同模型的配置和实现只存在这一份，不复制到各模型目录。Ling 与 MiMo 的 remote implementation 随各自 checkpoint 固定在其 `raw/` 内，不能用这里其它型号的配置默认值代替。

[Qwen 官方项目说明快照](raw/qwen_project_README.md) 固定 commit `2ea10dc725823bf7c3e21ce8557cbe15245132ae`；News 第 51–52 行分别记录 Qwen3.6-35B-A3B（2026-04-16）与 Qwen3.5 小模型（2026-03-02）的发布。该上游项目后续重命名/更新为涵盖 Qwen3.8 的系列入口；本任务只用其历史 News，模型结构仍分别取已固定 checkpoint，不继承后续系列参数。
