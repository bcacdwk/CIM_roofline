# P2 最小公共端口变更清单

本文件只读NOR/FeNOR路线卡后形成，不改变已冻结P1接口/数值。P1二元数字保持、输入选择、25bit归约、比较/状态和独立构建机制可复用；P2不能把三端阈值器件换名塞入已冻结的ohmic1T1R请求。

|模块边界|最小需要|不能继承的假设|
|---|---|---|
|阈值晶体管前端|给state、选通状态、Vg/Vd/Vs及实际工作域的I–V/小型表；门/漏/源C、几何和共享节点；case compact模型解发展/漏电。|P1 `R_on/off+auto-sized access` 不等于存储晶体管阈值机制；静态V/I不覆盖偏置变化。|
|独立外围入口|直接实例化已修正native RowDecoder/MUX/VSA/DFF/Adder，用case实际gate/BL/SL负载；导出同样的初始化与阶段/时钟分项。|不调用RRAM写算法；不复制旧完整读access。正常负载必须来自阵列/层网络，不只剩DFF+ADC修补。|
|reference/sense|复用P1“native尺寸/负载→case真实data/reference瞬态→替换发展项”的边界；reference资源、sense threshold、offset要求明确。|低偏置的端点全差不能当单支reference margin；不可通过无限拉长恒ΔI时间越过不可达摆幅。|
|高/负偏置控制|数字命令路径仍可native；实际rail开关为独立额定端口，带输出范围、Ron或限流、C、上/下沿、返回/抑制范围。|低压native decoder、LevelShifter类名和稳态供电条件不保证±2V或更高rail驱动/可靠性。|
|装载与状态|共享serial stage聚合可复用，case提供页/扇区或逐层写/抑制计数；原语includes/excludes禁止重复verify。|原生RRAM两极性平均pulse、完整旧20/40/80ns读slot均不适用。|

**NOR。** ESF1分栅器件为180nm三端工作点，来源的gate输入4.2V与另一图2.7V存在需作者澄清的域差。新入口首先应支持固定读bias下的状态/电容/选通网络及实际参考。外围工艺必须独立声明，不能把180nm器件几何偷偷按45nm F缩放；原生没有相应节点时用真实m/F转换和明确驱动表征。候选128×128bit映射K128×N16；256B页buffer、4KiB专用扇区与8数据页可由既有stage聚合表达。W25Q tPP/tSE属于跨实现完整引擎转用条件；它们包括内部verify/泵/恢复，外部只加实际页接收/命令和不被包括的外围。第三情景不能凭空造更短P/E。

**垂直AND FeFET。** 先给二维端口probe，但正式选择仍是四层IGO/SL-HZO网络。需要显式layer_count、active_layer、横向通路数、每层state及off current，BL/SL共享负载和gate terminal电荷；layer数仅增加容量/负载与泄漏，不能成吞吐倍率。负读gate −0.5V及±2V编程/三分之一抑制策略由case网络逐类检验；native负载对象只消费实际C/选择控制，不把铁电gate pulse当通道I×t编程。四种half-select电场和真实返回范围必须入资源/状态检查。来源RAWD<100ns最多是明确的观察服务条件，与计算bias-return取max覆盖；不称材料强制100ns等待。

最小实施顺序：先新增独立 `threshold_port` native外围入口（不动P1 binary入口）和case物理端口response；NOR状态/负载probe验证字段消费；二维FeFET端口probe验证负gate/写gate语义；再接四层共享节点/半选模型。共用数字模块若只重用不改，P1无需全部重跑；若修正触及公共源，则更新checkpoint并只复跑受影响P1点。当前尚无P2新后端构建或服务结果。
