# P5 总表与图表独立核对

结论：**PASS_overview_tables_figures_conditional_model_scope**。本审查未参与绘图生产；审查者是MRAM/GC04/FeNOR作者及NAND早期研究者，并独立审过PCM/NOR/FeRAM。这里核对汇总、单位、身份与图形，不对已接受器件重新做物理签核。

最终21个新配置是7例各optimistic/reference/pessimistic，ID与实际run均唯一，39个native构建目录均独立。管理区、compute-only包和最终运行的计算文件哈希逐项一致；完整包没有旧结果/legacy replay依赖。最后0执行失败，首次MRAM缺规范文档导致的3次打包失败保留且没有混入正式21点。

正式21/30点JSON与CSV逐点相同；每点rho/tau均以1e6逻辑Byte/s计算，RI*/U*独立重算一致，全部review绑定最终计算哈希。GC使用长期effective间隔形成主图成对率，单次/raw另列，未把raw/availability伪装为物理延迟。V4九点数值、ID、温度与原始结果逐项一致；summary/review/qualification原文件哈希与前期记录相同。旧NVM背景单独保存，不进入新计算或30点主表。

实际查看了七例paired/circles与十类paired/circles共4张最终PNG，并独立解析SVG major-grid坐标验证每十进制数量级的x/y长度相同。所有原始坐标未移动；圆包含全部实际sample及reference中心，完整圆边界位于坐标范围内。FeNOR三点完全重合时半径为0，不画虚假范围圆；NOR/NAND opt=ref明确标注。reference大点/optimistic三角/pessimistic方点、十进制MB/s、RI*=1和两代范围图例清晰；标签可辨，无缺失类别或截断圆。

V4的300/350/400K固定架构重新尺寸化与V5有限case政策范围在表/圆图图例区分。图注明确不同K/N、精度和资源，不能按MB/s作等工作量/等面积排名；圆不是置信域或全部可实现组合。21/30指配置数量，绝不声称都是不同坐标或硅保证。

精确数据、geometry、PNG/SVG哈希和检查记录见 `review.json` / `machine_audit.json`。所有器件范围仍保留各自模型与外部原语条件，本次PASS不增加ENOB、统计良率或STA资格。
