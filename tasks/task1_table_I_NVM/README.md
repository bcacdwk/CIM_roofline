# Table I · 原生 CIM 参考配置

本目录以文献支持的器件/阵列机制及共同28 nm外围参考政策，估算所选原生配置的streaming输入服务能力ρ、resident更新服务能力τ与RI*=ρ/τ。原生逻辑尺寸及有效容量由可计算映射确定，不统一为128×128或16 KiB；结果不是等面积或等计算量的技术排名。

## 当前入口

1. [共同方法与API](analysis/shared_baseline/README.md)：原生尺寸、保持与输出资源、ADC、真实写驱动、完整周期、维护及Table II接口。
2. [十例审阅状态与汇总](analysis/TEN_CASE_REVIEW.zh.md)；[共同计量和资源政策](analysis/TEN_CASE_CONVENTIONS.zh.md)。
3. [统一未取整JSON](analysis/data/ten_case_results.json)与[CSV](analysis/data/ten_case_results.csv)。
4. [正式三情景表与ρ–τ图](analysis/11_summary_figures/README.zh.md)。
5. [工作约定](AGENTS.md)、[文献目录](LITERATURE_CATALOG.md)、[证据覆盖](COVERAGE.md)、[来源清单](source_manifest.json)。

十例正文、输入、计算器、证据和独立PDF保存在`analysis/01_sram_acim/`至`analysis/10_fenor_3d/`。原始论文保存在对应`literature/`；笔记只提供导航，主要参数以原PDF页码、图号、偏置及测量/仿真身份为依据。

采用相容、固定组织的乐观/典型/悲观情景；组织和资源扩展、预擦除有限窗口、维护临界或不可行点另列。维护前与长期有效能力分别保存；完整擦除、恢复和终验不因payload换算消失。所有当前结果须结合审阅入口所列执行状态使用。

前端模式按偏置、负载、通路和建立/验收要求声明；同一参数的不确定性传播到全部相关服务。独立操作模式对照与共享参数敏感性分别保存。编码服务检查区分理想代数、实际分组后的名义量化及ENOB分辨尺度，保留ACIM近似部分和合同；原生吞吐不等同于任意INT8结果的精确可分辨能力。

NAND的[确定性量化诊断](analysis/04_nand_3d/data/quantization_diagnostics.json)暴露偏置重构的弱信号与抵消限制，部分正小结果会翻转符号。其主表数字保留为条件近似求值预算，`numerical_service_qualification`明确记录小信号资格未通过；计算检查通过不等于该精度资格已获确认。

Table II保持阶段入口的逻辑计数：单矩阵W[N,K]完整装载T_R、向量服务间隔Δ_S给出U*=T_R/Δ_S=(N b_R/b_S)RI*。原生宏向算子扩展必须重新检查输入共享、重放、分时及更新资源。

## 复算入口

```sh
/opt/anaconda3/bin/python analysis/shared_baseline/scripts/check_shared.py
/opt/anaconda3/bin/python analysis/scripts/export_ten_cases.py
/opt/anaconda3/bin/python analysis/scripts/check_ten_cases.py
sh analysis/scripts/build_ten_cases.sh
/opt/anaconda3/bin/python analysis/11_summary_figures/build_figures.py
/opt/anaconda3/bin/python analysis/11_summary_figures/build_loglog_circles.py
```

从本目录运行；生成器默认核对，`--emit`按各脚本说明刷新派生数据。PDF使用既有XeLaTeX和渲染入口。正式结果通过内部检查不代表用户已验收。
