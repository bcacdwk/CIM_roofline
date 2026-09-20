# 2026 3D vertical AND FeFET：二状态数字局部服务估算

当前统一入口：[十例复核](../TEN_CASE_REVIEW.zh.md) · [结果JSON](../data/ten_case_results.json) · [结果CSV](../data/ten_case_results.csv)。PDF首页结果卡与这些导出由统一适配器生成；本例原始未取整结果仍在 `data/results.json`。摘要统一十进制MB/s，情景分类见统一复核。


本轮保留 2026 vertical AND 身份与参考计算，澄清写后观察边界并加入固定外围敏感性。统一当前结论见[十例集中复核](../TEN_CASE_REVIEW.zh.md)。

主身份是 **3D vertical AND FeFET 二状态数字局部 CIM**，采用 FENOR-02 的 SL+O-poor switching 与 O-0.1s 扰动抑制条件。四层承载容量；R0 的32项读并行由32条横向读通路和4096个binary感测节点实现。主写域每次驱动16cell，八个位平面完成16Byte；20ns器件脉冲、100ns写后观察预算、终态读回和完整MVM分别计数。

阅读入口：[独立中文 PDF](output/fenor_3d.pdf)、[正文 TeX](tex/10_fenor_3d.tex)、[证据笔记](notes/evidence.zh.md)、[输入](data/inputs.json)、[统一结果与哈希](data/results.json)。独立编译入口是 [fenor_3d.tex](tex/fenor_3d.tex)。

参考结果：`B_S=128 Byte`、`B_R=16 Byte`、`ΔS=11530 ns`、`ΔR=1730 ns`；`ρ=11.1015 MB/s`、`τ=9.24855 MB/s`、`RI*=1.20035`。手算为 `(128/16)×1730/11530`。短／参考／长成对ridge范围0.8118–2.0156；这不是统计区间或整个技术族的严格包络。

资源对照增加八倍物理写驱动，使128cell同批，保留16路compare需八拍；ΔR=260ns，ρ不变、τ=61.5385 MB/s、ridge=0.180399。层数和128-bit输入接口本身不提供这项加速。

摘要 MB/s 为十进制 10^6 Byte/s；矩阵为 16384 Byte = 16 KiB。B_R=16 Byte 只适用于一个输入索引、16 个对齐连续输出的 INT8 更新，八个位平面全部终验后提交；1024 个事务聚合完整矩阵，参考占用 1.77152 ms，无周期维护折扣。

写后窗口主点仍为 g=100 ns：最后写偏置退回已在窗口内，后续 40 ns 完整 binary read 单独负责读偏置、感测及读后恢复。FENOR-02 p.2 Fig.3(d) 的 RAWD<100 ns 未分解测试阶段，也没有证明 100 ns 是器件必需等待。固定参考外围/16-cell 写资源，`ΔR=930+8g ns`；g=150 ns 的额外预留对照为 ΔR=2130 ns、τ=7.51174 MB/s、RI*=1.47788，ρ不变。150 ns 不是测量上界；不从 `<100 ns` 推成零等待或已证实更短下限。

从本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_fenor.py
FENOR_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

输入变化后先显式执行 `python scripts/check_fenor.py --emit`。默认检查只读；依赖共同`shared_baseline/data/shared_parameters.json`及其计算API，结果记录两者SHA-256。构建用XeLaTeX/ctex/Fandol；渲染用pypdfium2。build/tmp缓存被本地.gitignore排除。

PDF 已由本目录脚本重建；最终十例视觉复核记录见统一审阅，默认复算检查覆盖新观察窗对照。

证据与原值回查已覆盖两篇VLSI关键图及FENOR-04/06的条件差异。尚待主审的电路条件是4096SA的资源实现、SL+O-poor和O-0.1s工艺组合、16列多目标掩码下驱动负载/扰动、100ns观察窗和一次终态verify。它们均明确作为条件工程预算，而非已测宏参数。一次verify失败需异常处理；本例未伪造重试率。论文应用描述不用于推定LLM匹配或跨介质最优。
