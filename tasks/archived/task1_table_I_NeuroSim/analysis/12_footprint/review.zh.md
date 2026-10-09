# 独立复核：存储密度与 F_mem²

复核者只写非同步独立目录；不修改公共代码、既有十例/30点或论文。独立算术从原始 PDF 抽取与目视开始，不读取生产 CSV 补数，不导入生产计算函数。生产复跑与最终图渲染目检均已完成并通过。

## 已完成的来源复核

- SACIM-03 PDF p3 §III 的 0.994 µm²、28 nm 与 p2 的 9T1C 一bit及上层 MOM 重叠关系一致；不另加电容面积。
- SDCIM-01 PDF p1 §II.A/ Fig1 和 p3 Fig8：每列128个bit，8列tile共1024 bit；图中阵列的91 µm × **6.4 µm**包括共享NOR、局部隔离/连接与分布式15:4压缩器。外侧39 µm HCA tree/BFA区域排除；裸6T核心0.379 µm²不作为完整tile主值。初次低分辨率目视把6.4误读8.4，交叉复核用原PDF字符（x=532.1786, top=405.577起字符6、.、4）和放大裁图纠正后，独立脚本已更新。采用完整已标注tile，不按晶体管数量缩放，也不尝试闭合整个宏面积。
- NAND-04 PDF p2 Fig1/§II.A：40 nm BL pitch × 0.75 µm SSL pitch；块中原文计数13824 BL × 32 WL × 3 SSL，确定每BL/SSL/WL一个独立物理SLC位；不因SGVC两侧额外乘2。三SSL存MSB两份与LSB一份是上层CIM映射，排除于原生存储口径。32为来源模型L0，NAND-05实测文字为16层；不把32称实测。保持0.03 µm²横向tile，L0与500的b分别32/500，一次折叠。
- MRAM-06 Supplement p10的约1600F²明确指IBMD bitcell；主文p1明确40 nm CMOS。其两个1T1MTJ支路及本地latch/共享尾部结构是完整单位，互补支路仅一个自由bit。1600×0.04²=2.56 µm²是文献工程估计，40 nm按nominal node解释，不冒充实测half-pitch。未替换成旁引1200F²旧2T2M设计。
- GC-04 PDF p6 §III.A：3T1C layout 6 µm²、10 fF MOM在metal4–7，同页/主文报告65 nm CMOS。主图一原生3T1C独立bit，取消原MLC容量收益；伪差分两cell属于上层CIM映射而不压缩此b。
- FENOR-02 PDF p2 Figs1c/2c、p3 Figs10/11：X pitch120 nm、Y pitch170 nm是孔阵列完整横向重复pitch，不是孔径100 nm或膜厚；同孔split S/D及两侧通道共享gate，没有两个独立存储自由度的证据。每孔每层一bit；保留四层b=4，A=0.0204 µm²。此为论文TCAD/SPICE布局模型与四层容量计数，非四层实测提取面积；256层含WL接触8.37 Gb/mm²不作本轮主输入。F=60 nm仅X方向half-pitch，不是垂直40 nm层距。

## 缺口处理

NOR-03现有二元商品来源没有所需完整原生cell版图；其他模拟NOR的1.5 µm²不对应当前身份。RRAM-05 p3 Fig4仅给m=4版图和相对30.3%开销及晶体管W/L，不足推当前m=1绝对tile。PCM-03给完整宏与访问组织，没有相容独立bitcell尺寸；不得以宏容量/面积或heater接触替代。FERAM-02的1X、5 nm HZO厚度和电容截面不能确定完整1T1C投影及精确平面F。这四项保留null/N/A，不能填0。

## 独立算术与 NeuroSim

`independent_recompute.py` 用独立记录的源参数按高精度Decimal算A/b、1/a、a/(F/1000)²，检查倒数、alpha还原、仅改变F不改变密度、NAND 1/32/500三点一次折叠及SLC/互补计数。随后 `compare_production.py` 比较规范JSON，缺口必须为null。

两例NeuroSim通过全新源码副本与独立编译运行，锁SHA 8a88abf85844c0e1ba17cc771ea535fff6040456，结果为普通SRAM阵列2220.35968 µm²、0.13552 µm²/bit；常规1T1R为380.633088 µm²、0.023232 µm²/bit。两例实际阵列几何用tech.featureSize=22 nm；cell.featureSize=40 nm用于某些辅助参数，param.arrayheight不等于实际lengthCol。areaArray、usedArea和total area已区别验证。它们只证明接口链与单位，不作为十类面积来源。

## 最终状态

**PASS。** DCIM高度与GC来源页码纠正后，从独立目录重跑公开入口，生产JSON与独立复跑JSON逐字节一致；原文重抽算术比较全部通过，四个缺口均为null。正式单页双面板PDF已用PDFium以180 dpi实际渲染并目检，坐标/方向/顺序、投影纹理、名义node星号、N/A、互补一bit说明完整，文字无裁切与碰撞。PDF SHA-256：`a290cfabd8c23a322927ac306bd4f834030772df9e1f576db4eba1f3b904407e`。

以supervisor的1509项开始快照独立复核，既有NeuroSim输入、30点结果、历史与原图保持；唯一必要导航变更由集成者处理。运行期间观察到其他并发论文修改，复核者未写入，保留这些变化而不声称整仓库论文bytewise未变。


## 可复跑的小型复核材料

[独立源事实复算](review/independent_recompute.py) · [生产比较器](review/compare_production.py) · [独立结果](review/independent_results.json) · [比较结果](review/comparison.json) · [来源复核](review/reviewed_sources.json) · [独立探针复核](review/independent_probe_review.json) · [PDF目视复核](review/visual_review.json) · [范围检查](review/boundary_report.json)

在新的非同步目录执行，例如：

```sh
python3 -B <task>/analysis/12_footprint/review/independent_recompute.py --output independent_results.json
python3 -B <task>/analysis/12_footprint/review/compare_production.py \
  --production <task>/analysis/12_footprint/results/footprint_results.json --output comparison.json
```
