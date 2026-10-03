# 十类 CIM 技术：三种成对情景

ρ、τ 单位为十进制 MB/s。RI* = ρ/τ；INT8 下 U* = N·RI*。K×N 为输入×输出逻辑元素数。典型为选定原生参考配置。

| 技术 | 原生 K×N / 更新组织 | 乐观 ρ | 乐观 τ | 乐观 RI* | **典型 ρ** | **典型 τ** | **典型 RI*** | 悲观 ρ | 悲观 τ | 悲观 RI* |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SRAM ACIM | 128×128 · 16 B groups | 83 | 7,300 | 0.011 | **40** | **3,200** | **0.012** | 17 | 1,600 | 0.010 |
| SRAM DCIM | 128×16 · 16 B groups | 460 | 7,300 | 0.063 | **390** | **3,200** | **0.12** | 190 | 1,600 | 0.12 |
| 2D NOR | 128×128 · sector/page overwrite | 34 | 0.080 | 420 | **24** | **0.080** | **300** | 18 | 0.0091 | 2,000 |
| 3D NAND | 4608×480 · block/page replace | 17 | 1.2 | 14 | **14** | **1.2** | **12** | 11 | 0.56 | 20 |
| RRAM | 128×64 · 8 KiB epoch; 16 B groups | 48 | 7.1 | 6.7 | **25** | **4.3** | **5.8** | 12 | 1.7 | 7.0 |
| MRAM | 256×32 · 8 B groups | 750 | 130 | 5.6 | **320** | **76** | **4.1** | 160 | 53 | 3.0 |
| PCM | 256×128 · 32 B row stripes | 5.2 | 8.0 | 0.65 | **2.5** | **6.9** | **0.36** | 1.0 | 4.9 | 0.21 |
| HfO2 FeRAM | 128×128 · 16 B groups | 69 | 310 | 0.22 | **27** | **110** | **0.25** | 13 | 53 | 0.24 |
| Gain-cell eDRAM | 64×64 · 16 B groups | 15 | 200 | 0.076 | **9.0** | **170** | **0.054** | 5.4 | 120 | 0.047 |
| 3D FeFET | 128×128 · 16 B groups | 100 | 81 | 1.3 | **47** | **60** | **0.78** | 23 | 41 | 0.57 |

三种情景是相同组织和资源下的可持续成对条件，不是独立读写极值、统计区间或资源扩展对照。
τ 使用完整矩阵有效逻辑容量与完整装载服务时间；局部更新分组不改变分子边界。NOR/NAND 包含持续擦写，Gain-cell 包含周期刷新。
不同原生配置的能力不表示等面积或相同计算量的性能排名。完整资源和更新形状在统一机器数据中保留。
NAND为条件近似求值预算：偏置编码量化可使弱信号或抵消输出符号翻转，未保证小信号准确度；确定性诊断见案例正文与数据。

## 逐例模式和来源

- [SRAM ACIM](../../01_sram_acim/tex/01_sram_acim.tex)：binary_charge_domain_approximate_BPBS。更新：aligned 16 Byte update; 128 active binary write drivers; 1 complete write cycles per local transaction。
- [SRAM DCIM](../../02_sram_dcim/tex/02_sram_dcim.tex)：native D6CIM128x16INT8 tile; no unused output capacity tiles in primary configuration。更新：one128bit aligned local row;16Byte payload,128 complete cycles cover matrix。
- [2D NOR](../../03_nor_2d/tex/03_nor_2d.tex)：binary NOR + local exact digital reduction。更新：whole-matrix sustained overwrite: 4 sector erases and 64 full page programs。
- [3D NAND](../../04_nand_3d/tex/04_nand_3d.tex)：SLC SGVC current-sum ACIM, base4 offset encoding, approximate INT8。更新：sustained whole-matrix replace;64block erases+6144page programs。
- [RRAM](../../05_rram/tex/05_rram.tex)：WH-2T1R32-item ACIM with native CIMSEL time selection。更新：single-domain sustained whole8192B matrix load;512local16B groups。
- [MRAM](../../06_mram/tex/06_mram.tex)：complementary 2T2MTJ bitcell digital CIM; exact integer arithmetic conditional on correct storage/sensing。更新：one selected row x eight aligned INT8 outputs; sixteen banks, 64 complementary pairs。
- [PCM](../../07_pcm/tex/07_pcm.tex)：8-plane binary/SLC voltage-mode approximate ACIM; one native256x1024bank;8activeWL。更新：wholematrix1024aligned32Brow-stripedtransactions。
- [HfO2 FeRAM](../../08_feram_hfo2/tex/08_feram_hfo2.tex)：HZO 1T1C binary memory with local exact-integer digital CIM, existing 4096-bit read-code register reused across 8 input bits, destructive full activated-row writeback。更新：one aligned128bit local row external overwrite;1024 row transactions complete matrix。
- [Gain-cell eDRAM](../../09_gain_cell_edram/tex/09_gain_cell_edram.tex)：ACIM_binary_endpoints_pseudodifferential_3T1C。更新：16 aligned INT8 Bytes per transaction; 256 transactions complete matrix。
- [3D FeFET](../../10_fenor_3d/tex/10_fenor_3d.tex)：binary 3D vertical AND FeFET; digital local CIM。更新：one input index x sixteen aligned outputs; all eight binary planes together。
