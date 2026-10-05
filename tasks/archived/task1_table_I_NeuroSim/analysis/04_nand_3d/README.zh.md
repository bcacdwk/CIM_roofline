# 3D NAND 参考配置

逻辑矩阵 **4608 × 240**；输入 8 bit、权重 8 bit，逻辑输入/权重分别为 1/1 Byte/element。完整输入 payload 为 4608 Byte，完整矩阵 payload 为 1105920 Byte；内部编码、位平面和维护不增加逻辑 payload。

split-sign/base-4 映射，数据页与参考页均计时；仿射乘法/舍入与校准除法仍是未完全闭合的非零算术预算。

[输入、资源与映射](input.json) · [实际解析与模块返回](resolved.json) · [计算结果](result.json) · [阶段来源](stage_sources.json) · [方法与适用条件](../METHOD.zh.md) · [源参数引用和哈希](../../provenance/input_sources.json)

统一复算入口：`../shared/run_evaluation.py`。本目录结果由统一入口生成；十例主表与图只读[权威数据](../data/ten_case_results.json)。构建和完整 trace 留本地区。

[配对情景服务输入与来源](scenarios.json)列出 optimistic/reference/pessimistic 的少量变化因素及共同消费者；同名子目录 `scenarios/` 保存各情景的独立解析和执行结果。读取[三情景权威数据](../data/paired_scenario_results.json)时使用同一情景成对的 ρ/τ，不拼接两侧最值。
