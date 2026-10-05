# Step4 V4 独立审查

结论：**带明确模型条件通过**。九个主点及九个独立诊断均由新源码目录重新构建，完整服务、输入消费、资源、面积和图形检查通过；没有未处理的阻断项。这不等于硅签核、精确模拟 INT8 资格、用户验收或外部 ChatGPT 验收。

本 reviewer 为本轮新启动的 `/root/v4_reviewer`，未编写生产实现，也不是 V3 reviewer；本线程无已知历史工程参与。审查提出的修订由 supervisor/case agent 实现。规范源快照绑定仓库 HEAD `752d7329d031d3b341df4f60971f8a65191fb54d` 及27个规范文件的 SHA-256，而不是仅依赖 Git HEAD。

## 独立重构建和依赖

仅 V4 独立包：`/Users/shine/neurosim/runs/step4-v4/reviewer-independent-20261005/only_v4`；完整运行：`/Users/shine/neurosim/runs/step4-v4/reviewer-ninepoints-20261005`。包内没有历史 results、pilots 或 replay。实际执行 `--case all --scenario all --diagnostics --plots --no-export`，18个源码/二进制目录全部新建；九个主点和全部原生 raw 字段与 supervisor 的 `/Users/shine/neurosim/runs/step4-v4/reference-v4-20261005` 完全一致，且双方规范输入快照相同。

独立 Python audit hook 覆盖入口、worker、后置数值与作图脚本的真实 open/subprocess 路径，没有发现历史结果依赖。另核对所有 compiler/executable 命令、源码路径和二进制哈希。它是 Python 审计及构建命令证据，不冒称操作系统全量 syscall trace；锁定 NeuroSim 上游源码仍是必需依赖。构建仅保留上游 NULL 作为数值0的转换警告，没有编译错误或原生运行错误。

## 九个成对主点

B_S=256 Byte、B_R=7936 Byte；同一请求不重叠，单次 latency=Δ_S。速率为十进制 MB/s。下表是条件模型返回，不是统计区间。

|架构|温度 K|Δ_S μs|T_R μs|ρ MB/s|τ MB/s|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|---:|
|SRAM ACIM|300|1.83101565|2.00828886|139.813114|3951.62278|0.0353811893|1.09681687|
|SRAM ACIM|350|1.98960188|2.6026923|128.668957|3049.15029|0.0421982996|1.30814729|
|SRAM ACIM|400|2.17541132|3.31823206|117.678895|2391.63502|0.0492043702|1.52533548|
|1T1R RRAM|300|39.7768474|434.378778|6.43590472|18.2697692|0.352270719|10.9203923|
|1T1R RRAM|350|51.9450432|543.972813|4.92828544|14.5889644|0.337809135|10.4720832|
|1T1R RRAM|400|66.350365|674.95407|3.85830583|11.7578371|0.328147583|10.1725751|
|SRAM DCIM|300|0.147879789|2.91209431|1731.13582|2725.18647|0.635235732|19.6923077|
|SRAM DCIM|350|0.189959634|3.74074357|1347.65473|2121.50335|0.635235732|19.6923077|
|SRAM DCIM|400|0.24023043|4.73069154|1065.64352|1677.556|0.635235732|19.6923077|

独立脚本从原生分项重新组合服务，未导入主 evaluator：ACIM 一个外部输入 capture、两个完整8bit pass、公共校正及完整256行覆盖写；DCIM26个求值周期、512个完整装载周期与模拟写路径的真实完成边沿；RRAM原生bank求值、每pass512beat gather、staging、native tree、Q4校正，以及2304beat装入、4608脉冲、512次行验证、全部收尾。全部满足ρ=256/Δ、τ=7936/T_R、RI*=ρ/τ、U*=T_R/Δ=31RI*。

## 输入与资源确实进入模型

JSON唯一解析输入生成request.h并替换Param构造器。独立检查实际温度、金属电阻、源文件构造值、原生尺寸、ADC和写口资源，并验证未知字段、错误逻辑形状/位宽、越界温度与小于2的时钟预算被拒绝。三主情景除温度外的请求完全相同；温度分别为300/350/400K，线阻倍率为1/1.2255/1.451。WL TG、RRAM access/MUX等实际尺寸随原生模型变化，因此不能称同一芯片PVT；350K为选择的warm reference，非median。SAR公式保持源码固定值，不添加没有来源的温度响应。

ACIM保持256×256bit、32个9bit ADC、MUX8和256bit写口；DCIM保持256×256bit、64棵256-input/4bit树及4×64bit并行写外围。RRAM是16个16×288bank，共512 ADC；每bank一个288bit目标缓冲，12,288bit全局partial staging只存求值结果，不是权重矩阵shadow。输出经真实native AdderTree和29bit signed correction，Q4在ADC差值后不提前移除。两pass的A/C、B/D保持和最后全WL归零均已核对。

