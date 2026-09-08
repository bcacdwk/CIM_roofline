# 人工下载清单 V2（C 轮）

更新：2026-09-08。**本文件按用户要求覆盖 `DOWNLOAD_REQUESTS_V1.md`；内容版本为 V2，路径不变。** [V1 原始快照](history/r0/DOWNLOAD_REQUESTS_V1.md)只供历史核对，不再执行其中 A/B 任务。

A/B 主文 **55/55 已到齐，缺主文 0 份**；用户本轮补充 29 份主文和 1 份产品简表。Everspin v3.7 已替代原请求 v3.4，不用找旧版。
目前本地共 **64 份 PDF**：56 份主文记录（含归并的会议版）、5 份 SI、3 份相关版本/简表。代理在收到停止下载指令前额外取得 1 份主文与 2 份 SI；以下均已排除这些文件。**今后下载全部由用户负责，代理不再下载。**

**本次仅需 5 个资料包：4 篇主文 + 1 份已有论文的补充材料。** 路径均相对仓库根目录；照给定文件名存放即可，不必再次下载 A/B。优先取得前 3 包，其余 2 包同批可一起补齐。

## 优先下载

- [ ] **PCM-06 — Fully On-Chip MAC at 14 nm Enabled by Accurate Row-Wise Programming of PCM-Based Weights and Parallel Vector-Transport in Duration-Format**；2021；IEEE Transactions on Electron Devices
  - DOI：[https://doi.org/10.1109/ted.2021.3115993](https://doi.org/10.1109/ted.2021.3115993)。
  - 官方／备用合法入口：[入口 1](https://research.ibm.com/publications/fully-on-chip-mac-at-14-nm-enabled-by-accurate-row-wise-programming-of-pcm-based-weights-and-parallel-vector-transport-in-duration-format)；[入口 2](https://ieeexplore.ieee.org/document/9566604/)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-06_2021_RowWise_ClosedLoopProgramming.pdf`
  - 为何需要：PCM-02 pp.9–10 的 row-wise closed-loop programming 转引该文，实际是明确的正文追溯缺口。
  - 下载内容：TED 68(12), 6629–6636（8 页）期刊主文；不再另取同题 VLSI 2021 会议版。
  - 当前情况：身份与摘要已核验；预期用途尚未由主文确认。 官方主文直接访问未取得 PDF，需要用户权限／手动访问。
  - 避免重复／误用：与 PCM-02 同一 IBM 技术线，提供方法细节，不新增独立工艺交叉证据。

- [ ] **RRAM-06 — A 40nm 2Mb ReRAM Macro with 85% Reduction in FORMING Time and 99% Reduction in Page-Write Time Using Auto-FORMING and Auto-Write Schemes**；2019；2019 Symposium on VLSI Technology
  - DOI：[https://doi.org/10.23919/vlsit.2019.8776540](https://doi.org/10.23919/vlsit.2019.8776540)。
  - 官方／备用合法入口：[入口 1](https://research.tsmc.com/page/rram/1.html)；[入口 2](https://ieeexplore.ieee.org/document/8776540/)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/05_rram/RRAM-06_2019_AutoForming_AutoWrite.pdf`
  - 为何需要：RRAM-02 p.5 主要给脉冲数改善，RRAM-05 p.7 只有读侧完整时序；普通产品 RRAM-04 的封装写周期不能补局部 page 操作。
  - 下载内容：VLSI 2019 主文 T232–T233（2 页）；勿只保存会议摘要。
  - 当前情况：身份与摘要已核验；预期用途尚未由主文确认。 官方主文直接访问未取得 PDF，需要用户权限／手动访问。
  - 避免重复／误用：产业/NTHU 同技术生态，作步骤补充；99% 改善不能先写成绝对周期，也不能遗漏被移入 standby 的 RESET。

- [ ] **SACIM-05 — 8-Bit Precision 6T SRAM Compute-in-Memory Macro Using Global Bitline-Combining Scheme for Edge AI Chips**；2024；IEEE Transactions on Circuits and Systems II: Express Briefs
  - DOI：[https://doi.org/10.1109/tcsii.2023.3331375](https://doi.org/10.1109/tcsii.2023.3331375)。
  - 官方／备用合法入口：[入口 1](https://ieeexplore.ieee.org/document/10314139/)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/01_sram_acim/SACIM-05_2024_GlobalBitlineCombining_8bit.pdf`
  - 为何需要：SACIM-03 pp.2–4 和 CMOS-05 p.4：实际 CIM 输入负载与完整多位服务比通用 RF DAC headline 更相关。
  - 下载内容：主文 5 页（2304–2308）；若页面另列技术附件，一并保存。
  - 当前情况：身份与摘要已核验；预期用途尚未由主文确认。 官方主文直接访问未取得 PDF，需要用户权限／手动访问。
  - 避免重复／误用：NTHU/ITRI 系列，与 SRAM-DCIM、PCM 部分候选团队有关；收到全文后核对其与已有 384-kb 前作的版本关系，不重复请求前作。
  - 年份说明：IEEE 页面首次发表 2023-11-09；期刊卷期为 2024-04，文件名使用卷期年。

- [ ] **MRAM-06 — A lossless and fully parallel spintronic compute-in-memory macro for artificial intelligence chips**；2025；Nature Electronics
  - DOI：[https://doi.org/10.1038/s41928-025-01479-y](https://doi.org/10.1038/s41928-025-01479-y)。
  - 官方／备用合法入口：[入口 1](https://www.nature.com/articles/s41928-025-01479-y)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/06_mram/MRAM-06_2025_LosslessParallelSpintronicCIM.pdf`
  - 为何需要：MRAM-02 p.2 正文实际是 near-memory；新文官方摘要明确 bitcell 内数字乘法，已取得 SI Fig.2 也显示两阶段写互补 MTJ。
  - 下载内容：主文 1046–1058 及随正文附带的 Extended Data；15 页 Supplementary Information 已有，不用重复下载。
  - 当前情况：主文未到。官方摘要确认 40 nm、数字 bitcell 乘法；本地 SI p.4 Fig.2 已确认先两 MTJ 写 0 再目标写 1 的流程，绝对完整周期待主文。 官方主文直接访问未取得 PDF，需要用户权限／手动访问。
  - 避免重复／误用：Li/Chai 等团队不同于 Jung/Samsung 和 Chiu/TSMC，提供机制互补，不能将其 headline 与前两者平均。

- [ ] **PCM-04-SI — Reducing the stochasticity of crystal nucleation to enable subnanosecond memory writing：Supplementary Materials**；2017；Science
  - DOI：[https://doi.org/10.1126/science.aao3212](https://doi.org/10.1126/science.aao3212)。
  - 官方入口：[Science 论文页](https://www.science.org/doi/10.1126/science.aao3212) → Supplementary Materials；[原文列出的 DC1 入口](https://www.science.org/doi/suppl/10.1126/science.aao3212)。
  - 建议保存路径：`tasks/task1_table_i/rebuild/literature/07_pcm/PCM-04_2017_Subnanosecond_ScSbTe_Supplement.pdf`
  - 为何需要：主文 p.4 将 Materials and Methods 放在附件，RESET 的 Fig.S6、脉冲/器件/测量终点条件不能从 headline 判断。
  - 下载内容：**只取补充材料**，应含 Materials and Methods、Figs.S1–S11、References 42–52。主文已经有，不重复。
  - 当前情况：主文 5 页完整；Science 访问返回限制页，未得到 SI。亚纳秒结果暂仅作材料条件对照，未用作完整阵列写时间。

## 已补齐，不需要下载

- [CMOS-07](LITERATURE_CATALOG.md#CMOS-07)：11 页公开作者修订稿已在本地，补普通 28 nm SRAM 服务；不再请求内容相同的正式版。
- [MRAM-02](LITERATURE_CATALOG.md#MRAM-02)：13 页 SI 已补齐，并已核查感测与 PUF/普通写回的区别。
- [MRAM-06](LITERATURE_CATALOG.md#MRAM-06)：15 页 SI 已归档；本次只补主文。
- NeuRRAM、Jung MRAM、IBM 两篇 PCM 主文的 Methods/Extended Data 已有。核查出版页后，未发现还需另取的技术 SI PDF；演示视频不作为缺件请求。

## 暂不扩充的真实缺口

- **3D NAND SLC 完整 program/erase 与 plane 命令约束**：已有 SLC 器件（NAND-05）及 SLC burst（NAND-02），但没有核实到一份公开完整、明确属于目标 3D SLC 产品的部件 datasheet。保留缺口，不让用户猜产品，也不混入普通 2D SLC 资料。
- **通用 28 nm SRAM compiler 全时序库**：未取得官方公开完整库；CMOS-03、CMOS-07 与实际 CIM macro 可支持明确假设的参考服务。未把第三方转载的商业 databook 列为请求。
- **阵列尺寸、精度、ADC 共享及介质状态模式**：这些是后续参考情景的选择，不能单靠继续增加论文解决。本轮不先固定数值。

C 轮没有为了各类平均凑数再发一长串候补。检索去留记录见 [C_SEARCH_LOG.md](C_SEARCH_LOG.md)，现有全文处理见 [FULLTEXT_REVIEW_R1.md](FULLTEXT_REVIEW_R1.md)。
