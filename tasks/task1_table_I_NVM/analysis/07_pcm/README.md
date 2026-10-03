# PCM 原生 bank 的八行电压求和

一个256×1024-cell sub-bank采用每权重8个SLC，形成`W[128,256]` INT8，32768 Byte逻辑/物理数据容量。原PCM-03的8 WL活动和电压等级间隔保留，32行组覆盖256输入；128 ADC、16数字通道、24-bit输出。

| 固定配置情景 | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|
| 乐观 | 5.21 | 7.97 | 0.653 |
| 典型 | 2.50 | 6.87 | 0.364 |
| 悲观 | 1.04 | 4.95 | 0.211 |

典型完整向量间隔102.410 µs，完整矩阵装载4.766720 ms。局部32 Byte行内列组更新时间4.655 µs，1024组完整覆盖；τ=32768/T_R，U*=T_R/ΔS=128·RI*=46.5455。连续/稀疏小更新须按实际列组利用率重算，平均16 KiB成本不是实际请求延迟。

- [中文PDF](output/pcm.pdf) · [章节](tex/07_pcm.tex) · [独立编译](tex/pcm.tex)
- [输入/证据](data/inputs.json) · [原生资源及配对结果](data/results.json) · [文献和推导笔记](notes/evidence.zh.md)
- [复算](scripts/check_pcm.py) · [公共方法](../shared_baseline/README.md)

32实际IDAC逐平面写：固定原生WL行r，选列c=4h+s；其他列BL/SL等电位inhibit，其他行gate关闭。列读/写隔离、8平面路由、256-bit缓冲及22.4 mA RESET/4 mA SET公共回流均列账，不需要per-cell gate mux。PCM-06提供行并行机制依据；PCM-01的32 IDAC及波形是跨实现锚点，不把其对角gate直接嫁接本bank。

典型写服务73%来自完整125 ns RESET和300 ns SET（含50 ns尾沿）。主二态终验共用F_A需满足同一IM、访问栅电平、钳位/列负载和q=0/1最弱码建立条件；这是参考资格，尚非单cell与八WL实测等价。独立长观察协议要求至少256+512 ns，实际前端为max(F_A,768 ns)；参考F_A=20 ns时ρ保持2.50 MB/s，τ为1.93 MB/s；共享F_A=768 ns的条件敏感性同时重算两路，ρ=0.157 MB/s、τ=1.93 MB/s、RI*=0.0814。两者分别为操作模式和参数敏感性，均不是新典型。SET总250 ns解释及g10/50 ns转换余量另列。8行是所选实现条件，不是PCM材料上限；低RI*不能独立表示动态更新适配。

```sh
/opt/anaconda3/bin/python scripts/check_pcm.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

`--emit`更新本例机器数据和生成表；默认只读。检查原生尺寸/精度、32768权重覆盖、行/列半选条件、IDAC与ADC路由、独立典型算术、完整装载/U*、源PDF哈希及生成同步；另核对F_A、TA、TD跨服务传播及独立观察模式，完整T_R/U*随之重算。外审重点是一次端态程序、公共回流/列路由的实际时序及q=0/1终验兼容。

结果卡`tex/result_card.tex`由`../scripts/export_ten_cases.py --emit`唯一生成，中央脚本默认只读逐字校验；本例保留全部物理、算术和正文生成项检查。中央卡更新后统一重建PDF并逐页渲染。
