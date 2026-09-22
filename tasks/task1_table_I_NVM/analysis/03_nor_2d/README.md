# 2D NOR Flash：二进制局部数字求值与完整更新

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

主情景采用 binary NOR 状态、R0 的 32项×16输出数字路径：32个独立读分片、4096本地SA，八个读分片共用一个4KiB擦除域。完整16KiB矩阵需64个256Byte页program及4个sector erase；更新始终单域。原生粒度可以聚合整矩阵，无额外逻辑payload。

参考结果：ΔS=32.010µs，ΔR=205.605800ms，ρ=0.00399875GB/s，τ=0.0000796865GB/s，RI*=50.1810。短/参考/长配对ridge为61.51/50.18/390.41。读时延主要由二进制感测支配；更新87.55%为擦除。若32个读分片必须各自独占sector，读能力不变、τ降低约7.13倍，ridge升至约357.7。

这是文献支持的条件性参考宏，不是已制造NOR DCIM芯片。NOR-01完整随机读时间与NOR-02完整binary program/erase互补；NOR-04/05用于解释模拟电流VMM和精调为何是另一服务。未把SPI速率当编程完成，未把普通binary页写冒充模拟精度。

## 阅读入口

- [独立中文PDF](output/nor_2d.pdf)，6页。
- [章节TeX](tex/03_nor_2d.tex)；[独立入口](tex/nor_2d.tex)。
- [参数原值、PDF页/图表和工程桥接](notes/parameter_evidence.zh.md)。
- [输入](data/inputs.json)、[统一结果与操作计数](data/results.json)、[来源与共享哈希](data/provenance.json)、[校验项](data/validation.json)。
- [复算脚本](scripts/check_nor.py)、[构建脚本](scripts/build.sh)、[视觉复核](notes/review.zh.md)。

## 复现

从本目录运行：

```sh
/opt/anaconda3/bin/python scripts/check_nor.py
sh scripts/build.sh
```

默认计算只读；修改明确输入或共同参数后，显式更新再构建：

```sh
/opt/anaconda3/bin/python scripts/check_nor.py --emit
sh scripts/build.sh
```

使用共享 `dcim_service`、`front_ns`、`page_service`、`metrics` 与公共JSON，不复制共同常数或公式。自检另用手算核对参考点，并遍历逻辑地址证明页/sector覆盖。构建需XeLaTeX/ctex/Fandol；渲染需pypdfium2/Pillow。临时build/tmp文件被忽略，保留一份有效PDF。

## 主审重点

重点复核读分片与擦除域分开的工程映射及其电气条件：128-SA宽、32读片并行、8片共享sector擦除和页抑制。原文并不报告这个改造宏，其宽度/负载/高压隔离与移植后的完整周期须待电路验证。4sector主布局和32sector对照已把这项不确定性的更新后果量化。没有未填数值的主服务；也没有把精调的缺失完整服务强行伪造为本模式数据。

未修改共享基线、其他案例、原PDF、主论文或Table II；未使用Git操作。
