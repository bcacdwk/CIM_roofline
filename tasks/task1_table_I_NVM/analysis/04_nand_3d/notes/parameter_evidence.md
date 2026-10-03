# 参数证据与采用条件

PDF页序从1计；NAND-04 pp.2–3页图已核查BL switch matrix、三SSL复制及独立block SL/ADC。原始PDF保持不变。

## E01 — NAND-04

定位：PDF pp.2–3, II-A–C, Fig.3

原值：13824 BL ×32 WL ×3 SSL/block;64 blocks/subarray;144 um BL length;4 blocks per 8-bit output

采用：One64block subarray;30data+2referenceWL;K4608,N240;two magnitude polarities x4base4 blocks/output;original3BL copies x3SSL cells/digit retained

身份：`reported_model_to_mapping`。

## E02 — NAND-05

定位：PDF pp.1–3, Fig.6

原值：16-layer64Gb SGVC SLC;mean ON2nA,sigma0.3nA,OFF<0.5pA;VG1V,VBL0.2V,Vpass4.5V

采用：Retain original device/bias and saturated ON platform;NAND-04 p.2 explicitly requires two-state write-verify Vt control;no evidence for extra per-cell analog-current fine tuning or a numerical timing multiplier

身份：`measured_device`。

## E03 — NAND-04

定位：PDF p.3, Table1

原值：WL303ns;BL12ns@50% sparsity;SL530–750ns@max-bit input;native SL capacitance about16pF

采用：Keep native load/bias and budgets530/640/750ns;active BL grouping/mapping and25uA frontend differ from original max-bit case;BL12ns source is50% sparsity;not a measured group deadline or I/C rescaling

身份：`reported_RC_model_to_budget`。

## E04 — NAND-05

定位：PDF pp.1–2, II(a),(g);Fig.14

原值：SL multi-bit sense about1us;VGG7 current average7uA,max25uA;forecast/readout design rather than measured complete CIM chip

采用：25uA fixed current-sense full-scale design target;four row groups of1152 constrain nominal dense maximum20.736uA;530–750ns SL establishment +ADC is a conditional local-read budget, not a measured deadline

身份：`reported_design_to_explicit_frontend_choice`。

## E05 — NAND-04 / NAND-05

定位：04 p.3;05 p.2 Fig.13

原值：7-bit SAR in NAND-04;7–8-bit SA in algorithm study of NAND-05

采用：Nominal10bit/~8ENOB ADC unchanged;0-25uA range;29bit signed output container;approximate integer-count reconstruction

身份：`quantization_contract`。

## E06 — NAND-06

定位：PDF pp.5,25,31,43,58 Table14

原值：SLC2KB+64B page,64pages/block;tPROG typ/max300/600us;tERASE typ/max1/3.5ms;busy/status for complete program/erase

采用：Complete SLC internal program/verify and erase status budget;cross-implementation timing only,not proof of SGVC ON-current distribution;no extra loop count without evidence

身份：`manufacturer_datasheet_cross_implementation`。

## E07 — NAND-05

定位：PDF p.2 II(e),p.4 Fig.12

原值：one or two known-code WLs;calibration divider/register and inference multiplier

采用：2referenceWL ×3SSL/block;3samples for each of4 row groups;256 gain/offset pairs,24bit each,16 calibration arithmetic channels;finite residual/clipping check

身份：`reported_mechanism_to_finite_schedule`。

## E08 — NAND-04 Fig.3 BL switch matrix and independent block SL;explicit signed mapping

定位：PDF pp.2–3;native BL/SSL/WL and digital adder/shifter path

原值：Nonnegative BL input and separate block SL/ADC results;no native negative current

采用：Store w+=max(w,0) and w-=max(-w,0) in separate4block groups;apply abs(x) under two input-sign BL masks;digital polarity subtraction and signed accumulation;41,472bit resident row staging and16lane encoding charged

身份：`supported_native_path_reference_mapping`。

## E09 — NAND-02

定位：PDF pp.1–3, Figs.15.1.2/5

原值：verify sensing and pump transitions;SLC burst pump skip saves about11%

采用：Keep full program/erase budget;no extra duplicate verify and no unqualified11% discount

身份：`operation_coverage`。

## 参考实现及证据边界

双幅值存储与输入符号掩码是依照原生BL和独立block通路构造的参考映射，不是原论文已经测量的signed INT8宏。编码、保持、格式器、校准与两次符号求值的成本见当前正文及结果。

12 ns BL原模型限定50%稀疏，SL530–750 ns为原max-bit映射模型；本例保原偏置和16 pF负载并声明条件桥接，没有I/C机械缩放。二态write-verify、ON平台和SL校准分别有据；SLC完整P/E仍为跨实现时间锚点，无额外模拟精调循环的证据。

名义量化改善去除公共偏置；稀疏单位和一般抵消仍受计数分辨率限制。诊断不移植原4I4W/VGG准确率，也不认证器件噪声或实际模拟通路。
