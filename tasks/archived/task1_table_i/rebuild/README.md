# Table I 重建：R1 文献复核 / 下载清单 V3

**状态：V2 五包全部验收，SRAM DCIM 补选完成，等待用户补充 V3 两篇主文。**

本轮检查并规范命名 4 份新主文和 1 份 SI，依据实际正文更新用途/限制；另补选 2 篇 SRAM DCIM。只处理文献准备，没有确定共同延时、计算 ρ/τ/RI* 或制作新版 Table I；主论文、Table II 与共享 docs 未改。

## 当前入口

- **[下载清单 V3](DOWNLOAD_REQUESTS_V1.md)**：沿用用户指定文件路径，只剩 SDCIM-04、SDCIM-05 两篇主文；DOI、官方链接和保存路径均已列出。
- **[本轮验收、正文发现与 DCIM 补选](V2_INTAKE_AND_DCIM_REVIEW.md)**：5 个包的到件情况、实际用途、仍缺的依据和去留结论。
- [完整目录](LITERATURE_CATALOG.md) · [全部逐篇审阅](FULLTEXT_REVIEW_R1.md) · [覆盖矩阵](COVERAGE.md)
- [检索取舍](C_SEARCH_LOG.md) · [机器清单](source_manifest.json) · [资料根目录](literature/)

## 数量与筛选

原 A/B 的 55 条主文记录及 V2 的 5 个资料包都已齐全。当前共 **62 条来源记录、61 个去重包、60 条本地主文记录、69 份 PDF**（60 主文、6 SI、3 相关版本/简表）。两篇新增 DCIM 目前只有题录/摘要依据，未假称已审全文。

SRAM DCIM 专属候选由 **3 增至 5**；新增 TVLSI 2024 的 signed MAC/可调加法树，以及 JSSC 2026 的数字 transpose SRAM/精确近似双模式。只请求期刊版，不同时索取同主题 ISSCC 前作。

本地 60 条主文的用途筛选：43 核心、14 补充、1 条件保留、1 版本归并、1 结构对照。**本轮未发现应整篇删除的无关新文献。** RRAM-06 只报告归一化时序但方法有用；PCM-04 的 SI 已补齐，现作材料对照。FENOR 同工作归并、FeNAND 对照和旧产品 brief 的处理继续有效。

**论文下载全部由用户负责；本轮代理下载 PDF 为 0。** V2 五份来件已重命名，PDF 字节保持不变。原先 11 个分类 README 中错误的 PDF 忽略说明已修正，用户允许 PDF 纳入 Git 的设置保留。

## 边界与停止点

只写入 `tasks/task1_table_i/rebuild/`。根目录 Zhou 两篇和此前任务文件保留；HEAD 为 `5201afdbfbee9ffc2ed4b25f67c9989aa6081a1c`。用户已有 `.DS_Store`、`tasks/.DS_Store` 修改未清理；未暂存、提交、推送、切分支或回退。

[R0/V1 快照](history/r0/)和[V2 快照](history/r1_v2/)只供回溯，旧请求已关闭。当前以 source_manifest.json 为准；旧 R0/R1 固定计数脚本不是当前入口，勿重新运行覆盖新状态。

收到两篇 DCIM 后继续正文适用性核验；本轮到此停止，不自动进入 R2。没有需要用户先决定的实质问题。
