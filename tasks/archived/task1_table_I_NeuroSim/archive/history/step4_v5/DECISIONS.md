# V5 决策记录（追加）

## D001 · 2026-10-05 · 本轮授权与生产责任

采用用户V5任务书，历史AGENTS原文保持。Supervisor不写生产代码。公共维护者为integrator，案例各有独立owner，reviewer不参与被审实现。拒绝把历史“supervisor唯一生产作者”扩展到V5。

## D002 · 2026-10-05 · 配额与第一组委派

平台只允许root外三名agent并发，已真实启动integrator、pcm_author、mram_author。PCM/MRAM先交短路线卡释放槽，随后立即启动NAND预研与独立边界review，其他四例路线依次轮换。该轮换执行用户第一组全部职责，不虚构同时存在的五个子agent。

## D003 · 2026-10-05 · V4继承的资格

只读继承V4九点及其条件性身份；300/350/400K是固定架构自动尺寸化的热设计情景。ACIM多行稳定性未认证、RRAM Q4模拟误差与供电条件、DCIM数字预算均不得在V5总览升级为等精度硅结论。V5情景围绕各器件主导输入选择，不机械复制三温点。

## D004 · P0 · 实际线程上限与独立性

首批MRAM返回后尝试新建NAND agent，平台实际返回 `agent thread limit reached`。因此三个现有子线程轮换职责：integrator仍唯一公共作者；pcm_author先审公共边界和MRAM路线（不审自己PCM），mram_author先做NAND预研。后续案例按两组分配，最终分组交叉独立复跑，任何作者不审自己参与的生产实现；共享代码由未写共享实现的案例作者审查并披露参与。若出现交叉生产参与则另行隔离，不能用名称变更制造独立性。

## D005 · P0 · PCM身份与证据约束

同源40nm TiSbTe候选优先二元电流感测＋真实数字归约。拒绝用宽阻态分布支持精确模拟popcount。作者实际PDF图核查发现DC_SET与PULSE_SET不同，脉冲SET/RST分布存在跨器件重叠；因此只能研究有终验接受窗口的有限成功服务，失败不计payload，不推定良率。低读偏置如非原文测量必须标工程工作点并检查适用域。三情景可用来源支持的脉宽政策，rho相同合法；没有来源的尾沿/冷却不得猜测拆分。

## D006 · P0 · MRAM写资格

同源低偏置P/AP电阻和准静态阈值不能产生纳秒双向写波形。旧特殊宏20/30ns access不得补入。P1允许继续寻找相容公开STT紧凑模型形成明确model reference及有限成功条件，不要求假称实测典型；写电流/脉冲和完整验证未闭合前不发布正式点。

## D007 · P0 · 外围节点与成功退出码

真实smoke发现原生Technology不支持40nm且错误分支可能exit(0)。保留失败现场，使用受支持45nm/LSTP做外围工具链probe；与40nm材料来源明确分开，不称同工艺宏复现。构建/运行质量门同时检查错误文本、必需结构输出与物理量，不能只看进程返回0。32-DFF smoke是工具链资格，不是案例后端完成。

## D008 · P0 · 案例与交叉review分组

计划A组由pcm_author负责PCM/NOR/FeRAM，B组由mram_author负责MRAM/FeNOR/GC/NAND；公共实现仍仅integrator。A审B、B审A，各自使用新源码/构建/运行目录并独立重数。公共边界和模块由两位非公共实现者审查；最终报告逐项披露曾参与的案例。源代码建议/缺陷报告可以交维护者修复，但reviewer不直接写被审生产代码。

## D009 · P0 · NAND的资料资格

作者核原文发现引用链的32层实验说法与被引原文16层64Gb不符；32层必须标组织延伸。2nA/0.2V工作点不能给出饱和string的小信号gds。新增3D-FPIM候选含可研究寄生公式但模板几何有FIXME、且50nA时间编码不同身份；不能移植完整时间。已有signed映射/页数探针只通过组织计数，不证明端口动态。P4继续尝试有来源小网络/端口表征，真实缺口单列。

