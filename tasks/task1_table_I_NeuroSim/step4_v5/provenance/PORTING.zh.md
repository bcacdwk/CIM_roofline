# V5 P1 移植记录（初版，独立复核待完成）

原始上游均只读。公共正式构建从锁定 MLPInferenceV3.0 `6098feabaf17b8209a8edbef4a9c963b5f015132` 提取必要源码到独立目录，补丁只施于副本。原 Param 构造函数保留，实际 `processNode` 在唯一 request 输入处赋值后再构造电路；不使用 MLP DNN/训练执行。

1. **阵列感测电容接口**：原 CMOS-access digital path 的 VSA 仅传 wire-only `capBL`；本轮明确采用读列包含 access drain 的1T1R映射，改传已经Initialize得到的 `capCol`。`mlp_binary_column_load.patch`范围仅此端口。实际原始/修正C、VSA及原始诊断均导出，不宣称适用于任意存储器拓扑。
2. **译码器一致性**：原1bit `numNand=numNor=0` 却计MUX NAND链，且面积包络可为零。`mlp_decoder_consistency.patch`把此路径改为真实两级互补INV，含面积、前级/后级负载与最坏路径；同时修正实际NAND/NOR串联数、odd地址扇出和末级driver前驱负载。多位路径仍为保守串行包络，不是精确STA。当前目标是面积/时延；未把未使用Power路径升级为能源签核。
3. **写返回并非驱动RC**：原 `DecoderDriver::CalculateLatency` 的 `readLatency`计算TG/线RC，而 `writeLatency=cell.writePulseWidth*numWrite`。本轮材料pulse=0时后者自然为0。V5导出 `write_column_driver_native_pulse_proxy_s` 保留证据，写控制edge改用同一TG在相同负载/原生bias下真实计算的 `readLatency`。这只覆盖低压控制选择/建立，**不证明热写或STT写电流、program rail下的Ron/headroom、高压可靠性和供电**。这些仍由案例独立原语/能力条件负责；材料脉冲不从这个RC推导。原native中的write_mux×2是两步写计数，不自动代表物理上升/下降两edge；外层按实际setup/release另计。
4. **binary reference与sense阈值**：VSA `voltageSenseDiff`接受权威 `sense_threshold_V`；这是明示的工程感测要求，不表示平台预测offset/noise。原端点 `I_on−I_off` 与被动端点峰值仅诊断。案例必须从真实data/reference网络及原生实际C求阈值到达时间，以该compact发展项替换原线性发展项；保留原生内部预充与enable，不重复收费。所有reference支路和匹配C都需计量。
5. **低read-rail预充**：不能把native Vdd下的PMOS Rpre直接当0.1/0.2V源、0V gate的可导通PMOS。V5采用显式NMOS低rail端口，gate=原生Vdd，检查 `Vdd−Vread−Vth>0`；以native等效Ron乘overdrive比 `(Vdd−Vth)/(Vdd−Vread−Vth)` 的紧凑关系计算驱动能力，保留额外drainC、data/reference两组支路、控制扇出/驱动面积及到声明误差的RC。它是最小模型扩展，非提取SPICE。外部预充可与已保留的native预充时钟相位并行取max，再保留enable相位；不得把全部外部C藏进原capS1局部预充时间。
6. **状态与数字外围**：实际新增25bit加/减、全输出组保持、移位/反馈MUX、input行/bit选择、weight hold、8bit差值加OR零检测/sticky/status/retry。每row显式WL enable NAND+INV及扇出驱动，使预充时访问管全部关闭；setup/release/面积有单独输出。原native短位宽unsigned归约保留原始分项，案例不能免费当25bit MAC，也不能把闲置native归约再计一次。
7. **时钟与无效门**：组合最长实际路径输出半周期保留约束；不是DFF完整STA。初始100MHz合成探针被约24ns最小period门拒绝，不能为了速度保留。错误文本、退出码、必需正值、有限性共同检查；Training40nm不支持时曾exit(0)，失败现场保留。

