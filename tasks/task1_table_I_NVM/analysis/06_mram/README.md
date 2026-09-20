# MRAM：互补数字 CIM 与完整两相写验

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

阅读 [独立中文 PDF](output/mram.pdf)，章节源为 [06_mram.tex](tex/06_mram.tex)，独立入口为 [mram.tex](tex/mram.tex)。详细原值、PDF页码与工程桥接见 [证据笔记](notes/evidence.zh.md)。

主路径采用 MRAM-06 的互补2T2MTJ bitcell数字机制，使用共同R0的32项×16输出调度。没有混入MRAM-01的电阻求和/TDC时序；原40nm数字机制与28nm读写宏证据被明确分开。

更新每组8个INT8权重：128 MTJ先同时置P，64目标支路再置AP；64条单端感测通道分左右两批核验全部128个物理状态。物理编码128bit装载一次，有效payload仅8Byte。驱动数量是独立配置，未从接口宽度推断。

| 情景 | ΔS (ns) | ΔR (ns) | ρ (GB/s) | τ (GB/s) | RI* |
|---|---:|---:|---:|---:|---:|
| 短 | 1284 | 56 | 0.09969 | 0.14286 | 0.6978 |
| 参考 | 2570 | 95 | 0.04981 | 0.08421 | 0.5914 |
| 长 | 5140 | 130 | 0.02490 | 0.06154 | 0.4047 |
| 参考，恰一次整组重写 | 2570 | 180 | 0.04981 | 0.04444 | 1.1206 |

主表是一次完整两相写和两支路verify通过的有限预算；对照保留一次失败及重写的全部占用。原MRAM-03的20ns/约1e-5及30ns/1Mb零错地板只是量级锚点，不是新互补实现成功率；没有无限重试或平均次数假设。共同状态容量16384Byte，整矩阵顺序2048组、参考194.56μs，τ不变。

输入 [data/inputs.json](data/inputs.json)，统一结果与成对操作数 [data/results.json](data/results.json)；共享JSON/API和所有源PDF哈希随输入保存。脚本导入共享API，默认只读：

```sh
/opt/anaconda3/bin/python tasks/task1_table_I_NVM/analysis/06_mram/scripts/check_mram.py
```

显式刷新数据、构建、渲染全部页面：

```sh
sh tasks/task1_table_I_NVM/analysis/06_mram/scripts/build.sh
```

只刷新派生文件用 `check_mram.py --emit`。最终PDF为六页；临时编译/渲染文件在本地.gitignore忽略。检查覆盖数据/API一致、源哈希、容量与选通/驱动、两支路verify、位串行轮数、独立手算和事务聚合。

待主审的主要工程条件为：0.9V新bitcell在4096活动pair下的3/5/10ns读槽、128路第一相电流与SL供流、绝对状态verify误判裕量。无需将这些条件抹成null，也不将其写成硅测保证。寿命与读扰动另列，不加入瞬时τ；未修改其他案例或共享文件。