RRAM最终连线为16条读向point links、16条写向broadcast branches及hub选择，外部写口仍32bit。512个staging D-pin/bit、每bank9个写D-pin/bit、16link root输入负载均计入实际驱动。每轮和最终布局重算所有依赖对象；300/350/400K实际面积分别约4.788/5.179/5.595mm²，分项和真实容纳于固定规则的近方形布局。这些是原生宏布局估计，不是提取版图，也不能用于等面积或最优架构排名。

## 实际发现与修订

- 一位RRAM相位选择曾使用numNand=numNor=0的RowDecoder，同时保留无条件MUX门链，面积和负载不自洽；最终改为有负载、RC和面积的互补INV选择。
- MUX enable NAND2串联电阻、前级所见driver输入电容、NOR真实输入数和driver面积已一致。ADC名义码与验证expected码由实际输入重新派生。
- 奇数地址位的直接NOR扇出在原生Power计数中存在，却未进入Latency。独立C++探针显示350K staging odd位负载122.351fF，而原计时paired负载仅0.418fF。最终使用真实最大地址负载，保留原串行门链作为保守包络；staging decoder实际返回9.934ns。它不声称精确STA。
- ACIM修为一次外部输入接受、跨两pass保持，避免无契约的第二次外部重采样。
- RRAM早期布局最终tree面积改变后未重新迭代，实际分项超过包络12%–14%；最终版本每轮及末次都重新计算，已闭合。
- RRAM方向连线、hub和端点负载从原来的未明确共享Bus语义改为明确的实际资源，并进入两路服务。

独立因果诊断还验证：driver55使真实driver宽度、前级电容和面积变化；wire扰动进入各真实金属与阵列电阻；20ns脉冲仅使resident增加4608×10ns；两次尝试需求增加实际编程/验证，不重复装入行数据、不改变硬件或stream；read activity改变读RC，不污染固定完整写。它们是分开的诊断，未混入主九点。

## 物理与数值资格不能升级

SRAM ACIM的256WL读稳定性、模拟transfer和9ENOB仍未验证。更合理的MUX驱动只修正时序量级，原NVM特殊电荷域/隔离读口宏不能为stock parallel SRAM提供这些资格。

RRAM采用generic8k/24kΩ器件、5kΩ access、0.5V读、1V10ns编程和显式1.1V access条件，不是特定22nm实测材料包。低阻稳定read rail、名义ADC gain和有界program-verify成功是必要条件；失败不发布compute-ready。LevelShifter仍是同技术低压公式移植，电源/高压可靠性不在本地服务资格内。

独立远端等效电阻递归法复算了linear ladder，未调用主三对角solver。每温度检查全部65536个full-active HRS/LRS布局及65536个all-LRS活动布局，16row主设计最大已检查count误差0.677692/0.748616/0.818938。它不是所有3^16状态、噪声或非线性器件的穷尽。V3长列256row的wire-only dense count约49.4377也由新输入重构复现，没有读取旧结果。

更关键的是完整近似输出：独立ladder求解加直接位权重重构逐项复现最终有限向量诊断。满正幅输出相对误差4.296875%/4.6875%/5.078125%；signed_cancel真值为0时残差16891/762/889；mixed中非零小真值最大相对误差11.625/4.78125/2.80208。**因此Q4只是格式，29bit只是容器，时序optimistic也不是精度optimistic；该参考不能当精确INT8或弱信号工作量的硬件资格。** 没有把拟合端点增益或CPU校正免费加入性能模型。

须拒绝候选材料中的一项早期错误说法：无饱和理想线性half-up量化满足Q(a+2m)-Q(a)=2m，分数HRS baseline本身不会使V3理想两codes/count失去整数精确性。真实问题是分布线阻破坏理想线性，固定2/4码也不是任意变更输入的通用接口。V4的13/29和Q4是新的分bank近似设计。

DCIM的名义数字算术和状态保持通过；公共时钟采用50%组合预算及原生捕获抽象。三例都不是晶体管/clock-tree/完整提取寄生签核，也没有据此承诺网络精度。独立复核按具体覆盖机制报告，没有用assertion数量替代物理模型覆盖。

## 图形与可追溯证据

从独立九点重新生成三张PNG和对应SVG。独立几何脚本用单位法向量重构圆，直接解析SVG中的九个真实marker坐标与颜色，并由实际轴显示框核算等log10比例及RI*=1的45°线。全部原点、paired_id、圆端点、reference包容及完整显示吻合，无fallback。三张最终PNG已逐张查看，无裁切或碰撞，且与主run同名PNG哈希完全相同。最终输出没有PDF，未宣称PDF QA。

详细机器结果：[review.json](review.json)。核心独立证据为 [服务](independent_services.json)、[输入链](independent_inputs.json)、[因果诊断](independent_diagnostics.json)、[依赖与fresh build](independent_dependencies.json)、[实际SVG几何](independent_geometry.json)、[物理向量](independent_quantized_vectors.json)、[视觉QA](visual_qa.json)。自写脚本、原C++ odd负载探针及所有完整本地运行保留在reviewer目录；由supervisor白名单导出小型证据。审查完成后停止于本轮V4，不自动进入Step5。
