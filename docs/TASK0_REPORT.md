# Task 0 修订与交接

日期：2026-09-07；状态：**已提交待审阅，未验收**。

基线：`1cf153e7934283ebf728c403ddf06209ee4c6acf`；执行分支：`main`。

计量约定：`MODEL_CONVENTIONS.md v0.1-candidate`（Task 0 修订候选，待审阅）。

## 起点与范围

先检查 Git 状态、HEAD、分支及 remote。起点只有用户未提交的 `README`，内容完整保留并更新交接；仓库实际没有 `README.md`，本轮不另建重复入口。此前没有计量约定或任务文档。已通读 1460 行主 TeX，并阅读历史报告的公式验证、维护／寿命、scope、第二轮一致性及引用记录；其 `main.tex`、旧版本和“已修复”结论仅作线索。

本轮完成理论候选基线，未开展器件重新标定、Table I/II/III 数据制备、完整训练或全系统分析。主文保持中文 `ctexart` 与原章节主线，没有套用最终 I–V 结构或四页模板。

## 核心决定及修改位置

| 类型 | 决定及理由 | 主源 `CIM_Roofline_Paper/cim_roofline.tex` 位置 |
|---|---|---|
| 作者约定（本任务指定） | 固定求值服务单元；输入／写入分别计逻辑 payload，区分内部物理步骤，需求与能力同范围同模式 | “四个指标与驻留强度” `sec:cim_indicators`；详细规则见约定文档 |
| 作者约定 | `W` 为工作窗口、`T` 为完成时间；重载／KV／实际更新不可移出窗口；维护计服务代价，寿命另列 | `sec:cim_indicators`、`sec:modes` |
| 代数及语义修正 | `max` 是必要时间下界，不以重叠为前提；静态分支单独处理；resident 目标需求率改为 `ρ/RI` | “公式与几何” `sec:cim_formula`、“上界可达性与流水线” `sec:pipeline`、`sec:modes` |
| 计量修正 | `M` 统一有用 OP，稠密 `1 MAC=2 OP`；仅保留同次执行的 `κ` 换算；GPU 流量另记 `Q_GPU` | `sec:gpu_model`、`sec:transform`／`sec:comparison`、`para:kappa_def` |
| 示意假设 | 128×128、8-bit、10 ns 仅为完整精度 MVM 服务间隔示例；矩形阵列单边界、无额外重放，`τ` 保留符号 | `para:sram_example`／`eq:tops_demystify`、`para:resident_example`／`eq:rect_work`／`eq:rect_resident` |
| 来源支持与删减 | 收紧经典模型“失效”、瞬时 MAC、物理同质性等判断；撤下未核实的跨文献批评和长综述表 | 摘要、`sec:intro`、`sec:background`、`sec:roofline_review`、`sec:insight` |

精简对应表 `tab:comparison` 保留任务量、服务率、强度、纵轴、上界、分区及 ridge。前半篇 34 个原 label 中保留 26 个；删除的 8 个属于旧综述表及双向等价／横轴变换，当前无引用依赖。删除旧版完成状态注释及 `dQ_R/dt`，图注明确曲线为上界，ridge 不等于最优性能。

## 一手来源核对（本轮实际查阅）

