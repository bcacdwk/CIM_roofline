# RRAM 原生共享读线与二态更新

八个完整64×128等尺度WH-2T1R宏构成`W[64,128]` INT8，8192 Byte有效容量、65536 cell。每宏四个64×32子阵列保留共享TBL，由CIMSEL分时；32项活动、128 ADC、16数字通道。

| 固定资源情景 | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|
| 乐观 | 47.5 | 7.11 | 6.69 |
| 典型 | 25.0 | 4.29 | 5.82 |
| 悲观 | 11.7 | 1.68 | 7.00 |

典型ΔS=5.130 µs；完整8192 Byte装载T_R=1.911760 ms，τ=8192/T_R，U*=T_R/ΔS=64·RI*。完整装载包含512个16 Byte事务及写rail建立/退出。

- [中文PDF](output/pdf/rram.pdf) · [正文](tex/05_rram.tex) · [独立入口](tex/rram.tex)
- [输入及证据](data/inputs.json) · [原生资源/结果/两表接口](data/results.json) · [证据笔记](notes/parameter_evidence.zh.md)
- [复算](scripts/check_rram.py) · [方法与QA](notes/method_review.zh.md)

128实际写驱动、256窗口比较器、300 µA/lane及38.4 mA总额定计入资源，16驱动只作缩资源对照。每宏同WL16列独立BL/SL、八宏并行，无共享TBL的免费切分。写rail在整矩阵期间保持，开始/退出各1 µs；每次尝试仍付50/100/250 ns局部选通/退偏与新的二态验证。1 pF/lane负载上限及电流余量检查说明这一工程时隙的条件，不称实测转换时间。

完整1 µs SET/RESET借自跨stack实际波形；源文30/40 µS目标不能保证本LRS窗83–125 µS可达。1/1、2/1、4/2是限定次数内完成的工程情景；2/1给较慢RESET多留一次修正，并非实测均值或良率分位。LRS8–12 kΩ/HRS≥70 kΩ是约束可校准电流与漏电的参考窗，未被原文证明为计算精度充分界；LRS过冲需额外反极性救援时不计作当前情景成功。典型独立16 Byte请求需5.730 µs；主结果不是任意小请求吞吐。

`service_modes`区分T2/TBL求值与T1/BL/SL窗口读验；两前端5 ns分别设参。公共T_I、T_D及T_B=T_A能力预算联动相关服务，T_B共享预算政策不代表同一物理ADC。`calculate(parameter_overrides={...})`通过公共参数解析器重算两路；独立扰动断言覆盖11个参数、完整矩阵与U*。同模式参数敏感性、有限完成次数与W16资源对照分别标记。

```sh
/opt/anaconda3/bin/python scripts/check_rram.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

`--emit`更新现有机器数据及生成TeX。八组检查包含原生映射/完整覆盖、独立典型算术、模式依赖的解析斜率、输入字段消费、固定资源与主导参数对照、两表接口、原始PDF哈希及生成同步。

正式PDF由统一构建入口重编译并逐页渲染；`tmp/pdfs/rendered/contact.png`按当前PDF的实际页数生成。最终视觉与日志记录见统一审阅入口。

结果卡`tex/result_card.tex`由`../scripts/export_ten_cases.py --emit`唯一生成，中央脚本默认只读逐字校验；本例检查保留全部模型、数据和正文生成项。统一卡生成后由统一构建重编译并复核PDF。
