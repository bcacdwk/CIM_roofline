# Gain-cell eDRAM：同状态读写与刷新

主 Agent 已完成全文、关键证据、独立复算和最终 PDF 审阅；结论为有条件的参考设计估算。统一结果与保留事项见[七例集中审阅](../REMAINING_SEVEN_REVIEW.zh.md)。

阅读入口：[六页中文 PDF](output/gain_cell_edram.pdf)；[中文章节](tex/09_gain_cell_edram.tex)，独立入口为 [gain_cell_edram.tex](tex/gain_cell_edram.tex)。

主模式选 GC-04 的 3T1C current-programmed 二进制端点 ±700 nA 伪差分 ACIM，以原 65 nm 器件/宏为依据接共同 28 nm 外围；不是已测 28 nm 宏。每 INT8 权重16cell、总262144cell，八平面并行，保留64行负载，每次16输出，128差分ADC/128真实pair写driver，一个更新域。

关键原文补充：GC-04 p.9–10/Fig.16 **实测完整65ns** 两步电流编程，包含5ns粗写；p.8/Fig.12的60ns另属仿真。0.4ms保持仅是99.7%测试cell漂移<1原ADC LSB，不是无错保证。采用端点符号判决避免把多级漂移直接四舍五入为原码；尾部、噪声、反复刷新裕量仍需验证。

| 情景 | 无维护 CS/CR (ns) | 全矩阵刷新 (µs/400µs) | ρ (GB/s) | τ (GB/s) | RI* |
|---|---:|---:|---:|---:|---:|
| 短 | 14852 / 71 | 189.440 | 0.00453421 | 0.118560 | 0.0382440 |
| 参考 | 23690 / 80 | 266.240 | 0.00180431 | 0.0667875 | 0.0270156 |
| 长 | 35860 / 105 | 384.000 | 0.000140279 | 0.00598857 | 0.0234244 |

表内吞吐含每周期116/185/280ns批边界最大空隙；长点仅3.93%可用率，展示刷新临界，未裁成统一折扣。CA=TI+tm+TA，tm工程预算100/150/200ns；共享TI、TA、TD实际传播。原180ns完整5bit-ADC宏仅作量级锚，不重复叠入服务。

参考手算：每16Byte写CR=3×5+65=80ns；每组刷新175+5+80=260ns，共1024组；α=1−(266240+185)/400000=0.3339375。ρ=128α/23690，τ=16α/80，RI*=(128/16)×80/23690。结果是固定全矩阵刷新策略的稳态平均，不是每请求latency或cold首次装载时间。新写不抵扣刷新是控制选择；允许抵扣时应重算。

仅保留一个资源对照：16→32输出组，同时ADC及pair driver翻倍，数字重构仍16通道，本地sign decoder随ADC翻倍。实际维护重新计数，参考ρ约提升3.7倍，而非只除以两倍求值轮数。GC-01/02/03/05作为机制与边界说明；没有混用GC02的5µs/99%作为精确保证，也没有将GC05 storage更新当作stationary提交。

- [证据与工程桥接](notes/evidence.zh.md)：原值、页码/图表、模拟/实测、保持单位及不同组织。
- [输入 JSON](data/inputs.json)：共享基线哈希、5份原PDF哈希、原值/选择、编码与读写维护资源。
- [结果 JSON](data/results.json)：完整原始与维护后服务、操作计数、来源、单位、配对范围与32输出对照。
- [复算脚本](scripts/check_gain_cell_edram.py)：直接导入共享API，默认只读；`--emit`显式刷新派生JSON/TeX。

从本目录复现：

```sh
/opt/anaconda3/bin/python scripts/check_gain_cell_edram.py
GAIN_CELL_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

六页已逐页目视检查，最终构建无溢出、字体缺字或警告。默认计算不改共享文件；导入共享API前关闭bytecode生成。未做Git操作，交付文件均在本案例目录，临时build/tmp由本地.gitignore忽略。

待主审/电路验证条件已具体写入正文与数据：1ns MAC/64ns单行等电荷读脉冲；读每支路200fF有效C和±224mV ADC量程，新增读C在写时隔离，使写负载仍接近原50fF；128对同时写供流与完整65ns建立；端点符号读噪声/尾部；固定相位禁发窗口调度。这些条件未用额外shadow、ECC或无限重试隐藏。