## D010 · P0→P1 · 七卡与实施门

七例路线/来源账本均已由对应作者实际完成；公共边界经独立新快照修复复核PASS，仅限契约。PCM/MRAM读/端口可实现，参考写与物理资格仍需P1闭合。允许公共真实array探针与作者源证据闭合并行，不等待已有缺口自动消失；这不发布任何正式点。其余四例路线待后续对应独立review，先明确依赖与缺口。

## D011 · P0 · 特殊机制与资源

NOR/FeRAM候选缩为明确K128×N16、128bit服务域，属于新参考组织，避免免费沿用4096路；实际并行仍须电气证明。NOR ESF1读点与商品P/E引擎属于跨实现条件转用。FeRAM 14ns是完整写标签，不能拆每极性。GC_3T1C源码状态初始化/写更新缺陷和`Read=V*G`不支持GC04状态物理，只借相容外围；400us的原测量温度未给，99.7%/原LSB条件不能升级全bit保证。FeNOR RAWD<100ns不是固定额外100ns材料等待，观察窗口与端口return的包括范围应单列。

## D012 · P1 · MRAM相容模型替代

接受B组继续移植公开UMEM 1.0.1同包电阻/双向临界电流/时间状态模型（作者报告SHA `3cd6275284951b8033c9637bd8094ec05b716a4b`，由集成登记核对）。这是deterministic model-reference，不和MRAM06的40nm实测均值拼接，不提供WER/热噪声成功保证。原校准实验与作者模型来源资格分列，两个写方向与读扰应在同模型中检查。

## D013 · P1 · 感测reference与摆幅

公共全Ion-Ioff差分probe不足以证明single-cell/mid-reference每支裕量。PCM实际构建已揭示这一边界，100mV默认阈值不可通过单纯加时或无来源提高读bias绕开。可研究显式低阈值感测并披露offset/噪声条件、相容读工作点，或显式互补编码并完整计两个物理单元/读写/verify；任何设计变化修改实现身份，不能免费安装reference。PCM高热写电流导致大access与pitch/列负载的实际代价保留。

## D014 · P1 · UMEM约定与读域

MRAM作者发现源码与手册实验图的电極极性约定不同。保留原源码状态/端口方向，显式报告model electrode convention，不称直接复现实验极性、不混翻参数方向求快值。原Carboni实验采用沿前次program极性的读偏置；固定读可作为经模型检验的预测工作点但不能称该实验已验证。若选择依赖前次极性的硬件策略，必须实际计端口/状态资源，禁止免费全矩阵shadow。数值收敛、反向pulse与读扰探针是P1必需证据。

## D015 · P1 · 公共v1闭环与写边沿

完整外围v1已实际构建，立即交案例作者成对运行，不为通用化延迟交付。使用实际本域时钟门；默认10ns被合成路径否定时必须选合法周期。MLP DecoderDriver.writeLatency实际是cell.writePulseWidth代理，不可当TG RC；公共维护者另记录同TG负载的选择边沿，并披露电压/headroom/控制路径适用域，不将其称完整高流编程driver。source pulse原语与选择RC只按未重叠覆盖计费。

## D016 · P1 · MRAM实际写路径与身份冻结候选

B组实际加入Vgs源极退化与wire后，理想1kΩ下短脉冲成功不再成立，反向160ns失败/320ns才翻转；据此选固定资源500ns/1us/2us的完整状态求解政策候选。不是对总时间缩放，非统计概率。候选新身份K64×N64、8个64×64二元MTJ bank、65nm外围1.1V gate、96F pitch；每SA 12kΩ匹配C工程reference，5mV门限/2mV误差预算条件。与旧2T2MTJ及P0候选规模分开，全部bank/写lane及参考资源须正式账本验证。

