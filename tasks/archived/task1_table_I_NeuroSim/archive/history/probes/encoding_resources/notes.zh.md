# 十例典型输入与编码/资源探针

本目录仅完成 Step 2 输入规范和机制检查，不产生十例新性能表。十个配置位于 `../../configs/cases/`，版本为 `2.0.0`，状态为 `input_specification`。源数据锁定 NVM v3 `a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0`；每例保存原始 inputs、results 中的原生组织、calculator 及共享计量文件的路径和 SHA-256。结果文件仅提取组织/资源，未导入旧 rho、tau、完整装载时间或吞吐作为新目标。所有 JSON pointer 均由 runner 实际解析，calculator 仅读取，不调用 `--emit`。

运行入口：

```sh
NEUROSIM_REPO_ROOT="<仓库根>" python3 run.py \
  --root "$HOME/neurosim" \
  --out "$HOME/neurosim/runs/step2/cases-新的名称" \
  --cxx /opt/homebrew/bin/g++-16
```

该探针使用 Python 标准库，接受但不使用 CXX 参数。入口先把配置和探针复制到新本地目录并记录哈希，再从本地副本计算；管理区只读。不构造完整 NAND 矩阵，不加载模型。统一 runner 的 snapshot 布局也受支持：配置相对探针定位，NVM 仓库由 `NEUROSIM_REPO_ROOT` 明确传入。

## 规范语义

- `logical` 的 K/N 保持十例原生组织；权重矩阵顺序是 `W[N,K]`。输入/权重均为有符号 8 bit，每元素 1 Byte。旧 `b_S=b_R=1` 绝不是一位运算。完整矩阵 `B_R_Byte=K*N` 与小事务 `resident_transaction_Byte` 分开；输出容器为 `16+ceil(log2(K))` bit。
- `physical` 保留银行、平面、分层、访问方向、互补/复制以及有效容量。逻辑 K/N 不直接写进 NeuroSim `numRowSubArray/numColSubArray`。未构造的原生 RC 负载、延迟和间隔保持空值与具体缺口。
- `resources` 区分 installed、active 与原生资源记录。NOR/NAND 原生页内写并行未知时保存空值，不把 128 bit 端口说成 128 个真实编程驱动。MRAM 的 65536 个本地 IBMD 与 4096 个活动读通道、FeRAM 的 4096 个 restore BL 与 128 个外写 BL，以及 FeFET 的 288 个偏置节点与 128 个目标位分别计数。
- `service_schedules` 是顺序嵌套循环；`stage.count` 是该服务单位内的总次数。runner 展开循环核对总次数。RRAM 每次 RESET/SET attempt 后立即读验和 done 提交，所有事务共享一次 rail 进入/退出；PCM 每个 32-cell plane batch 后完成两次新读验；NOR 先擦 sector 再编页；NAND 先 block erase、逐 output-row 编码/数据页、参考页及最终校准；GC 逐 refresh group 读、解码、装入并重写。不能据平面 DAG 将这些阶段跨全矩阵重新排序。
- 完整本征周期是 opaque block，包括的感测、内部 verify、恢复或命令捕获只收一次。01 电荷前端保留；02 D6CIM 完整 HCA/BFA MAC 不追加通用读/ADC；03/04 完整页 P/E 不猜内部脉冲。GC-04 始终为硅 CMOS pseudo-differential 3T1C，不借用 IGZO 或 MLP hybrid 器件身份。

## 外围接口与未完成项

外围主政策为 `lv_v14_22nm_lstp_300k_v1`。低压 CMOS 用 V1.4 锁定快照、22 nm LSTP、300 K；原生器件偏置/负载独立保存，不将器件全体缩放到此工艺。目标周期 5 ns，实际周期须取目标与所用感测/组合关键路径的较大者，DFF 返回一周期本身不能证明收敛。

公共绑定已选择：`digital_tick` 来自 `lv_core.actual_period_ns`；`adc_batch` 来自真实 `SarADC::CalculateLatency(numRead=1)`；`input_step` 继续使用 v3 专用输入/复位预算。完整 front 已含输入建立的地方不再加一次。RRAM 二值窗口时隙继承 `T_B=T_A` 能力政策，但并非同一个 SAR 物理电路；PCM verify、NAND 校准与 GC refresh 的真实转换消费者继承同一 ADC 绑定。维护占用及不可抢占 guard 必须随替换时序重算。

SarADC 返回秒；DFF 同步返回 cycles；Adder 始终返回秒；AdderTree 同步返回向上取整后的 cycles，异步测物理秒。时间域转换只做一次，cycles 明确关联 clock_id。数字主路线为独立 Adder/AdderTree + DFF；ShiftAdd 自带 DFF，且 numReadPulse 影响内部容量，故只列比较路径，不机械设成 1 或叠加在主链。SwitchMatrix 的全局寄生依赖和混合单位写路径不用于默认替换原生选通/写驱动。

数字重构沿用 v3 的固定寄存到寄存 tick 计划，DFF 一周期是唯一计时来源；Adder/AdderTree 仅检查组合关键路径，不再加其同步向上取整周期。串接的组合逻辑延迟相加后再约束周期，不能只取各门延迟的最大值。端口阶段另显式乘每事务的数据/控制拍数；NAND 数据/参考页分别为 290/110 拍。

01/05 的 pilot 使用 10 bit SAR 码，移位/符号扩展后叶子容器为 `10+7+1=18` bit、8 输入 tree、16 路，23 bit 最终累加。128 个 SAR 码保留至两数字拍完成，不开始下一转换，也不增加中间 bank；若第二拍需重算 plane sum，tree 与最终 adder 的串接延迟一起限制该拍。数字感测例使用 32 个 8 bit 有符号叶子与实际输出容器。DFF 的输入、输出、operand capture 及事务/页暂存复用已声明资源。原生电容负载与电气收敛仍须 Step 3 实例化；本轮不宣称十例电路已经得到完整替换。

## 探针覆盖

编码检查包含 `0, ±1, -128, 127`、全部 INT8 补码回环、混合向量以及全部 65536 对 INT8 的 NAND split-sign/base-4 理想乘积。NAND 模型显式正/负权重 block、两输入符号相位、三输入复制以及 LSB 一份/MSB 两份 SSL 编码；不使用旧 offset 编码。

资源检查包括十例有效容量/物理位点、输入输出容器、页/块数量、NAND 48 bit 有效数据端口与 128 bit 参考页端口、PCM row-striped 唯一覆盖、互补编码装入量、GC 两数据拍、有限 ADC/SA/hold、实际写/恢复资源及偏置节点。尾批使用向上取整和实际有效 payload；扩大并行但没有 ADC/hold 的配置会被拒绝，缩窄 SA 会支付额外读批。理想编码正确性不等于 ADC 精度、器件状态裕度或网络准确率验证。

完整证据由 runner 写入本地 `summary.json`、`assertions.json`、`raw-output.json`、`commands.json`、`invocation.json` 和 `source_hashes.json`；最终报告由 supervisor 汇总。
