# 最新状态：read修后复跑；resident暂时blocked

独立review确认三个修复项：未感测64列历史电荷必须进source KCL；首行verify前realclear；hotprogram BL不能假设已在readsafe域。前两项已实现，新的read-only快照运行中；第三项正尝试唯一SKY130额定HV有源端口。旧三点已在candidate_points.json撤销、移至withdrawn_candidate_points.json，仅供审计，不得正式图示。

# PCM P1 当前可交接状态

三个最终作者候选已实际fresh构建运行，状态ready_for_review/conditional，未独立验收。入口为REPORT.zh.md、candidate_points.json、reference_snapshot.json；生产代码/输入已冻结供B组独立审核，当前只补诊断/报告。原P1探索和失败记录如下，均不得替代最终包。

# PCM P1 当前状态（最终修复前）

本例作者同时曾编写 NOR/FeRAM P0 卡，独立公共 P0 reviewer 与 MRAM 预审；不对本人 PCM 作独立通过。

已真实构建：`integrator-pcm-reference-probe-20261005a` 因访问宽度超过10µm失败；`...b` 500Ω访问/8µm pitch成功但原100mV单cell-reference门失效。`case-pcm-pcm-author-ref-v1-20261005` 因1.1V请求不匹配native1.0V失效。`case-pcm-pcm-author-{opt,ref,pess}-v2-20261005` 曾完成3个conditional候选，但后续reference隔离/数字保持和source网修复使其失去最终资格。`case-pcm-pcm-final-ref-gate-20261005` 已按修后代码重构，80ns clock因MUX按128行并流过度尺寸化而不合格（最小983.6ns）。以上失败/旧快照均保留，不作为正式点。

现有规范：`inputs.json`唯一输入；`case_adapter.py` prepare/evaluate；`adapter.py`含真实有限状态计数、带故障全覆盖、signed bit-serial与被动/共享source RC求解。实际K128N16、8cell/weight、64SA/两读组、16 current lanes、128bit weight/target holds、400bit outputs、64 reference。低压1.0V LSTP45nm外围与40nm材料身份分开，0.2V读为工程条件。端态窗口是先验表征条件；现场verify仅判binary readback，不假称单阈值测出窗口。

固定 source 网：128data+64reference列各128µm长、2µm×1µm；1536µm×20µm×2µm边缘汇流条；工程Cu等效rho2.2e-8Ωm。机器计算localR1.408Ω、sharedR0.8448Ω，16×0.5mA产生7.4624mV source drop；原细row产生81.92V，明确否定。43.280fF/column的几何耦合由prepare加到native extraC，四极端数据负载的耦合RK4网络纳入实际read共同source电流。reference switch R只计一次；matched reference shunt cap扣除真实switch/precharge/SA寄生后实现总C匹配。

当前等待公共最后两项：单行数字读MUX按一活动行尺寸化（read_mux_IR_fraction=0.5）、独立100Ω program route真实R/W/C/driver/容量，避免旧2625Ω写TG的0.5mA压降超native电压。`write_current_A`从RESET/SET最大值唯一派生。强writeTG关闭后的端口电容/路径归属必须清楚。reference/data开启沿同步属于尚需明确的native时序端口条件，不能把不同enable时延的先行放电默默丢掉。

公共维护者将发布稳定字段/哈希；随后作者按实际clock gate重新确定同一工作clock，fresh跑reference再全部三点，导出小型评审包。写波形10/100、20/200、100/1000ns为同源plateau有限操作政策，不是材料分布。source-equivalent pulse/current/quench/compliance和10mV SA+5mV总误差预算保持显式条件，无yield、BER、原子热写或硅STA保证。