## D017 · P1/P2邻阶段并行

P1公共v1冻结到`provenance/p1_api_checkpoint.json`，作者分别运行完整服务。公共维护者可并行实现隔离threshold_port三端外围probe，依P2_PORT_REQUIREMENTS，不修改P1架构或将裸FET套RRAM auto-access/write。这样利用等待案例模型/运行的依赖空档；P1修复/集成优先，触及共享原子才重跑受影响回归。此并行不跳过P1独立review、不发布P2正式点。

## D018 · P1 · 数字功能缺口必须修后重跑

公共自查指出25bit shifted-weight MUX只有bit位置选择，缺input-bit=0的mask门及Adder/Subtractor输出到accumulator的选择MUX。CPU signed-vector等式不能替实际硬件。必须补真实门、控制扇出/负载与clock，并检查同一图input/weight/sign/feedback功能与保持；旧候选数值保留但不验收。修后更新共享hash，两作者全部三点fresh构建，独立review绑定修后包。

## D019 · P1 · 参考隔离与局部回流条件

固定reference预充时必须实际隔离地，否则分压会使假定初态不成立；公共补真实TG/driver/R/C及开关生命周期，两例受影响重跑。仅单access可驱动及总电流限额不证明细SL能承载共享回流：MRAM候选显式上层SLstrap并将IR带入同状态求解，PCM依自身热写布局检查，不抄同尺寸。三情景保持该硬件固定，几何/RC/压降/电流导出。允许未被局部物理否定的明确稳定rail/失调条件，不追求全芯片PDN/STA；已知失败不可conditional包装。

## D020 · P1 · 单行MUX尺寸与独立写TG

两作者修后真实运行都拒绝80ns clock：PCM group-select约492ns、MRAM约265ns，因MLP `digitalModeNeuro && !parallelRead`仍按Ron/(numRow×2)并流目标自动尺寸化。批准仅该单行模式改activeRows=1，保留同源/2目标；原过度尺寸化对照/失败不删。实际readMUX R增加、动态reference裕量、面积/负载与clock必须全重算，不单独缩末时延。

PCM独立写colDecoderDriver约2625Ω在0.5mA下压降超过native1V，不能拿readMUX替代或仅查access Ion。公共新增明确write-route目标并实例化真实W/C/area/driver/edge，作者提供对应电流/端口合规，MRAM不必沿用PCM粗驱动。外部current engine覆盖边界仍独立，不由低压端态R推热态program电压。

## D021 · P1独立review · 真实清零与未感测BL

独立review确认accumulator/status/retry清零缺门，功能检查从零初态不能证明跨请求状态正确。必须计真实清零门、控制负载与周期，并用非零旧请求/失败状态连续检查；不能以Python重新赋0替硬件。PCM WLon下未感测64BL仍可能通过历史电荷产生source电流，不能假设免费停车；case网络加入残留0/readrail与LRS/HRS端点，MRAM同类结构同步核查。所有受影响点新构建，修前候选不通过。

## D022 · P1 · PCM高压返回路线与阻断出口

PCM source只给current waveform，未给hot BL terminal voltage/compliance；post-program不能自动套read历史0..0.2V界。允许A组实际尝试有来源的独立额定HV isolation/return/clamp紧凑端口，V/I额定、R/C/切换时间须有公开表征或可复算模型，资源/读C/时间全计，native1V TG不能冒高压支持。工程compliance上限与source pulse是否在该域联合验证分列。定向核原文/补充及一条替代，若仍缺足够证据则正式resident blocked、read部分保留，不用无来源clamp凑tau；其他案例继续，不让单例拖停。

## D023 · P2/P4 · 无实测校准与真实阻断的界线

