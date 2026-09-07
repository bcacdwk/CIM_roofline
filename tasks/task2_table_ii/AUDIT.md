# Task 2 审计与交接

完成日期：2026-09-07。授权基线：`6817194a3be1ba18ad2c3eb9273bb25a0fa470c2`。

## 交付状态

Table II 已实际生成、编译并渲染检查。`output/table_ii.pdf` 共 2 页：第 1 页为英文通栏表及表注，第 2 页为 9 条解析完整的参考文献。可复用片段 `tex/table_ii.tex` 不含 documentclass，独立入口显式将表号设为 II。共 10 个主表行，所有数值来自配置、事件计数和显示脚本。

`SUPPORT.zh.md` 包括符号推导、真实模型目录、双级映射、每行自动代入、参数观察、配对条件及约 300–600 字中文论文改写说明。主数据包含 607 条记录（含保留分项和需求汇总，不能全部相加）；两个模型有 16 个独立矩阵形状。`data/task3_demands.json` 是可供 Task 3 使用的完整需求导出，未添加任何硬件服务率。

## 来源核查

- 官方 Qwen 模型 API 返回实际仓库 commit；以完整 commit 重新取得 config.json、model card 和 LICENSE。原始文件保留，没有权重下载。
- 7B revision：`d149729398750b98c0af14eb82c78cfe92750796`；14B revision：`97e1e76335b7017d8f67c08a19d103c0504298c9`。
- Transformers：v4.45.2 解引用 commit `53fad641cfdb5105e2470bcf3ef17ea8e25cc300`；PyTorch：v2.4.1 commit `ee1b6804381c57161c477caa380a840a84167676`。实际源码与许可证保留。
- 原始论文覆盖 Qwen2.5 报告、Attention、GQA、ISAAC、FlashAttention。manifest JSON/CSV 与 sources/README.md 有版本、URL、日期、文件、定位、支持点、SHA-256 和提交策略。
- 源码 AST 独立解析 Q/K/V/O、gate/up/down、LM head 的构造参数与 bias；16 个目录形状全部吻合。没有以“7B/14B”名称或旧表近似推算。
- 用目录矩阵、bias、embedding 与 RMSNorm 合计参数数：7B=7,615,616,512，14B=14,770,033,664；分别与官方 API 快照 safetensors.total 一致。快照动态点赞、下载计数不参与结果。
- 未发现阻塞此任务的真实模型定义冲突。tokenizer token 数与 config vocab_size 的对象差别，以及配置中旧 transformers_version 与选定核查代码版本的差别，已明确说明。use_sliding_window=False 与实际 full causal 解释一致。
- 所有论文全文及提取文本位于默认忽略的 `sources/local-only/`；公开配置、代码与相应 LICENSE 保留。自己的笔记、定位、推导和数据可提交。

## 采用的参考窗口和映射

| ID 族 | 主约定 | 与输出能力配对时的要求 |
|---|---|---|
| G0 | W 已驻留且不改写，decode U=B | 整矩阵或全部 tile 已保留，容量不能省略 |
| G1 | 独立矩阵装入一次，随后服务本窗口全部 U；prefill U=BN | logical_operator 要完整容量；tile_port 可逐 tile，需外部输入和部分和工作区 |
| G2 | gate 的 U=2048 分四组512，组间因共享区域调度逐出；四次 placement | 每个 epoch 所有有效权重各写一次；没有重复扩大有效 M |
| A1 | 标准 causal、包括当前位置；C 为 append 前历史，t_j=C+j；K:t_j×d，Vᵀ:d×t_j；组内共享，主副本 D=1 | 所有历史 KV tile 保留；边界 tile 有效元素 append；K 行／V 列更新、QK 与 AV 归并分别适配 |
| T1 | W/Wᵀ 预驻留；每 microbatch 临时装入 Xᵀ 求 dW；A 次后两权重布局各更新一次 | 保留两布局、临时区和外部梯度累加；transpose 不是免费能力 |
| F1 | QKV 或 gate/up 拼输出轴后一次接收 X，仅作对照 | 扩大服务边界才能共享输入；不与主独立投影混加 |

逻辑与 tile 两级均提供。r/c 保持参数，默认 128×128 和192×160 是实例化例子；第二组也使真实 head dimension 出现边界 tile。有效 payload 不包含内部补零；固定槽容量另列。K、V 两方向的端口重复根据形状各自计算。公式与记录区分实际写入累计量、最终容量、最小驻留容量和逻辑槽数。

推理 B=1/8，prefill N=2048/8192，decode append 后 L_v=2048/8192；训练 microbatch B=1、L=2048、A=1/16。主格式 BF16/2 Byte，另有 INT8 输入／INT8 vs INT4 权重、7 份 KV 副本和 dW 角色交换对照。它们是分析场景，不是官方训练配置或硬件支持声明。

## 独立检查与结果

先实现通用符号内核并通过小规模测试，再实例化模型。最终 `scripts/test_counts.py` 的 15 项测试全部通过；不是只把同一闭式公式运行两次。

