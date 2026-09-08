# Table I · CIM / NVM 文献资料集

**READY FOR ANALYSIS — 文献准备完成，可直接开展后续参考设计分析。**

统一目标：在明确的小规模 sub-array/local macro 边界，使用共同的 **28 nm CMOS 外围参考条件**，结合各介质的实际器件/阵列约束，形成可解释、可复算的量级范围。这是文献支持的参考设计，不是已制造芯片的性能排名。

## 从这里开始

1. [分析约定与交接](AGENTS.md)：后续工作的边界、口径和顺序。
2. [文献目录](LITERATURE_CATALOG.md)：全部有效来源、DOI、PDF 和正文笔记入口。
3. [证据覆盖](COVERAGE.md)：各组能支持什么、哪些条件需要在建模时声明。
4. [机器清单](source_manifest.json)：身份、工艺/状态、用途、正文定位、路径与哈希。

## 资料结构

```text
task1_table_I_NVM/
  README.md
  AGENTS.md
  LITERATURE_CATALOG.md
  COVERAGE.md
  source_manifest.json
  literature/
    00_cmos_periphery/
    01_sram_acim/
    02_sram_dcim/
    03_nor_2d/
    04_nand_3d/
    05_rram/
    06_mram/
    07_pcm/
    08_feram_hfo2/
    09_gain_cell_edram/
    10_fenor_3d/
```

每个分类目录只有一份 `NOTES.zh.md` 和有效 PDF。**55 份主文 + 4 份 SI，共 59 份 PDF**；44 份核心来源、11 份补充来源。SRAM DCIM 五篇全文均已齐全。共享来源只保存一份，没有历史版本、下载清单、搜索记录、脚本、旧表或临时文件。

**后续 Agent 使用本地资料即可，不再自动检索或下载文献。** 文件齐全不等于所有参数都有无歧义的直接实测值：已把器件/宏/系统层级、仿真与实测、读后恢复、写验及文内标注差异写进笔记。遇到这些限制，应明确参考情景与假设，不补造数字。

固定 source_id 用于跨文档引用，不要求连续。只使用本目录列出的来源和当前分析约定；不从旧表的数字反推目标范围。

本次交付止于资料准备；未计算最终 ρ、τ、RI*，未制作新 Table I，未改主论文或 Table II。
