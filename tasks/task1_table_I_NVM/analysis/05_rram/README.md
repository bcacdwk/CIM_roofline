# RRAM 二状态位切片的局部服务估算

本分析固定共同 128×128 INT8 任务与 28 nm 外围，采用二状态 HRS/LRS、八个等尺度权重位平面、32 项输入分组和单 cell 顺序写验。它是首轮介质参考设计，不是最终 Table I 速率行。

- [中文章节 PDF](output/pdf/rram.pdf)：6 页；前 4 页为连贯分析，后 2 页为紧凑参数证据表。
- [章节 TeX](tex/05_rram.tex) 与 [独立编译入口](tex/rram.tex)。
- [参数证据表](notes/parameter_evidence.zh.md)：PDF 页序/图表、原值单位与条件、采用理由；由 JSON 生成。
- [原始证据及参考输入](data/inputs.json)、[派生结果](data/results.json)、[实际读取来源与哈希](data/provenance.json)。
- [方法审阅记录](notes/method_review.zh.md) 与 [最小计算检查脚本](scripts/check_rram.py)。

在前端电流到电压接口能纳入原 PH0=5 ns 预算（`h_A=0`）的条件下，短/参考/长公共时隙得到 ΔS=5380/10250/21780 ns，ρ≈0.02379/0.01249/0.00588 GB/s。额外接口建立时长 `h_A` 以参数保留；这不是未经条件限定的物理范围。

完整二状态写周期尚缺同一实现的绝对 SET/RESET、高压建立、恢复、校准窗口及成功重试分布。主结果的 τ、RI* 点值因此设为 `null`，保留完整操作公式；不借用 NeuRRAM 的多级 8.52 次/56 µs 或 Fujitsu 封装产品的毫秒时长。对于已选择的单 cell、至少一次 pulse+ADC verify 策略，可以给出数学边界：参考点 τ≤3.1189 MB/s、RI*≥4.0039。物理编程和重试只会收紧它，边界不是介质测量。另给完整单 cell 时间对应 RI*=1/10/100 的反解门槛，不指定任意典型写时间。

相对 R0 的主结构例外是 128→32 输入项/组（RRAM-05 的本地线性证据）；仍有八平面并行、每平面16 ADC、16数字通道、顺序调度。128-bit 写口只装入编码数据，实际编程并行度取 `p=1`。所有 R1–R5 记录在输入 JSON。

复算命令从本目录执行：

```sh
/opt/anaconda3/bin/python scripts/check_rram.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

更新原始 JSON 后先执行 `scripts/check_rram.py --emit` 生成结果与表格。脚本通过 `importlib` 导入共享 `check_shared.py`，不重写吞吐公式，不在共享目录生成 bytecode。默认检查不修改任何文件。`build/` 和 `tmp/` 被本目录 `.gitignore` 忽略。

已完成最终同基线核对：JSON SHA256 `6460c046e34818041458c7a68d2cb5f3f8593096192cb6db6a31a97f00598a42`；脚本 SHA256 `eaa2e2675d03d81140633727077de25ce494b897070e6f95b20ae15c2c2614f3`。原文哈希均与资料清单一致。编译无 overfull、未定义引用或缺字警告；最终 6 页已逐页渲染目视检查。来源未复制、下载或修改。

最终共享方法 TeX SHA256 为 `b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9`。共享修改仅为 C 节接口 `w_IO` 的排印修复，公共公式、JSON 参数及计算 API 不变；已同步 `data/provenance.json`，重新计算、编译并核对 PDF，全部数值与首轮完全一致。二状态完整写周期、校准窗口、成功重试分布及前端接口条件缺口仍保留。
