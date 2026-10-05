# SRAM DCIM 参考配置

逻辑矩阵 **128 × 16**；输入 8 bit、权重 8 bit，逻辑输入/权重分别为 1/1 Byte/element。完整输入 payload 为 128 Byte，完整矩阵 payload 为 2048 Byte；内部编码、位平面和维护不增加逻辑 payload。

所选数字 SRAM 参考实现；原生 MAC 完整周期采用有来源服务预算。

[输入、资源与映射](input.json) · [实际解析与模块返回](resolved.json) · [计算结果](result.json) · [阶段来源](stage_sources.json) · [方法与适用条件](../METHOD.zh.md) · [源参数引用和哈希](../../provenance/input_sources.json)

统一复算入口：`../shared/run_evaluation.py`。本目录结果由统一入口生成；十例主表与图只读[权威数据](../data/ten_case_results.json)。构建和完整 trace 留本地区。
