# PCM P1 独立审查：修复请求，尚非最终结论

绑定冻结前端源码 `cf67a7b44bbfc61faa127c1c568fa8d5267034f7d49f125bc5a5ee4709e69d9b`、PCM input `54e1cc24…` / adapter `29baca4d…` / local adapter `d7d79da0…`。已从独立新目录真实构建reference；此次构建仅是修复前证据，不发PASS。

1. **共享门图缺显式清零。** Feedback MUX选择不同输出组，accumulatorKeep仅old/new；zero-mask位于weight操作数，因此add0保持上次结果。generic DFF未实现reset。独立逐位加法反例：上次acc=17，下一次全零输入MVM后仍17；verify sticky上次为1，下一请求全比较通过也仍1。公共维护者已接受添加clear门、driver、真实负载及跨请求反例。
2. **共享源线遗漏未感测BL。** PCM物理WL激活128列，SA只取64列。未感测64列可保留前row高R对应BL电荷，在当前row低R时向SL放电。当前KCL只包含64 data+64 reference，除非有实际停车/隔离资源，否则缺少这一状态路径。PCM作者已接受增加第4未感测节点、其独立C与0/Vread历史初态和LRS/HRS组合；不凭空新增免费停车。
3. **来源边界复核。** 已独立查看TiSbTe原PDF p3并提取正文：Fig6确实区分DC_SET/PULSE_SET，pulse分布不能当全部≤20kΩ；有限accepted endpoint服务必须持续明确未知yield和binary verify不在线证明电阻窗口。源脉冲plateau范围、0.5mA RESET与0.2mA SET有同源证据；端口compliance/尾沿未分解条件不升级为NeuroSim材料预测。

下一步：等待修复后的完整哈希与三点；独立再次新源码/新构建，并按闭式物理批次、RC/KCL、电气负例、真实gate/keep/clear路径及来源资格审查。详细本地证据：`/Users/shine/neurosim/runs/step4-v5/p1/pcm-independent-prereview-20261005/`。
