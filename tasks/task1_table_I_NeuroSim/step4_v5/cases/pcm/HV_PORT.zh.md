# 唯一 HV 替代端口：已有可运行局部结果，完整 resident 尚未闭合

已定向取得并锁定 SkyWater 公共 HV 元件数据，不以普通1V TG承担未知hot-BL电压。官方 `nfet_g5v0d10v5` 给出的模型域为VDS 0–11V、VGS 0–5.5V、VBS −5.5–0V；这与将器件缩成45nm是不同事情。原始I–V是20µm/0.5µm NMOS和7µm/0.5µm PMOS测量；几何C来自另一个锁定TT模型，二者分开标记，不能称同一芯片联合测量。

[官方元件域](https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html)；源码/原始数据完整SHA和提取规则见`hv_data.json`。只取两器件的必要I–V、TT参数和Apache许可；完整文件留`/Users/shine/neurosim/runs/step4-v5/p1/pcm-hv-port-20261005/`，管理区仅14KB小表、脚本和许可。

`hv_port_probe.py`已实际执行：NMOS20µm/.5µm的几何上界Cg=40.79fF、Cd=27.52fF；4.5V是本次工程compliance上限，**不是TiSbTe论文的实测电压**。16路主动clamp的峰值需求184.45mA，共同/局部ground上界172mV。以更弱的实测VGS4V、VBS−2.5V曲线及全程最坏ground计算，gate有效后把代表性463.44fF节点由4.5V降至.2V需约0.446ns。不能把这个数当成含模式转换、驱动或极化热过程的完整返回时间。

OFF隔离须先把低压侧主动park至0；由整个drain电容耦合作保守上界检查feedthrough与漏电，需要128个真实LVpark器件，不是把浮置低压节点视为永远安全。高压clamp时所有数据WL必须关闭，剩余电荷不能借PCM自身放电来隐藏再加热。1V→5V的cross-coupled小电路也用实测I–V跑过：每侧16个并联HV N、一个HV P，输入有效后输出翻转约3.542ns；每个低压输入负载653fF，不能省略其LV驱动。未把理想logic命令到HV gate的全过程称为已完成。

现有可行证据支持继续实现，但还不构成正常tau：需把LV driver、HV output buffer、mode/波形时序和全部read负载接入；移走/隔离所有可能暴露在hot域的1V支路；计入128隔离/128返回clamp/128程序输出及局部电源电流需求；建立首次verify前所有列的残压界。高侧程序输出可另用实测HV P管（两只7µm在5V栅源差、0.5V输出headroom下约1.10mA），不能把G=5V的N管默认当成可把任意节点驱到4.5V的高侧开关。

仍无原TiSbTe器件在选定compliance、新负载和新quench控制下的联合波形证据。该条件必须独立陈述；不能用冷态读电阻反推热写电压。当前正式resident保持blocked；原10/100、20/200、100/1000ns脉宽候选没有因此被重新验收。此局部探针不作全PDK或全芯片签核。

```sh
python3 -B '<V5>/cases/pcm/hv_port_probe.py' --native '<fresh-read-run>/resolved.json' --out '<new-local-path>/hv-port.json'
```


## 完整拓扑否定项（2026-10-05）

`hv_topology_boundary.json` 保留了列端方案之外的反例：同一 hot BL 接到全部 128 行；未选行的有限 PCM 电阻把电压传至其 OFF 访问管漏端。在选择的 4.5 V compliance 下，只有列端 HV 开关不能保证这些 45 nm／1 V 管的漏端额定。因此原拓扑仍不得给 resident 条件通过。热写时只保持选中 WL 有效也不能保护另外 127 行；先关 WL 再 clamp 更不能自动解决。

已量化一个必要的全 HV 访问替代：16384 个 20 µm／0.5 µm 额定管，仅 channel+diffusion 约 0.8192 mm²；每 WL 栅负载 5.221 pF，每 BL 单元漏负载 3.523 pF，未含外围／导线。0→4.5 V 的该 BL 电荷为 15.85 pC；即使全部 0.5／0.2 mA 用于充电，也需 31.7／79.3 ns，不能与 PCM 终端电流脉冲混称。它还需要 128 个实际 5 V WL 驱动及新的 pitch／C／源网与 quench 模型；原生 45 nm access 的宽度、面积和时序不得继续代替它。

最小闭合需求是原材料兼容的访问／电压与终端波形表征，或完成全 HV 访问重新设计并证明新负载下的终端电流与返回。现有文献未提供联合证据，唯一公开 HV 替代已得到真实有源局部探针，但没有据此制造完整服务点。只读模型保持可运行，resident 阻断；其余案例继续推进。