用户允许无实测校准、边界明确的参考模型，不要求全TCAD或唯一辨识性。FeNOR/NAND缺直接gds曲线不自动blocked；须实际尝试机制相容、有来源物理方程/参数的紧凑I-V/C网络，工程假设与标定点公开，以另一状态/负载/几何或独立物理极限交叉检查。测量bias未给不能称唯一提取/原实验复现，同拟合点不能兼作验证。只有端口域、电场/状态/泄漏/动态自洽且不与证据冲突才可条件性model-reference；核心参数仍任意或无支持物理模型则blocked。不能为21点凑数，也不能将缺少完整材料签核误作用户未要求的停止门。

## D024 · P1独立review · DC校准与两态IR边界

MRAM native R_eff含CACTI系数（65nm此点1.77×VDD/Ion），只用于尺寸/时序，不能直接当零VDS微分R。B按实际W/Ion/Vth统一access/readMUX/writeTG/reference-N-only的饱和锚紧凑模型，原R-matched仅敏感性；不改变资源，不称foundry I-V预测。物理局部检查通过后所有三点新hash重跑，完整clock slots可掩盖微小delay变化。

P/AP不能共用单向“最坏”source IR：独立quiet reference下，最大source rise对P不利却可能让AP更有利。最终P采用64列最大初始电压固定负载上界，AP采用0-drop下界，各自检查捕获/共同窗口和全WL读扰。sidebound-final三个新构建使用相同最终模型，原候选仅保留历史，不沿用旧审查PASS。

## D025 · P1/P3 · PCM全HV与GC规模修订

PCM列端HV隔离仍不能保护每个关断LV access drain。A取得真实3um/.5um SKY130 HV访问样本后，继续全HV-access新1T1R参考属于用户授权范围；旧45nm-access identity和其read-only审查保留，不把未完成重设计说成材料绝对不可行。全新geometry/C/WL/BL/driver/return/current-compliance与服务必须重算，不追最小面积、不偷沿用旧资源。

GC原100ns clock被真实数字连接路径否定，至少172.77ns故用200ns。若完整事件轨迹证实K64N64在400us内不能容纳维护及完整请求，可改K64N16、16384cells、8planes及128pair并行的新宏；保留失败设计与新implementation_id。这是架构收缩，不是快角；不扩大保持域，真实离散调度决定有效rho/tau，允许样本非单调。

## D026 · P3 · FeRAM保守观察政策

允许以同源Fig10 100ns观察域推进保守read-dwell参考，不称材料常数、快速动力学识别或NeuroSim预测。A选择在实际稳定bias后另等100ns，明确这是额外保守服务政策，不把原波形内建立再宣称收费；原图100ns起止/包含范围仍单列。电荷模型、实际HV驱动、感测、全破坏域保持/恢复仍独立闭合，Fig12只作非拟合电荷/面积检查，不作速度验证；旧8/20/50ns完整读预算不回填。

## D027 · P1 · MRAM内部验收

接受`reviews/p1_mram`的最终PASS_conditional_model_scope，sidebound-final input/case/UMEM/kernel哈希与最新统一fresh集成匹配。三点可以进入条件性总表，保留WER/良率/噪声/STA及体效应/速度饱和未校准条件。此为内部独立审查，不代表用户或外部ChatGPT预验收；P5仍须绑定最终全局包复跑。

## D028 · 最新用户收敛指令 · 数量级优先

用户明确不要过于死板/严格：目标是solid数量级范围，不要求每处严格闭合，NeuroSim也有bug，token和时间有限。已真实通知全部三名子agent并收到执行回应。此指令优先于此前过细的执行习惯：只修影响机制、量级、主要资源/计数及真正可行性的缺陷；次要未知用可见保守端口块/模型条件/局限。停止逐管完善和反复不必要全量构建，已接受MRAM不重开。NOR直接收敛三点，PCM/FeRAM用已有实测HV I/C与明确保守预算完成，GC保关键调度、FeNOR/NAND用有物理依据的紧凑模型。最终一次集成/分组独立复跑与表图仍必须完成，不因放宽严谨度编造结果或忽略已知失败。


