# 2D NOR：二进制感测、有限保持与持续页／扇区更新

原生参考为**128×128 INT8**：32个512-Byte读分片，八片共一个4-KiB sector，64个256-Byte页／四sector全利用。4096 SA将一个32×16×8-bit tile捕获进4096-bit单bank保持，跨八个输入位复用；完整向量需32读／捕获和256数字轮，输出128×23bit。

典型 **ρ=24.20 MB/s、τ=0.07969 MB/s、RI*=303.65**。ΔS=5290ns；完整持续覆写T_R=205.6058ms，含64页program、四次完整sector erase和实际装入／控制。U*=38866.88=128RI*，使用完整装载接口。MB=10^6 Byte。

主三情景固定SA、tile保持、数字通道、256-Byte页缓冲和单native page engine。读100/120/130ns以NOR-01完整随机周期作工程量级桥接；NOR-02的页program typ0.4/max3ms、sector erase typ45/max400ms保留BUSY完整终点。乐观／典型采用typ写，悲观采用max写；没有证据时不创造更快完整写入值。erase约占典型写侧87.5%。

独占sector组织对照保留32读片和64有效页，但分配128KiB、擦除32sector：τ=0.01118MB/s、RI*=2164.47；未用空间不计payload。预擦页burst不替代持续覆写。无周期refresh／restore，维护前后局部能力相同；耐久单列。

入口：[正文PDF](output/nor_2d.pdf)、[中文TeX](tex/03_nor_2d.tex)、[原值与桥接](notes/parameter_evidence.zh.md)、[输入](data/inputs.json)、[结果](data/results.json)、[检查记录](notes/review.zh.md)。`native_configuration`列出原生与资源，所有情景`mapping_interface`给出完整T_R／RI*／U*。每页等效平均成本并非单笔页请求延迟。

```sh
/opt/anaconda3/bin/python scripts/check_nor.py
/opt/anaconda3/bin/python scripts/check_nor.py --emit
NOR_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
```

默认检查只读；`--emit`刷新结果／来源／validation及TeX。原生页与block/full-load计算均使用shared API。外部审阅重点是128-SA读片负载、32片选择隔离、八片共sector的高压隔离，以及完整商品时序向本地参考宏的迁移；未将其描述为同芯片CIM实测。
