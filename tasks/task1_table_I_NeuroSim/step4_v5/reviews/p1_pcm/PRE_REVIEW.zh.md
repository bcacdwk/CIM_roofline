# PCM 独立预审入口（尚无 PASS）

角色披露：本reviewer是MRAM生产作者，也是FeNOR/GC/NAND P0路线作者；未写PCM源码、配置或证据。曾向公共维护者指出MRAM参考支路隔离、源回流和单行MUX尺寸化问题，这些共享修复也影响PCM；公共生产代码由integrator维护。本次独立性针对PCM器件输入/热写/计数/服务，公共接口历史参与明确保留。

已只读浏览PCM当前inputs/adapter/evidence。正式审查必须等作者给出最后输入/代码与公共checkpoint哈希，再在全新本地目录构建三点。预审不复用生产二进制、不发布PASS。

待独立核验：

- 同源Ti0.4Sb2Te3的电流脉冲和Fig6 DC_SET/PULSE_SET差别；accepted endpoint服务不是全体器件yield。冷读R不能外推0.5mA热写compliance。
- K128×N16、16384bit，16写lane每极性1024批；每row完整RESET再masked SET，64SA给两verify组，共256组。所有逻辑payload只算2048B一次。
- 低rail预充时数据WL与reference隔离均OFF；native实际C/新writeTG、sourcegrid KCL和最坏负载组合；参考state误差预算是否含预充/负载。
- 实际门连接的zero mask、signed add/sub、非选组反馈、per-beat ingress与target mask；先脉冲后完整终验，失败budget为0payload。
- 原生时钟内阶段不双计；物理脉冲尾沿/冷却的包含范围，完整外部波形条件足以支持reference结论，未明确电压不能称native预测了热写。

独立审核包运行根：`/Users/shine/neurosim/runs/step4-v5/p1/pcm-independent-prereview-20261005/`。当前仅预审状态，最终三个配置的fresh build、独立逐项计数/局部电路与失败门结果另存。