## D029 · P2 · NOR内部验收

接受B组`reviews/p2_nor2d`的PASS_conditional_model_scope，最终计算快照f08958add106ed192955b380b84e0693ea17d085739b6c368d7892cff3010fc8。独立三次新构建、原W25Q P/E资料、16页/1扇区/33720 SPI bits/51事务/6930求值周期已核。ESF1读状态与商品P/E引擎是明确条件性转用；4pF/BL资源与本地数字精度条件保留。optimistic/reference相同点属真实结果，不调整数据使圆图好看。P5最终包仍统一绑定；不再追加微小器件误差门。


## D030 · 资源收敛 · NAND owner移交

总览脚本已实际预演，integrator当前有实现容量。为落实D028时间/token约束，将NAND后续案例生产从B移交integrator，B集中FeNOR与A组案例轻量review，A继续PCM/FeRAM并独立审GC/NAND/FeNOR。移交等待B完成当前原子写入并发短handoff，明确停止写后integrator接管cases/nand3d；任何时点单一owner。公共代码/最终集成/制图仍integrator唯一owner。NAND审查A未参与生产，此调整不削弱独立性、不跳过case。

D030执行确认：B已落`cases/nand3d/HANDOFF_TO_INTEGRATOR.md`并明确停止NAND写入，integrator正式接管；PDF未取得全文的情况如实标注，官网已核参数与未核部分分列。


## D031 · P3 · GC04内部验收

接受A组`reviews/p3_gc04` PASS_conditional_model_scope，绑定095f2d8a8fe534039a0fe5fb26b003def10e1c62ef10ff16162cfb9203fb6fd0。最终包一次3fresh与独立整数tick维护重建、16384cells/256SAR/128差码/1.024nF/Xsum主要资源一致，无影响量级阻断。保留volatile、K64N16新架构、Q4近似、FF80C保持/未标温测量写转用条件；51.4µs首单不是124.289µs长期resident间隔。三点正式采用含维护rho/tau，raw另列。大宏/300µs政策失败留档，不重开已接受细节。


## D032 · P5 · 最终复跑去重

落实D028：final all统一生产仍在新目录全量运行最终配置；最终独立审查汇集每例已经完成的新源码/新构建/新运行三点，并逐项绑定最终计算依赖与输入hash。相关hash完全未变时无需仅因阶段名P5再重复一次同样构建；最终21点每点仍必须有真实独立fresh run、独立主计数与最终hash匹配证据。公共或案例计算修改只重跑受影响点，不沿用修前PASS。全包包含其他新增案例/报告导致archivehash变化不等于已审case计算变化。A/B最终新增hash/结果/图表资格核对，不重复已通过局部物理研究。


## D033 · P1 · PCM全HV新身份内部验收

接受B组`reviews/p1_pcm_hv` PASS_conditional_model_scope，最终计算SHA6ff0664ad5deb7a7a3f432420a003251b4b2417a6399925d6f8d7286c03ffb2d。三情景独立fresh、16384HV访问/128SA/16热写lane/1024每方向批/128行readback/256比较/2048MAC及主要端口边界通过。rho .246238193、tau2.561210564/2.195677121/1.135795261 MB/s。保留TiSbTe端态窗口/材料波形可在3.983V compliance交付、35mV裕量等条件，不宣称良率/漂移或PDN签核。旧低压身份与其partial review完整保留，不追溯通过。


## D034 · P2独立复核 · FeNOR实际目标选择资源

A轻量审查发现128bit/row编程声明与native program_lanes=16不一致，这是主要资源计数缺陷，不能作为次要模型误差忽略。B只将该例实际目标MUX配置改128（既有128targethold与HV端口），重算其mask/control负载与可行周期，重跑本例最终3及A独立3。旧0c37bc03…候选不进入正式资格；其他案例/共享代码不动，符合D028/D032。无需扩展新的微观时序优化。


