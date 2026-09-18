# 原始量到参考预算的桥接

PDF定位为本地1基页序；工程选择与原文值分列。

| ID | 来源/定位 | 原值、单位与条件 | 采用与桥接理由 |
|---|---|---|---|
| E01 | NAND-04 · PDF pp.2–3 II-A/C, Figs.1/3 | 13824 BL × 32 WL × 3 SSL/block; 64 blocks/subarray; BL length 144 μm；作者32 nm外围CIM结构模型；非商品16-KiB页 | 保留几何；2个subarray共128块组成一份状态。每WL/SSL物理页13824 bit=1728 Byte；每块8个数据页，另2校准页。 |
| E02 | NAND-05 / NAND-04 · 05 PDF pp.1–3, Fig.6; 04 PDF p.7 Figs.7/8 | SLC ION≈2 nA, sigma≈0.3 nA; IOFF<0.5 pA; selected VG=1 V, VBL=0.2 V, Vpass=4.5 V; no-input-copy SL current distribution also reported；05为16-layer SGVC实际器件；04为32-WL模型。饱和平台降低对Vth漂移敏感性，仍有cell电流变异 | 主情景c=1，一逻辑bit对应一个SLC cell；128输入最大256 nA。108复制是组织对照，非INT8逻辑必需。保留近似误差，不施加逐cell多级电流精调。 |
| E03 | NAND-04 · PDF p.3 Table 1 / II-C | WL setup 303 ns; BL setup 12 ns @50% sparsity; SL setup 530–750 ns @max-bit input; native SL capacitance ~16 pF；RC/HSPICE估计，非新积分前端实测 | WL每输出组一次(8次/向量)，BL每求值一次。新前端建立用530/640/750 ns负载锚定预算；恢复另分配同长预算，属新增选择。640是中点。 |
| E04 | 本文设计 / NAND-04 · 参考前端选择；04 PDF p.3的16 pF负载锚点 | Added feedback/integration capacitor CF=16 pF/channel; useful output swing 0.4 V; 128 channels；工程资源选择；额外总积分电容2048 pF，不能冒称原文已有。虚地SL保持源文器件偏置 | Tint=CF×0.4V/(128×c×2nA)：c=1为25 μs，c=108为0.231481 μs。新电容、摆幅与时间推导分开标记；普通存储tR不作CIM周期。 |
| E05 | NAND-04 / NAND-05 · 04 PDF p.2 II-A及p.4; 05 PDF p.2及p.3 Fig.6 | Both binary threshold states use write-verify; programming voltage ~20 V; selected VG lies on ON-current plateau；SLC两阈值分类及饱和读；不是8-bit模拟cell目标 | 完整P覆盖泵建立、program/verify循环、恢复；目标是源文SLC窗口/电流分离量级，剩余0.3nA随机变异由近似计算承担。 |
| E06 | NAND-01 · PDF p.2 Key Specifications | MLC tPROG typ/max=1.3/2.5 ms; TLC=1.63/5 ms; both tBERS typ/max=15/45 ms；32-stack floating-gate商品MLC/TLC，非所选SGVC SLC；完整内部操作块含相应模式的verify | 选择P=1.3/2.5/5 ms，E=15/30/45 ms作为两阈值参考服务预算；30是擦除中点。借用完整高压/写验/擦除的量级，不迁移其多级终点或保证，不按小页/有效cell数缩时。 |
| E07 | NAND-02 · PDF pp.1–3, Figs.15.1.2/5 | Verify includes CLK_UP/sense/CLK_DOWN/strobe and low/high levels; SLC burst saves ~11% interior time by pump set/reset skip；QLC产品的SLC-cache机制；未报告SLC绝对P/E | 确认verify与泵建立/恢复不能漏计；参考程序逐页完整执行、不取11%折扣。截止仍未通过阈值verify则失败，不把该payload计为成功。 |
| E08 | NAND-05 · PDF p.2 II-(e); p.4 Fig.12 | One or two WL known codes; calibration divider/register and inference multiplier；已知码校准与数字校正结构；固定拍数由本文选择 | 固定2校准WL，零/满量程两读后计算系数，再半输入复测，共3读/2WL建立；16通道24步倒数、比较与存储计226TD。每次求值另1拍数字校正，kA=3。 |
| E09 | NAND-01 / NAND-03 · 01 PDF p.2; 03 PDF p.1及p.2 Fig.30.5.6 | MLC/TLC normal tR=77/100 μs; QLC 6 planes,16kB page,1.3ms program,75MB/s die throughput；普通存储判决/多阈值模式，且die throughput含plane并行 | 仅作数量级和层级核查；不用tR代替SL-CIM积分，不用die吞吐或接口带宽代替单更新域。 |
| E10 | shared_baseline · shared_parameters.json: common_conditions / R0 | 128×128 INT8; BS=128 Byte; BR=16384 Byte; 8 planes ×16 ADC; (TI,TA,TD)=(2,10,2)/(5,20,5)/(10,50,10) ns; write port128 bit；已接受共同选择；ACIM近似、128×24-bit输出；无等面积约束 | 逻辑/时隙不改；导入共享接口算服务。额外数字校正与积分资源显式列为结构接入选择；不声称c=1/c=108等最终误差。 |
