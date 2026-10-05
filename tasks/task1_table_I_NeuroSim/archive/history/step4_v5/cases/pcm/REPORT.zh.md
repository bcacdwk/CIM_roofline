# PCM 全HV新参考：三点已独立复核并内部验收

新身份 `pcm_tst_fullHV130_3um_1t1r_binary128sa_k128n16_v2` 保持常规1T1R与同源TiSbTe电流脉冲，使用实际SKY130 3µm/.5µm额定HV访问管、HV隔离/返回、128SA和128参考。它不是旧电压求和宏，也不是先前45nm低压访问阵列。旧低压read-only合格／resident阻断身份已原样保留在 `lv_readonly/`，对应独立审查不被追溯升级。

K128×N16、signed INT8、16384物理cell；全部128列一次二元读，128bit保持，8个25bit数字lane分两组逐input bit计算。16个真实编程电流lane，1024个RESET批和1024个保留SET批；每行最终全128bit读回，8个byte比较器分两组比较，失败不提交payload。

三组完整参数包为RESET/SET 20/100、50/200、100/1000ns，固定硬件/温度与读端口。它们来自同一材料脉宽平台，是有限成功工作点政策，不是器件分布、实测典型或重试概率。完整当前电流波形原语包含其终止/quench；阵列已断开后的BL电荷返回另计，未把它当额外材料尾沿。

SKY130原始I–V与独立TT电容几何分别锁定。3µm实际管在保守4V gate/body−2.5V下提供.5mA需约.503V；加真实金属/回流后，材料端compliance约3.983V。两只P7输出每lane额定候选能力1.101mA、16路总上界17.61mA，小于声明20mA程序供电；16路主动返回峰值30.61mA，小于40mA条件。未选访问管也都是HV，因而不再把hot BL接到未选1V访问管。

实际read总C约718.6fF/支路；native只承担真实LV译码、通用电压SA/hold和数字算术，PCM不调用极化模型。HV控制由已锁有源I/C及保守端口块承载，完整控制约28.18ns、返回40ns；本地0.2V预充按16 data+16 ref为一组分八组，前组保持连接到共同release。旧整读写时隙没有参与。

耦合源线网络遍历工作电阻窗、其他列状态、初始误差与使能偏移，并包含未选行漏电上界。所需差分35mV；另用矩阵指数检查实际20ns控制捕获以及端口提前边界，最小37.06mV。SA由计入资源的共享脉冲控制器在合格窗口触发，不是假定预充期间一直启用。30mV SA与5mV剩余误差仍是工程资格，非噪声/STA认证。

必须保留的条件：TiSbTe终端电流波形须能在上述compliance和新负载下复现；论文没有直接给出本组合的端电压/quench联合表征。ON5–20k/OFF200k–2M是已表征工作cell窗口，Fig6脉冲分布重叠使它不能代表全阵列yield，binary verify也不在线证明电阻窗。HV动态控制、局部供电与阈值感测为边界清楚的模型参考，不是全芯片签核；长期漂移/重校准不在本地服务窗口。

三点精确 `(ρ,τ,RI*,U*)`、原生参数、各阶段、resource与来源条件在 `candidate_points.json` / `reference_snapshot.json`；独立aperture检查在 `controlled_aperture.json`。真实新构建路径：`/Users/shine/neurosim/runs/step4-v5/component-services/case-pcm-pcm-HV-{optimistic,reference,pessimistic}-r1-20261005`。主入口：

```sh
python3 -B '<V5绝对路径>/run_components.py' --case pcm --scenario reference --run-id '<新的唯一ID>'
```

B组已完成本新身份的独立三点fresh复核，结论`PASS_conditional_model_scope`，supervisor按D033内部验收。见[新HV独立审查](../../reviews/p1_pcm_hv/REVIEW.zh.md)；未沿用旧read-only PASS。
