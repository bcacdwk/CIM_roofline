# 3D NAND：有限混合前端参考模型

三情景已实际新构建，待独立复核；计算快照 `f7b131fd97fbcc77a5d835066421d2f589f50d2007df661ec0b830ae9999080d`。不是原论文宏重现、精确INT8或材料速度极限。正式量为近似Q4服务能力，端口与工程组织条件如下。

K4608×N240，64 block×32 WL×3 SSL×13824 BL；30数据WL＋2参考WL。正负幅值分块、四个base-4位组、三BL复制与三SSL一元权重，共72物理cell/INT8权重。总84934656 cell，6144页（5760数据＋384参考）、64次完整erase。原实测源为16层；32层是保持紧凑参数的组织延伸，不冒称同源实测32层。

## 器件和外围各自承担什么

- `string_probe.py` 的EKV前向减反向电流串联求解每个GSL、storage/pass FET、SSL及内部节点。16层工作点归一到2nA，32层不再次归一。`string_ports.json` 是可重建的电气表征，不是旧性能结果。
- 64条SL各使用TIA及反相偏置buffer，共128个LTC6268式放大器。固定20kΩ/1pF反馈，Cin、有限DC增益、GBW、双向slew和offset进入实际KCL；buffer把负TIA输出转换到native SAR的0..1.1V域。原被动SL的背景反例保留，未用旧530–750ns时隙。
- 内部channel电容由显式几何给出约10.36aF/node；EKV实际节点微分导纳构成保守局部RC代理，reference的0.1%建立余量约292ns。不是用饱和电流V/I代替瞬态，也不是TCAD保证。
- native MLP负责实际BL负载/选择、低压地址译码、寄存、35bit加减和16路有限算术；Training负责64个10bit SAR。额定SKY130读偏置端口按既有I/C与负载预算，限于0..4.5V；完整20V P/E及read-safe隔离属于另一个明确条件原语。
- 放大器typ静态功耗10.56W；悲观Iq规格包14.72W。此混合前端资源不能被描述为原集成低功耗NAND宏，未开展能效优化。

## 服务组织与实际资源

初始400ns controller候选被实际409ns组合约束拒绝；统一改为500ns，三情景保持同一资源/政策。输入先经16路signed-to-magnitude编码到4608×9bit hold；32个输入digit/sign/group mask逐个生成并保存在13824bit BL mask hold，每个mask访问30条数据WL，总960次64通道阵列求值。

每组ADC码在16路35bit算术中完成offset、11步有符号串行乘法及舍入，再以8个输出通路完成base-4与正负合并。所有240个32bit输出保留。固定点码直接进入运算，不用点积真值校正。慢点主要来自所选本地数字组织，而非声称NAND材料本身只能这样慢。

resident阶段表按工作类型汇总时间，并非把全部输入暂存后再装载。实际次序为：先invalidate并erase全部64 block；随后每次接收一个4608权重输出行到41472bit staging，串行生成其24页；每页逐48bit packet送入8bit P/E端口，program/verify-ready后才重用buffer；当前行24页完成后才接收下一行。最后装入384参考页，执行2 reference WL×4 group×3已知输入等级的24组校准，计算256对gain/offset并发布ready。只有一个行staging和48bit formatter packet，完整page buffer归P/E引擎，无整矩阵shadow。

源SLC为2048+64B/64页block；目标为1728B/96页block。完整program 300/600µs与erase 1/3.5ms是显式跨实现条件，含内部pulse/verify/pump/recovery，不按容量缩放，也不重复内部verify。选定controller每500ns接收一个物理Byte，虽慢于源25ns最低周期但满足其时序；这是模型组织的主要装载瓶颈。

## 参考值、范围和精度限制

|情景|Δ_S (ms)|T_R (s)|ρ MB/s|τ MB/s|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|
|optimistic|37.8735|8.160085|0.121668185|0.135528000|0.897734674|215.456322|
|reference|37.8735|8.160085|0.121668185|0.135528000|0.897734674|215.456322|
|pessimistic|37.8735|10.163285|0.121668185|0.108815211|1.118117439|268.348185|

三点是同硬件的LTC规格与P/E有限政策包。optimistic/reference性能重合是controller量化与相同typ P/E的真实结果，不制造散布。reference约110ns达到TIA/ADC建立目标，2倍SL负载独立对照约196ns；真实同1024计数的两个inactive背景均为21 codes，而此前被动SL为82/55 codes。

**这仍是有限标定域近似服务。** 单个孤立string量化为0；nominal dense校准残差约2.9%，极端pass背景约+44%/−22%。两sign phase可消固定baseline，但不能消除所有状态相关gain差。采样10bit和输出Q4不等于ENOB，也不与二元数字案例等精度。数据范围、slot计数与被排除的精度结论随机器文件保留，不推广到任意网络准确率。

复跑：`python3 -B step4_v5/v5.py run --case nand3d --scenario reference --run-id <unique>`。全部完整trace/源码/二进制在 `/Users/shine/neurosim/runs/step4-v5/p4/`。独立review只需复核最终快照、主导计数/负载/状态与上述资格，按当前任务尺度不再展开全部微观签核。