API v1 基本字段/函数固定；后续只修实际发现或为独立专用端口加入有界扩展。P1 reference/三情景和review会绑定最终规范文件哈希，不能把本记录的构建成功当最终服务验收。

8. **P1功能闭合修订**：原第一批候选尚缺zero mask、加/减结果选择、分组/分beat保持选择和被动reference预充隔离，现都以实际gate/MUX/驱动和寄生实例化；这些早期候选不得作为最终服务点。共享字段见PROBE_API末节，数字最长组合路径按最终连接负载重算。固定reference在预充期直接接地会产生分压；新增每SA隔离TG，OFF预充、ON发展、VSA latch后OFF，参考瞬态必须采用真实R/C并检查匹配C非负。functional_probe实际使用布尔门/逐bit加减和寄存保持，对故意去mask或去hold的反事实会失败；不将CPU dot一致性升为模拟准确率。

外部UMEM `1.0.1@3cd6275284951b8033c9637bd8094ec05b716a4b` 已登记到V5独立依赖锁，原参数/源哈希和符号约定在MRAM专用model.lock，MIT notice随独立case包复制。模型符号约定与手册图示差异不静默反转，也不升级成实测MRAM06器件包。

9. **单行MUX／真实write route与enable匹配**：作者实际80ns运行被983.6ns（PCM）/530.4ns（MRAM）数字period门否定，定位为digital sequential仍按`Ron_total/(2*numRow)`尺寸化readMUX。`mlp_single_row_mux_and_write_target.patch`仅修CMOS digital非parallel模式，以一条真实选中行和明确IR比例设计；parallel旧公式不变。该变化重新计算真实串联R、W/C/area与sense，不能被叫末端延迟缩放。write TG另有独立R目标，PCM旧2625Ω×0.5mA=1.3125V的已知超额不能隐藏于externalengine；目标重选需进入真正program网络及原生实际能力门。OFF写TG的两个drain在read端仍存在，已传播到sense/precharge/referenceC；写驱动自身输出C与其它连接C分别计一次。

原先dataWL与reference控制约32ns/4ns不同，简单取max会导致ref提前放电。现用与WL相同enable NAND/INV结构及匹配WL总C/线RC的replica，address先建立，共用enable驱动并计dummy扇出/门面积与匹配C；referenceN分支导通，P门保持Vdd，实际N宽增大保留目标R。step-port模型的名义开启对齐，未宣称真实模拟ramp/skew为零；作者须将残余条件/有限margin检查写入资格。此前过度MUX、未计writeOFFC、未匹配enable候选全部保留本地并从正式资格中排除。

10. **独立review要求的clear修复**：B组只读复核确认generic DFF没有reset引脚模型，old/new keep MUX与weight zero-mask不能清旧accumulator。现所有输出、sticky/status/retry的最终D口有实际NAND+INV clear门，active-low控制buffer驱动全部fanout，正常数据路径也重算其负载/延迟。不是新增完整控制框架。案例必须在MAC前与首次resident program/verify前初始化；one-clock标签只有在真实clear路径满足该周期时成立。functional_probe以非零旧值/连续请求运行，故意去clear会失败；旧只从全0开始的局部PASS不升级为完成服务证明。

### P2 positive lower-rail threshold controls, 2026-10-05

仅新增隔离的 threshold_port_probe 路径，不改变 P1 kernel/patch/hash。原生
RowDecoder 只做地址选择，显式 NAND global-enable 与按实际 WL 电容加载的低正电压
INV 负责全 WL 关闭和开启。低电压 PMOS 以原生 W/R/Vth 作一阶过驱动端口扩展，
不是原生高压支持。增加 read-rail PMOS 预充及完整 N/P 参考隔离 TG；分别导出两侧
寄生、两个控制沿和参考内部初态。参考固定电阻/匹配电容属于架构资源，不是
Flash 中间态。原生 VSA 仍只作为局部感测外围，实际 FET/gate-ramp/reference
瞬态与有效域由案例紧凑模型负责。首构建的 currentOnN/P 字段名错误仅编译失败，
修为 MLP 实际 currentOnNmos/Pmos 后在新目录构建，失败现场保留。
