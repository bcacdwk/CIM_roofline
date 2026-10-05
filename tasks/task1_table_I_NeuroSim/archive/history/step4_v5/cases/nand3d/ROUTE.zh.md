# 3D NAND P0 路线卡（2026-10-05）

**拟保留 split-sign/base-4 SLC SGVC、BL输入／block共享SL求和。已有证据足以锁定映射与读DC量级，尚不足以独立预测完整string动态；正式reference未闭合。已实际检查两条补充公开模型路线，并运行可辨识性／映射探针。**

- **映射／端口**：K4608×N240 signed INT8；64 block×32 WL×3 SSL×13824 BL；30数据WL+2参考WL。4个base-4位组×正负两bank，三BL复制输入、三SSL按LSB一次/MSB两次表示权重；72物理cell/INT8权重。每次1152项、两输入符号mask，group最密20.736μA；64 SL通路和ADC是明确资源。完整覆盖含64 erase、5760数据page+384参考page（6144页），1728B物理页口、逐行9bit幅值/符号暂存和校准，不能免费预擦除。
- **直接证据**：NAND-05 pp1–3 Fig6实测16层64Gb SGVC、约3nm poly-Si，VG=1V/VBL=0.2V/Vpass=4.5V；ON均值2nA、σ0.3nA、OFF<0.5pA；图给Id–Vg平台，没给Id–Vds或瞬态。NAND-04 pp2–3是32层模型，BL pitch40nm、SSL pitch0.75μm、block553×2.25μm、64block BL长144μm、SL约16pF；p7称修改BSIM拟合原实验，未公开参数表/netlist。**该文称来源芯片32层，而被引05原文明示16层；32层应列模型组织延伸，不能说实测32层同器件。**
- **紧凑前端计划**：选中WL状态相关电流源/平滑MOS网络，串联31个pass段、SSL/GSL及沟道，显式VBL/VSL compliance与节点电容；SL需要电压钳位/跨阻或电流积分接收器，连接锁定NeuroSim的BL选择、译码、感测/ADC和数字归约。2nA/0.2V=100MΩ仅工作点V/I，不提供gds，不能把32层展开成并联RRAM或TSV。高压4.5V read-pass及约20V program须另有真实端口/驱动来源，低压LevelShifter不能承担完整供电。
- **已经尝试的补路**：① SNU-HPCS/3D-FPIM `bd17a3a3c7a6a2ef98beb7a5379e2110f94df706`：选取README、SubArray、Calculate.py和小配置查读，确有基于几何的WL/BL/string/SSL寄生式；但Samsung64层圆柱macaroni参数模板全是FIXME，其PIM为50nA电流＋时间编码/积分，不能移植其完整周期到SGVC。可借公式结构，须补适用几何。② 2025 APS DOI10.7498/aps.74.20250891及作者仓库：160nA产品级、SL分区，表4直接输入7μs×block数、13μs BL等时隙，不闭合本例string动态；不采用它的更快/更慢总时隙。只下载必要2.2MB论文及约45KB代码到非同步区。
- **局部实际探针**：`identifiability_probe.py`独立枚举65536组signed标量，经三BL×三SSL编码全部相符，独立核算页/参考占用。两个正参数网络可匹配同一2nA读点，却因gds与sense反馈不同得到不同动态，证明单点I/V+16pF不足；探针数值只是不可辨识性反例，不是三情景。10bit/25μA名义ADC为12.207个2nA单元/LSB，稀疏单位和非对称抵消不能称精确INT8。
- **P/E外部原语**：NAND-06 SLC产品完整tPROG=300/600μs、tERASE=1/3.5ms，含内部pulse/verify/pump/recovery至ready；只作同厂异实现条件服务。其2048+64B页、64页block与本参考1728B/96page不相同，不能移植保证或按页大小缩时，也不再增加内部verify。05要求两状态write-verify，普通产品通过不等于2nA平台已标定。
- **范围／停点**：固定室温和资源，优先pass/状态图样与可辨识的sense负载族、完整P/E typ/max；未得DC输出斜率/端口C与独立动态检查前不发布rho。旧WL303ns、BL12ns@50%稀疏、SL530–750ns@max-bit仅对照；不能据同一时隙拟合RC再称独立验证。最小后续为适用SGVC端口I–V/C数据或公开完整模型/几何＋一种独立负载状态校验；可新建有明确模型身份的参考，但不得隐瞒该缺口。
