# 2026 3D vertical AND FeFET：二状态数字局部服务

本例采用 FENOR-02 的 SL-HZO／O-poor IGO 与四层 vertical AND 拓扑。原生参考逻辑矩阵为 **128×128 INT8**，32 条横向读通路、64 条带／通路、4 层×16 列／条带，共131072个二状态 cell；有效容量16384 Byte，无权重复制。每向量输入128 Byte，交付128×23-bit结果。

4096 个 SA将32×16×8-bit tile读入单个4096-bit保持块，跨八个输入位复用；完整求值32次物理读／捕获、256轮数字归约。外部更新采用一个域、128-bit编码接口；八个位平面条带共128cell同时写，288个实际偏置驱动节点，完整两相、含退偏的观察窗口、读回、一拍捕获和16通道八拍比较全部计入。终验复用同一tile bank，更新和streaming互斥。

| 相容条件情景 | ρ (MB/s) | τ (MB/s) | RI* |
|---|---:|---:|---:|
| 乐观 | 105 | 81 | 1.3 |
| 典型 | 47 | 60 | 0.78 |
| 悲观 | 23 | 41 | 0.57 |

MB=10^6 Byte。典型 `ΔS=2730 ns`、对齐16-Byte更新 `ΔR=265 ns`；1024事务覆盖整矩阵，`T_R=271360 ns`、`U*=T_R/ΔS=99.3993=128 RI*`。Table II映射使用完整装载接口，不能把小事务时间比或此宏门槛直接套到任意输出维度。

三个主情景使用固定 SA／保持／数字通道／写驱动额定能力，配对本地读20/40/80 ns、边沿5/10/20 ns和数字拍2/5/10 ns；写后观察均100 ns。每节点60 µA、总17.28 mA的固定参考驱动额定能力覆盖最快负载需求；典型7.68 mA为10 ns边沿需求。读与边沿均为工程预算；100 ns来自RAWD证据支持的保守选择，不是固有必需等待。

独立资源对照将写驱动减少为单条带16cell：完整16-Byte更新1770 ns，τ=9.04 MB/s、RI*=5.19，ρ不变。固定主资源仅将观察预留取150 ns时，ΔR=315 ns、τ=50.8 MB/s、RI*=0.923；该额外预留不混入普通悲观端。无周期refresh或破坏性restore，维护前后局部能力相同；耐久不折入瞬时τ。

阅读入口：[正文PDF](output/fenor_3d.pdf)、[正文TeX](tex/10_fenor_3d.tex)、[证据与原图定位](notes/evidence.zh.md)、[输入](data/inputs.json)、[未取整结果](data/results.json)。统一入口为[十例复核](../TEN_CASE_REVIEW.zh.md)及[汇总JSON](../data/ten_case_results.json)。主导因素为有限保持后的物理读／数字归约、八条带真实写资源，以及观察和终验占用。

从本目录复算：

```sh
/opt/anaconda3/bin/python scripts/check_fenor.py
/opt/anaconda3/bin/python scripts/check_fenor.py --emit
FENOR_PYTHON=/opt/anaconda3/bin/python sh scripts/build.sh
/opt/anaconda3/bin/python scripts/render_pdf.py
```

默认检查只读，`--emit`同步结果与生成表；所有维度经本例配置显式传入shared API。`native_configuration`保存物理/逻辑组织和资源；每情景`mapping_interface`保存完整装载的T_R、RI*、U*，局部事务字段与维护前后能力另存。源PDF和共享参数/API均有哈希。

外部器件／电路审阅仍需判断4096 SA与32项归约的负载/时序、SL+O-poor与O-0.1s组合、288节点多目标驱动和半选、100 ns观察及一次终验的充分性。算术复算和PDF检查不替代这些验证。