- [Williams 等作者稿](https://escholarship.org/content/qt78h8v7mr/qt78h8v7mr.pdf)：§3、Fig. 1（PDF 第 2–3 页），§5（第 4–5 页缓存与流量），§7（第 10 页其他存储层级）。支持上界、实际层级流量与局部性依赖，不支持旧稿所谓三条“原文明确前提”。出版站页面访问返回 403，使用机构存档作者稿，未更换原 bibliography 引用。
- [Jia 等作者接受稿](https://www.princeton.edu/~nverma/VermaLabSite/Publications/2021/JiaOzatayTangValaviPathakLeeVerma_JSSC2021.pdf)：§II-C、Fig. 2（PDF 第 3 页，已渲染核对）。明确写入／计算受限、权重写入摊销及复制对复用的影响；**Fig. 2 纵轴实际为 Energy Eff. (OPS/W)**，旧稿称吞吐已纠正。保留该联系，不宣称首次区分或首次得到两段式曲线。

其他旧文献的细节与器件数字未在本轮重新核实，删除对应强断言，不换引用来支撑原断言。既有 bibliography 原文保留，其中部分条目带旧数值注释；它们属于待核实研究材料，不是当前标定结果，后续仍须回查原文。

## 旧内容隔离与全篇同步

`CIM_Roofline_Paper/archive/task0_legacy.tex` 原样保留基线从“硬件与 workload 的定量标定”到“结论”之前的三个完整章节，开头注明基线、未复核、非编译及不得直接用作已验证表格数据。逐字比较通过。当前主文无 `input/include` 引入归档；`sec:quantitative` 仅保留硬件能力、workload 需求、适配分析待重建说明。

摘要、引言目录介绍和 `sec:conclusion` 已撤下 FeNOR 天然匹配、主流 CIM 上训练／decode 普遍分区、RRAM/NOR 只能静态、NAND 适合训练及 PD 融合必然／最优等结论。历史报告、根目录 PDF／演示稿、备份 zip 和已跟踪 aux/log 等均未改动。归档不代表判定所有旧数字错误。

## 检查与构建

在仓库根目录运行：

```sh
/opt/anaconda3/bin/python scripts/check_task0.py
git diff --check
```

全部通过：128 Byte、16384 MAC、32768 OP、12.8 GB/s、3.2768 TOPS；矩形阵列及异精度／半字节精度关系；`Q_R=0` 无除零；增加写入需求不提高上界；完整同比例复制的 RI 不变；实际执行单位恒等式及动态两种上界写法一致。结构检查覆盖 34 个 label、11 处交叉引用、2 个正文引用 key；归档片段及 bibliography 与基线逐字比较通过。脚本只验证代数、示意值和源文引用结构，不是器件实测验证，也不证明 TeX 全部主张。

通读修订正文并用 `rg` 搜索 ADC、纯硬件／算法属性、静态规模无关、上下界、等价、ridge、MAC／OP、bit／Byte、GB／GiB 及旧版注释。当前命中均为限定条件、对旧说法的否定或保留的 bibliography，未发现旧口径作为现行主张；摘要、结论和图表注释一致。

在 `CIM_Roofline_Paper/` 内运行：

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error \
  -outdir=build/task0 cim_roofline.tex > build/task0/build-console.txt 2>&1
```

XeTeX 0.999998 / TeX Live 2026，latexmk 完成引用收敛及 xdvipdfmx 转换，最终 **14 页**。无 undefined reference/citation、缺字或 overfull；保留原 CJK font family 重定义的两条提示及 bibliography 一条 underfull hbox（badness 1014）。无需字体 fallback；仅移除模型末尾一处强制分页，避免算例尾段孤立成页，未做投稿排版。

已用已有 `pdfplumber`／PDFium 渲染全部页面并检查页面总览、定义／上界／表／算例及结论页，未见缺字、裁切、公式或表格重叠；字符边界检查通过。Poppler 未安装，未增加系统依赖。系统 `/usr/bin/python3` 被 Xcode 未接受许可阻止，改用已有 Anaconda Python 3.12.7；未接受或修改系统许可。

最终 PDF 已从 `build/task0/cim_roofline.pdf` 同步至主源旁；逐字节相同。构建日志、提取文本和渲染页面仅留在被忽略的 `build/task0/`，不提交。仅新增该 build 路径的 `.gitignore` 规则。

## 剩余事项与下一轮输入

未发现阻塞该理论候选基线使用的代数矛盾。**Table I/II 的计量准备不再受输入／输出、逻辑／物理字节混用阻塞，但尚待 Task 0 审阅验收才能启动**；旧表不能直接继承。硬件资料中的服务间隔、完整输出要求、写入粒度和维护覆盖范围仍需逐条取证，workload 映射也须重建；未覆盖项只能给出明确忽略该项的乐观上界。

下一轮固定输入字段：

- 硬件：服务边界、逻辑阵列与物理映射、macro/bank 配置、`b_S/b_R`、计算／写入模式、每间隔输入／写入逻辑 Byte、latency 与 service interval 的区别、输出完成条件、共享资源与维护覆盖情况及原文位置。
- Workload：窗口起止与上下文、初始驻留状态、实际更新／KV／重载策略、分块／广播接收端／重放映射、两侧精度、`Q_S/Q_R` 及有用 OP 计数。

按既有 `main → origin/main` 工作流提交并普通推送，不 force push；最终 commit SHA 和推送结果以交付回复为准。审查中发现的两个未跟踪 `.DS_Store` 不纳入交付、不删除。到此停止，不进入 Task 1/2。
