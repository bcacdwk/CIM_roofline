# V5 / V4 分层总览与有限成对范围图

`compare_v4.py` 与 `plot_overview.py` 是结果生成后的独立步骤，不由任何正式计算
runner 导入，也不进入 compute-only 包。最终七例21点和加入V4后的10类30点已正式
导出并通过独立表图复核；早期12点预演只作为过程记录保留。

输入为 `export_points.py` 的 `points.json`。每条记录保留身份、K/N、精度、资源、
模型类别、源后端SHA、single/raw/effective时间、rho/tau/RI/U与配置/计算哈希。
只有 `accepted=true` 且 `plot_eligible=true` 的有限正成对值进入图。GC 主图只接受
已通过实际调度的长期有效率；raw能力继续在表中独立保留。blocked、infeasible、
未复核候选不变成普通点/圆；缺少三情景的部分点集明确标partial且不画普通圆。

V4从只读 `step4_v4/results/reference-v4-20261005/summary.json` 读取九点，并核对
当时 `reports/review.json` 的对应值和资格；没有重新计算或重新验收V4。V4的
300/350/400K是固定架构、原生重新尺寸化的热设计情景，350K不是统计中位数。
V5是逐例器件/协议/运行条件的有限情景。两种范围语义在表列、圈线型和图例分开。
V4 RRAM Q4模拟残差、SRAM ACIM多行稳定性条件与DCIM名义算术资格原样保留。

横轴tau，纵轴rho，十进制MB/s。等log10显示长度；RI*=1在屏幕上45度。reference
大圆点、optimistic空心三角和pessimistic空心小方块位于真实坐标，按同一硬件身份
连接。重合点不加jitter，标签注明opt=ref或all coincide；大reference与空心端点
可叠放，但不改变数据。完整圆边界参加自动轴范围，标签仅在屏幕偏移排布。

圆沿用旧NVM端点中垂线投影规则，复用V4的退化处理：若端点重合或reference不在
该圆中，改用这三个实际点的最小包围圆；三点完全重合时只保留点，不制造非零
半径。原规则、fallback原因、实际中心/半径/点距均保存到geometry.json。圆仅
概括有限样本，不是置信区域或圈内所有读写组合均可实现。K/N、精度、节点和资源
不同，输入MB/s不构成等工作量、等面积或材料本征速度排名。

旧NVM背景只有显式 `--legacy-background` 才读取其统一结果；另写
`legacy_background.json/csv`，并列旧推荐参考与新实现身份/数值，不生成统一
“工具修正倍率”。它不参与 V4+V5 主点合并、任何新计算或普通圆。

```sh
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py compare \
  --v5-points /local/final-export/points.json --output-dir /local/combined
python3 -B tasks/task1_table_I_NeuroSim/step4_v5/v5.py plots \
  --points /local/combined/combined_points.json --output-dir /local/figures
```

`plots` 自动使用已安装的 `/opt/anaconda3/bin/python`，可由
`NEUROSIM_PLOT_PYTHON`覆盖；未安装/升级依赖。PNG/SVG和matplotlib缓存一开始就写
本地非同步区，正式导出只选PNG/SVG、点表与必要几何记录，不复制缓存。可用
同一绘图入口先对纯V5表产生七例图，再对combined表产生十类总览。

本地预演：`/Users/shine/neurosim/runs/step4-v5/p5/plots-preview-r2-20261005`。
4类12点，横纵每decade显示129.2像素；四个生产图标签布局penalty均0。已实际查看
圆图和成对点图，圈/坐标/文字完整，无数据移位。四个专门几何示例覆盖端点重合、
三点重合、opt=ref、reference在原圆外；这些测试坐标从未作为器件点绘制。
这是生产作者自查，不替代A/B最后的独立数字/图表复核。
