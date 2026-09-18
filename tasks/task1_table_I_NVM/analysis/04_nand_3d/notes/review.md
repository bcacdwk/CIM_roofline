# 方法问题与复核记录

本轮只写`analysis/04_nand_3d/`，不改源PDF、共享基线、其他案例、主论文、Table II；没有网络检索或文献复制，没有Git暂存/提交/推送/分支操作。起点已存在的`.DS_Store`修改未处理。

## 同一基线

实际读取的共享JSON和脚本SHA256与主Agent给定值一致，完整记录见`data/inputs.json`。脚本通过importlib导入`acim_service`、`front_ns`、`program_sequence_ns`、`metrics`计算；`sys.dont_write_bytecode=True`避免在shared目录产生pycache。6组检查验证来源哈希、原生尺寸/逻辑覆盖、完整事务/单域、WL与求值不同次数、缺失输入不伪造、派生文件同步；共享12组检查亦通过。

## 证据闭合的层次

- NAND-04 pp.2–3提供原生CIM模型结构及WL/BL/SL组件时序；Table 1是模型估计，不是SLC硅测cycle。NAND-05 16-layer实测电流与NAND-04 32-WL参考结构保持分离。
- 108次等权复制来自13824/128的映射推导，最大电流27.648 μA、计数步长216 nA均由2 nA电流锚点换算；SL负载/响应移植条件尚待电路验证。复制没有改变输入bit数或有用payload。
- 数据页数1024与逻辑字节16384闭合；页bit片段不能直接冒充完整INT8事务。原生96页/block中，仅八页属于当前固定数据映射；校准页、未用WL/SSL都不增加擦除摊销的有用页数。
- NAND-05 p.2 II-(e)、p.4 Fig.12要求一或两个WL已知码校准；erase后需要重建。C_app/C_rw是每个**整矩阵事务的总校准服务时间**，非每块时间。新权重引起背面图案变化时append不能默认C=0。
- NAND-01 MLC/TLC、NAND-03 QLC和NAND-02 QLC产品SLC burst相对时间均不能给SLC-CIM细调终点的绝对P/E。数值tau/ridge保留null，提供操作系数及反推时间预算是当前有证据的结果，不是未填空表。

## 共享方法接入注意事项

现有顺序组合和例外规则已能处理下列问题，无需改变共享理论。

1. WL按输出组、BL/SL按input-bit求值调用，介质步骤可能需要不同重复次数；共享的组合接口能表达，但不能把所有时间塞入一个t_m后错误重计或无限摊销。
2. 存储原生页与完整逻辑resident事务不同；必须聚合足够的位平面与状态，分子才是完整INT8字节。
3. 擦除损毁校准/参考状态，维护页program和总校准服务必须计时，不能加payload；Np/e只能数实际有用服务。
4. 普通read/verify、CIM ADC和高压program引擎不一定同资源。本文保留page-buffer验证、CIM独立SL ADC与一个更新域，不把商品plane/die并行当局部能力。

## PDF检查

按PDF技能在首次创建前执行一次artifact marker。采用XeLaTeX生成独立6页PDF；pypdfium2渲染、接触表及关键页逐页目视复核。首次证据表的长JSON字段造成越界，已改断行与左对齐并重编译、重渲染；当前日志无Underfull、Overfull、缺字或未定义引用；NAND-02参考文献段仅作局部左对齐，原题名内容保留，未全局抑制告警。页序、公式、表题、参考文献及证据表均可读。

最终同一基线已确认。JSON/计算API未变；共享方法TeX只修正w_IO排印，最终SHA256为`b623299c49cc3f19a9bd41cdd324929dd166513cd36e0aaaba6adc402568b7b9`。重跑/编译确认几何、计数、三组读结果及全部resident系数不变；SLC P/E/C真实证据缺口继续保留。
