# 二进制PCM：独立参考设计估算

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

阅读 [中文PDF](output/pcm.pdf)、[章节TeX](tex/07_pcm.tex)、[证据和桥接笔记](notes/evidence.zh.md)。[输入JSON](data/inputs.json)区分原值与选择，[结果JSON](data/results.json)保存配对结果、完整阶段、对角映射、来源和共享基线哈希。

主模式为8位平面binary/SLC电压式近似ACIM，8行求和、128个ADC、16数字通道；一更新域32个实际IDAC逐平面写，32Byte对角权重事务需要8批program及16次重新读验。每cell mode mux支持同一状态的WL求值和diagonal编程；资源和寄生条件在正文说明。

参考点：ΔS=51.210μs，ΔR=4.655μs，BS=128Byte，BR=32Byte；ρ=0.0024995GB/s，τ=6.87433MB/s，RI*=0.363601。三组配对ridge约0.211–0.653。完整矩阵512事务无遗漏/重复，装载2.383360ms，聚合τ不变；稀疏/连续更新不自动获得满32Byte利用率。

读侧16行组主导；主写SET/RESET波形占73.0%。Binary终验复用同一IM/钳位/列负载电压前端，要求F_A涵盖主读q=0/1最弱有效等级及mode/access兼容，终验每批重新建立和转换。唯一组织对照使用768ns保守模拟弱信号前端，参考ΔR=16.623μs、τ=1.92504MB/s、ridge=1.29842；该对照读验占73.9%，不将它当SLC必需。SET/RESET各一次的正常端态服务有最终真实校验；未达窗不得计成功payload。原模拟30次CLT、材料亚ns、FPGA等待、实验1000pulse不进入主写预算。SET250ns是否含50ns尾沿保留歧义，主用300ns，另存250ns敏感性。

复现（本目录执行）：

```sh
/opt/anaconda3/bin/python scripts/check_pcm.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

修改输入后显式 `/opt/anaconda3/bin/python scripts/check_pcm.py --emit` 刷新结果与数字表，再构建。默认检查只读，导入共享API且关闭pycache；无复制常数/通用公式。输出只有当前 `output/pcm.pdf` 一套，构建及渲染在ignored目录。

待主审：一次端态程序对所选PCM栈的适配、同一电压前端对binary最弱q=0/1终验的建立兼容。本文不给未经报告的批良率或最坏写时长；8行电压式组织也不是PCM材料的必需限制。VSA到SAR的9等级译码、每cell模式mux、电流供电及恢复阶段已有明确资源/时间预算，但不是新芯片电路验证。