| 检查 | 独立方法与结果 |
|---|---|
| 非方阵、精度、半字节 | 多组小矩形逐有效元素计数，含 INT8/INT4、INT4/BF16；3 个 INT4 元素精确保留3/2 Byte |
| 静态、一／多次装载 | 明确0/1/3次写入索引，与输入工作解耦；静态 RI 用状态而非 JSON Infinity |
| 非整除 tile 与广播接收端 | 5×7、3向量、3×4 tile 的完整写入／输入／MAC 索引保存在 data；有效权重35、槽位48，输入每元素两个输出接收端，输入列不再乘重复因子 |
| 完整模式重复 | 输入和实际 placement 同乘4，Q_S/Q_R 同比增加、RI 不变 |
| Batch 与 GQA | B=1/8 权重共享；session KV 随B变化；显式 Hq=6、Hkv=2，通过 head-owner 索引核对 |
| Decode 长度边界 | append 后长度1/2/5，C=L_v−1；当前 token 包括在有效项中 |
| Prefill 与逐步 append | 空 KV 起逐次 decode 累计与对应 causal prefill 完全一致，含 tile 与非整除形状 |
| 三角、矩形、mask/padding | 枚举完整矩形且传入被 mask 零值，与逐前缀对照；有用OP相同，执行OP与输入不同 |
| 两次 attention 输入 | query 与概率各为一个明确服务族；没有给 QK 输出再加一笔，也没有漏掉 AV 输入 |
| 独立 K/V/query/probability 精度 | 不同角色分别用 BF16/INT8/INT4，与枚举元素数按各自格式换算一致 |
| KV 副本 | query 工作分配保持输入总量，3份副本的写入与容量同步乘3 |
| 前向、dX、dW | 每项形状和MAC索引独立枚举；NumPy 小矩阵关系及每个X、W元素的标量损失中心有限差分通过 |
| 训练周期与累积 | A=1/16 的每 microbatch 临时X写入索引、W与Wᵀ末尾更新索引独立列举；同周期没有初始装载重复收费 |
| 事件／组件／表格 | 607条事件重汇总精确一致；attention组件、cycle按A倍组件加末尾更新重汇总一致；10行显示由精确数据生成 |
| 来源／引用 | SHA-256验证与AST维度核对通过；9个t2_ citation keys均在独立bibliography及来源清单中解析 |

主证据：`output/tests.txt`、`output/export_audit.json`、`data/independent_enumeration.json`。参数化闭式在 `scripts/counts.py`，显式枚举在 `scripts/test_counts.py`，源码 AST 与产物审计在 `scripts/verify_exports.py`。

## 构建与视觉检查

仓库根目录：

```sh
/opt/anaconda3/bin/python3 tasks/task2_table_ii/scripts/build.py
```

该脚本生成数据和表片段，核查导出／来源，更新中文逐行代入，运行15项测试，再在任务 tex/build 目录内执行 latexmk。独立编译命令：

```sh
cd tasks/task2_table_ii/tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../build table_ii_standalone.tex
```

环境为现有 Python 3.12.7、NumPy 1.26.4、pdfplumber 0.11.7、pypdfium2 4.30.0、TeX Live 2026 / latexmk 4.88；没有安装或修改共享依赖。本机系统 python3 受 Xcode license 状态影响，改用已有 Anaconda。未发现 Poppler，使用现有 PDFium 以2倍比例渲染全部页面。

最终两页 PNG 已逐页目视检查：表号II，公式、行序、分数、配对值、表注和引用均清楚；无裁切、重叠或未解析引用。表主体9pt、表注8pt；数学分式上下标按 TeX 正常缩小，不通过缩整表塞入完整数据集。通栏宽度约514pt，表及注释总高度约269pt，满足约半页的设计目标。独立入口第一页临时用单栏容纳通栏浮动体，后页恢复双栏；可复用 table* 片段用于IEEE双栏原文。

最终日志无 overfull box、LaTeX error 或 undefined citation；`output/pdf_qa.json` 保留页面边界与字号统计。构建缓存和 PNG 位于默认忽略的 build/；可交付 PDF 保留在 output/。空白首页问题在独立入口中已修复。

## 剩余事项与后续接口

本任务交付无未解的计数／配置冲突。后续尚需按真实硬件核对：BF16或其他目标格式支持、逻辑tile与物理配置转换、容量／驻留策略、append粒度、转置布局、重放、部分和和输出完成。这些是Task3配对条件，没有用未经验证的硬件假设填补。

硬件不支持某个理想参考时，应通过 `counts.py` 参数和事件重算；可用 `generate.py --tile R C` 导出不同 r/c 的实例。logical_operator 是需求参考，不声称单 macro 能装下完整矩阵。attention和训练周期总量只描述所声明范围的需求，保留分项；没有构造跨模式统一ρ或完整训练step性能。没有进入Table I、Table III或主论文整合。

## 工作区边界

起始HEAD与授权基线一致。结束时只读检查共享README、计量约定、主论文和根.gitignore相对基线无diff；原有 `.DS_Store` 未清理。没有执行git add、commit、push、checkout、reset、stash或其他共享Git状态变更，也未修改另一任务目录。

**仅修改 tasks/task2_table_ii/，未提交、未推送。**
