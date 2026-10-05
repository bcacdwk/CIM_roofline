# NAND 作者交接（2026-10-05）

从本交接起 NAND case 唯一生产 owner 改为 integrator。B 作者已停止此目录写入；没有 NAND 正式点或独立PASS。

已有小文件：`ROUTE.zh.md`、`evidence.json`、`identifiability_probe.py`、`string_probe.py`、`source_line_probe.py`。大材料/运行在 `/Users/shine/neurosim/runs/step4-v5/p0/nand-route-20261005`、`/Users/shine/neurosim/runs/step4-v5/p4/nand-string-20261005`。

1. 原组织证明：K4608/N240，64block×32WL×3SSL×13824BL，30data+2referenceWL；split-sign/base4/3BL复制×3SSL unary，72physicalcell/INT8。65,536 scalar physical编码零错；6144 page programs=5760data+384reference、64erase，总84934656cells。源NAND05实测16layer，NAND04称32引用05；32必须标组织延伸，不能叫同源实测32layer。
2. 第二路线 `string_probe.py` 是真实 GSL+每个selected/pass FET+SSL 的串联内部node求解，采用EKV1995 Eq28/30/31前减反电流，非staticV/I。Is在16layer/50%后台/Vg1/VBL.2/Vpass4.5拟2nA；n3、Vt低−.8/高1.7为原Fig6形状的显式工程候选，不是唯一提取。Vg1→5 plateau只增9.08%，不同状态/背景/SL/8/32层已跑；32层不再归一强行维持2nA。可作有限model-reference，不须唯一gds实测。原EKV论文已存 `/p2/fenor-port-20261005/EKV1995.pdf`，p91公式目视核对；DOI10.1007/BF01239381。
3. `source_line_probe.py` 给出被动SL替代的真实反例：每block41472 strings，inputgroup最多10368 active，其余BL0+低Vt字符串会在SL抬高时反向吸流。16pF、40ns工程积分（不是旧530ns）全参考SL30.803mV；25µA等效10bit量程，孤立1string输出0，同1024active在两种inactive背景是82/55 codes。见 `shared_SL_probe_r2.json`。不能只数activecurr或以两reference消掉所有后台。这个是所选紧凑模型中的反例，不声称实测NAND芯片有同样百分比误差。
4. 原SL16pF可作外部局部负载，原WL303ns/SL530–750ns完整标签仅对照。NAND06完整SLC P/E是300/600µs program、1/3.5ms erase（请核原spec）；已包括pulse/verify/pump/recovery，2048+64B/64page与本例1728B/96page是条件性跨实现转用，不按byte缩放或再收费。
5. root已批准有来源的外部TIA/clamp有限端口。官方LTC6268/6269入口 https://www.analog.com/en/products/ltc6268.html；datasheet `https://www.analog.com/media/en/technical-documentation/data-sheets/62689f.pdf` 下载尝试因HTTP/2 INTERNAL_ERROR失败，不能当已取得全文；目标是本P4目录 `LTC6268_6269.pdf`，可用curl --http1.1重试必要小文件。官网核到GBW500MHz、unity350MHz、Cin450fF、slew400V/µs、supply3.1..5.25V、Iq16.5mA/amp、I_bias3fAtyp/4pAmax125°C；openloopgain搜索主源见80V/mV项，尚须核完整表的典型/最小与负载域。建议有限单dominant-pole+slew模型，Rf约25kΩ、Cf约.5..1pF为工程稳定性起点，Csl16pF+Cin实际接入；这些尚未生产实现或优化。±2.5V可让SL0 virtualground与负TIA输出处于真实供电域；SAR0..1.1V需要实际offset/inversion/buffer，64SL若每路两放大器就是128amp，Iq总2.112A/5V约10.56W，必须披露hybrid商业前端资源/功耗代价，不能叫集成低功耗原宏或漏掉负输出转换。root允许来源明确hybrid model-reference，不要求全OTA晶体管。
6. 代表性检查应保背景依赖/残余SL、稀疏/抵消、有限ADC量程/参考页、校准归属；phase正负输入都执行可消一些固定offset，但不能免费假消所有状态依赖误差。全部编码/页口/参考/erase+calibration进入resident。native继续适用WL/BL/SSL驱动、SAR/数字，外部AMP保持可见。

建议最短下一步：核LTC规格域→固定有限Rf/Cf并解SL/TIA动态+一不同C或背景对照→给native外围负载和完整服务次数→reference/三有限包→A轻量独立审。不要再扩全TCAD、SPICE、材料分布或公共框架。
