# 3D NAND 原生 signed INT8 近似参考

一个64-block subarray实现 `W[240,4608]`。正、负权重幅值各用四个base-4 block，输入幅值经正／负符号BL掩码分两次读出，消除ADC之前的大公共偏置。原13824 BL、32 WL、3 SSL、三BL复制、30数据WL和2参考WL保持；每权重72cell，有效容量1,105,920 Byte，物理容量10,616,832 Byte。

| 固定组织情景 | ρ (MB/s) | τ (MB/s) | RI* | U* |
|---|---:|---:|---:|---:|
| 乐观 | 8.42 | 0.579 | 14.5 | 3491 |
| 典型 | 6.83 | 0.577 | 11.8 | 2839 |
| 悲观 | 5.55 | 0.282 | 19.7 | 4733 |

典型ΔS=674.86 μs，TR=1.91611972 s，U*=240·RI*。每向量固定960次求值及61,440次标量转换，包括空符号掩码。64个10-bit ADC、25 μA额定量程、2 nA名义电流和16 pF原生SL负载保持；没有新增反馈积分电容或提高ADC位宽。

- [正文PDF](output/nand_3d.pdf) · [中文完整推导](tex/04_nand_3d.tex)
- [输入](data/inputs.json) · [完整精度结果](data/results.json) · [名义数值诊断](data/quantization_diagnostics.json) · [验证项](data/validation.json)
- [证据](notes/parameter_evidence.md) · [参考实现与检查说明](notes/review.md)
- [五ACIM共同名义检查](../shared_baseline/data/nominal_service_diagnostics.json) · [统一入口](../TEN_CASE_REVIEW.zh.md)

输入新增4608符号位及16路幅值编码。写侧显式配置41,472 bit单输出行暂存、16条目/拍编码／格式器；128bit名义口实际每拍仅输出48个数据页物理位，参考常量页仍128bit/拍。完整装载为5760数据页、384参考页、64次erase、69120拍行编码和12轮SL校准；两种极性均全部program。无全矩阵shadow。

同一10-bit理想器件诊断下：全零0→0，全正单位4608→4592，负单位−4608→−4592，对称±1和±127抵消0→0。孤立单位1→0、小幅非对称向量2→24仍暴露计数量化分辨率。约8 ENOB只报告分辨尺度，不替换实际码宽。通过名义诊断不等于电路或应用准确率认证。

旧 `x+128,w+128` 映射保留为 `legacy_offset_comparison`，独立记录K4608/N480、旧资源和吞吐，`scenario_class=restricted_encoding`、`workload_mapping_eligibility=false`。它不进入新主点或通用signed INT8适配。新参考的近似signed映射资格仍须与具体应用误差要求相容。

SL建立530/640/750 ns保持为原负载／偏置的条件桥接，完整SLC program/erase采用300/600 μs与1/3.5 ms跨实现锚点；不称为新映射实测期限。正常读与装载校准的共享参数同步传播。

在本目录复算：

```sh
/opt/anaconda3/bin/python scripts/check_nand.py
sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

`--emit`刷新现有结果、诊断及生成TeX。9组检查包含完整编码／容量、65,536个标量物理编码、独立典型算术、真实48bit页格式器、服务参数导数、量化及旧受限对照、两表接口、来源哈希和生成同步。结果卡由公共 `../scripts/export_ten_cases.py --emit` 唯一生成。
