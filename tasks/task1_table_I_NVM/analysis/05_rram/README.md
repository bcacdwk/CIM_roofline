# RRAM 二状态位切片的局部服务估算

已完成同一共享基线下的有限条件工程估算：二状态 HRS/LRS、八个等尺度权重位平面、32项读分组，16个独立编程/二状态窗口读验通道。完整RESET、masked SET、重试、HV建立/恢复及本地读回全部计入。这是参考设计服务预算，不是同一芯片实测复原或材料保证区间。

- [中文章节 PDF](output/pdf/rram.pdf)、[章节 TeX](tex/05_rram.tex)、[独立入口](tex/rram.tex)。
- [参数证据表](notes/parameter_evidence.zh.md)：原值、PDF定位、操作锚点和工程选择分开。
- [输入及R1–R5记录](data/inputs.json)、[结果/物理映射/对照](data/results.json)、[来源与哈希](data/provenance.json)。
- [方法审阅](notes/method_review.zh.md)、[计算检查](scripts/check_rram.py)。

<!-- BEGIN GENERATED RESULTS -->
| 成对情景 | ΔS (µs) | ΔR (µs) | ρ (GB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|---:|---:|
| 短预算 | 5.380 | 48.340 | 0.02379 | 0.33099 | 71.881 |
| 参考 | 10.250 | 72.970 | 0.01249 | 0.21927 | 56.952 |
| 长预算 | 21.780 | 148.100 | 0.00588 | 0.10804 | 54.399 |
<!-- END GENERATED RESULTS -->

主成对范围：ρ≈0.00588–0.02379 GB/s、τ≈0.10804–0.33099 MB/s、RI*≈54.4–71.9。GB/MB均为十进制。

16-lane来自八位平面×两个列组；同一输出WL上分两相位写，八批覆盖16个完整INT8权重。需要16个耐压/限流驱动、32个binary比较器、2个组地址计数器及mask/done状态；电源预算0.30 mA/lane、总4.8 mA，最高1.8 V需专用耐压I/O。没有从128-bit数据口推出128-cell并行。

程序采用文献实际1 µs SET/RESET脉宽作为跨stack操作预算，高压建立/回读各预留1 µs；本地binary完整sense采用共同10/20/50 ns能力预算，另计输入选通、5 ns建立和控制。尝试次数RESET/SET为1/1、2/1、4/2；成功条件是每批全部活动cell在对应次数内达到所选LRS 8–12 kΩ、HRS≥70 kΩ窗口。窗口和次数是参考设计选择，未移用NeuRRAM的8.52次、56 µs、成功率或电导终点。其1–10 µs外部受限读回不压入主本地服务。

参考点仅启用一个lane时，保持相同binary预算得到ΔR=1167.370 µs、τ=0.013706 MB/s、RI*=911.118；同lane改用已有SAR，在统一完整sense预算下数值相同。这个对照分离了并行资源收益与感测选择，没有无依据删除校验时间。

从本目录复算：

```sh
/opt/anaconda3/bin/python scripts/check_rram.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

更新输入后用 `scripts/check_rram.py --emit` 刷新数字表与结果。脚本通过 `importlib` 调用共享接口，关闭bytecode；`build/`、`tmp/`被本目录忽略。

共享JSON SHA256：`6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42`；共享脚本：`eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3`；方法TeX：`b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9`。三者未修改。
