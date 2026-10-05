# 3D NAND 独立轻量审查

结论：**PASS_conditional_model_scope，仅有限标定域近似Q4**。绑定最终计算SHA `f7b131fd97fbcc77a5d835066421d2f589f50d2007df661ec0b830ae9999080d`，一次新包/新native构建的三点与生产一致。Δ均37.8735ms，TR为8.160085/8.160085/10.163285s，ρ均.121668185MB/s，τ为.135528000/.135528000/.108815211MB/s。

独立从K4608×N240重建64block×32WL×3SSL×13824BL=84934656cell、每权重72cell、5760数据页＋384参考页=6144页、64次全erase；每页1728B，共10616832物理Byte。32个真实输入mask各读30 data WL，共960次64通道读。2 reference WL×4 group×3 level=24次校准，256对gain/offset真实存储。41472bit只是一行staging，48bit只是formatter packet；不是免费预装整矩阵。

独立得到75747个500ns stream周期；resident非P/E为12505770周期，再加6144个300/600µs完整program与64个1/3.5ms完整erase，直接得到上述TR。内部pulse/verify/pump/恢复已经属于P/E原语，未再收费。原Macronix文献页25/31/58核到2112B源page和时间值；目标1728B/96page block的转用是条件，不是目标SGVC保证。

实际码路径是固定参考校准、11步有符号串行运算与base-4/sign合并；65536组独立编码组合及每情景1024个整数ADC码算术检查通过。真值只出现在离线编码/误差核查，没有替换实际输出。**这些通过不代表精确INT8**：nominal dense残差2.8846%，孤立string的delta code为0，极端pass背景+44.2308%/−21.6346%均保留。不得与二元数字案例称等精度，也不得把10bit/Q4当ENOB。

String实际解selected/pass/GSL/SSL与内部节点；16层归一到2nA后，32层未重新归一。内部RC用局部微分导纳与几何C，不是饱和I的V/I。有限TIA/反相buffer的A0、GBW、slew和负载已进入计算，另一2×SL负载点另查。128个外部放大器是明显的混合前端代价：典型10.56W，悲观14.72W；厂家[原始数据表](https://www.analog.com/media/en/technical-documentation/data-sheets/62689f.pdf)的每放大器16.5/23mA支持该计量。它不是原集成低功耗NAND宏。

审查者未编写NAND string/TIA/mapping/runner，仅提供过通用公开HV源入口；已披露相关参与。没有要求修成高精度ADC、全器件TCAD或PCB签核。新run在 `p4/case-nand3d-reviewer-nand-{ref,opt,pess}-final-20261005`；`review.json`绑定源码/输入，`independent_counts.py/json`保留独立计数，`PE_source_check.json`保留原语核查。未发现会改变主数量级、资源或已声明精度身份的阻断。
