# MRAM：原生互补bank、有限权重保持与完整两相写验

原生取MRAM-06的**64 bank×256 row×4 bit**；两个bank合成INT8输出，得到 **K=256、N=32**，有效8192Byte、物理131072MTJ。互补编码不增加逻辑payload，输出32×24bit。

IBMD原latch输出IN∧W，不能跨任意输入位当作W缓存。本参考令IN=1感测W，增加原加法树之前的4096路16:1抽头／选择／隔离、4096-bit单tile寄存及4096个数字AND，再接共同16条32项归约通道。完整向量16读／16捕获、128数字轮；新抽头和选择时序在物理读槽内，捕获另1TD。原256项归约树不作为同时活动的额外吞吐资源。

| 固定资源情景 | ΔS (ns) | ΔR (ns) | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|---:|---:|
| 乐观 | 340 | 60 | 753 | 133 | 5.65 |
| 典型 | 810 | 105 | 316 | 76.2 | 4.15 |
| 悲观 | 1620 | 150 | 158 | 53.3 | 2.96 |

更新一组八INT8权重，128MTJ先全P、64目标支路再AP；固定128条200µA写驱动和SL25.6mA额定能力。64路独立单端终验分左右两批，每批读、1TD捕获、1TD比较；128-bit目标和128-bit状态寄存分别计入。完整两相写槽以MRAM-03的20/30ns完整access量级支持，原概率地板不移植为新宏成功率。

典型完整装载1024笔、`T_R=107520ns，U*=132.74074=32RI*`。每16KiB平均更新成本215040ns只是平均换算，不是原生8KiB请求延迟。ρ较大与原生K/N及保持有关，不能称为MTJ材料提速。恰一次整组重写且随后通过的对照为ΔR200ns、τ40MB/s、RI*7.9012，独立于普通悲观点。无周期refresh／restore，维护前后能力相同；寿命另列。

阅读：[正文PDF](output/mram.pdf)、[正文TeX](tex/06_mram.tex)、[证据与原图定位](notes/evidence.zh.md)、[输入](data/inputs.json)、[结果](data/results.json)。顶层`native_configuration`区分有效容量、MTJ和新增资源；每情景`mapping_interface`来自共享API、包含对应完整T_R／U*。

```sh
/opt/anaconda3/bin/python scripts/check_mram.py
/opt/anaconda3/bin/python scripts/check_mram.py --emit
BASELINE_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
```

默认检查只读，构建入口显式生成结果／表并渲染所有PDF页。检查覆盖原生bank地址、真实4096节点抽头、单tile保持、两相／绝对终验、独立阶段算术、完整矩阵及源哈希。外部审阅重点是选择布线与读槽、AND／归约周期、条件200µA驱动及绝对终验裕量，内部检查不等于用户验收。
