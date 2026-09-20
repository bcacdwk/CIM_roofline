# 3D FeNOR / vertical FeFET 局部服务估算

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

主身份是 **3D vertical AND FeFET 二状态数字局部 CIM**，采用 FENOR-02 的 SL+O-poor switching 与 O-0.1s 扰动抑制条件。四层承载容量；R0 的32项读并行由32条横向读通路和4096个binary感测节点实现。主写域每次驱动16cell，八个位平面完成16Byte；20ns器件脉冲、100ns写后观察预算、终态读回和完整MVM分别计数。

阅读入口：[独立中文 PDF](output/fenor_3d.pdf)、[正文 TeX](tex/10_fenor_3d.tex)、[证据笔记](notes/evidence.zh.md)、[输入](data/inputs.json)、[统一结果与哈希](data/results.json)。独立编译入口是 [fenor_3d.tex](tex/fenor_3d.tex)。

参考结果：`B_S=128 Byte`、`B_R=16 Byte`、`ΔS=11530 ns`、`ΔR=1730 ns`；`ρ=0.0111015 GB/s`、`τ=0.00924855 GB/s`、`RI*=1.20035`。手算为 `(128/16)×1730/11530`。短／参考／长成对ridge范围0.8118–2.0156；这不是统计区间或整个技术族的严格包络。

唯一结构对照增加八倍物理写驱动，使128cell同批，保留16路compare需八拍；ΔR=260ns，ρ不变、τ=0.0615385GB/s、ridge=0.180399。层数和128-bit输入接口本身不提供这项加速。

从本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_fenor.py
FENOR_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

输入变化后先显式执行 `python scripts/check_fenor.py --emit`。默认检查只读；依赖共同`shared_baseline/data/shared_parameters.json`及其计算API，结果记录两者SHA-256。构建用XeLaTeX/ctex/Fandol；渲染用pypdfium2。build/tmp缓存被本地.gitignore排除。

当前交付为6页，已逐页渲染并视觉检查；构建无overfull或缺字，默认复算检查通过。

证据与原值回查已覆盖两篇VLSI关键图及FENOR-04/06的条件差异。尚待主审的电路条件是4096SA的资源实现、SL+O-poor和O-0.1s工艺组合、16列多目标掩码下驱动负载/扰动、100ns观察窗和一次终态verify。它们均明确作为条件工程预算，而非已测宏参数。一次verify失败需异常处理；本例未伪造重试率。论文应用描述不用于推定LLM匹配或跨介质最优。
