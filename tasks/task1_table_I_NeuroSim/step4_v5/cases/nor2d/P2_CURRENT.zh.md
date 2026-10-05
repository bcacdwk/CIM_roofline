**当前治理状态：B组独立三点PASS，supervisor D029内部accepted。下面运行/参数记录保留；“待审”字样只描述当时作者交付阶段。**

# NOR P2 当前快照

作者A组；公共后端仍由integrator唯一维护。已完成首个完整reference真实构建，尚未独立验收。最新作者运行：`/Users/shine/neurosim/runs/step4-v5/component-services/case-nor2d-nor2d-full-reference-r1-20261005`。

该候选Δ=1.386ms、TR=52.077656ms、ρ=.184704185MB/s、τ=.078651773MB/s、RI*=2.34837915、U*=37.5740664。下一步是关闭实际native TG关断泄漏初态、数值收敛/反事实、最终三点fresh构建和B组独立审查。当前不把这些候选直接标accepted。

K256×N16，32768物理二元位，16完整256B页、1完整4KiB扇区。64SA/2列组，8个25bit MAC，128bit权重行保持，256B输入寄存；完整P/E引擎另计256B页缓冲。源W25Q支持50MHz单bit SPI，所有Write Enable、opcode、24bit地址、全页数据、CS边界和完成状态均计量。tPP/tSE已包括内部pulse/verify/泵/返回，不再拆费。源商品完整引擎→ESF1新读阵列是条件性移植，不是目标芯片保证。

I–V由原图1.1/1.3V拟合，1.2V非拟合点误差−.154%。所有255未选行采用0.25V图点经单调性得到的150.5pA/支路上界。VD=.8..1V饱和延伸仍是有域紧凑模型。几何C来自公开物理关系和明确工程输入，不说ESF1实测C。

已经替换无资格的理想开关/1.3V代替1.2V方案：实际低rail NAND/INV+allWL-off EN，1V PMOS预充，真实互补TG参考及600k后内部节点(关断时靠真实R复位)，native W/Ion/Vth、有限N/P边沿、数据BL/SA两节点。没有采用原完整100/120/130ns读access。

原额外500fF读C在不利reference gate-charge上界下出现早期反极性约−22.8mV，已否定。当前固定额外4pF/BL，128个真实积分/读端口电容；actualsensedC约4.207pF。SA20mV+10mV剩余误差预算、独立±.2%预充和±1ns偏移仍是明确设计资格条件。源N/P全部不利gate charge分别作保守注入界，不依赖理想相消。reference 100.31ns达30mV；早期最差−7.352mV未越−10mV假锁存门，VD最小.8858V在域。native comparator是抽象threshold latch，非噪声/STA认证。

预充实际Ion偏置模型约92.79ns，预留完整200ns；其20mA供电条件下初始128路需求16.45mA。原生VSA的2/f明确拆成一次预充时钟和一次输出时钟：预充与外部RC取max，阈值发展由case网络替换，不把同一内部相位再收费。实际数字最小period158.17ns，200ns通过。

三个固定硬件bias政策为1.3/1.2/1.1V，前两点源typ P/E、后者源max。没有捏第三个P/E中值；最终读率可能被相同数字/clockslot主导而重合，必须保留完整中间量与点ID。
