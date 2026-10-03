# SRAM DCIM：D6CIM原生单tile

[中文 PDF](output/sram_dcim.pdf) · [章节](tex/02_sram_dcim.tex) · [输入](data/inputs.json) · [结果](data/results.json) · [证据](notes/evidence.zh.md)

主配置保留SDCIM-01原生128×128物理bit，即K128×N16 INT8、2048 Byte有效容量。16条HCA/BFA每轮16项，静态连接跨八输入bit，完整向量64个MAC时钟；输入128 Byte，输出16×23bit。没有额外权重shadow、ADC或读恢复。

| 情景 | Δ_S (ns) | 16 Byte写 (ns) | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|---:|---:|
| 短 | 279.2 | 2.2 | 460 | 7300 | 0.063 |
| 典型 | 330 | 5 | 390 | 3200 | 0.12 |
| 长 | 660 | 10 | 190 | 1600 | 0.12 |

典型未取整ρ=387.8787879 MB/s、τ=3200 MB/s、RI*=0.12121212；128次完整写装载矩阵，T_R=640 ns、U*=T_R/Δ_S=1.93939=16·RI*。原生单tile和N128容量组织具有不同输出规模，不能仅按ρ比较同等工作性能。

原4.3 ns MAC下端来自0.9 V/233 MHz完整周期；5/10 ns为工程预算。普通写2.2/5/10 ns以CMOS-07同步周期和CMOS-03 6T终点为跨实现依据，128个真实写驱动和供电固定，完整周期已含捕获/控制/恢复，不重复加2TD。该普通写移植仍需外部电路判断。

`native_configuration`完整声明资源；各情景`mapping_interface`通过公共API保存完整装载T_R与U*，原始/有效相同。八个原生tile、单活跃控制域的K128×N128组织另列，保留16项原归约；不使用32项同钟对照。已有静态连接不重复收费。

复算：

```sh
/opt/anaconda3/bin/python scripts/check_sram_dcim.py --emit
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

默认复算只读。检查原生覆盖、已含阶段、普通写驱动、完整装载、Table II接口、来源哈希和生成同步。正式统一结果卡由汇总导出更新。
