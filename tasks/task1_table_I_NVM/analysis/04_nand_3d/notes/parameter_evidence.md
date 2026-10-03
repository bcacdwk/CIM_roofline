# 参数证据与采用条件

PDF页序从1计。原器件/模式、报告身份、采用值和推导分开；公共源登记在任务总目录。

## E01 — NAND-04

定位：PDF pp.2–3, II-A–C, Fig.3

原值：13824 BL ×32 WL ×3 SSL/block;64 blocks/subarray;144 um BL length;4 blocks per 8-bit output

采用：One complete subarray;30 data WL +2 calibration WL;K4608,N480;3 BL copies and 3 SSL cells per 2-bit digit are encoding, not extra useful weights

身份：`reported_model_to_mapping`。

## E02 — NAND-05

定位：PDF pp.1–3, Fig.6

原值：16-layer64Gb SGVC SLC;mean ON2nA,sigma0.3nA,OFF<0.5pA;VG1V,VBL0.2V,Vpass4.5V

采用：Retain original device/bias;no increased current or invented integration capacitor

身份：`measured_device`。

## E03 — NAND-04

定位：PDF p.3, Table1

原值：WL303ns;BL12ns@50% sparsity;SL530–750ns@max-bit input;native SL capacitance about16pF

采用：WL retained per output group;BL12ns and native SL530/640/750ns as explicit compatible frontend service budgets;640ns is an engineering interior point

身份：`reported_RC_model_to_budget`。

## E04 — NAND-05

定位：PDF pp.1–2, II(a),(g);Fig.14

原值：SL multi-bit sense about1us;VGG7 current average7uA,max25uA;forecast/readout design rather than measured complete CIM chip

采用：25uA fixed current-sense full-scale design target;four row groups of1152 constrain nominal dense maximum20.736uA;530–750ns SL establishment +ADC is a conditional local-read budget, not a measured deadline

身份：`reported_design_to_explicit_frontend_choice`。

## E05 — NAND-04 / NAND-05

定位：04 p.3;05 p.2 Fig.13

原值：7-bit SAR in NAND-04;7–8-bit SA in algorithm study of NAND-05

采用：Common nominal10-bit/~8 effective-bit converter;range0–25uA,quantized approximate normalized sum;29-bit final signed integer container;no exact16-bit partial-sum claim

身份：`quantization_contract`。

## E06 — NAND-06

定位：PDF pp.5,25,31,43,58 Table14

原值：SLC2KB+64B page,64pages/block;tPROG typ/max300/600us;tERASE typ/max1/3.5ms;busy/status for complete program/erase

采用：short/reference300us+1ms;long600us+3.5ms;complete-cycle cross-implementation SLC budgets,not SGVC measurements or guarantees;no page-size scaling

身份：`manufacturer_datasheet_cross_implementation`。

## E07 — NAND-05

定位：PDF p.2 II(e),p.4 Fig.12

原值：one or two known-code WLs;calibration divider/register and inference multiplier

采用：2referenceWL ×3SSL/block;3samples for each of4 row groups;256 gain/offset pairs,24bit each,16 calibration arithmetic channels;finite residual/clipping check

身份：`reported_mechanism_to_finite_schedule`。

## E08 — explicit mapping and shared_baseline

定位：signed affine identity;common resource/API policy

原值：x=xprime−128,w=wprime−128

采用：y=sum(xprime*wprime)−128sum(xprime)−128sum(wprime)+16384K;480×21bit weight-sum metadata generated during complete load;16-lane input sum and output correction costs explicitly charged

身份：`algebra_and_resource_choice`。

## E09 — NAND-02

定位：PDF pp.1–3, Figs.15.1.2/5

原值：verify sensing and pump transitions;SLC burst pump skip saves about11%

采用：Keep full program/erase budget;no extra duplicate verify and no unqualified11% discount

身份：`operation_coverage`。

偏置编码最大中间值为4608×255²=299635200；使用30-bit signed中间通道及29-bit最终输出。权重和/输入和各21bit。480×30=14400bit，480×29=13920bit。
