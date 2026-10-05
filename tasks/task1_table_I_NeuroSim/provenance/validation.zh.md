# 复算与迁移验证

2026-10-05：十个参考配置通过集成构建及未参与实现的独立审查。独立审查使用仅含当前公共代码、十例输入和锁文件的 28 文件小包，外部运行根只提供指向锁定源码的 worktrees.json；逐例重新编译，未复用生产二进制。

13,036 个逐叶值、131 条服务阶段与选定机器证据精确相等，覆盖 K/N、payload、raw/effective 时间、时钟、操作计数、资源、模块返回、维护、ρ/τ/RI*/U*；同一编译器上未使用浮点容差。来源路径元数据因迁移而更新，不参与计算比较。GC 的实际维护帧为 399998.5 ns，busy 66176 ns，guard 115.5 ns，availability 0.8342706285148569。

当前计算不读取 archive、旧结果、legacy replay 或兄弟 NVM 运行产物。输入原文来源和哈希见 [input_sources.json](input_sources.json)，代码提取来源见 [code_sources.json](code_sources.json)。上游真实分支、SHA、接口版本与版权仍保留。

归档的 1101 个原始文件（14,966,596 字节）全部逐项哈希相等；恢复关系与独立审查证据保存在 [archive](../archive/README.zh.md)。完整新构建、trace 与原始日志留非同步本地区；正式表图也通过独立审查：十个点及表格同源、双对数轴等比例、标签无裁切，PDF 字体嵌入及两页合并版逐页真实渲染通过。详细检查见 [图表说明](../analysis/11_summary_figures/README.zh.md)。未完成的材料/电路适用条件见 [METHOD](../analysis/METHOD.zh.md)，本次整理未宣称解决这些模型条件。
