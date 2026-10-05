# Step4 V3 路线决策与源码入口

本轮从 `CIM_roofline@b7795fd5acc8f5f3816d1022111330fc569b6853` 接续，只有 `.DS_Store` 为已有工作区修改。实际本地根是 `/Users/shine/neurosim`；`NEUROSIM_ROOT` 未设置。三个锁定上游均核验 SHA 和干净工作树。未下载、迁移或改动锁定源码。

## 三个独立身份

- `ns_sram_acim`：Training V2.1 SRAM conventionalParallel。原生 WL switch、SRAM 单元与 BL/WL RC、precharger、MUX、SAR、ShiftAdd。不是旧 9T1C 电荷域前端。
- `ns_rram_1t1r`：Training V2.1 CMOS-access binary RRAM。器件参数来自锁定 MLPInferenceV3.0 的 `DigitalNVM` 参考包，仅借输入而不拼接其最终读写数字。不是旧 WH-2T1R 的分离 CIM/memory 通道。
- `ns_sram_dcim`：DCIM V1.0-dev 的 Type::DCIM 专用 NOR 与 256-input/4-bit AdderTree。`operationmode=1` 在 Type::DCIM 下进入该专用路径，并不等于普通 SRAM sequential。不是 DRAM，也不是旧 D6CIM MAC 时隙。

## 为什么没有机械统一到一个分支

Training 有可审查的读写聚合；DCIM 专用分支有其固有数字计算组织。统一分支会丢失 DCIM 的原生路径。两族均选22nm/LSTP/300K，但 Training 的32nm wire设置与 DCIM 分支22nm节点原生40nm wire/阻挡层模型不同，这些差异在解析值中保留，不能解释为完全同一工艺实现。

默认 Training 为 FeFET、32nm、5bit cell；仅替换 `memcelltype` 不足以得到本轮输入。每次新构造显式参数包，检查初始化后的实际值。DCIM 默认1nm、启用校准；本轮明确选22nm并记录校准政策，不能沿用标签猜测。

## 原生实现发现的必要修正

Training 的 SRAM 初始化缺少 access gate/drain 对 WL/BL 的阵列加载；相邻 V1.4 实现具有这些负载项。补丁在本例同一个 Technology/MemCell/SubArray 上计算，写侧不调用另一独立 SRAM 总时间。`SwitchMatrix`、`NewSwitchMatrix` 写聚合错误复用了按 `numRead` 算出的 DFF 时长，需要改按 `numWrite` 计。

Training 每个输入位进入一次 `CalculateLatency`。逐 MUX 预充／转换的 SRAM 服务每组都需 BL 建立；不能只收一次 colDelay。MUX 选择也不能无证据地除以输入位数。修正的是明确操作次数与状态变化，不把原生返回非零当作正确性的证据。

DCIM README 限制256×256；`SubArray.cpp` 的 `numCol/4` sense/precharge/write对象及四倍面积复制决定其四象限组织。专用计算为64条4bit权重树，而非65536个INT8权重；多位合并与符号校正必须有资源和时间。上游无完整写聚合，SRAM 存储负载及同对象写路径须补齐；同步 `(numReadPulse+1)/numReadPulse` 的整数截断须修正。

## 小而相容的器件包

[MLPInferenceV3.0 `Cell.cpp`（锁定提交）](https://github.com/neurosim/NeuroSim/blob/6098feabaf17/Cell.cpp#L630) 的 DigitalNVM 明确 `cmosAccess=true`、`isSTTMRAM=false`、binary状态、Ron=8kΩ、Roff=24kΩ、access=5kΩ、read=0.5V、SET/RESET各1V与10ns。本轮将其标记为上游参考输入，不能宣称它是一颗经22nm硅测校准的特定RRAM器件。该源的5ns readPulseWidth注释为由SA决定，不作为独立材料读时隙再叠加。

RRAM 非零HRS电导需要同阵列参考感测；只把电流除以LRS电导、免费认成整数popcount是不成立的。选每8个权重位配一个HRS参考列，再计原生Adder的基线减法。ADC转移函数及增益校准是明确数值条件；名义码宽不是实测ENOB。

## 共同数值与服务边界

共同 K=256、N=31、signed INT8。第32组unsigned权重固定1；两次完整8bit原生求值及三次有寄存25bit原生加减完成offset校正，见 [接口](../INTERFACE.md)。这是一项最小符号扩展，不是免费CPU后处理，也不是重新设计公共大门图。

主例采用请求间不重叠；原生内部ShiftAdd或DCIM流水按真实返回单位保留。写是全部物理位覆盖，SRAM不因新旧相等或训练平均变化率跳过。RRAM显式RESET/SET方向、有限驱动批次与同阵列验证。输入/写数据位于公开本地端口；已安装寄存、编码、捕获、返回compute-ready的边界计入。外部电源已稳定，level shifting不代表建模整套电源系统。

最终模型覆盖、数值、诊断与独立审查在正式报告中收敛；本文件记录路线理由，不宣布验收。
