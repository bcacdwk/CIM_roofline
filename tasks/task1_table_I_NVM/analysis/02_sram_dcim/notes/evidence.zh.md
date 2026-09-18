# SRAM DCIM 参数证据表

由 `data/inputs.json` 生成；页码为本地PDF页序。原始证据与采用值分开。

| 编号/来源/定位 | 原值与单位 | 条件与证据性质 | 采用与换算理由 |
|---|---|---|---|
| E01 / SDCIM-01 / PDF p.1 Fig.1 / II-A; p.2 first paragraph | 128×128 bit；128×16 INT8；16项×16输出/拍；64 clock/VMM [bit / elements / clocks] | 28 nm，6T binary SRAM，8-bit signed/unsigned full-precision；输出23 bit；reported_architecture | 一份128×128 INT8需8个容量分片；单分片64拍，顺序覆盖512拍；128个物理bit列除以每权重8 bit，仅16个逻辑输出；16项归约保留原结构 |
| E02 / SDCIM-01 / PDF p.1 Fig.1; p.2 II-D; p.3 Fig.5 / II-D | 16 HCA +16 BFA；8次input-bit展开后换行组；23-bit RCA [lanes / bit] | 静态dual-wordline access；每LBL 16 cell；BFA不在8输入位之间重切WL；reported_architecture | 每轮含本地读保持、1-bit输入×8-bit权重、16项归约、符号/移位/累加；无独立read_ns；完整计算周期覆盖读与算；64次行组选择支撑512个bit-round，不把静态WL重复解释成512次切换 |
| E03 / SDCIM-01 / PDF p.4 Fig.10(a); p.3 III; p.4 Table I | 0.9 V: 233 MHz；1.1 V: 正文360 MHz、图363 MHz [MHz] | 28 nm，VMM shmoo；温度未在该图明确报告；不采用最低0.6 V/30 MHz情景；measured | T_C=4.3/5/10 ns；4.3 ns由1000/233向上取0.1 ns；5/10由共同数字节拍选择；0.9 V与共同近标称点相邻；不从1.1 V高速点外推0.9 V；三值为预算不是PVT分位数 |
| E04 / SDCIM-01 / PDF p.1 Fig.1 / II-A | Write Data[127:0]；Addr[6:0]；CEB/WEB [bit / signals] | memory R/W column/row periphery，与VMM控制分开；未独立报告memory write ns；reported_architecture | 128 bit=16个完整INT8权重/事务；单分片单行，单更新域；每权重8 binary cell；bitcell互补内部节点不产生额外逻辑payload；不把CIM频率当写频率 |
| E05 / CMOS-07 / PDF p.1 timing description; p.2 Fig.2; p.9 Table II/III; p.8 V-B | 455 MHz；48 bit×1k word；2RW 8T；1.05 V typical；25 °C读写功耗测试 [MHz / bit / V / °C] | 28-nm eFlash工艺，高阈值；共同CLK上升沿捕获命令/地址/数据；图示连续write/write/read；频率非单独write-min测量；measured_and_timing_definition | 1000/455=2.197802… ns，取2.2 ns为写周期参考下端；5/10 ns为公共节拍预算；以完整时钟和同步写组织支持普通写，不用read access。跨48→128 bit与8T→6T是明确参考移植，需128路写驱动，非同芯片实测配对 |
| E06 / CMOS-07 / PDF p.9 Table II / III | 1.54 ns [ns] | 28-nm 48-kbit 2RW SRAM，typical read access；measured_excluded | 不用于t_write或独立DCIM读附加项；read access只覆盖读访问，不是周期，更不是写完成时间 |
| E07 / CMOS-03 / PDF p.1 II; p.3 IV-C / Figs.4–6 | 50 FO4≈1 ns；WL=25 FO4；15 fF/128 cell；SA offset0.1 V [ns / FO4 / fF / V] | HD 28 nm 6T，TT，nominal1 V；瞬态模型；周期末检查内部节点达到目标，支持back-to-back；目标BER<1e−9对应1MB/90% yield；model_and_success_endpoint | 仅支持同步完整写及数ns量级；不把1 ns当128-bit D6CIM实测写周期；约半周期WL脉冲≠完整更新；需含节点翻转、保持/关WL和下一周期可读 |
| E08 / SDCIM-03 / PDF p.1 memory/CIM paragraphs and measurement paragraph; p.2 Figs.11.7.2–5 | 3 ns/clock@0.8 V；8 clock/8-bit乘法；Σ4/Σ9/Σ32 post-sum [ns / clocks] | dynamic logic；memory和CIM模式分离；lossless bitwise computation；不同post-sum组织；measured_crosscheck | 仅交叉支持数ns计算时钟和逐位完整精度；不把24 ns直接作为128×128 MVM；3 ns是本宏时钟；输出数、post-sum及本地接口与D6不同 |
| E09 / shared_baseline / data/shared_parameters.json: common_conditions; reference_instance | 128×128 INT8；128×24-bit输出；T_D=2/5/10 ns；R0=32项×16输出/轮 [elements / bits / ns] | 28 nm，0.9 V/25 °C参考，非固定PVT验证；单独立服务单元/更新域；无等面积约束；accepted_reference_choice | 逻辑/精度/边界不变；D6型R2例外16项/轮；全向量捕获和提交2T_D；R0=256轮是其资源选择；D6型512轮是16项而非32项的结果，不是共享计数错误 |
| E10 / shared_baseline / tex/02_estimation_method.tex: C direct update; R4 | T_front=[2+n_b−χ]T_D；n_b=χ=1；完整周期已含则替代 [ns / beats] | 普通同步memory端口，无另外定义的任务握手，边界在其命令/数据捕获到下一可计算周期；accepted_reference_choice_with_R4_substitution | 主情景Δ_R=T_M=2.2/5/10 ns；T_front额外项为0；外层握手敏感性单列加2T_D；完整memory周期已含命令解码、数据建立、写驱动和可复用终点；不会在同一阶段上再加T_W |

SDCIM-02/04/05 保留目录与清单记录，但未用于本情景数值：02是65 nm；04性能标签混用且近似模式有不同延时；05有容量和FP8模式标注差异。主分析避免将这些headline拼接到D6型结构。

关键原始页面已渲染目视核验：SDCIM-01 pp.1/4、CMOS-03 p.3、CMOS-07 p.9；另外原文全文/相关页文字核验包括SDCIM-03 pp.1-3、CMOS-07 pp.1-2/7-9。

局限：128-bit 6T普通写完成周期没有同芯片实测值。本分析用同步28 nm CMOS证据、成功终点及共同节拍形成明确参考预算；不宣称0.9 V/25 °C严格PVT保证。