## D035 · P3 · FeRAM内部验收

接受B组`reviews/p3_feram` PASS_conditional_model_scope，绑定090bd4723ad86566350ac6dc4e9721a5d85af76b7fc4d052748c0e50bcd445fb。一次独立3fresh、源极化读/破坏恢复/14ns完整写包含边界、250.138fF电荷/另面积量级、128真通路×32行恢复/外写、512次MAC与局部HV电流条件通过。rho .238975594/.238633429/.236937195，tau37.5146542/36.9942197/34.5945946 MB/s。100ns额外dwell与完整write/restore原语是有边界参考政策，不称快极化动力学/硅精度或PDN签核。A组三例生产全部接受。


## D036 · P2 · FeNOR修后内部验收

接受A组`reviews/p2_fenor3d/review.json` PASS_conditional_model_scope，绑定81880c5e60e9cb036319b4643cf859694da84f3d04d0f621fd3e2e51758038fc，无未关闭主问题。修后独立3fresh及16384cell/单活跃层/2048SA+reference/4096tile/128bit实际program、128RESET+128PROGRAM、256半层verify、1194/1666cycles通过。D034的16bit目标资源错误已关闭，旧r1不追溯通过。rho .536013400/tau6.146458583三点真实相同；±50mV有限工程状态范围被固定数字/脉冲服务遮蔽，图只点不制造圆，非统计材料界。


## D037 · P4 · NAND有限近似模型内部验收

接受A组`reviews/p4_nand3d/review.json` PASS_conditional_model_scope，绑定f7b131fd97fbcc77a5d835066421d2f589f50d2007df661ec0b830ae9999080d，无主阻断。独立3fresh、75747个500ns stream周期、12,505,770非P/E resident周期+6144页（384参考）/64erase、65536标量编码及每情景1024个真实ADC整数码路径一致，无真值修正。三点rho .121668185，tau .135528000/.135528000/.108815211 MB/s。

仅接受有限标定域近似Q4服务：nominal残差2.8846%、isolated=0、极端pass背景+44.2308/−21.6346%显著保留，不能等同精确INT8/ENOB。128AMP典型10.56W/压力14.72W及跨SLC完整P/E转用条件公开，不是原低功耗NAND宏复现。七例21点全部为内部接受的条件模型服务点；P5表图/导出最终核对仍须完成。


## D038 · P5 · 最终快照、总表与图内部验收

接受B组`reviews/p5_overview` PASS_overview_tables_figures_conditional_model_scope。21配置/7例与30配置/10类、最终计算/输入/review精确绑定、CSV/JSON、十进制MB/s/RI/U、GC单次/raw/effective区分通过。V4九点逐值/ID/温度相同且原3关键文件hash未变，旧NVM10条独立背景。四张最终PNG实际目视、SVG每decade等比例/圆含全部sample与reference且不截边、退化与重合/标签/图例通过。只标签排布调整，坐标未改。无需再重跑或排图；integrator完成白名单/导航/报告后停止V5。


## D039 · V5结束 · 交付与保护关闭

integrator已完成最终白名单43项/2,411,985B、独立计算包82文件/928,081B、21点精确review绑定、V5七例及V4只读九点合并的30配置表图、旧NVM10条背景、报告与导航。Supervisor抽查最终报告/图、binding/保护清单和git diff：21/21无pending、21与30点表无失败；README/STATUS只追加14行，旧前缀保留；HEAD仍216d3f8…，保护历史未改、六锁定上游clean、无第三方大源码/缓存/二进制同步导出。两处.DS_Store范围外保留，未git add/commit/push。

七例所有主任务与独立review完成，全部点为明确条件模型而非硅签核。A/B/integrator均确认本轮职责完成并停止新增运行/修改。Supervisor完成治理并停止Step4 V5，下一动作是用户和外部ChatGPT审阅，不自动扩新器件/workload/论文。
