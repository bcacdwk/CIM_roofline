# 参数与证据定位

原值、采用选择和不采用理由独立记录；PDF页为本地1基页序。

| ID | 来源/定位 | 原值、单位与条件 | 采用与换算 |
|---|---|---|---|
| E01 | NAND-04 · PDF p.2 II-A, Fig.1; p.3 II-C, Fig.3 | 13824 BL × 32 WL × 3 SSL/block; 64 blocks/subarray; BL length 144 μm；作者CIM结构/RC模型，32 nm逻辑外围；不是量产页手册 | 原样保留物理几何。两subarray、128 blocks构成一份矩阵；一WL/一SSL的一页为13824 bit=1728 Byte。 |
| E02 | NAND-05 · PDF p.1 II-(b); p.3 Figs.5–6 | 16-layer, 64 Gb SLC; ION mean 2 nA, sigma 0.3 nA; IOFF <0.5 pA; Vg=1 V, VBL=0.2 V, Vpass=4.5 V；SGVC实际器件电流；full-block random code；非完整CIM芯片速度 | 二阈值SLC依据。NAND-04的32 WL结构另属模型，不把16层和32层说成同一实测芯片。 |
| E03 | NAND-04 · PDF p.3 Table 1及II-C | WL setup 303 ns; BL setup 12 ns @50% sparsity; SL setup 530–750 ns @max-bit input; SL capacitance ~16 pF；RC/HSPICE估计，64-block subarray；SL不是完整SLC read cycle | WL每输出组一次(8次/向量)；BL和SL每求值一次(64次)。SL中点640 ns仅插值情景；复制108份使电流接近原负载，范围仍以适配成功为条件。 |
| E04 | NAND-05 · PDF p.1 II-(a); p.4 Fig.15 | Tread ~1 μs with multibit output; ~10 μA MAC current; 7–8-bit SA resolution；加速器设计预估，非单cell测量；包括多位SA输出 | 仅对530–750 ns阵列建立加共同ADC的微秒量级交叉检查，不把1 μs再叠加或当独立硅证据。 |
| E05 | NAND-04 · PDF p.2 II-A; p.4 II-C | Both states programmed with write-verify; programming voltage ~20 V；两阈值都细调以控制导通电流 | 完整P必须含charge-pump建立、所有program/verify循环、恢复及可计算终点；完整P未给，保持未知。 |
| E06 | NAND-05 · PDF p.2 II-(e); p.4 Fig.12 | Sacrifice one or two WLs per block for known-code SA calibration; on-the-fly calibration；读取已知码后校准SA；重写/漂移可能需要重新校准 | 主情景1个校准WL，另核对2个。擦除后每块增加1或2个完整校准页program；C_cal为整矩阵事务的总校准时间，未报告，参数化。 |
| E07 | NAND-01 · PDF p.2 Key Specifications | MLC: tPROG 1300/2500 μs, tBERS 15/45 ms, tR 77 μs; TLC: 1630/5000 μs, 15/45 ms, 100 μs (typ/max)；MLC 2b/c与TLC 3b/c分列；16,384+2,208 Byte/page; 1024/1536 pages/block | 仅说明商品存储模式完整周期及粒度不同；全部不代入SLC主情景，也不充当SLC上/下界。 |
| E08 | NAND-02 · PDF p.1及p.3 Fig.15.1.5 | Fast SLC burst ~11% interior tPROG reduction; first/last ~5.5%; pump held between pages；332-WL QLC产品的SLC-cache burst；未给SLC绝对P或E | 证明泵建立/最终恢复必须计入有限窗口；不把11%或QLC >85 MB/s作为SLC绝对时间，不采用burst收益。 |
| E09 | NAND-03 · PDF p.1及p.2 Fig.30.5.6 | QLC 4b/c; 6 planes; 16 kB page; tPROG 1.3 ms; die throughput 75 MB/s；321-layer 2 Tb芯片；6-plane并行 | 仅核对die/plane吞吐与页cycle不同；不代入SLC单更新域。 |
| E10 | shared_baseline · shared_parameters.json: common_conditions / reference_instance | 128×128 INT8; BS=128 Byte; BR(full)=16384 Byte; R0: 8 weight planes, 16 ADC/plane; (TI,TA,TD)=(2,10,2)/(5,20,5)/(10,50,10) ns; 128-bit write interface；已接受公共工程选择；ACIM校准近似部分和、128×24-bit输出 | 逻辑合同和时隙不变；所有次数由导入的acim_service/front_ns/program_sequence_ns接口计算。 |
